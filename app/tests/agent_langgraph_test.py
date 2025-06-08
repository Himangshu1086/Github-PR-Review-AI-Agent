import pytest
from unittest.mock import patch, MagicMock
from app.agent_langgraph import analyze_file
from app.prompt import make_review_prompt
import pytest
from app.agent_langgraph import collect_result
from app.agent_langgraph import cleanup_state


@pytest.fixture
def sample_state():
    return {
        "current_file": {
            "filename": "sample.py",
            "content": "print('hello')",
            "owner": "octocat",
            "repo": "test-repo",
            "pr_number": 42
        }
    }

# ✅ Test: Success case
@patch("langchain_openai.ChatOpenAI.invoke")
@patch("app.agent_langgraph.make_review_prompt", wraps=make_review_prompt)
def test_analyze_file_success(mock_prompt, mock_invoke, sample_state):
    mock_invoke.return_value.content = '{"files": [], "summary": {"total_issues": 0}}'

    result = analyze_file(sample_state)

    assert "current_result" in result
    assert result["current_result"]["filename"] == "sample.py"
    assert isinstance(result["current_result"]["code_review"], dict)
    mock_prompt.assert_called_once()
    mock_invoke.assert_called_once()

# ❌ Test: LLM returns invalid JSON
@patch("langchain_openai.ChatOpenAI.invoke")
def test_analyze_file_json_error(mock_invoke, sample_state):
    mock_invoke.return_value.content = "invalid json"

    result = analyze_file(sample_state)
    assert "current_result" in result
    assert "Expecting value" in result["current_result"]["code_review"]

# ❌ Test: LLM throws an exception
@patch("langchain_openai.ChatOpenAI.invoke", side_effect=Exception("LLM unavailable"))
def test_analyze_file_invoke_exception(mock_invoke, sample_state):
    result = analyze_file(sample_state)
    assert "current_result" in result
    assert "LLM unavailable" in result["current_result"]["code_review"]





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
