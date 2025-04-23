@echo off
:: Script Name: AgreeDog_builder.bat
:: Author: Amer N Tahat, Collins Aerospace.
:: Date: 19 Dec 2024
:: Version: 1.0
:: Description: This script creates a single-file binary assuming Python 3.9.7 is installed and properly configured.
::              Unlike the Linux shell script version, this batch script assumes system dependencies are handled manually,
::              as they are simpler to configure on Windows.
::
:: Create the AgreeDog binary using PyInstaller

@echo off
:: Force using a specific Python interpreter from the virtual environment
set PYTHON_EXE=C:\Users\amer_\AppData\Local\Programs\Python\Python311\python.exe

:: Use that Python to run PyInstaller
%PYTHON_EXE% -m PyInstaller --onefile ^
    --add-data uploaded_dir;uploaded_dir ^
    --add-data assets;assets ^
    INSPECTA_Dog.py

if %ERRORLEVEL% neq 0 (
    echo Error creating the binary.
    exit /b 1
)

echo Binary creation complete.
pause