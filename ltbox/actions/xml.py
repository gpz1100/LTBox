import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..constants import *
from .. import utils
from ..crypto import decrypt_file

def _scan_and_decrypt_xmls(lang: Optional[Dict[str, str]] = None) -> List[Path]:
    lang = lang or {}
    OUTPUT_XML_DIR.mkdir(exist_ok=True)
    
    xmls = list(OUTPUT_XML_DIR.glob("rawprogram*.xml"))
    if not xmls:
        xmls = list(IMAGE_DIR.glob("rawprogram*.xml"))
    
    if not xmls:
        print(lang.get("act_xml_scan_x", "[*] No XML files found. Checking for .x files to decrypt..."))
        x_files = list(IMAGE_DIR.glob("*.x"))
        
        if x_files:
            print(lang.get("act_xml_found_x_count", "[*] Found {len} .x files. Decrypting...").format(len=len(x_files)))
            utils.check_dependencies(lang=lang) 
            for x_file in x_files:
                xml_name = x_file.stem + ".xml"
                out_path = OUTPUT_XML_DIR / xml_name
                if not out_path.exists():
                    print(lang.get("act_xml_decrypting", "  > Decrypting {name}...").format(name=x_file.name))
                    if decrypt_file(str(x_file), str(out_path), lang=lang):
                        xmls.append(out_path)
                    else:
                        print(lang.get("act_xml_decrypt_fail", "  [!] Failed to decrypt {name}").format(name=x_file.name))
        else:
            print(lang.get("act_xml_none_found", "[!] No .xml or .x files found in 'image' folder."))
            print(lang.get("act_xml_dump_req", "[!] Dump requires partition information from these files."))
            print(lang.get("act_xml_place_prompt", "    Please place firmware .xml or .x files into the 'image' folder."))
            return []
            
    return xmls

