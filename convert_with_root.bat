@echo off
setlocal

echo Checking for required files...
set "MISSING_FILE="
if not exist "%~dp0python3\python.exe" set "MISSING_FILE=Python Environment"
if not exist "%~dp0tools\ksuinit" set "MISSING_FILE=ksuinit"
if not exist "%~dp0tools\magiskboot.exe" set "MISSING_FILE=magiskboot.exe"

if defined MISSING_FILE (
    echo Error: Dependency '%MISSING_FILE%' is missing.
    echo Please run 'install.bat' first to download all required files.
    pause
    exit /b
)
echo All dependencies are present.
echo.


set "CURRENT_DIR=%~dp0"
set "TOOLS_DIR=%CURRENT_DIR%tools\"
set "TMP_DIR=%TOOLS_DIR%tmp_patch\"
set "KSU_APK_URL=https://github.com/KernelSU-Next/KernelSU-Next/releases/download/v1.1.1/KernelSU_Next_v1.1.1-spoofed_12851-release.apk"
set "KSU_APK_NAME=KernelSU_Next_v1.1.1-spoofed_12851-release.apk"

echo Starting KernelSU Boot Image Patcher...

if not exist "%CURRENT_DIR%vendor_boot.img" (
    echo Error: vendor_boot.img not found.
    pause
    exit /b
)

echo Backing up original vendor_boot.img to vendor_boot.bak.img...
move "%CURRENT_DIR%vendor_boot.img" "%CURRENT_DIR%vendor_boot.bak.img"

if exist "%TMP_DIR%" (
    echo Cleaning up previous temporary directory...
    rmdir /s /q "%TMP_DIR%"
)
mkdir "%TMP_DIR%"

echo Copying files to temporary directory...
copy "%CURRENT_DIR%vendor_boot.bak.img" "%TMP_DIR%\vendor_boot.img"
copy "%TOOLS_DIR%magiskboot.exe" "%TMP_DIR%"
copy "%TOOLS_DIR%ksuinit" "%TMP_DIR%"

cd "%TMP_DIR%"

echo.
echo Unpacking boot image...
magiskboot.exe unpack vendor_boot.img

echo.
echo Patching ramdisk...
echo Adding /ksuinit and patching /init.
magiskboot.exe cpio ramdisk.cpio "add 0755 /ksuinit ksuinit"
magiskboot.exe cpio ramdisk.cpio "patch"

echo.
echo Repacking boot image...
magiskboot.exe repack vendor_boot.img

if exist "new-boot.img" (
    echo.
    echo Renaming patched image to vendor_boot.img...
    move "new-boot.img" "%CURRENT_DIR%vendor_boot.img"
    echo Success: Patched image saved as '%CURRENT_DIR%vendor_boot.img'
) else (
    echo.
    echo Error: Patched image not found. Restoring original backup.
    move "%CURRENT_DIR%vendor_boot.bak.img" "%CURRENT_DIR%vendor_boot.img"
)

cd "%CURRENT_DIR%"
echo Deleting temporary directory '%TMP_DIR%'
rmdir /s /q "%TMP_DIR%"

echo.
echo Patching script finished.
echo.

echo Checking for KernelSU Next Manager APK...
if exist "%CURRENT_DIR%%KSU_APK_NAME%" (
    echo KernelSU Next Manager APK already exists.
) else (
    echo APK not found. Attempting to download...
    curl -L "%KSU_APK_URL%" -o "%CURRENT_DIR%%KSU_APK_NAME%"
)
echo.

echo Now running convert.bat...
echo.

call convert.bat

endlocal