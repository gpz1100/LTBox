# LTBox

## ⚠️ Important: Disclaimer

**This project is for educational purposes ONLY.**

Modifying your device's boot images carries significant risks, including but not limited to, bricking your device, data loss, or voiding your warranty. The author **assumes no liability** and is not responsible for any **damage or consequence** that may occur to **your device or anyone else's device** from using these scripts.

**You are solely responsible for any consequences. Use at your own absolute risk.**

---

## 1. Core Vulnerability & Overview

This toolkit exploits a security vulnerability found in certain Lenovo Android tablets. These devices have firmware signed with publicly available **AOSP (Android Open Source Project) test keys**.

Because of this vulnerability, the device's bootloader trusts and boots any image signed with these common test keys, even if the bootloader is **locked**.

This toolkit is an all-in-one collection of scripts that leverages this flaw to perform advanced modifications on a device with a locked bootloader.

### Target Models

* Lenovo Legion Y700 (2nd, 3rd, 4th Gen)
* Lenovo Tab Plus AI (AKA Yoga Pad Pro AI)
* Lenovo Xiaoxin Pad Pro GT

*...Other recent Lenovo devices (released in 2024 or later with Qualcomm chipsets) may also be vulnerable.*

## 2. Toolkit Purpose & Features

This toolkit provides an all-in-one solution for the following tasks **without unlocking the bootloader**:

1.  **Region Conversion (PRC → ROW)**
    * Converts the region code in `vendor_boot.img` to allow flashing a global (ROW) ROM on a Chinese (PRC) model.
    * Re-makes the `vbmeta.img` with the AOSP test keys to validate the modified `vendor_boot`.
