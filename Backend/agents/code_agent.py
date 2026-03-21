import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from llm.llm_router import ask_llm


def run_code_review(diff_data: dict) -> str:
    """Run code review on a commit diff using LLM directly"""

    # Format the diff for the prompt
    formatted_diff = f"""
Commit : {diff_data.get('sha', 'N/A')}
Author : {diff_data.get('author', 'N/A')}
Message: {diff_data.get('message', 'N/A')}

Changed Files:
"""
    for f in diff_data.get("files", []):
        formatted_diff += f"""
--- {f['filename']} ({f['status']}) ---
+{f['additions']} additions, -{f['deletions']} deletions

Diff:
{f['patch'][:2000]}
"""

    prompt = f"""
You are a Senior Code Reviewer with 10+ years of experience.

Review the following code changes and provide a structured report with exactly these 7 sections:

1. **Summary**         - What does this change do?
2. **Bugs Found**      - Any logical errors or bugs?
3. **Security Issues** - Any vulnerabilities?
4. **Code Quality**    - Style, readability, best practices?
5. **Performance**     - Any performance concerns?
6. **Suggestions**     - Specific improvements with examples
7. **Overall Score**   - Rate: Excellent / Good / Needs Work / Poor

Code Changes:
{formatted_diff}

Provide a thorough, professional review.
"""

    result = ask_llm(prompt)
    return result