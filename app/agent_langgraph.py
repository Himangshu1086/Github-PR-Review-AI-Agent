from dotenv import load_dotenv
load_dotenv()
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain_core.runnables import RunnableLambda
from typing import Dict, List, TypedDict, Any
from app.prompt import make_review_prompt
import os
import json


llm = ChatOpenAI(model="gpt-4", temperature=0.3)

class ReviewState(TypedDict):
    files: List[Dict[str, Any]]
    index: int
    current_file: Dict[str, Any]
    results: List[Any]
    current_result: Any
    owner: str
    repo: str
    pr_number: int

### NODES ###

def analyze_file(state: Dict) -> Dict:
    try:
        file = state["current_file"]
        state['owner'] = file['owner']
        state['repo'] = file['repo']
        state['pr_number'] = file['pr_number'] 
        prompt = make_review_prompt(file["filename"], file["content"])
        response = llm.invoke([HumanMessage(content=prompt)]).content
        return {**state, "current_result": {"filename": file["filename"], "code_review": json.loads(response)}}
    except Exception as e:
        print(f"Error in analyze_file: {e}")
        file = state.get("current_file", {})
        return {**state, "current_result": {"filename": file.get("filename", "unknown"), "code_review": str(e)}}

def collect_result(state: Dict) -> Dict:
    try:
        if "current_result" not in state:
            print("Warning: 'current_result' missing in state during collect_result. Appending error placeholder.")
            file = state.get("current_file", {})
            result_to_add = {"filename": file.get("filename", "unknown"), "code_review": "Error: current_result missing"}
        else:
            result_to_add = state["current_result"]
        results = state["results"] + [result_to_add]
        new_state = dict(state)
        new_state["results"] = results
        new_state.pop("current_result", None)
        return new_state
    except Exception as e:
        print(f"Error in collect_result: {e}")
        file = state.get("current_file", {})
        return {**state, "error": str(e), "current_result": {"filename": file.get("filename", "unknown"), "code_review": str(e)}}

def add_inline_comments(state: Dict) -> Dict:
    try:
        owner = state.get("owner")
        repo = state.get("repo")
        pr_number = state.get("pr_number")
        results = state.get("results", [])

        # for result in results:
        #     filename = result.get("filename")
        #     code_review = result.get("code_review")
        #     # If code_review is a list of issues, post each as an inline comment
        #     if isinstance(code_review, list):
        #         for issue in code_review:
        #             line = issue.get("line")
        #             body = issue.get("issue")
        #             suggestion = issue.get("suggestion")
        #             comment_body = body
        #             if suggestion:
        #                 comment_body += f"\nSuggestion: {suggestion}"
        #             if owner and repo and pr_number and filename and line and comment_body:
        #                 post_general_pr_comment(owner, repo, pr_number, comment_body)
        
        return state
    except Exception as e:
        print(f"Error in add_inline_comments: {e}")
        return {**state, "error": str(e)}

def increment_index(state: Dict) -> Dict:
    try:
        state = dict(state)
        state["index"] += 1
        if state["index"] < len(state["files"]):
            state["current_file"] = state["files"][state["index"]]
        return state
    except Exception as e:
        print(f"Error in increment_index: {e}")
        return {**state, "error": str(e)}

def cleanup_state(state: Dict) -> Dict:
    try:
        new_state = dict(state)
        new_state.pop("current_result", None)
        return new_state
    except Exception as e:
        print(f"Error in cleanup_state: {e}")
        return {**state, "error": str(e)}

### GRAPH ###

def build_graph(files: List[Dict]):
    builder = StateGraph(ReviewState)

    initial_state = {
        "files": files,
        "index": 0,
        "current_file": files[0],
        "results": [],
        # if needed for context
        # "owner": owner,
        # "repo": repo,
        # "pr_number": pr_number,
    }

    builder.add_node("analyze_file", RunnableLambda(analyze_file))
    builder.add_node("collect_result", RunnableLambda(collect_result))
    builder.add_node("add_inline_comments", RunnableLambda(add_inline_comments))
    builder.add_node("increment_index", RunnableLambda(increment_index))
    builder.add_node("cleanup_state", RunnableLambda(cleanup_state))

    builder.set_entry_point("analyze_file")
    builder.add_edge("analyze_file", "collect_result")
    builder.add_edge("collect_result", "add_inline_comments")
    builder.add_edge("add_inline_comments", "increment_index")

    def should_continue(state: Dict):
        return "analyze_file" if state["index"] < len(state["files"]) else "cleanup_state"

    builder.add_conditional_edges("increment_index", should_continue)
    builder.set_finish_point("cleanup_state")

    return builder.compile(), initial_state