2.  **Rooting**
    * Patches the stock `boot.img` by replacing the original kernel with [one that includes KernelSU](https://github.com/WildKernels/GKI_KernelSU_SUSFS).
    * Re-signs the patched `boot.img` with AOSP test keys.
3.  **Region Code Reset**
    * Modifies byte patterns in `devinfo.img` and `persist.img` to reset region-lock settings.
4.  **EDL Partition Dump/Write**
    * Dumps the `devinfo` and `persist` partitions directly from the device to the `backup` folder.
    * Flashes the patched `devinfo.img` and `persist.img` from the `output_dp` folder to the device.
5.  **Anti-Rollback (ARB) Bypass**
    * Dumps current firmware via EDL to check rollback indices.
    * Compares them against new firmware images provided by the user.
    * Patches the new firmware (e.g., `boot.img`, `vbmeta_system.img`) to match the device's *current* (higher) index, allowing a downgrade.
6.  **Full Firmware Flashing**
    * Decrypts and patches Lenovo RSA firmware XML files (`*.x` -> `*.xml`).
    * Automates the entire process of converting, patching, and flashing a full ROW firmware, including `devinfo`/`persist` and Anti-Rollback patches.

## 3. Prerequisites

Before you begin, place the required files into the correct folders. The script will guide you if files are missing.

* **For ALL EDL Operations (Menu 1, 2, 4, 6, 8, 10):**
    * The EDL loader file (`xbl_s_devprg_ns.melf`) **MUST** be placed in the `image` folder.

* **For `Patch & Flash ROW ROM` (Main Menu 1) or `Modify XML` (Advanced 9):**
    * You must copy the **entire `image` folder** from your unpacked Lenovo RSA firmware (the one containing `*.x` files, `*.img` files, etc.) into the LTBox root directory.
    * The script will prompt you for this folder. It is typically found in `C:\ProgramData\RSA\Download\RomFiles\[Firmware_Name]\`.

* **For `Convert ROM` (Advanced 1) or `Create Rooted boot.img` (Advanced 5):**
    * Place the required source `.img` files (e.g., `vendor_boot.img`, `vbmeta.img`, `boot.img`) into the `image` folder.

* **For `devinfo/persist` patching (Advanced 2, 3):**
    * **Menu 2 (Dump):** Dumps `devinfo.img` and `persist.img` *to* the `backup` folder.
    * **Menu 3 (Patch):** Reads `devinfo.img` and `persist.img` *from* the `backup` folder, and saves patched versions to `output_dp`.

* **For `Anti-Rollback` (Advanced 6, 7):**
    * These tools require the **new (downgrade)** firmware's `boot.img` and `vbmeta_system.img` to be in the `image` folder for comparison.
    * **Menu 6 (Read):** Will automatically dump your *current* device's firmware to `input_current` to perform the comparison.

## 4. How to Use

1.  **Place Files:** Put the necessary files (especially the `image` folder and/or EDL loader) into the correct location as described in **Section 3**.
2.  **Run the Script:** Double-click `start.bat`.
3.  **Select Task:** Choose an option from the menu.
    * **Menu 1** is the fully automated process.
    * **Menu 2** opens the advanced menu for individual steps.
4.  **Get Results:** After a script finishes, the modified images will be saved in a corresponding `output*` folder (e.g., `output`, `output_root`, `output_dp`, `output_anti_rollback`).
5.  **Flash the Images:** The `patch_all` and `flash_edl` menus handle this automatically. You can also flash individual `output*` images manually.

## 5. Script Descriptions

* **`start.bat`**: This is the main script you will run. It provides access to all functions.

### Main Menu

* **1. Patch and Flash ROW ROM (Recommended):**
    * This is the all-in-one automated function. It runs the following steps in order:
    1.  Waits for the user to provide the full RSA firmware `image` folder.
    2.  `convert_images` (Patches PRC files to ROW in `output` folder).
    3.  `modify_xml` (Decrypts and patches `.x` files, saves to `output_xml`).
    4.  `read_edl` (Dumps `devinfo/persist` to `backup` folder. **Requires EDL connection.**).
    5.  `edit_devinfo_persist` (Patches `devinfo/persist`, saves to `output_dp`).
    6.  `read_anti_rollback` + `patch_anti_rollback` (Dumps current boot/vbmeta, compares to `image` folder, and patches if needed, saving to `output_anti_rollback`. **Requires EDL connection.**).
    7.  `flash_edl` (Copies all `output*` files to `image`, flashes main firmware, flashes `output_dp`, flashes `output_anti_rollback`, and reboots. **Requires EDL connection.**).
* **2. Advanced Tools:**
    * Opens a submenu for all individual tasks.
* **3. Exit:**
    * Closes the script.

### Advanced Menu

* **1. Convert ROM (PRC to ROW):** Reads `vendor_boot.img` / `vbmeta.img` from `image`, saves patched files to `output`.
* **2. Dump devinfo/persist via EDL:** Dumps partitions directly into the `backup` folder. Requires EDL loader in `image`.
* **3. Patch devinfo/persist (Region Code Reset):** Reads `devinfo/persist` from `backup`, saves patched files to `output_dp`.
* **4. Write devinfo/persist via EDL (Flash patched):** Reads patched images from `output_dp` and flashes them. Requires EDL loader in `image`.
* **5. Create Rooted boot.img:** Reads `boot.img` from `image`, saves patched file to `output_root`.
* **6. Read Anti-Rollback (Dump current, Compare):** Dumps `boot`/`vbmeta_system` to `input_current`, compares indices against `image` folder, and reports if patching is needed.
* **7. Patch Anti-Rollback (Create patched images):** Runs the same "Read" step, and if patching is needed, saves patched `boot`/`vbmeta_system` to `output_anti_rollback`.
* **8. Write Anti-Rollback (Flash patched images):** Flashes the patched images from `output_anti_rollback`.
* **9. Modify XML for Update (RSA Firmware):** Reads `.x` files from `image`, saves patched `.xml` files to `output_xml`.
* **10. Flash EDL (Full Firmware Flash):** Copies all `output*` contents into `image` (overwriting) and flashes the entire folder. This **includes** flashing `output_dp` and `output_anti_rollback` images at the end before resetting.
* **11. Clean Workspace:** Deletes all `input*`, `output*`, `image`, `working`, `avb` folders, and downloaded tools. **Keeps `python3` and `backup` folders.** (Exits after running).
* **12. Back to Main Menu:** Returns to the main menu.

* **`info_image.bat`**: A separate utility script. Drag & drop `.img` file(s) or folder(s) onto this script to see AVB (Android Verified Boot) information.
    * *Output: `image_info_*.txt`*