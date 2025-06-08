import httpx
import base64
from urllib.parse import urlparse
from dotenv import load_dotenv
from app.lib.logger import logger
load_dotenv()

def parse_repo_url(repo_url):
    parsed = urlparse(repo_url)
    parts = parsed.path.strip("/").split("/")
    logger.info(f"Parsed repo URL: owner={parts[0]}, repo={parts[1]}")
    return parts[0], parts[1]  # owner, repo

async def fetch_pr_files(owner, repo, pr_number, GITHUB_TOKEN):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    logger.info(f"Fetching PR files: {owner}/{repo} PR#{pr_number}")
    async with httpx.AsyncClient() as client:
        resp = await client.get(url,headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        })
        logger.info(f"GitHub API GET {url} status: {resp.status_code}")
        resp.raise_for_status()
        return resp.json()

async def fetch_file_content(owner, repo, file_path, head_sha, GITHUB_TOKEN):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={head_sha}"
    logger.info(f"Fetching file content: {owner}/{repo}/{file_path}")
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        })
        logger.info(f"GitHub API GET {url} status: {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()
        return base64.b64decode(data["content"]).decode("utf-8")

def post_general_pr_comment(owner, repo, pr_number, body, GITHUB_TOKEN):
    '''
    Post a general (non-inline) comment on a pull request.
    '''
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    logger.info(f"Posting general PR comment to {owner}/{repo} PR#{pr_number}")
    data = {"body": body}
    response = httpx.post(url, headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }, json=data)
    if response.status_code != 201:
        logger.error(f"❌ Failed to post comment: {response.status_code} {response.reason_phrase}")
        logger.error(f"🔎 Response: {response.text}")
        logger.error(f"📤 Data sent: {data}")
    else:
        logger.info(f"Successfully posted general PR comment.")
    response.raise_for_status()
    return response.json()

def post_inline_comment(owner, repo, pr_number, filename, line: int, body, GITHUB_TOKEN):
    """
    Post an inline comment to a pull request on a specific file and line.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/comments"
    logger.info(f"Posting inline comment to {owner}/{repo} PR#{pr_number} file {filename} line {line}")
    headers = {
        "Authorization": f"{GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "body": body,
        "commit_id": get_latest_commit_sha(owner, repo, pr_number, GITHUB_TOKEN),
        "path": filename,
        "side": "RIGHT",
        "start_line":1,
        "start_side":"RIGHT",
        "line": line
    }
    response = httpx.post(url, headers=headers, json=data)
    if response.status_code != 201:
        logger.error(f"Failed to post inline comment: {response.status_code} {response.reason_phrase}")
        logger.error(f"Response content: {response.text}")
        logger.error(f"Data sent: {data}")
        logger.error("Possible causes: line number not in diff, file not in PR, or commit SHA mismatch.")
    else:
        logger.info(f"Successfully posted inline comment.")
    response.raise_for_status()
    return response.json()

def get_latest_commit_sha(owner, repo, pr_number, GITHUB_TOKEN):
    """
    Get the latest commit SHA for a pull request.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    logger.info(f"Fetching latest commit SHA for {owner}/{repo} PR#{pr_number}")
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = httpx.get(url, headers=headers)
    logger.info(f"GitHub API GET {url} status: {resp.status_code}")
    resp.raise_for_status()
    sha = resp.json()["head"]["sha"]
    logger.info(f"Latest commit SHA: {sha}")
    return sha