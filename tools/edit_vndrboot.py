import sys

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <vendor_boot.img>")
    sys.exit(1)

input_file = sys.argv[1]
output_file = "vendor_boot_prc.img"

patterns_to_find = {
    b"\x2E\x52\x4F\x57": b"\x2E\x50\x52\x43",  # .ROW -> .PRC
    b"\x49\x52\x4F\x57": b"\x49\x50\x52\x43"   # IROW -> IPRC
}

try:
    with open(input_file, "rb") as f:
        content = f.read()

    modified_content = content
    found_count = 0

    for target, replacement in patterns_to_find.items():
        count = modified_content.count(target)
        if count > 0:
            print(f"Found '{target.hex().upper()}' pattern {count} time(s). Replacing...")
            modified_content = modified_content.replace(target, replacement)
            found_count += count

    if found_count > 0:
        with open(output_file, "wb") as f_out:
            f_out.write(modified_content)
        print(f"\nPatch successful! Total {found_count} instance(s) replaced.")
        print(f"Saved as '{output_file}'")
    else:
        print("No target patterns found. No changes made.")

except FileNotFoundError:
    print(f"Error: File not found at '{input_file}'")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)