import subprocess
import requests
import sys

API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImRhbmllbGh3YW5nMDYyM0BnbWFpbC5jb20iLCJhc3Nlc3NtZW50IjoiYWkiLCJjcmVhdGVkX2F0IjoiMjAyNS0wMy0xMlQxOTowMDo0Ny43ODQ3NTk0MzRaIiwiaWF0IjoxNzQxODA2MDQ3fQ.JbkjSQ-o5BAIJ_40hn-56JNGd00HwqeTrbi_gxBdX_c"
API_URL = "https://mintlify-take-home.com/api/message"

def get_git_commits(n):
    try:
        result = subprocess.run(
            ["git", "log", f"-n {n}", "--pretty=format:%h %s"], capture_output = True, text = True, check = True)
        commits = result.stdout.strip().split("\n")
        return commits
    except subprocess.CalledProcessError:
        print("Error: Failed to retrieve commits, please ensure that you are in a Git repository.")
        sys.exit(1)

def generate_changelog(commits):
    if not commits:
        return "No commits found."
    prompt = "Please generate a user-friendly changelog for the following Git commit messages: \n" + "\n".join(commits)
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"prompt": prompt}
    try:
        response = requests.post(API_URL, json = payload, headers = headers)
        response.raise_for_status()
        return response.json().get("message", "No response from API.")
    except requests.exceptions.RequestException as e:
        print(F"Error: API request failed. Details: {e}")
        sys.exit(1)

def main():
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
    commits = get_git_commits(num_commits)
    changelog = generate_changelog(commits)
    print("\nGenerated Changelog: \n")
    print(changelog)

if __name__ == "__main__":
    main()

