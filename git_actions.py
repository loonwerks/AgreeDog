"""
@Author: Amer N. Tahat, Collins Aerospace.
Description: Git actions have been upgraded to use the GitHub CLI and GitHub tokens more securely.
Date: 1st Aug 2024
"""
import os
import subprocess
import json
import shutil
from datetime import datetime

CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)

def pull_repo():
    try:
        subprocess.run(['git', 'pull'], check=True)
        return True
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Error pulling the repository: {e}")

def copy_temp_to_shared():
    temp_history = 'temp_history'
    shared_history = 'shared_history'

    if not os.path.exists(temp_history):
        os.makedirs(temp_history)
        #raise ValueError(f"The '{temp_history}' folder is missing.")

    if not os.path.exists(shared_history):
        os.makedirs(shared_history)

    try:
        # Copy contents from temp_history to shared_history
        for item in os.listdir(temp_history):
            s = os.path.join(temp_history, item)
            d = os.path.join(shared_history, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
    except Exception as e:
        raise ValueError(f"Error copying files: {e}")

def add_commit_push(commit_message):
    try:
        subprocess.run(['git', 'add', 'shared_history'], check=True)
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        subprocess.run(['git', 'push'], check=True)
        return True, "Changes have been pushed to the remote repository successfully."
    except subprocess.CalledProcessError as e:
        return False, f"Error pushing to the repository: {e} check .gitignore"

def limit_commit_message_length(commit_message, word_limit=100):
    words = commit_message.split()
    if len(words) > word_limit:
        commit_message = ' '.join(words[:word_limit])
    return commit_message

def filter_alphanumeric_characters(commit_message):
    return ''.join(c for c in commit_message if c.isalnum() or c.isspace())

def git_commit_push(commit_message):
    config = load_config()
    current_directory = os.getcwd()

    try:
        # Pull the latest changes
        pull_repo()

        # Copy temp-history to shared-history
        copy_temp_to_shared()

        # Add, commit, and push changes
        default_commit_message = "Update shared history"
        if not commit_message.strip():
            commit_message = default_commit_message
        else:
            commit_message = limit_commit_message_length(commit_message)
            commit_message = filter_alphanumeric_characters(commit_message)

        success, message = add_commit_push(commit_message)
        return success, message
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"An unexpected error occurred: {e}"
