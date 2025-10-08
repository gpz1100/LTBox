# Android vendor_boot Patcher and vbmeta Resigner

## ⚠️ Disclaimer

**This project is for educational purposes ONLY.**

Modifying your device's boot images comes with significant risks, including the possibility of bricking your device. The author is not responsible for any damage that may occur.

**Use this at your own risk.**

This set of scripts automates the process of region code conversion for `vendor_boot.img` and re-signing the corresponding `vbmeta.img`. It also provides an option to patch the `vendor_boot.img` with **KernelSU Next** to enable root.

## Prerequisites

Before you begin, you must provide the following files from your device's stock firmware:

* `vendor_boot.img`
* `vbmeta.img`

Place these two files in the main directory alongside the scripts. All other dependencies (like Python, `magiskboot`, and signing keys) will be downloaded automatically.

## How to Use

1.  **Place Images:** Put your `vendor_boot.img` and `vbmeta.img` files into the root folder.
2.  **Install Dependencies:** Run the `install.bat` script first. This will download and set up all the necessary tools and keys.
3.  **Run the Script:**
    * Simply run `convert.bat`.
    * If you want to **add root** during the process, run `convert_with_root.bat` instead.
4.  **Flash the Images:** Once the script is finished, a new `vendor_boot.img` and a re-signed `vbmeta.img` will be ready in the output folder. You can now flash these to your device using `fastboot`.

## Script Descriptions

* **`install.bat`**: Checks for required tools and keys, and downloads them if they are missing.
* **`convert.bat`**: The main script. It handles the region code conversion and re-signs the `vbmeta.img` **without** adding root.
* **`convert_with_root.bat`**: An alternative to the main script. It first patches the `vendor_boot.img` with **KernelSU Next** and then runs the conversion and re-signing process.