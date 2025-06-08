import pytest
from app.prompt import make_review_prompt
from app.agent_langgraph import collect_result
from app.agent_langgraph import cleanup_state
import json
from unittest.mock import patch, MagicMock
from app.agent_langgraph import analyze_file



@pytest.fixture
def sample_state():
    return {
        "current_file": {
            "filename": "sample.py",
            "content": "\n".join([f"line {i}" for i in range(1000)]),  # triggers chunking
            "owner": "octocat",
            "repo": "test-repo",
            "pr_number": 42
        }
    }

# ✅ Success: Multiple chunks processed with valid JSON
@patch("langchain_openai.ChatOpenAI.invoke")
@patch("app.agent_langgraph.make_review_prompt", wraps=make_review_prompt)
def test_analyze_file_success_multiple_chunks(mock_prompt, mock_invoke, sample_state):
    mock_invoke.return_value.content = '{"files": [], "summary": {"total_issues": 0, "critical_issues": 0}}'

    result = analyze_file(sample_state)
    assert "current_result" in result
    assert result["current_result"]["filename"] == "sample.py"
    assert isinstance(result["current_result"]["code_review"], list)
    assert all(isinstance(c, dict) for c in result["current_result"]["code_review"])
    assert mock_invoke.call_count >= 2  # multiple chunks
    assert mock_prompt.call_count == mock_invoke.call_count

# ❌ LLM returns invalid JSON for one chunk
@patch("langchain_openai.ChatOpenAI.invoke", side_effect=[
    MagicMock(content='{"files": [], "summary": {"total_issues": 1, "critical_issues": 0}}'),
    MagicMock(content="INVALID_JSON")
])
def test_analyze_file_partial_invalid_json(mock_invoke, sample_state):
    result = analyze_file(sample_state)
    reviews = result["current_result"]["code_review"]
    assert isinstance(reviews, list)
    # Fix: Ensure fallback chunk error is preserved
    assert any(isinstance(chunk, dict) and "error" in chunk for chunk in reviews)


# ❌ Entire prompt call fails (simulate LLM crash)
@patch("langchain_openai.ChatOpenAI.invoke", side_effect=Exception("LLM crashed"))
def test_analyze_file_invoke_crash(mock_invoke, sample_state):
    result = analyze_file(sample_state)
    reviews = result["current_result"]["code_review"]
    assert isinstance(reviews, str) or isinstance(reviews, list)
    
    # If returned as a str due to total failure
    if isinstance(reviews, str):
        assert "LLM crashed" in reviews
    else:
        assert any("LLM crashed" in json.dumps(chunk) for chunk in reviews)


def test_analyze_file_single_chunk(monkeypatch):
    mock_response = MagicMock()
    mock_response.content = '{"files": [], "summary": {"total_issues": 0, "critical_issues": 0}}'

    with patch("langchain_openai.ChatOpenAI.invoke", return_value=mock_response):
        state = {
            "current_file": {
                "filename": "quick.py",
                "content": "print('ok')",
                "owner": "octocat",
                "repo": "repo",
                "pr_number": 1
            }
        }
        result = analyze_file(state)
        assert result["current_result"]["filename"] == "quick.py"


# ✅ Edge Case: Empty file content
def test_analyze_file_empty_content():
    state = {
        "current_file": {
            "filename": "empty.py",
            "content": "",
            "owner": "octocat",
            "repo": "test-repo",
            "pr_number": 1
        }
    }
    result = analyze_file(state)
    assert result["current_result"]["filename"] == "empty.py"
    assert result["current_result"]["code_review"] == []

# ❌ Critical state missing (missing 'current_file')
def test_analyze_file_missing_key():
    bad_state = {}
    result = analyze_file(bad_state)
    assert "current_result" in result
    assert "unknown" in result["current_result"]["filename"]
    assert "current_file" in result["current_result"]["code_review"]







def test_collect_result_with_current_result():
    state = {
        "current_file": {"filename": "file1.py"},
        "current_result": {"filename": "file1.py", "code_review": "Looks good"},
        "results": []
    }

    new_state = collect_result(state)

    assert "current_result" not in new_state
    assert "results" in new_state
    assert new_state["results"] == [{"filename": "file1.py", "code_review": "Looks good"}]

def test_collect_result_missing_current_result():
    state = {
        "current_file": {"filename": "file2.py"},
        "results": []
    }

    new_state = collect_result(state)

    assert "current_result" not in new_state
    assert "results" in new_state
    assert new_state["results"] == [{"filename": "file2.py", "code_review": "Error: current_result missing"}]

def test_collect_result_with_exception(monkeypatch):
    # Simulate a corrupted state (e.g., `results` is not a list)
    state = {
        "current_file": {"filename": "file3.py"},
        "current_result": {"filename": "file3.py", "code_review": "bad"},
        "results": None  # this will raise an exception when trying to add
    }

    new_state = collect_result(state)

    assert "error" in new_state
    assert "current_result" in new_state
    assert new_state["current_result"]["filename"] == "file3.py"
    assert "code_review" in new_state["current_result"]
    assert "TypeError" in new_state["error"] or "unsupported operand" in new_state["error"]










import pytest
from app.agent_langgraph import build_graph


@pytest.fixture
def sample_files():
    return [
        {
            "filename": "file1.py",
            "content": "print('Hello')",
            "owner": "octocat",
            "repo": "Hello-World",
            "pr_number": 1
        },
        {
            "filename": "file2.py",
            "content": "print('World')",
            "owner": "octocat",
            "repo": "Hello-World",
            "pr_number": 1
        }
    ]


def test_build_graph_returns_valid_outputs(sample_files):
    graph, state = build_graph(sample_files)

    assert hasattr(graph, "invoke")
    assert isinstance(state, dict)
    assert state["files"] == sample_files
    assert state["index"] == 0
    assert state["current_file"] == sample_files[0]
    assert state["results"] == []


def test_graph_executes_all_files(sample_files):
    graph, state = build_graph(sample_files)
    result = graph.invoke(state)

    assert isinstance(result, dict)
    assert "results" in result
    assert len(result["results"]) == len(sample_files)
    assert result["index"] == len(sample_files)


def test_should_continue_branching_logic(sample_files):
    # Reconstruct the branching logic manually
    def should_continue(state):
        return "analyze_file" if state["index"] < len(state["files"]) else "cleanup_state"

    assert should_continue({"index": 0, "files": [1, 2]}) == "analyze_file"
    assert should_continue({"index": 2, "files": [1, 2]}) == "cleanup_state"
