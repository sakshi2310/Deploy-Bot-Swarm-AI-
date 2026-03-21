import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


def parse_github_url(url: str) -> str:
    """
    Converts any GitHub URL format to 'owner/repo' string
    """
    url = url.strip().rstrip("/")

    if url.startswith("https://github.com/"):
        url = url.replace("https://github.com/", "")
    elif url.startswith("http://github.com/"):
        url = url.replace("http://github.com/", "")

    if url.endswith(".git"):
        url = url[:-4]

    parts = url.split("/")
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"

    raise ValueError(f"Invalid GitHub URL: '{url}'")

def get_repo_files(repo: str, path: str = "") -> list:
    """Get list of Python files in a GitHub repo"""
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        raise Exception(f"GitHub API error: {response.status_code} - {response.text}")

    files = []
    for item in response.json():
        if item["type"] == "file" and item["name"].endswith(".py"):
            files.append({
                "name": item["name"],
                "path": item["path"],
                "download_url": item["download_url"]
            })
    return files


def get_file_content(download_url: str) -> str:
    """Download and return raw file content"""
    response = requests.get(download_url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch file: {response.status_code}")
    return response.text


def get_latest_commit_diff(repo: str) -> dict:
    """Get the latest commit and its changed files"""
    url = f"https://api.github.com/repos/{repo}/commits"
    response = requests.get(url, headers=HEADERS, params={"per_page": 1})

    if response.status_code != 200:
        raise Exception(f"GitHub API error: {response.status_code}")

    commits = response.json()
    if not commits:
        raise Exception("No commits found in repo")

    latest = commits[0]
    sha = latest["sha"]
    message = latest["commit"]["message"]
    author = latest["commit"]["author"]["name"]

    detail_url = f"https://api.github.com/repos/{repo}/commits/{sha}"
    detail = requests.get(detail_url, headers=HEADERS).json()

    changed_files = []
    for f in detail.get("files", []):
        changed_files.append({
            "filename": f["filename"],
            "status": f["status"],
            "additions": f["additions"],
            "deletions": f["deletions"],
            "patch": f.get("patch", "")
        })

    return {
        "sha": sha[:7],
        "message": message,
        "author": author,
        "files": changed_files
    }


def get_pr_diff(repo: str, pr_number: int) -> dict:
    """Get files changed in a specific Pull Request"""
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        raise Exception(f"GitHub PR API error: {response.status_code}")

    files = []
    for f in response.json():
        files.append({
            "filename": f["filename"],
            "status": f["status"],
            "additions": f["additions"],
            "deletions": f["deletions"],
            "patch": f.get("patch", "")
        })

    return {"pr_number": pr_number, "files": files}