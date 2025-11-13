import re
import shutil
import sys
from pathlib import Path
from typing import Dict, Optional, Any, Tuple, Union

from ..constants import *
from .. import utils

def _patch_vendor_boot_logic(content: bytes, lang: Optional[Dict[str, str]] = None, **kwargs: Any) -> Tuple[bytes, Dict[str, Any]]:
    lang = lang or {}
    patterns_row = {
        b"\x2E\x52\x4F\x57": b"\x2E\x50\x52\x43",
        b"\x49\x52\x4F\x57": b"\x49\x50\x52\x43"
    }
    patterns_prc = [b"\x2E\x50\x52\x43", b"\x49\x50\x52\x43"]
    
    modified_content = content
    found_row_count = 0

    for target, replacement in patterns_row.items():
        count = content.count(target)
        if count > 0:
            print(lang.get("img_vb_found_replace", f"Found '{target.hex().upper()}' pattern {count} time(s). Replacing...").format(pattern=target.hex().upper(), count=count))
            modified_content = modified_content.replace(target, replacement)
            found_row_count += count

    if found_row_count > 0:
        return modified_content, {'changed': True, 'message': lang.get("img_vb_replaced_total", f"Total {found_row_count} instance(s) replaced.").format(count=found_row_count)}
    
    found_prc = any(content.count(target) > 0 for target in patterns_prc)
    if found_prc:
        return content, {'changed': False, 'message': lang.get("img_vb_already_prc", ".PRC patterns found (Already patched).")}
    
    return content, {'changed': False, 'message': lang.get("img_vb_no_patterns", "No .ROW or .PRC patterns found.")}

def edit_vendor_boot(input_file_path: str, lang: Optional[Dict[str, str]] = None) -> None:
    input_file = Path(input_file_path)
    output_file = input_file.parent / "vendor_boot_prc.img"
    
    if not utils._process_binary_file(input_file, output_file, _patch_vendor_boot_logic, copy_if_unchanged=True, lang=lang):
        sys.exit(1)

def check_target_exists(target_code: str, lang: Optional[Dict[str, str]] = None) -> bool:
    lang = lang or {}
    target_bytes = f"{target_code.upper()}XX".encode('ascii')
    files_to_check = [BASE_DIR / "devinfo.img", BASE_DIR / "persist.img"]
    found = False
    
    for f in files_to_check:
        if not f.exists():
            continue
        try:
            content = f.read_bytes()
            if content.count(target_bytes) > 0:
                found = True
                break
        except Exception as e:
            print(lang.get("img_chk_err_read", f"[!] Error reading {f.name} for check: {e}").format(name=f.name, e=e), file=sys.stderr)
    return found

def detect_region_codes(lang: Optional[Dict[str, str]] = None) -> Dict[str, Optional[str]]:
    lang = lang or {}
    results: Dict[str, Optional[str]] = {}
    files_to_check = ["devinfo.img", "persist.img"]

    if not COUNTRY_CODES:
        print(lang.get("img_det_warn_empty", "[!] Warning: COUNTRY_CODES list is empty."), file=sys.stderr)
        return {f: None for f in files_to_check}

    for filename in files_to_check:
        file_path = BASE_DIR / filename
        results[filename] = None
        
        if not file_path.exists():
            continue
            
        try:
            content = file_path.read_bytes()
            for code, _ in COUNTRY_CODES.items():
                target_bytes = b'\x00\x00\x00' + f"{code.upper()}".encode('ascii') + b'XX\x00\x00\x00'
                if target_bytes in content:
                    results[filename] = code
                    break
        except Exception as e:
            print(lang.get("img_det_err_read", f"[!] Error reading {filename}: {e}").format(name=filename, e=e), file=sys.stderr)
            
    return results

def _patch_region_code_logic(content: bytes, lang: Optional[Dict[str, str]] = None, **kwargs: Any) -> Tuple[bytes, Dict[str, Any]]:
    lang = lang or {}
    current_code = kwargs.get('current_code')
    replacement_code = kwargs.get('replacement_code')
    
    if not current_code or not replacement_code:
        return content, {'changed': False, 'message': lang.get("img_code_invalid", "Invalid codes")}

    target_string = f"000000{current_code.upper()}XX000000"
    target_bytes = b'\x00\x00\x00' + f"{current_code.upper()}".encode('ascii') + b'XX\x00\x00\x00'
    
    replacement_string = f"000000{replacement_code.upper()}XX000000"
    replacement_bytes = b'\x00\x00\x00' + f"{replacement_code.upper()}".encode('ascii') + b'XX\x00\x00\x00'

    if target_bytes == replacement_bytes:
        return content, {'changed': False, 'message': lang.get("img_code_already", f"File is already '{replacement_code.upper()}'.").format(code=replacement_code.upper())}

    count = content.count(target_bytes)
    if count > 0:
        print(lang.get("img_code_replace", f"Found '{target_string}' pattern {count} time(s). Replacing with '{replacement_string}'...").format(target=target_string, count=count, replacement=replacement_string))
        modified_content = content.replace(target_bytes, replacement_bytes)
        return modified_content, {'changed': True, 'message': lang.get("img_code_replaced_total", f"Total {count} instance(s) replaced.").format(count=count), 'count': count}
    
    return content, {'changed': False, 'message': lang.get("img_code_not_found", f"Pattern '{target_string}' NOT found.").format(target=target_string)}

def patch_region_codes(replacement_code: str, target_map: Dict[str, Optional[str]], lang: Optional[Dict[str, str]] = None) -> int:
    lang = lang or {}
    if not replacement_code or len(replacement_code) != 2:
        print(lang.get("img_patch_code_err", f"[!] Error: Invalid replacement code '{replacement_code}'. Aborting.").format(code=replacement_code), file=sys.stderr)
        sys.exit(1)
        
    total_patched = 0
    files_to_output = {
        "devinfo.img": "devinfo_modified.img",
        "persist.img": "persist_modified.img"
    }

    print(lang.get("img_patch_start", f"[*] Starting patch process (New Region: {replacement_code})...").format(code=replacement_code))

    for filename, current_code in target_map.items():
        if filename not in files_to_output:
            continue
            
        input_file = BASE_DIR / filename
        output_file = BASE_DIR / files_to_output[filename]
        
        if not input_file.exists():
            continue
            
        print(lang.get("img_patch_processing", f"\n--- Processing '{input_file.name}' ---").format(name=input_file.name))
        
        if not current_code:
            print(lang.get("img_patch_skip", f"[*] No target code specified/detected for '{filename}'. Skipping.").format(name=filename))
            continue

        success = utils._process_binary_file(
            input_file, 
            output_file, 
            _patch_region_code_logic, 
            copy_if_unchanged=True,
            current_code=current_code, 
            replacement_code=replacement_code,
            lang=lang
        )
        
        if success:
             pass

    print(lang.get("img_patch_finish", f"\nPatching finished."))
    return total_patched