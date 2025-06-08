from app.lib.logger import logger


def generate_github_markdown_review(data):
    lines = []
    logger.info("Starting to generate GitHub markdown review.")

    for review in data:
        filename = review.get("filename", "Unknown File")
        lines.append(f"### 📄 `{filename}`")
        logger.debug(f"Processing file: {filename}")

        review_data = review.get("code_review", {})
        for file in review_data.get("files", []):
            for issue in file.get("issues", []):
                issue_type = issue.get("type", "info").capitalize()
                line_number = issue.get("line", "?")
                description = issue.get("description", "No description")
                suggestion = issue.get("suggestion", "No suggestion")

                lines.append(f"- **Line {line_number}** [{issue_type}]: {description}")
                lines.append(f"  - 💡 _Suggestion_: {suggestion}")
                logger.debug(f"Issue found: {issue_type} at line {line_number}")

        summary = review_data.get("summary", {})
        total = summary.get("total_issues", 0)
        critical = summary.get("critical_issues", 0)
        lines.append(f"\n> 🔎 **Summary**: {total} issue(s), {critical} critical\n")
        logger.info(f"Summary for {filename}: {total} issues, {critical} critical.")

    logger.info("Completed generating GitHub markdown review.")
    return "\n".join(lines)
