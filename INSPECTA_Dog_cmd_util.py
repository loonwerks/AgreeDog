"""
@Author: Amer N. Tahat, Collins Aerospace.
Description: INSPECTADog basic cmd line utilities.
Date: July 2024
"""
import os
import sys
#import shutil
import argparse
import warnings
import pandas as pd

def get_args():
    parser = argparse.ArgumentParser(description="Process AADL model and counterexample paths.")
    parser.add_argument(
        "--working-dir",
        required=False,
        type=str,
        default=None,
        help="Path to the working directory containing the AADL files."
    )
    parser.add_argument(
        "--user-open-api-key",
        type=str,
        required=False,
        default=None,
        help="API key for accessing external services (optional)."
    )
    parser.add_argument(
        "--counter-example",
        type=str,
        required=False,
        default="",
        help="Path to the counterexample file (optional), we assume Agree will save it in a counter_examples directory."
    )
    parser.add_argument(
        "--start-file",
        type=str,
        required=False,
        default="Car.aadl",
        help="Name of the specific AADL file to search for in the working directory (optional)."
    )
    return parser.parse_args()

def clean_aadl_files(upload_dir):
    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        if filename.endswith('.aadl') and os.path.isfile(file_path):
            os.remove(file_path)

def create_agree_files_file(directory):
    """Creates an empty _AgreeFiles file in the specified directory."""
    agree_files_path = os.path.join(directory, "_AgreeFiles")
    with open(agree_files_path, 'w') as f:
        f.write("")  # Create an empty file
    print(f"Created missing '_AgreeFiles' file in directory: {directory}")

def get_agree_files_path(directory, working_dir_exists):
    """
    Returns the path of the _AgreeFiles file, ensuring it is updated with the latest .aadl files.
    Issues a warning if the file did not exist initially.
    """
    agree_files = os.path.join(directory, "_AgreeFiles") if working_dir_exists else os.path.join(directory, "packages/_AgreeFiles")

    # Determine the path to search for .aadl files
    parent_directory = directory if working_dir_exists else os.path.join(directory, "packages")

    # Check if _AgreeFiles exists
    file_existed = os.path.exists(agree_files)

    # Update or create the _AgreeFiles file
    update_agree_files_file(parent_directory, agree_files)

    # Issue a warning if the file was created (did not exist before)
    if not file_existed:
        warnings.warn(
            f"The expected '_AgreeFiles' file was not found in the directory: {parent_directory}. "
            "The AgreeDog has created and updated the file, "
            "when an aadl file is added to a the training set it should be removed from this list.",
            UserWarning
        )

    return agree_files

def update_agree_files_file(directory, agree_files_path):
    """Updates or creates the _AgreeFiles file with the .aadl files from the specified directory."""
    try:
        # Get all .aadl files in the directory
        aadl_files = [f for f in os.listdir(directory) if f.endswith(".aadl")]

        # Create or overwrite the _AgreeFiles file with the .aadl filenames
        with open(agree_files_path, 'w') as agree_file:
            for aadl_file in aadl_files:
                agree_file.write(f"{aadl_file}\n")

        print(f"_AgreeFiles updated at: {agree_files_path}")
    except Exception as e:
        print(f"Error updating _AgreeFiles: {e}")

def read_counter_example_file(file_path):
    if file_path.endswith('.xls'):
        # Read .xls file
        try:
            data = pd.read_excel(file_path, engine='xlrd')
            return data.to_string()  # Convert DataFrame to string for compatibility with your prompt format
        except Exception as e:
            print(f"Error reading .xls file: {e}")
            return ""

    elif file_path.endswith('.ods'):
        # Read .ods file
        try:
            import pandas_ods_reader as ods_reader
            data = ods_reader.read_ods(file_path, 1)  # Reads the first sheet
            return data.to_string()  # Convert DataFrame to string
        except Exception as e:
            print(f"Error reading .ods file: {e}")
            return ""

    elif file_path.endswith('.csv'):
        # Read .csv file
        try:
            data = pd.read_csv(file_path)
            return data.to_string()  # Convert DataFrame to string
        except Exception as e:
            print(f"Error reading .csv file: {e}")
            return ""

    elif file_path.endswith('.txt') or file_path.endswith('.aadl'):
        # Read aadl and txt as a standard text file
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except UnicodeDecodeError:
            # If UTF-8 fails, fall back to ISO-8859-1 or another encoding
            with open(file_path, 'r', encoding='ISO-8859-1') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return ""

# Helper function to dynamically locate resource paths
def get_resource_path(relative_path):
    """
    Dynamically resolve file paths for PyInstaller bundles and development environments.
    For specific directories or files, use sys._MEIPASS when running as a PyInstaller bundle.
    """
    pre_bundled_added_data_to_pyinstaller = {"uploaded_dir", "assets",
                                             "config.json"}  # Directories or files that require sys._MEIPASS

    # Extract the base name from the relative path (directory or file name)
    base_name = os.path.basename(relative_path)

    if getattr(sys, 'frozen', False) and base_name in pre_bundled_added_data_to_pyinstaller:
        # Running as a PyInstaller bundle and resource is in the specific set
        base_path = sys._MEIPASS
    else:
        # Default behavior: Use the absolute path of the current directory
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def ensure_writable_directories(directories):
    """
    Ensure necessary directories exist, creating them if needed.
    Args:
        directories (list): List of directories to ensure.
    """
    for directory in directories:
        full_path = get_resource_path(directory)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory exists: {full_path}")