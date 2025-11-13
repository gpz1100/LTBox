import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, Optional, Union

from ..constants import *
from .. import utils, downloader

def patch_boot_with_root_algo(work_dir: Path, magiskboot_exe: Path, lang: Optional[Dict[str, str]] = None) -> Optional[Path]:
    lang = lang or {}
    original_cwd = Path.cwd()
    os.chdir(work_dir)
    
    patched_boot_path = BASE_DIR / "boot.root.img"
    
    try:
        print(lang.get("img_root_step1", "\n[1/8] Unpacking boot image..."))
        utils.run_command([str(magiskboot_exe), "unpack", "boot.img"])
        if not (work_dir / "kernel").exists():
            print(lang.get("img_root_unpack_fail", "[!] Failed to unpack boot.img. The image might be invalid."))
            return None
        print(lang.get("img_root_unpack_ok", "[+] Unpack successful."))

        print(lang.get("img_root_step2", "\n[2/8] Verifying kernel version..."))
        target_kernel_version = get_kernel_version("kernel", lang=lang)

        if not target_kernel_version:
             print(lang.get("img_root_kernel_ver_fail", "[!] Failed to get kernel version from 'kernel' file."))
             return None

        if not re.match(r"\d+\.\d+\.\d+", target_kernel_version):
             print(lang.get("img_root_kernel_invalid", f"[!] Invalid kernel version returned from script: '{target_kernel_version}'").format(ver=target_kernel_version))
             return None
        
        print(lang.get("img_root_target_ver", f"[+] Target kernel version for download: {target_kernel_version}").format(ver=target_kernel_version))

        kernel_image_path = downloader.get_gki_kernel(target_kernel_version, work_dir, lang=lang)

        print(lang.get("img_root_step5", "\n[5/8] Replacing original kernel with the new one..."))
        shutil.move(str(kernel_image_path), "kernel")
        print(lang.get("img_root_kernel_replaced", "[+] Kernel replaced."))

        print(lang.get("img_root_step6", "\n[6/8] Repacking boot image..."))
        utils.run_command([str(magiskboot_exe), "repack", "boot.img"])
        if not (work_dir / "new-boot.img").exists():
            print(lang.get("img_root_repack_fail", "[!] Failed to repack the boot image."))
            return None
        shutil.move("new-boot.img", patched_boot_path)
        print(lang.get("img_root_repack_ok", "[+] Repack successful."))

        downloader.download_ksu_apk(BASE_DIR, lang=lang)
        
        return patched_boot_path

    finally:
        os.chdir(original_cwd)
        if work_dir.exists():
            shutil.rmtree(work_dir)
        print(lang.get("img_root_cleanup", "\n--- Cleaning up ---"))

def get_kernel_version(file_path: Union[str, Path], lang: Optional[Dict[str, str]] = None) -> Optional[str]:
    lang = lang or {}
    kernel_file = Path(file_path)
    if not kernel_file.exists():
        print(lang.get("img_kv_err_not_found", f"Error: Kernel file not found at '{file_path}'").format(path=file_path), file=sys.stderr)
        return None

    try:
        content = kernel_file.read_bytes()
        potential_strings = re.findall(b'[ -~]{10,}', content)
        
        found_version = None
        for string_bytes in potential_strings:
            try:
                line = string_bytes.decode('ascii', errors='ignore')
                if 'Linux version ' in line:
                    base_version_match = re.search(r'(\d+\.\d+\.\d+)', line)
                    if base_version_match:
                        found_version = base_version_match.group(1)
                        print(lang.get("img_kv_found", f"Full kernel string found: {line.strip()}").format(line=line.strip()), file=sys.stderr)
                        break
            except UnicodeDecodeError:
                continue

        if found_version:
            return found_version
        else:
            print(lang.get("img_kv_err_parse", "Error: Could not find or parse 'Linux version' string in the kernel file."), file=sys.stderr)
            return None

    except Exception as e:
        print(lang.get("img_kv_err_unexpected", f"An unexpected error occurred: {e}").format(e=e), file=sys.stderr)
        return None