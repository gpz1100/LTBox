import re
import shutil
import sys
from pathlib import Path
from typing import Dict, Optional, Any, Tuple, Union

from .. import constants as const
from .. import utils
from .. import constants as const
from ..i18n import get_string

def _patch_vendor_boot_logic(mm: Any, **kwargs: Any) -> Dict[str, Any]:
    patterns_row = {
        const.ROW_PATTERN_DOT: const.PRC_PATTERN_DOT,
        const.ROW_PATTERN_I: const.PRC_PATTERN_I
    }
    patterns_prc = [const.PRC_PATTERN_DOT, const.PRC_PATTERN_I]
    
    found_row_count = 0

    for target, replacement in patterns_row.items():
        start = 0
        while True:
            idx = mm.find(target, start)
            if idx == -1:
                break
            
            mm[idx:idx+len(target)] = replacement
            found_row_count += 1
            start = idx + len(target)

    if found_row_count > 0:
        print(get_string("img_vb_found_replace").format(pattern="ROW->PRC", count=found_row_count))
        return {'changed': True, 'message': get_string("img_vb_replaced_total").format(count=found_row_count)}

    found_prc = False
    for target in patterns_prc:
        if mm.find(target) != -1:
            found_prc = True
            break
            
    if found_prc:
        return {'changed': False, 'message': get_string("img_vb_already_prc")}
    
    return {'changed': False, 'message': get_string("img_vb_no_patterns")}

def edit_vendor_boot(input_file_path: str) -> None:
    input_file = Path(input_file_path)
    output_file = input_file.parent / "vendor_boot_prc.img"
    
    if not utils._process_binary_file(input_file, output_file, _patch_vendor_boot_logic, copy_if_unchanged=True):
        raise RuntimeError("Failed to process vendor_boot binary.")

def detect_region_codes() -> Dict[str, Optional[str]]:
    results: Dict[str, Optional[str]] = {}
    files_to_check = ["devinfo.img", "persist.img"]

    if not const.COUNTRY_CODES:
        print(get_string("img_det_warn_empty"), file=sys.stderr)
        return {f: None for f in files_to_check}

    for filename in files_to_check:
        file_path = const.BASE_DIR / filename
        results[filename] = None
        
        if not file_path.exists():
            continue
            
        try:
            content = file_path.read_bytes()
            for code, _ in const.COUNTRY_CODES.items():
                target_bytes = b'\x00\x00\x00' + f"{code.upper()}".encode('ascii') + b'XX\x00\x00\x00'
                if target_bytes in content:
                    results[filename] = code
                    break
        except Exception as e:
            print(get_string("img_det_err_read").format(name=filename, e=e), file=sys.stderr)
            
    return results

def _patch_region_code_logic(mm: Any, **kwargs: Any) -> Dict[str, Any]:
    current_code = kwargs.get('current_code')
    replacement_code = kwargs.get('replacement_code')
    
    if not current_code or not replacement_code:
        return {'changed': False, 'message': get_string("img_code_invalid")}

    target_string = f"000000{current_code.upper()}XX000000"
    target_bytes = b'\x00\x00\x00' + f"{current_code.upper()}".encode('ascii') + b'XX\x00\x00\x00'
    
    replacement_string = f"000000{replacement_code.upper()}XX000000"
    replacement_bytes = b'\x00\x00\x00' + f"{replacement_code.upper()}".encode('ascii') + b'XX\x00\x00\x00'

    if target_bytes == replacement_bytes:
        return {'changed': False, 'message': get_string("img_code_already").format(code=replacement_code.upper())}

    count = 0
    start = 0
    while True:
        idx = mm.find(target_bytes, start)
        if idx == -1:
            break
        mm[idx:idx+len(target_bytes)] = replacement_bytes
        count += 1
        start = idx + len(target_bytes)

    if count > 0:
        print(get_string("img_code_replace").format(target=target_string, count=count, replacement=replacement_string))
        return {'changed': True, 'message': get_string("img_code_replaced_total").format(count=count), 'count': count}
    
    return {'changed': False, 'message': get_string("img_code_not_found").format(target=target_string)}

def patch_region_codes(replacement_code: str, target_map: Dict[str, Optional[str]]) -> int:
    if not replacement_code or len(replacement_code) != 2:
        msg = get_string("img_patch_code_err").format(code=replacement_code)
        print(msg, file=sys.stderr)
        raise RuntimeError(msg)
        
    total_patched = 0
    files_to_output = {
        "devinfo.img": "devinfo_modified.img",
        "persist.img": "persist_modified.img"
    }

    print(get_string("img_patch_start").format(code=replacement_code))

    for filename, current_code in target_map.items():
        if filename not in files_to_output:
            continue
            
        input_file = const.BASE_DIR / filename
        output_file = const.BASE_DIR / files_to_output[filename]
        
        if not input_file.exists():
            continue
            
        print(get_string("img_patch_processing").format(name=input_file.name))
        
        if not current_code:
            print(get_string("img_patch_skip").format(name=filename))
            continue

        success = utils._process_binary_file(
            input_file, 
            output_file, 
            _patch_region_code_logic, 
            copy_if_unchanged=True,
            current_code=current_code, 
            replacement_code=replacement_code
        )
        
        if success:
             total_patched += 1

    print(get_string("img_patch_finish"))
    return total_patched