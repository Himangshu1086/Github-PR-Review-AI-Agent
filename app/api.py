from fastapi import APIRouter
from app.schemas import AnalyzePRRequest
from app.tasks import analyze_pr_task
from fastapi import HTTPException
from app.worker import celery_app
from app.lib.logger import logger  # <-- Add this import

router = APIRouter()

@router.post("/analyze-pr")
def analyze_pr(request: AnalyzePRRequest):
    logger.info(f"Received analyze-pr request: repo_url={request.repo_url}, pr_number={request.pr_number}")
    task = analyze_pr_task.delay(request.repo_url, request.pr_number, request.github_token)
    logger.info(f"Dispatched analyze_pr_task with id: {task.id}")
    return {"task_id": task.id}

@router.get("/status/{task_id}")
def get_status(task_id: str):
    logger.info(f"Checking status for task_id: {task_id}")
    result = celery_app.AsyncResult(task_id)
    logger.info(f"Task {task_id} status: {result.status}")
    return {"task_id": task_id, "status": result.status}

@router.get("/results/{task_id}")
def get_results(task_id: str):
    logger.info(f"Fetching results for task_id: {task_id}")
    result = celery_app.AsyncResult(task_id)
    if result.ready():
        logger.info(f"Task {task_id} completed. Returning result.")
        return result.result
    logger.warning(f"Task {task_id} not yet complete.")
    raise HTTPException(status_code=202, detail="Task not yet complete")