from fastapi import APIRouter
from app.schemas import AnalyzePRRequest
from app.tasks import analyze_pr_task
from fastapi import HTTPException
from app.worker import celery_app


router = APIRouter()

@router.post("/analyze-pr")
def analyze_pr(request: AnalyzePRRequest):
    task = analyze_pr_task.delay(request.repo_url, request.pr_number, request.github_token)
    return {"task_id": task.id}


@router.get("/status/{task_id}")
def get_status(task_id: str):
    result = celery_app.AsyncResult(task_id)
    return {"task_id": task_id, "status": result.status}


@router.get("/results/{task_id}")
def get_results(task_id: str):
    result = celery_app.AsyncResult(task_id)
    if result.ready():
        return result.result
    raise HTTPException(status_code=202, detail="Task not yet complete")
