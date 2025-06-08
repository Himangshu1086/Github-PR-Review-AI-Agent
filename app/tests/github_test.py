import pytest
import base64
from unittest.mock import patch, MagicMock
from app.github import (
    parse_repo_url,
    fetch_pr_files,
    fetch_file_content,
    post_general_pr_comment,
    post_inline_comment,
    get_latest_commit_sha
)

# === parse_repo_url ===
def test_parse_repo_url():
    owner, repo = parse_repo_url("https://github.com/user/repo-name")
    assert owner == "user"
    assert repo == "repo-name"

# === fetch_pr_files ===
@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_fetch_pr_files(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"filename": "file.py"}]
    mock_get.return_value = mock_response

    result = await fetch_pr_files("user", "repo", 1, "ghp_xxx")
    assert result == [{"filename": "file.py"}]

# === fetch_file_content ===
@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_fetch_file_content(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    encoded = base64.b64encode(b'print("hello")').decode("utf-8")
    mock_response.json.return_value = {"content": encoded}
    mock_get.return_value = mock_response

    content = await fetch_file_content("user", "repo", "file.py", "37dwd2e3" ,"ghp_xxx")
    assert content.strip() == 'print("hello")'

# === post_general_pr_comment ===
@patch("httpx.post")
def test_post_general_pr_comment_success(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 123}
    mock_post.return_value = mock_response

    response = post_general_pr_comment("user", "repo", 1, "Hello PR!", "ghp_xxx")
    assert response["id"] == 123

@patch("httpx.post")
def test_post_general_pr_comment_failure(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_response.raise_for_status.side_effect = Exception("Boom")
    mock_post.return_value = mock_response

    with pytest.raises(Exception):
        post_general_pr_comment("user", "repo", 1, "Test", "ghp_xxx")

# === get_latest_commit_sha ===
@patch("httpx.get")
def test_get_latest_commit_sha(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"head": {"sha": "abc123"}}
    mock_get.return_value = mock_response

    sha = get_latest_commit_sha("user", "repo", 1, "ghp_xxx")
    assert sha == "abc123"

# === post_inline_comment ===
@patch("app.github.get_latest_commit_sha", return_value="abc123")
@patch("httpx.post")
def test_post_inline_comment_success(mock_post, mock_sha):
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": "comment-id"}
    mock_post.return_value = mock_response

    response = post_inline_comment("user", "repo", 1, "file.py", 10, "Nice line!", "ghp_xxx")
    assert response["id"] == "comment-id"

@patch("app.github.get_latest_commit_sha", return_value="abc123")
@patch("httpx.post")
def test_post_inline_comment_failure(mock_post, mock_sha):
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.text = "Unprocessable"
    mock_response.raise_for_status.side_effect = Exception("Invalid line")
    mock_post.return_value = mock_response

    with pytest.raises(Exception):
        post_inline_comment("user", "repo", 1, "file.py", 99, "Invalid line!", "ghp_xxx")
