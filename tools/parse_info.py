import sys
import subprocess
import re

def parse_vbmeta_info(avbtool_path, vbmeta_img_path):
    try:
        python_executable = sys.executable
        process = subprocess.Popen(
            [python_executable, avbtool_path, "info_image", "--image", vbmeta_img_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            return None, None

        pub_key = None
        algorithm = None

        pub_key_match = re.search(r"Public key \(sha1\):\s*([0-9a-fA-F]+)", stdout)
        if pub_key_match:
            pub_key = pub_key_match.group(1)

        algorithm_match = re.search(r"Algorithm:\s*(\w+)", stdout)
        if algorithm_match:
            algorithm = algorithm_match.group(1)

        return pub_key, algorithm
    except Exception:
        return None, None

def parse_footer_info(avbtool_path, vendor_boot_img):
    try:
        python_executable = sys.executable
        process = subprocess.Popen(
            [python_executable, avbtool_path, "info_image", "--image", vendor_boot_img],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            return None, None, None, None

        img_size_match = re.search(r"Image size:\s*(\d+)\s*bytes", stdout)
        salt_match = re.search(r"Salt:\s*([0-9a-fA-F]+)", stdout)
        prop_match = re.search(r"Prop: com.android.build.vendor_boot.fingerprint -> '([^']+)'", stdout)

        img_size = img_size_match.group(1) if img_size_match else None
        salt = salt_match.group(1) if salt_match else None
        prop_val = prop_match.group(1) if prop_match else None
        prop_key = "com.android.build.vendor_boot.fingerprint" if prop_match else None

        return img_size, salt, prop_key, prop_val
    except Exception:
        return None, None, None, None

def main():
    if len(sys.argv) < 4:
        return 1

    vendor_boot_img = sys.argv[1]
    py_avbtool_path = sys.argv[2]
    vbmeta_img_path = sys.argv[3]

    pub_key, algorithm = parse_vbmeta_info(py_avbtool_path, vbmeta_img_path)
    if pub_key:
        print(f"PUBLIC_KEY={pub_key}")
    if algorithm:
        print(f"ALGORITHM={algorithm}")

    img_size, salt, prop_key, prop_val = parse_footer_info(py_avbtool_path, vendor_boot_img)
    if img_size:
        print(f"IMG_SIZE={img_size}")
    if salt:
        print(f"SALT={salt}")
    if prop_key:
        print(f"PROP_KEY={prop_key}")
    if prop_val:
        print(f"PROP_VAL='{prop_val}'")

    return 0

if __name__ == "__main__":
    sys.exit(main())