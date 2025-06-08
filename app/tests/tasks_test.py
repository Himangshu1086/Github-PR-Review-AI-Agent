import pytest
from unittest.mock import patch, MagicMock
from app.tasks import analyze_pr_task

@pytest.fixture
def fake_inputs():
    return {
        "repo_url": "https://github.com/user/repo",
        "pr_number": 42,
        "github_token": "ghp_mocked"
    }

@pytest.fixture
def mock_request():
    return MagicMock(id="mock-task-id")

def run_wrapped_task(mock_request, *args):
    return analyze_pr_task.__wrapped__.__get__(MagicMock(request=mock_request))(*args)


# === ✅ Case 1: Full success ===
@patch("app.tasks.post_general_pr_comment")
@patch("app.tasks.generate_github_markdown_review", return_value="### Review")
@patch("app.tasks.build_graph")
@patch("app.tasks.fetch_file_content", return_value="print('hi')")
@patch("app.tasks.fetch_pr_files", return_value=[{"filename": "file1.py"}])
@patch("app.tasks.get_latest_commit_sha", return_value="abc123")
@patch("app.tasks.parse_repo_url", return_value=("user", "repo"))
def test_task_success(mock_parse, mock_sha, mock_fetch_files, mock_file_content, mock_graph_fn, mock_markdown, mock_post, fake_inputs, mock_request):
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {"results": [{"filename": "file1.py", "issues": []}]}
    mock_graph_fn.return_value = (mock_graph, {"files": []})

    result = run_wrapped_task(mock_request, fake_inputs["repo_url"], fake_inputs["pr_number"], fake_inputs["github_token"])

    assert result["status"] == "completed"
    assert "results" in result
    assert mock_post.called
    assert mock_markdown.called
    assert mock_graph.invoke.called


# === ❌ Case 2: parse_repo_url fails ===
@patch("app.tasks.parse_repo_url", side_effect=Exception("parse error"))
def test_parse_repo_url_error(mock_parse, fake_inputs, mock_request):
    result = run_wrapped_task(mock_request, fake_inputs["repo_url"], fake_inputs["pr_number"], fake_inputs["github_token"])
    assert result["status"] == "failed"
    assert "parse error" in result["error"]


# === ❌ Case 3: get_latest_commit_sha fails ===
@patch("app.tasks.get_latest_commit_sha", side_effect=Exception("sha fail"))
@patch("app.tasks.parse_repo_url", return_value=("user", "repo"))
def test_sha_fetch_error(mock_parse, mock_sha, fake_inputs, mock_request):
    result = run_wrapped_task(mock_request, fake_inputs["repo_url"], fake_inputs["pr_number"], fake_inputs["github_token"])
    assert result["status"] == "failed"
    assert "sha fail" in result["error"]


# === ❌ Case 4: fetch_pr_files fails ===
@patch("app.tasks.fetch_pr_files", side_effect=Exception("fetch_pr_files error"))
@patch("app.tasks.get_latest_commit_sha", return_value="abc123")
@patch("app.tasks.parse_repo_url", return_value=("user", "repo"))
def test_fetch_pr_files_error(mock_parse, mock_sha, mock_fetch, fake_inputs, mock_request):
    result = run_wrapped_task(mock_request, fake_inputs["repo_url"], fake_inputs["pr_number"], fake_inputs["github_token"])
    assert result["status"] == "failed"
    assert "fetch_pr_files error" in result["error"]


# === ❌ Case 5: fetch_file_content fails ===
@patch("app.tasks.fetch_file_content", side_effect=Exception("file content error"))
@patch("app.tasks.fetch_pr_files", return_value=[{"filename": "file1.py"}])
@patch("app.tasks.get_latest_commit_sha", return_value="abc123")
@patch("app.tasks.parse_repo_url", return_value=("user", "repo"))
def test_fetch_file_content_error(mock_parse, mock_sha, mock_files, mock_content, fake_inputs, mock_request):
    result = run_wrapped_task(mock_request, fake_inputs["repo_url"], fake_inputs["pr_number"], fake_inputs["github_token"])
    assert result["status"] == "failed"
    assert "file content error" in result["error"]


