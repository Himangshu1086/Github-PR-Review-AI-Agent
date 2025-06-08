from app.lib.logger import logger

def code_review_json_to_markdown(reviews):
    md_output = []

    logger.info(f"Converting {len(reviews)} reviews to markdown format.")
    for file_review in reviews:
        filename = file_review.get("filename", "unknown file")
        md_output.append(f"### 📄 File: `{filename}`\n")
        logger.debug(f"Processing file: {filename}")

        for issue in file_review.get("code_review", []):
            line = issue.get("line", "?")
            desc = issue.get("issue", "No description provided.")
            md_output.append(f"- **Line {line}**: {desc}")
            logger.debug(f"Added issue for line {line}: {desc}")

        md_output.append("")  # newline between files

    logger.info("Markdown conversion complete.")
    return "\n\n".join(md_output)
