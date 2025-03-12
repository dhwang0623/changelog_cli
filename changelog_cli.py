import subprocess
import requests
import sys

"""
Changelog CLI Tool

This script fetches recent Git commit messages and generates a structured changelog using the Mintlify API.

To avoid manual copying the file everytime I want to use it, I would convert it to a global CLI tool and creating it as a package.
"""

API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImRhbmllbGh3YW5nMDYyM0BnbWFpbC5jb20iLCJhc3Nlc3NtZW50IjoiYWkiLCJjcmVhdGVkX2F0IjoiMjAyNS0wMy0xMlQxOTowMDo0Ny43ODQ3NTk0MzRaIiwiaWF0IjoxNzQxODA2MDQ3fQ.JbkjSQ-o5BAIJ_40hn-56JNGd00HwqeTrbi_gxBdX_c"
API_URL = "https://mintlify-take-home.com/api/message"

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
            ["git", "log", f"-n {n}", "--pretty=format:%h %s"], capture_output = True, text = True, check = True)
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
    condensed_commits = condense_commits(commits)
    commits_text = "\n".join(condensed_commits)
    prompt = f"""Generate a structured changelog based on the following commit messages:

    {commits_text}:

    Please format the changelog usinng Markdown with the following sections:
    -**New Features** (for new functionality)
    -**Improvements** (for enhancements and general improvements)
    -**Deprecations** (for removed features)
    -**Bug Fixes** (for fixed issues)
    -**Performance Enhancements** (for otimizations)

    Ensure each section is clear and concise, using bullet points and commit references where it is relevant. 
    If a section does not apply, omit it from the changelog.
    """
    
    payload = {
        "model": "claude-3-5-sonnet-latest",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ], 
        "max_tokens": 4096,
        "temperature": 0.5
    }
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(API_URL, json = payload, headers = headers)
        response.raise_for_status()
        response_data = response.json()
        if "content" in response_data and isinstance(response_data["content"], list):
            changelog_text = "\n".join([item["text"] for item in response_data["content"] if "text" in item])
            return changelog_text or "No response from API."
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

