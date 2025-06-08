def code_review_json_to_markdown(reviews):
    md_output = []

    for file_review in reviews:
        filename = file_review.get("filename", "unknown file")
        md_output.append(f"### 📄 File: `{filename}`\n")

        for issue in file_review.get("code_review", []):
            line = issue.get("line", "?")
            desc = issue.get("issue", "No description provided.")
            md_output.append(f"- **Line {line}**: {desc}")

        md_output.append("")  # newline between files

    return "\n\n".join(md_output)
