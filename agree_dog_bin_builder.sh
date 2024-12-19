#!/bin/bash
# Script Name: optimized_agree_dog_bin_builder.sh
# Author: Amer N Tahat,  Collins Aerospace.
# Date: 18 Dec 2024
# Version: 1.0
# Description: This script creates a single-dir binary -- assuming Python 3.9.7 bin path /usr/local/bin/pyhton3.
# TODO autoamte python installation

# Exit on any error
set -e

# Function to check and install a system dependency
check_and_install_git() {
    if ! dpkg -l | grep -q "git"; then
        echo "Git is not installed. Installing git..."
        sudo apt update
        sudo apt install -y git
    else
        echo "Git is already installed."
    fi
}

# Function to check and install PyInstaller
check_and_install_pyinstaller() {
    if ! pip show pyinstaller >/dev/null 2>&1; then
        echo "PyInstaller is not installed. Installing PyInstaller..."
        pip install pyinstaller
    else
        echo "PyInstaller is already installed."
    fi
}

# Check for git
echo "Checking for external dependency: git..."
check_and_install_git

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "No virtual environment found. Creating one..."
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating the virtual environment..."
source venv/bin/activate

# Check for PyInstaller in the virtual environment
echo "Checking for PyInstaller..."
check_and_install_pyinstaller

# Check for INSPECTA_Dog.py
if [ -f "INSPECTA_Dog.py" ]; then
    echo "INSPECTA_Dog.py found. Proceeding to create binary..."
else
    echo "Error: INSPECTA_Dog.py not found in the current directory!"
    exit 1
fi

# Create the binary using PyInstaller
echo "Creating the binary using PyInstaller..."
pyinstaller --onedir \
  --add-data "config.json:." \
  --add-data "uploaded_dir:uploaded_dir" \
  --add-data "conversation_history:conversation_history" \
  --add-data "temp_history:temp_history" \
  --add-data "shared_history:shared_history" \
  --add-data "counter_examples:counter_examples" \
  --add-data "assets:assets" \
  INSPECTA_Dog.py

echo "Binary creation complete."
echo "You can find the binary in the 'dist/INSPECTA_Dog' directory."