# === ❌ Case 6: build_graph fails ===
@patch("app.tasks.build_graph", side_effect=Exception("graph build error"))
@patch("app.tasks.fetch_file_content", return_value="code")
@patch("app.tasks.fetch_pr_files", return_value=[{"filename": "file1.py"}])
@patch("app.tasks.get_latest_commit_sha", return_value="abc123")
@patch("app.tasks.parse_repo_url", return_value=("user", "repo"))
def test_build_graph_error(mock_parse, mock_sha, mock_files, mock_content, mock_build, fake_inputs, mock_request):
    result = run_wrapped_task(mock_request, fake_inputs["repo_url"], fake_inputs["pr_number"], fake_inputs["github_token"])
    assert result["status"] == "failed"
    assert "graph build error" in result["error"]


# === ❌ Case 7: graph.invoke fails ===
@patch("app.tasks.build_graph")
@patch("app.tasks.fetch_file_content", return_value="code")
@patch("app.tasks.fetch_pr_files", return_value=[{"filename": "file1.py"}])
@patch("app.tasks.get_latest_commit_sha", return_value="abc123")
@patch("app.tasks.parse_repo_url", return_value=("user", "repo"))
def test_graph_invoke_error(mock_parse, mock_sha, mock_files, mock_content, mock_build, fake_inputs, mock_request):
    mock_graph = MagicMock()
    mock_graph.invoke.side_effect = Exception("invoke fail")
    mock_build.return_value = (mock_graph, {})

    result = run_wrapped_task(mock_request, fake_inputs["repo_url"], fake_inputs["pr_number"], fake_inputs["github_token"])
    assert result["status"] == "failed"
    assert "invoke fail" in result["error"]


# === ❌ Case 8: markdown generation fails ===
@patch("app.tasks.generate_github_markdown_review", side_effect=Exception("markdown error"))
@patch("app.tasks.build_graph")
@patch("app.tasks.fetch_file_content", return_value="code")
@patch("app.tasks.fetch_pr_files", return_value=[{"filename": "file1.py"}])
@patch("app.tasks.get_latest_commit_sha", return_value="abc123")
@patch("app.tasks.parse_repo_url", return_value=("user", "repo"))
def test_markdown_gen_fails(mock_parse, mock_sha, mock_files, mock_content, mock_build, mock_md, fake_inputs, mock_request):
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {"results": [{"filename": "file.py", "issues": []}]}
    mock_build.return_value = (mock_graph, {})

    result = run_wrapped_task(mock_request, fake_inputs["repo_url"], fake_inputs["pr_number"], fake_inputs["github_token"])
    assert result["status"] == "failed"
    assert "markdown error" in result["error"]


# === ❌ Case 9: posting comment fails ===
@patch("app.tasks.post_general_pr_comment", side_effect=Exception("post fail"))
@patch("app.tasks.generate_github_markdown_review", return_value="markdown")
@patch("app.tasks.build_graph")
@patch("app.tasks.fetch_file_content", return_value="code")
@patch("app.tasks.fetch_pr_files", return_value=[{"filename": "file1.py"}])
@patch("app.tasks.get_latest_commit_sha", return_value="abc123")
@patch("app.tasks.parse_repo_url", return_value=("user", "repo"))
def test_post_comment_fail(mock_parse, mock_sha, mock_files, mock_content, mock_build, mock_md, mock_post, fake_inputs, mock_request):
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {"results": [{"filename": "file.py", "issues": []}]}
    mock_build.return_value = (mock_graph, {})

    result = run_wrapped_task(mock_request, fake_inputs["repo_url"], fake_inputs["pr_number"], fake_inputs["github_token"])
    assert result["status"] == "failed"
    assert "post fail" in result["error"]
