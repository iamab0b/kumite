import json
import sys
import textwrap
from lint_comments import findings_for


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    tool_input = payload.get("tool_input") or {}
    path = tool_input.get("file_path") or ""
    pieces = []
    if "content" in tool_input:
        pieces.append(tool_input["content"] or "")
    if "new_string" in tool_input:
        pieces.append(tool_input["new_string"] or "")
    for edit in tool_input.get("edits") or []:
        pieces.append(edit.get("new_string") or "")
    findings = []
    for piece in pieces:
        findings += findings_for(path, textwrap.dedent(piece))
    if not findings:
        return 0
    sys.stderr.write("Refused: this edit adds comments or docstrings to a code file. Put the explanation in docs/ or the commit message and retry without them.\n")
    for line, body in findings[:20]:
        sys.stderr.write(f"{path}:{line}: {body}\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
