@echo off
setlocal

echo --- Required Files Installer ---
echo.

:: ======================================================
:: Variable Definitions
:: ======================================================
set "TOOLS_DIR=%~dp0tools"
set "KEY_DIR=%~dp0key"
set "PYTHON_DIR=%~dp0python3"
set "PYTHON_VERSION=3.14.0"
set "PYTHON_ZIP_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip"
set "PYTHON_ZIP_PATH=%~dp0python_embed.zip"
set "PYTHON_PTH_FILE_SRC=%TOOLS_DIR%\python314._pth"
set "PYTHON_PTH_FILE_DST=%PYTHON_DIR%\python314._pth"
set "GETPIP_URL=https://bootstrap.pypa.io/get-pip.py"
set "GETPIP_PATH=%PYTHON_DIR%\get-pip.py"

:: ======================================================
:: Create Directories
:: ======================================================
if not exist "%TOOLS_DIR%" mkdir "%TOOLS_DIR%"
if not exist "%KEY_DIR%" mkdir "%KEY_DIR%"

:: ======================================================
:: 1. Setup Standalone Python Environment
:: ======================================================
echo [*] Checking for Python environment...
if exist "%PYTHON_DIR%\python.exe" goto PythonExists

echo [!] Python environment not found. Starting setup...

echo [*] Downloading Python embeddable package (%PYTHON_VERSION%)...
curl -L "%PYTHON_ZIP_URL%" -o "%PYTHON_ZIP_PATH%"
if errorlevel 1 (
    echo [!] Failed to download Python. Please check your internet connection.
    goto End
)

echo [*] Unpacking Python...
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"
tar -xf "%PYTHON_ZIP_PATH%" -C "%PYTHON_DIR%"
if errorlevel 1 (
    echo [!] Failed to unpack Python zip. Make sure tar is installed.
    goto End
)
del "%PYTHON_ZIP_PATH%"

echo [*] Configuring Python environment...
copy "%PYTHON_PTH_FILE_SRC%" "%PYTHON_PTH_FILE_DST%" > nul
if errorlevel 1 (
    echo [!] Failed to copy pth file for Python configuration.
    goto End
)

echo [*] Installing pip...
curl -L "%GETPIP_URL%" -o "%GETPIP_PATH%"
"%PYTHON_DIR%\python.exe" "%GETPIP_PATH%"
del "%GETPIP_PATH%"
if not exist "%PYTHON_DIR%\Scripts\pip.exe" (
    echo [!] Failed to install pip.
    goto End
)

echo [*] Installing cryptography library...
"%PYTHON_DIR%\Scripts\pip.exe" install cryptography
if errorlevel 1 (
    echo [!] Failed to install cryptography.
    goto End
)
    
echo [+] Python setup complete.
echo.
goto PythonDone

:PythonExists
echo [+] Python environment and packages already exist.
echo.

:PythonDone
:: ======================================================
:: 2. Download Required Binaries
:: ======================================================
echo [*] Checking for ksuinit...
if exist "%TOOLS_DIR%\ksuinit" goto ksuinit_exists
echo [!] 'ksuinit' not found. Attempting to download...
curl -L "https://github.com/KernelSU-Next/KernelSU-Next/raw/refs/heads/next/userspace/ksud_magic/bin/aarch64/ksuinit" -o "%TOOLS_DIR%\ksuinit"
if exist "%TOOLS_DIR%\ksuinit" (echo [+] Download successful.) else (echo [!] Download failed.)
:ksuinit_exists
echo.

echo [*] Checking for magiskboot.exe...
if exist "%TOOLS_DIR%\magiskboot.exe" goto magiskboot_exists
echo [!] 'magiskboot.exe' not found. Attempting to download...
curl -L "https://github.com/CYRUS-STUDIO/MagiskBootWindows/raw/refs/heads/main/magiskboot.exe" -o "%TOOLS_DIR%\magiskboot.exe"
if exist "%TOOLS_DIR%\magiskboot.exe" (echo [+] Download successful.) else (echo [!] Download failed.)
:magiskboot_exists
echo.

echo [*] Checking for avbtool.py...
if exist "%TOOLS_DIR%\avbtool.py" goto avbtool_exists
echo [!] 'avbtool.py' not found. Attempting to download...
curl -L "https://github.com/LineageOS/android_external_avb/raw/refs/heads/lineage-22.2/avbtool.py" -o "%TOOLS_DIR%\avbtool.py"
if exist "%TOOLS_DIR%\avbtool.py" (echo [+] Download successful.) else (echo [!] Download failed.)
:avbtool_exists
echo.

echo [*] Checking for testkey_rsa4096.pem...
if exist "%KEY_DIR%\testkey_rsa4096.pem" goto key4096_exists
echo [!] 'testkey_rsa4096.pem' not found. Attempting to download...
curl -L "https://github.com/LineageOS/android_external_avb/raw/refs/heads/lineage-22.2/test/data/testkey_rsa4096.pem" -o "%KEY_DIR%\testkey_rsa4096.pem"
if exist "%KEY_DIR%\testkey_rsa4096.pem" (echo [+] Download successful.) else (echo [!] Download failed.)
:key4096_exists
echo.

echo [*] Checking for testkey_rsa2048.pem...
if exist "%KEY_DIR%\testkey_rsa2048.pem" goto key2048_exists
echo [!] 'testkey_rsa2048.pem' not found. Attempting to download...
curl -L "https://github.com/LineageOS/android_external_avb/raw/refs/heads/lineage-22.2/test/data/testkey_rsa2048.pem" -o "%KEY_DIR%\testkey_rsa2048.pem"
if exist "%KEY_DIR%\testkey_rsa2048.pem" (echo [+] Download successful.) else (echo [!] Download failed.)
:key2048_exists
echo.

:End
echo All checks are done.
pause