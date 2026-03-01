import subprocess
import httpx


def get_repo_info(repo_url: str) -> dict:
    """Fetch repo metadata from GitHub API"""
    # Extract owner/repo from URL
    parts = repo_url.replace("https://github.com/", "").replace(".git", "").split("/")
    owner, repo = parts[0], parts[1]
    
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    
    response = httpx.get(api_url)
    response.raise_for_status()
    return response.json()


def clone_repository(repo_url: str, dest_path: str, branch: str = "main"):
    """Clone git repo to destination"""
    subprocess.run(
        ["git", "clone", "--depth", "1", "--branch", branch, repo_url, dest_path],
        check=True,
        capture_output=True,
        text=True
    )