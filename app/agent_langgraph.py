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
from app.lib.logger import logger 

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
        logger.info(f"Analyzing file: {file.get('filename')}")
        state['owner'] = file['owner']
        state['repo'] = file['repo']
        state['pr_number'] = file['pr_number'] 
        prompt = make_review_prompt(file["filename"], file["content"])
        logger.debug(f"Prompt sent to LLM: {prompt[:200]}...")  # Log first 200 chars
        response = llm.invoke([HumanMessage(content=prompt)]).content
        logger.info(f"Received LLM response for {file['filename']}")
        return {**state, "current_result": {"filename": file["filename"], "code_review": json.loads(response)}}
    except Exception as e:
        logger.error(f"Error in analyze_file: {e}")
        file = state.get("current_file", {})
        return {**state, "current_result": {"filename": file.get("filename", "unknown"), "code_review": str(e)}}

def collect_result(state: Dict) -> Dict:
    try:
        if "current_result" not in state:
            logger.warning("'current_result' missing in state during collect_result. Appending error placeholder.")
            file = state.get("current_file", {})
            result_to_add = {"filename": file.get("filename", "unknown"), "code_review": "Error: current_result missing"}
        else:
            result_to_add = state["current_result"]
        results = state["results"] + [result_to_add]
        new_state = dict(state)
        new_state["results"] = results
        new_state.pop("current_result", None)
        logger.info(f"Collected result for file: {result_to_add.get('filename')}")
        return new_state
    except Exception as e:
        logger.error(f"Error in collect_result: {e}")
        file = state.get("current_file", {})
        return {**state, "error": str(e), "current_result": {"filename": file.get("filename", "unknown"), "code_review": str(e)}}

def add_inline_comments(state: Dict) -> Dict:
    try:
        owner = state.get("owner")
        repo = state.get("repo")
        pr_number = state.get("pr_number")
        results = state.get("results", [])
        logger.info(f"Preparing to add inline comments for PR {owner}/{repo}#{pr_number}")
        # (Your inline comment logic here, add logger.info/error as needed)
        return state
    except Exception as e:
        logger.error(f"Error in add_inline_comments: {e}")
        return {**state, "error": str(e)}

def increment_index(state: Dict) -> Dict:
    try:
        state = dict(state)
        state["index"] += 1
        logger.debug(f"Incremented file index to {state['index']}")
        if state["index"] < len(state["files"]):
            state["current_file"] = state["files"][state["index"]]
            logger.info(f"Set current_file to {state['current_file'].get('filename')}")
        return state
    except Exception as e:
        logger.error(f"Error in increment_index: {e}")
        return {**state, "error": str(e)}

def cleanup_state(state: Dict) -> Dict:
    try:
        new_state = dict(state)
        new_state.pop("current_result", None)
        logger.debug("Cleaned up 'current_result' from state.")
        return new_state
    except Exception as e:
        logger.error(f"Error in cleanup_state: {e}")
        return {**state, "error": str(e)}

### GRAPH ###

def build_graph(files: List[Dict]):
    logger.info(f"Building review graph for {len(files)} files.")
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
    # builder.add_node("add_inline_comments", RunnableLambda(add_inline_comments))  --> add if you want inline comments
    builder.add_node("increment_index", RunnableLambda(increment_index))
    builder.add_node("cleanup_state", RunnableLambda(cleanup_state))

    builder.set_entry_point("analyze_file")
    builder.add_edge("analyze_file", "collect_result")
    # builder.add_edge("collect_result", "add_inline_comments")  --> add if want in line comments
    builder.add_edge("collect_result", "increment_index")

    def should_continue(state: Dict):
        return "analyze_file" if state["index"] < len(state["files"]) else "cleanup_state"

    builder.add_conditional_edges("increment_index", should_continue)
    builder.set_finish_point("cleanup_state")

    logger.info("Graph build complete.")
    return builder.compile(), initial_state