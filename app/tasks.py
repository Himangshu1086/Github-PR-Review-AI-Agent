from app.worker import celery_app
import time
from app.github import parse_repo_url, fetch_pr_files, fetch_file_content
import asyncio
from app.agent_langgraph import build_graph
from app.github import post_general_pr_comment
from app.utils import code_review_json_to_markdown

@celery_app.task(bind=True)
def analyze_pr_task(self, repo_url, pr_number, github_token):
    try:
        owner, repo = parse_repo_url(repo_url)

        async def gather_code():
            files_info = await fetch_pr_files(owner, repo, pr_number, github_token)
            all_files = []
            for f in files_info:
                file_path = f["filename"]
                content = await fetch_file_content(owner, repo, file_path, github_token)
                all_files.append({"filename": file_path, "content": content, "owner": owner, "repo": repo, "pr_number": pr_number})
            return all_files

        files = asyncio.run(gather_code())

        graph, state = build_graph(files)
        final_state = graph.invoke(state)

        markdown_comments = code_review_json_to_markdown(final_state["results"])
        post_general_pr_comment(owner, repo, pr_number, str(markdown_comments), github_token)

        return {
            "task_id": self.request.id,
            "status": "completed",
            "results": {
                "raw_output": final_state["results"]
            }
        }

    except Exception as e:
        return {"status": "failed", "error": str(e)}
    



