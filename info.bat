@echo off
setlocal

set "PYTHON=%~dp0python3\python.exe"
set "PY_AVBTOOL=%~dp0tools\avbtool.py"

if not exist "%PYTHON%" (
    echo Error: Python executable not found at "%PYTHON%"
    pause
    exit /b
)

if not exist "%PY_AVBTOOL%" (
    echo Error: avbtool.py not found at "%PY_AVBTOOL%"
    pause
    exit /b
)

echo Processing file: %1
echo ---------------------------------
"%PYTHON%" "%PY_AVBTOOL%" info_image --image "%1"
echo ---------------------------------
echo.
pause