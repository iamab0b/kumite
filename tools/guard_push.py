import json
import os
import re
import subprocess
import sys


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not re.search(r"\bgit\b[^|&;]*\bpush\b", command):
        return 0
    if os.environ.get("KUMITE_ALLOW_MAIN_PUSH") == "1":
        return 0
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=root).stdout.strip()
    names_main = re.search(r"\bpush\b.*\bmain\b", command) is not None
    if branch == "main" or names_main:
        sys.stderr.write("Pushing main directly is refused; work on a branch and merge after review. Set KUMITE_ALLOW_MAIN_PUSH=1 for a deliberate exception.\n")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
