from app.worker import celery_app
import time
from app.github import parse_repo_url, fetch_pr_files, fetch_file_content
import asyncio
from app.agent_langgraph import build_graph
from app.github import post_general_pr_comment,get_latest_commit_sha
from app.utils import generate_github_markdown_review
from app.lib.logger import logger  

@celery_app.task(bind=True)
def analyze_pr_task(self, repo_url, pr_number, github_token):
    try:
        logger.info(f"Starting analyze_pr_task for repo_url={repo_url}, pr_number={pr_number}")
        owner, repo = parse_repo_url(repo_url)
        logger.info(f"Parsed repo: owner={owner}, repo={repo}")
        commit_sha = get_latest_commit_sha(owner, repo, pr_number, github_token)

        async def gather_code():
            files_info = await fetch_pr_files(owner, repo, pr_number, github_token)
            logger.info(f"Fetched {len(files_info)} files for PR #{pr_number}")
            all_files = []
            for f in files_info:
                file_path = f["filename"]
                try:
                    content = await fetch_file_content(owner, repo, file_path, commit_sha, github_token)
                    logger.info(f"Fetched content for file: {file_path}")
                    all_files.append({
                        "filename": file_path,
                        "content": content,
                        "owner": owner,
                        "repo": repo,
                        "pr_number": pr_number
                    })
                except Exception as e:
                    logger.error(f"Skipping file {file_path} due to error: {e}")
            return all_files

        files = asyncio.run(gather_code())
        logger.info(f"Total valid files to review: {len(files)}")

        if not files:
            return {"status": "failed", "error": "No valid files to review."}

        def chunked(files, size):
            for i in range(0, len(files), size):
                yield files[i:i + size]

        batch_results = []
        for idx, batch in enumerate(chunked(files, 20), start=1):
            logger.info(f"Processing batch {idx} with {len(batch)} files")
            graph, state = build_graph(batch)
            final_state = graph.invoke(state, {"recursion_limit": 150})
            batch_results.extend(final_state["results"])

            markdown_comments = generate_github_markdown_review(final_state['results'])
            comment_title = f"🧪 Code Review Summary - Batch {idx}"
            logger.info(f"Posting PR comment for batch {idx}")
            post_general_pr_comment(owner, repo, pr_number, f"{comment_title}\n\n{markdown_comments}", github_token)

        logger.info(f"analyze_pr_task completed for PR #{pr_number}")
        return {
            "task_id": self.request.id,
            "status": "completed",
            "results": {
                "raw_output": batch_results
            }
        }

    except Exception as e:
        logger.error(f"Error in analyze_pr_task: {e}")
        return {"status": "failed", "error": str(e)}


# @celery_app.task(bind=True)
# def analyze_pr_task(self, repo_url, pr_number, github_token):
#     try:
#         logger.info(f"Starting analyze_pr_task for repo_url={repo_url}, pr_number={pr_number}")
#         owner, repo = parse_repo_url(repo_url)
#         logger.info(f"Parsed repo: owner={owner}, repo={repo}")
#         commit_sha = get_latest_commit_sha(owner, repo, pr_number, github_token)

#         async def gather_code():
#             files_info = await fetch_pr_files(owner, repo, pr_number, github_token)
#             logger.info(f"Fetched {len(files_info)} files for PR #{pr_number}")
#             all_files = []
#             for f in files_info:
#                 file_path = f["filename"]
#                 content = await fetch_file_content(owner, repo, file_path, commit_sha, github_token)
#                 logger.info(f"Fetched content for file: {file_path}")
#                 all_files.append({"filename": file_path, "content": content, "owner": owner, "repo": repo, "pr_number": pr_number})
#             return all_files

#         files = asyncio.run(gather_code())
#         logger.info(f"Total files to review: {len(files)}")

#         graph, state = build_graph(files)
#         logger.info("Graph built, invoking...")
#         final_state = graph.invoke(state, {"recursion_limit": 150})
#         logger.info("Graph execution complete.")
#         markdown_comments = generate_github_markdown_review(final_state['results'])
#         logger.info("Posting general PR comment with markdown summary.")
#         post_general_pr_comment(owner, repo, pr_number, str(markdown_comments), github_token)

#         logger.info(f"analyze_pr_task completed for PR #{pr_number}")
#         return {
#             "task_id": self.request.id,
#             "status": "completed",
#             "results": {
#                 "raw_output": final_state["results"]
#             }
#         }

#     except Exception as e:
#         logger.error(f"Error in analyze_pr_task: {e}")
#         return {"status": "failed", "error": str(e)}
    
