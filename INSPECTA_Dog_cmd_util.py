"""
@Author: Amer N. Tahat, Collins Aerospace.
Description: INSPECTADog basic cmd line utilities.
Date: July 2024
"""
import os
import shutil
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
        "--counter-example",
        type=str,
        default="",
        help="Path to the counterexample file (optional), we assume Agree will save it in a counter_examples directory."
    )
    parser.add_argument(
        "--start-file",
        type=str,
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
    """Returns the path of the _AgreeFiles file, creating it if necessary."""
    if working_dir_exists:
        agree_files = os.path.join(directory, "_AgreeFiles")
    else:
        agree_files = os.path.join(directory, "packages/_AgreeFiles")

    # Check if _AgreeFiles exists, create it if not
    if not os.path.exists(agree_files):
        warnings.warn(
            f"The expected '_AgreeFiles' file was not found in the directory: {directory}. "
            "The program will continue, but some functionality may be affected.",
            UserWarning
        )
        create_agree_files_file(directory if working_dir_exists else os.path.join(directory, "packages"))


    return agree_files

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
        # Read as a standard text file
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