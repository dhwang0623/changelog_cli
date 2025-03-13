from dotenv import load_dotenv
load_dotenv()
import os
import subprocess
import requests
import sys

"""
Changelog CLI Tool

This script fetches recent Git commit messages and generates a structured changelog using the Mintlify API.

To avoid manual copying the file everytime I want to use it, I would convert it to a global CLI tool and creating it as a package.
"""

API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"


if not API_KEY:
    print("Error: API key not found. Set GEMINI_API_KEY environment variable.")
    sys.exit(1)

def is_git_repo():
    """
    Checks if the current directory is a Git repository, preventing errors if the script is ran in a non-Git directory.
    """
    try:
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], check = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def fetch_git_commits(n):
    """
    Retrieves the last n commits from the Git repository.
    """
    try:
        result = subprocess.run(
            ["git", "log", f"-n {n}", "--pretty=format:%h|%s|%ci"], capture_output = True, text = True, check = True)
        commits = result.stdout.strip().split("\n")
        if not commits or commits == [""]:
            print("Warning: No recent commits found.")
            return ["No recent commits found"]
        return commits
    except subprocess.CalledProcessError:
        print("Error: Failed to retrieve commits, please ensure that you are in a Git repository.")
        sys.exit(1)

def condense_commits(commits):
    """
    If there are more than 50 commits, group them into sets of 5 for better readability and reduces API token usage.
    """
    if len(commits) > 50:
        grouped_commits = [f"{i // 5 + 1}. {', '.join(commits[i: i + 5])}" for i in range(0, len(commits), 5)]
        return grouped_commits
    return commits

def request_changelog_from_api(commits):
    """
    Sends the commit messages to the Mintlify API and retrieves the formatted changelog.
    """
    if not commits:
        return "No commits found."
    formatted_commits = []
    for commit in commits:
        parts = commit.split("|")
        if len(parts) == 3:
            commit_hash, message, timestamp = parts
            formatted_commits.append(f"- **{timestamp}** | `{commit_hash}`: {message}")
    commits_text = "\n".join(formatted_commits)
    prompt = f"""You are an AI assistant that generates structured changelogs from Git commits.

    ### **Rules for Formatting the Changelog**
    1. **Preserve commit order** (oldest first).
    2. **Include timestamps** for each commit.
    3. **Format output in Markdown with proper sections**.

    ### **Commits (Oldest to Newest)**
    {commits_text}

    ### **Generate the Changelog**
    Use the following structure:
    - **New Features**
    - **Improvements**
    - **Bug Fixes**
    - **Deprecations**
    - **Performance Enhancements**

    Each commit should include:
    - A bullet point (`-`)
    - The commit **timestamp**
    - The commit **hash** (formatted as inline code using backticks)
    - A **clear description**

    If a section does not apply, omit it.
    """
    
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "key": API_KEY
    }
    try:
        response = requests.post(API_URL, json = payload, headers = headers, params = params)
        response.raise_for_status()
        response_data = response.json()
        if "candidates" in response_data and response_data["candidates"]:
            return response_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return "No response from API."
    except requests.exceptions.RequestException as e:
        print(F"Error: API request failed. Details: {e}")
        sys.exit(1)

def main():
    """
    Handles the CLI arguments and executes the script.
    """
    if not is_git_repo():
        print("Error: This script must be ran in a Git repository.")
        sys.exit(1)
    if len(sys.argv) != 2:
        print("Usage: python changelog_cli.py <number_of_commits>")
        sys.exit(1)
    try:
        num_commits = int(sys.argv[1])
        if num_commits <= 0:
            raise ValueError
    except ValueError:
        print("Error: Please provide a valid positive number integer for the number of commits.")
        sys.exit(1)
    commits = fetch_git_commits(num_commits)
    changelog = request_changelog_from_api(commits)
    print("\nGenerated Changelog: \n")
    print(changelog)
    with open("changelog.md", "w") as f:
        f.write(changelog)
    print("\n Changelog saved to changelog.md")

if __name__ == "__main__":
    main()

