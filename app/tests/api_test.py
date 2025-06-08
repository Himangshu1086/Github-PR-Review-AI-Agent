import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

@pytest.fixture
def fake_request_payload():
    return {
        "repo_url": "https://github.com/Himangshu1086/Experten",
        "pr_number": 5,
        "github_token": "fake_token"
    }

# ✅ Success path for /analyze-pr
@patch("app.api.analyze_pr_task.delay")
def test_analyze_pr_success(mock_delay, fake_request_payload):
    mock_task = MagicMock()
    mock_task.id = "test-task-id"
    mock_delay.return_value = mock_task

    response = client.post("/analyze-pr", json=fake_request_payload)

    assert response.status_code == 200
    assert response.json()["task_id"] == "test-task-id"
    mock_delay.assert_called_once()

# ✅ Invalid payload (missing required fields)
def test_analyze_pr_invalid_payload_missing_field():
    response = client.post("/analyze-pr", json={"repo_url": "https://github.com/test/repo"})
    assert response.status_code == 422  # Pydantic validation error

# ✅ Celery delay() raises an exception
@patch("app.api.analyze_pr_task.delay", side_effect=Exception("Mock Celery failure"))
def test_analyze_pr_celery_error(mock_delay, fake_request_payload):
    with pytest.raises(Exception) as exc_info:
        client.post("/analyze-pr", json=fake_request_payload)
    assert "Mock Celery failure" in str(exc_info.value)

# ✅ Logger is called in /analyze-pr
@patch("app.api.logger.info")
@patch("app.api.analyze_pr_task.delay")
def test_analyze_pr_logs_called(mock_delay, mock_logger, fake_request_payload):
    mock_task = MagicMock()
    mock_task.id = "log-test-task"
    mock_delay.return_value = mock_task

    response = client.post("/analyze-pr", json=fake_request_payload)

    assert response.status_code == 200
    assert mock_logger.call_count >= 2
    mock_logger.assert_any_call(
        f"Received analyze-pr request: repo_url={fake_request_payload['repo_url']}, pr_number={fake_request_payload['pr_number']}"
    )

# ✅ Success path for /status/{task_id}
@patch("app.api.celery_app.AsyncResult")
def test_status_check(mock_async_result):
    mock_result = MagicMock()
    mock_result.status = "PENDING"
    mock_async_result.return_value = mock_result

    response = client.get("/status/some-task-id")
    assert response.status_code == 200
    assert response.json() == {
        "task_id": "some-task-id",
        "status": "PENDING"
    }

# ✅ /results/{task_id} when ready = True and result = dict
@patch("app.api.celery_app.AsyncResult")
def test_results_ready_with_data(mock_async_result):
    mock_result = MagicMock()
    mock_result.ready.return_value = True
    mock_result.result = {"status": "completed", "data": "done"}
    mock_async_result.return_value = mock_result

    response = client.get("/results/test-task-id")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

# ✅ /results/{task_id} when ready = True and result = None
@patch("app.api.celery_app.AsyncResult")
def test_results_ready_empty_result(mock_async_result):
    mock_result = MagicMock()
    mock_result.ready.return_value = True
    mock_result.result = None
    mock_async_result.return_value = mock_result

    response = client.get("/results/test-task-id")
    assert response.status_code == 200
    assert response.json() is None

# ✅ /results/{task_id} when not ready
@patch("app.api.celery_app.AsyncResult")
def test_results_not_ready(mock_async_result):
    mock_result = MagicMock()
    mock_result.ready.return_value = False
    mock_async_result.return_value = mock_result

    response = client.get("/results/wait-task-id")
    assert response.status_code == 202
    assert response.json() == {"detail": "Task not yet complete"}
