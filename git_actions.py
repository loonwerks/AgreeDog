"""
@Author: Amer N. Tahat, Collins Aerospace.
Description: Git actions have been upgraded to use the GitHub CLI and GitHub tokens more securely.
Date: Aug 2024
"""
import subprocess
import shutil
import os
import json
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
GIT_TOKEN = os.getenv('GH_TOKEN')
GIT_USER = os.getenv('GIT_USER')
GIT_EMAIL = os.getenv('GIT_EMAIL')

CONFIG_FILE = 'config.json'


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    return {}


def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)


def set_git_remote_url(username_env_var='GIT_USER', token_env_var='GH_TOKEN', repo_name="v2_CoqDog_Team_beta.git"):
    # Retrieve username and GitHub token from environment variables
    username = os.getenv(username_env_var)
    gh_token = os.getenv(token_env_var)

    # Check if username and token are set
    if not username or not gh_token:
        raise ValueError(f"Environment variables {username_env_var} and/or {token_env_var} are not set.")

    # Construct the remote URL
    remote_url = f"https://{gh_token}@github.com/{username}/{repo_name}"

    try:
        # Run the command to set the remote URL
        subprocess.run(['git', 'remote', 'set-url', 'origin', remote_url], check=True)
        print(f"Remote URL set to {remote_url}")
    except subprocess.CalledProcessError as e:
        print(f"Error setting remote URL: {e}")


def clone_repo(repo_url, method='https'):
    try:
        repo_name = "v2_CoqDog_Team_beta.git"
        set_git_remote_url(repo_name)
        #repo_name = repo_url.split('/')[-1].replace('.git', '')
        repo_name = repo_name.replace('.git', '')
        # Check if the repo already exists locally and remove it if it does
        if os.path.exists(repo_name):
            shutil.rmtree(repo_name)

        if method == 'gh':
            clone_command = ['gh', 'repo', 'clone', repo_url]
        else:
            clone_command = ['git', 'clone', repo_url]

        subprocess.run(clone_command, check=True)
        return repo_name
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Error cloning the repository: {e}")


def copy_folders(folders, repo_name):
    try:
        for folder in folders:
            dest = os.path.join(repo_name, os.path.basename(folder))
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(folder, dest)
        return True
    except Exception as e:
        raise ValueError(f"Error copying folders: {e}")


def add_commit_push(commit_message):
    try:
        set_git_remote_url("v2_CoqDog_Team_beta.git")
        # Set git username and email
        subprocess.run(['git', 'config', '--local', 'user.name', GIT_USER], check=True)
        subprocess.run(['git', 'config', '--local', 'user.email', GIT_EMAIL], check=True)
        # commit commands
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        #subprocess.run(['gh', 'repo', 'sync'], check=True)
        subprocess.run(['git', 'push', 'origin', 'master'], check=True)  # this command is good for https here we use gh
        return True, "  temp history folder have been pushed to the remote repository successfully."
    except subprocess.CalledProcessError as e:
        return False, f"Error pushing to the repository: {e}"


def limit_commit_message_length(commit_message, word_limit=50):
    words = commit_message.split()
    if len(words) > word_limit:
        commit_message = ' '.join(words[:word_limit])
    return commit_message


def filter_alphabetic_characters(commit_message):
    return ' '.join(filter(str.isalpha, commit_message.split()))


def git_commit_push(commit_message):
    folders = ["temp_history"]
    config = load_config()
    repo_url = config.get('repo_url')
    method = config.get('method')
    current_directory = os.getcwd()  # Save the current working directory
    try:
        repo_name = clone_repo(repo_url, method)
        if not repo_name:
            raise ValueError("Failed to clone the repository.")
        if not copy_folders(folders, repo_name):
            raise ValueError("Failed to copy the folders.")

        os.chdir(repo_name)
        default_commit_message = "Updates " + ' '.join(folders)
        if not commit_message.strip():
            commit_message = default_commit_message
        else:
            commit_message = limit_commit_message_length(commit_message)
            commit_message = filter_alphabetic_characters(commit_message)

        success, message = add_commit_push(commit_message)
        os.chdir(current_directory)  # Restore the original working directory
        return success, message
    except ValueError as e:
        os.chdir(current_directory)  # Restore the original working directory
        return False, str(e)
    except Exception as e:
        os.chdir(current_directory)  # Restore the original working directory
        return False, f"An unexpected error occurred: {e}"