def _get_partition_params(target_label: str, xml_paths: List[Path], lang: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    lang = lang or {}
    for xml_path in xml_paths:
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            for prog in root.findall('program'):
                label = prog.get('label', '').lower()
                if label == target_label.lower():
                    return {
                        'lun': prog.get('physical_partition_number'),
                        'start_sector': prog.get('start_sector'),
                        'num_sectors': prog.get('num_partition_sectors'),
                        'filename': prog.get('filename', ''),
                        'source_xml': xml_path.name
                    }
        except Exception as e:
            print(lang.get("act_xml_parse_err", "[!] Error parsing {name}: {e}").format(name=xml_path.name, e=e))
            
    return None

def _ensure_params_or_fail(label: str, lang: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    lang = lang or {}
    xmls = _scan_and_decrypt_xmls(lang=lang)
    if not xmls:
        raise FileNotFoundError(lang.get("act_err_no_xml_dump", "No XML/.x files found for dump."))
        
    params = _get_partition_params(label, xmls, lang=lang)
    if not params:
        if label == "boot":
            params = _get_partition_params("boot_a", xmls, lang=lang)
            if not params:
                 params = _get_partition_params("boot_b", xmls, lang=lang)
                 
    if not params:
        print(lang.get("act_err_part_info_missing", "[!] Error: Could not find partition info for '{label}' in XMLs.").format(label=label))
        raise ValueError(lang.get("act_err_part_not_found", "Partition '{label}' not found in XMLs").format(label=label))
        
    return params

def _modify_xml_algo(wipe: int = 0, lang: Optional[Dict[str, str]] = None) -> None:
    lang = lang or {}
    def is_garbage_file(path: Path) -> bool:
        name = path.name.lower()
        stem = path.stem.lower()
        if stem == "rawprogram_unsparse0": return True
        if "wipe_partitions" in name or "blank_gpt" in name: return True
        return False

    if OUTPUT_XML_DIR.exists():
        shutil.rmtree(OUTPUT_XML_DIR)
    OUTPUT_XML_DIR.mkdir(parents=True, exist_ok=True)

    print(lang.get("img_xml_scan", "[*] Scanning files in 'image' folder..."))
    
    x_files = list(IMAGE_DIR.glob("*.x"))
    xml_files = list(IMAGE_DIR.glob("*.xml"))
    
    processed_files = False

    if x_files:
        print(lang.get("img_xml_found_x", f"[*] Found {len(x_files)} .x files. Decrypting to '{OUTPUT_XML_DIR.name}'...").format(count=len(x_files), dir=OUTPUT_XML_DIR.name))
        for file in x_files:
            out_file = OUTPUT_XML_DIR / file.with_suffix('.xml').name
            try:
                if decrypt_file(str(file), str(out_file), lang=lang):
                    print(lang.get("img_xml_decrypt_ok", f"  > Decrypted: {file.name} -> {out_file.name}").format(src=file.name, dst=out_file.name))
                    processed_files = True
                else:
                    print(lang.get("img_xml_decrypt_fail", f"  [!] Decryption failed for {file.name}").format(name=file.name))
            except Exception as e:
                print(lang.get("img_xml_decrypt_err", f"  [!] Error decrypting {file.name}: {e}").format(name=file.name, e=e), file=sys.stderr)

    if xml_files:
        print(lang.get("img_xml_found_xml", f"[*] Found {len(xml_files)} .xml files. Moving to '{OUTPUT_XML_DIR.name}'...").format(count=len(xml_files), dir=OUTPUT_XML_DIR.name))
        for file in xml_files:
            out_file = OUTPUT_XML_DIR / file.name
            try:
                if out_file.exists():
                    out_file.unlink()
                shutil.move(str(file), str(out_file))
                print(lang.get("img_xml_moved", f"  > Moved: {file.name}").format(name=file.name))
                processed_files = True
            except Exception as e:
                print(lang.get("img_xml_move_err", f"  [!] Error moving {file.name}: {e}").format(name=file.name, e=e), file=sys.stderr)

    if not processed_files:
        print(lang.get("img_xml_no_files", f"[!] No usable firmware files (.x or .xml) found in '{IMAGE_DIR.name}'. Aborting.").format(dir=IMAGE_DIR.name))
        shutil.rmtree(OUTPUT_XML_DIR)
        raise FileNotFoundError(f"No .x or .xml files in {IMAGE_DIR.name}")

    rawprogram4 = OUTPUT_XML_DIR / "rawprogram4.xml"
    rawprogram_unsparse4 = OUTPUT_XML_DIR / "rawprogram_unsparse4.xml"
    
    if not rawprogram4.exists() and rawprogram_unsparse4.exists():
        print(lang.get("img_xml_copy_raw4", "[*] 'rawprogram4.xml' not found. Copying 'rawprogram_unsparse4.xml'..."))
        shutil.copy(rawprogram_unsparse4, rawprogram4)

    print(lang.get("img_xml_mod_raw", "\n[*] Modifying 'rawprogram_save_persist_unsparse0.xml'..."))
    
    rawprogram_save = OUTPUT_XML_DIR / "rawprogram_save_persist_unsparse0.xml"

    if not rawprogram_save.exists():
        rawprogram_fallback = OUTPUT_XML_DIR / "rawprogram_unsparse0-half.xml"
        
        if rawprogram_fallback.exists():
            print(lang.get("img_xml_rename_fallback", f"[*] '{rawprogram_save.name}' not found. Renaming '{rawprogram_fallback.name}'...").format(target=rawprogram_save.name, src=rawprogram_fallback.name))
            try:
                rawprogram_fallback.rename(rawprogram_save)
            except OSError as e:
                print(lang.get("img_xml_rename_err", f"[!] Failed to rename fallback file: {e}").format(e=e), file=sys.stderr)
                raise
        else:
            print(lang.get("img_xml_critical_missing", f"[!] Critical Error: Neither '{rawprogram_save.name}' nor '{rawprogram_fallback.name}' found.").format(f1=rawprogram_save.name, f2=rawprogram_fallback.name))
            print(lang.get("img_xml_abort_mod", "[!] Cannot proceed with Wipe/No Wipe modification. Aborting."))
            raise FileNotFoundError(f"Critical XML file missing: {rawprogram_save.name} or {rawprogram_fallback.name}")

    try:
        with open(rawprogram_save, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if wipe == 0:
            print(lang.get("img_xml_nowipe", "  > [NO WIPE] Removing metadata and userdata entries..."))
            for i in range(1, 11):
                content = content.replace(f'filename="metadata_{i}.img"', '')
            for i in range(1, 21):
                content = content.replace(f'filename="userdata_{i}.img"', '')
        else:
            print(lang.get("img_xml_wipe", "  > [WIPE] Skipping metadata and userdata removal."))
            
        with open(rawprogram_save, 'w', encoding='utf-8') as f:
            f.write(content)
        print(lang.get("img_xml_patch_ok", "  > Patched successfully."))
    except Exception as e:
        print(lang.get("img_xml_patch_err", f"[!] Error patching: {e}").format(e=e), file=sys.stderr)
        raise

    print(lang.get("img_xml_cleanup", "\n[*] Cleaning up unnecessary files in output folder..."))
    
    files_to_delete = []
    for f in OUTPUT_XML_DIR.glob("*.xml"):
        if is_garbage_file(f):
            files_to_delete.append(f)

    if files_to_delete:
        for f in files_to_delete:
            try:
                f.unlink()
                print(lang.get("img_xml_deleted", f"  > Deleted: {f.name}").format(name=f.name))
            except OSError as e:
                print(lang.get("img_xml_del_err", f"  [!] Failed to delete {f.name}: {e}").format(name=f.name, e=e))
    else:
        print(lang.get("img_xml_no_del", "  > No files to delete."))

    print(lang.get("img_xml_complete", f"[+] XML processing complete. All files are in '{OUTPUT_XML_DIR.name}'.").format(dir=OUTPUT_XML_DIR.name))


def modify_xml(wipe: int = 0, skip_dp: bool = False, lang: Optional[Dict[str, str]] = None) -> None:
    lang = lang or {}
    print(lang.get("act_start_xml_mod", "--- Starting XML Modification Process ---"))
    
    print(lang.get("act_wait_image", "--- Waiting for 'image' folder ---"))
    prompt = lang.get("act_prompt_image", 
        "[STEP 1] Please copy the entire 'image' folder from your\n"
        "         unpacked Lenovo RSA firmware into the main directory."
    )
    utils.wait_for_directory(IMAGE_DIR, prompt, lang=lang)

    if OUTPUT_XML_DIR.exists():
        shutil.rmtree(OUTPUT_XML_DIR)
    OUTPUT_XML_DIR.mkdir(exist_ok=True)

    with utils.temporary_workspace(WORKING_DIR):
        print(lang.get("act_create_temp", "\n[*] Created temporary '{dir}' folder.").format(dir=WORKING_DIR.name))
        try:
            _modify_xml_algo(wipe=wipe, lang=lang)

            if not skip_dp:
                print(lang.get("act_create_write_xml", "\n[*] Creating custom write XMLs for devinfo/persist..."))

                src_persist_xml = OUTPUT_XML_DIR / "rawprogram_save_persist_unsparse0.xml"
                dest_persist_xml = OUTPUT_XML_DIR / "rawprogram_write_persist_unsparse0.xml"
                
                if src_persist_xml.exists():
                    try:
                        content = src_persist_xml.read_text(encoding='utf-8')
                        
                        content = re.sub(
                            r'(<program[^>]*\blabel="persist"[^>]*filename=")[^"]*(".*/>)',
                            r'\1persist.img\2',
                            content,
                            flags=re.IGNORECASE
                        )
                        content = re.sub(
                            r'(<program[^>]*filename=")[^"]*("[^>]*\blabel="persist"[^>]*/>)',
                            r'\1persist.img\2',
                            content,
                            flags=re.IGNORECASE
                        )
                        
                        dest_persist_xml.write_text(content, encoding='utf-8')
                        print(lang.get("act_created_persist_xml", "[+] Created '{name}' in '{parent}'.").format(name=dest_persist_xml.name, parent=dest_persist_xml.parent.name))
                    except Exception as e:
                        print(lang.get("act_err_create_persist_xml", "[!] Failed to create '{name}': {e}").format(name=dest_persist_xml.name, e=e), file=sys.stderr)
                else:
                    print(lang.get("act_warn_persist_xml_missing", "[!] Warning: '{name}' not found. Cannot create persist write XML.").format(name=src_persist_xml.name))

                src_devinfo_xml = OUTPUT_XML_DIR / "rawprogram4.xml"
                dest_devinfo_xml = OUTPUT_XML_DIR / "rawprogram4_write_devinfo.xml"
                
                if src_devinfo_xml.exists():
                    try:
                        content = src_devinfo_xml.read_text(encoding='utf-8')

                        content = re.sub(
                            r'(<program[^>]*\blabel="devinfo"[^>]*filename=")[^"]*(".*/>)',
                            r'\1devinfo.img\2',
                            content,
                            flags=re.IGNORECASE
                        )
                        content = re.sub(
                            r'(<program[^>]*filename=")[^"]*("[^>]*\blabel="devinfo"[^>]*/>)',
                            r'\1devinfo.img\2',
                            content,
                            flags=re.IGNORECASE
                        )
                        
                        dest_devinfo_xml.write_text(content, encoding='utf-8')
                        print(lang.get("act_created_devinfo_xml", "[+] Created '{name}' in '{parent}'.").format(name=dest_devinfo_xml.name, parent=dest_devinfo_xml.parent.name))
                    except Exception as e:
                        print(lang.get("act_err_create_devinfo_xml", "[!] Failed to create '{name}': {e}").format(name=dest_devinfo_xml.name, e=e), file=sys.stderr)
                else:
                    print(lang.get("act_warn_devinfo_xml_missing", "[!] Warning: '{name}' not found. Cannot create devinfo write XML.").format(name=src_devinfo_xml.name))

        except Exception as e:
            print(lang.get("act_err_xml_mod", "[!] Error during XML modification: {e}").format(e=e), file=sys.stderr)
            raise
        
        print(lang.get("act_clean_temp", "[*] Cleaned up temporary '{dir}' folder.").format(dir=WORKING_DIR.name))
    
    print("\n" + "=" * 61)
    print(lang.get("act_success", "  SUCCESS!"))
    print(lang.get("act_xml_ready", "  Modified XML files are ready in the '{dir}'.").format(dir=OUTPUT_XML_DIR.name))
    print(lang.get("act_xml_next_step", "  You can now run 'Flash EDL' (Menu 10)."))
    print("=" * 61)