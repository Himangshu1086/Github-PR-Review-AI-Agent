
def make_review_prompt(filename: str, code: str) -> str:
    return f"""
You are a senior software engineer reviewing a pull request.

Your review should follow professional standards as outlined here:
https://google.github.io/eng-practices/review/reviewer/standard.html

Please analyze the following file and return your review as a JSON object in the following format:

{{
    "files": [
        {{
            "name": "{filename}",
            "issues": [
                {{
                    "type": "bug" | "style" | "performance" | "best_practice" | "readability" | "future_risk",
                    "line": <line_number>,
                    "description": "<clear explanation of the issue or concern>",
                    "suggestion": "<concise, actionable recommendation>"
                }},
                ...
            ]
        }}
    ],
    "summary": {{
        "total_files": <number_of_files_reviewed>,
        "total_issues": <total_number_of_issues_found>,
        "critical_issues": <number_of_critical_issues>
    }}
}}

Guidelines:
- Identify any potential **bugs or logic errors**.
- Flag violations of **style, naming, or formatting conventions**.
- Suggest improvements for **readability, maintainability**, and **performance**.
- Warn about **future risks**, such as fragile logic, unhandled edge cases, or scalability bottlenecks.
- Only flag real issues — do not invent problems or give vague advice.
- Do not review the code as if you're rewriting it yourself — focus on improving what's already there.

Now review the following file:

File: {filename}
Code:
{code}

Only output the JSON object, nothing else.
"""