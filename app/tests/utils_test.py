import pytest
from unittest.mock import patch
from app.utils import generate_github_markdown_review

# === Fixture: Normal code review with issues ===
@pytest.fixture
def sample_review_data():
    return [
        {
            "filename": "frontend/src/App.js",
            "code_review": {
                "files": [
                    {
                        "name": "frontend/src/App.js",
                        "issues": [
                            {
                                "type": "style",
                                "line": 1,
                                "description": "Format issue",
                                "suggestion": "Fix formatting"
                            },
                            {
                                "type": "bug",
                                "line": 2,
                                "description": "Null pointer possible",
                                "suggestion": "Add null check"
                            }
                        ]
                    }
                ],
                "summary": {
                    "total_files": 1,
                    "total_issues": 2,
                    "critical_issues": 1
                }
            }
        }
    ]

# === ✅ Test normal markdown output ===
def test_generate_github_markdown_output(sample_review_data):
    markdown = generate_github_markdown_review(sample_review_data)

    assert "### 📄 `frontend/src/App.js`" in markdown
    assert "- **Line 1** [Style]: Format issue" in markdown
    assert "- **Line 2** [Bug]: Null pointer possible" in markdown
    assert "💡 _Suggestion_: Add null check" in markdown
    assert "> 🔎 **Summary**: 2 issue(s), 1 critical" in markdown

# === ✅ Test empty input handling ===
def test_empty_review_data():
    markdown = generate_github_markdown_review([])
    expected = "### 📄 `Unknown File`\n\n> 🔎 **Summary**: 0 issue(s), 0 critical\n"
    assert markdown == expected

# === ✅ Test file with no issues ===
def test_review_data_without_issues():
    data = [{
        "filename": "frontend/src/Empty.js",
        "code_review": {
            "files": [],
            "summary": {
                "total_issues": 0,
                "critical_issues": 0
            }
        }
    }]
    markdown = generate_github_markdown_review(data)
    assert "frontend/src/Empty.js" in markdown
    assert "0 issue(s), 0 critical" in markdown

# === ✅ Logger is invoked ===
@patch("app.utils.logger")
def test_logger_calls(mock_logger, sample_review_data):
    _ = generate_github_markdown_review(sample_review_data)

    mock_logger.info.assert_any_call("Starting to generate GitHub markdown review.")
    mock_logger.info.assert_any_call("Summary for frontend/src/App.js: 2 issues, 1 critical.")
    mock_logger.info.assert_any_call("Completed generating GitHub markdown review.")
    assert mock_logger.debug.call_count >= 2
