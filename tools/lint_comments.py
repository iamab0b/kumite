import ast
import io
import json
import os
import subprocess
import sys
import tokenize

PY_PRAGMAS = ("# noqa", "# type:", "# pragma:", "# fmt:", "# isort:")
JS_PRAGMAS = ("// eslint", "// @ts-", "// prettier", "// biome", "/* eslint", "/// <reference")
CODE_SUFFIXES = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".ps1", ".sh")
SKIP_DIRS = {"node_modules", ".venv", "venv", "dist", "out", "build", ".vite", "__pycache__", ".git", "prep", "data"}
WORD_START = " \t;(&|"


def python_findings(text):
    findings = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError, IndentationError):
        return findings
    for tok in tokens:
        if tok.type != tokenize.COMMENT:
            continue
        if tok.start[0] == 1 and tok.string.startswith("#!"):
            continue
        if tok.string.startswith(PY_PRAGMAS):
            continue
        findings.append((tok.start[0], tok.string.strip()))
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return findings
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list):
            continue
        for stmt in body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                findings.append((stmt.lineno, "docstring or bare string statement"))
    return sorted(findings)


def js_findings(text):
    findings = []
    i = 0
    n = len(text)
    line = 1
    quote = None
    while i < n:
        ch = text[i]
        if ch == "\n":
            line += 1
            i += 1
            continue
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            i += 1
            continue
        if text.startswith("//", i):
            end = text.find("\n", i)
            end = n if end == -1 else end
            body = text[i:end]
            if not body.startswith(JS_PRAGMAS):
                findings.append((line, body.strip()))
            i = end
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            end = n if end == -1 else end + 2
            body = text[i:end]
            if not body.startswith(JS_PRAGMAS):
                findings.append((line, body.splitlines()[0].strip()))
            line += body.count("\n")
            i = end
            continue
        i += 1
    return findings


def hash_findings(text, block_open=None, block_close=None):
    findings = []
    quote = None
    in_block = False
    for lineno, raw in enumerate(text.splitlines(), 1):
        if lineno == 1 and raw.startswith("#!"):
            continue
        i = 0
        while i < len(raw):
            ch = raw[i]
            if in_block:
                end = raw.find(block_close, i)
                if end == -1:
                    break
                in_block = False
                i = end + len(block_close)
                continue
            if quote:
                if ch == quote:
                    quote = None
                i += 1
                continue
            if ch in ("'", '"'):
                quote = ch
                i += 1
                continue
            if block_open and raw.startswith(block_open, i):
                findings.append((lineno, raw[i:].strip()))
                in_block = True
                i += len(block_open)
                continue
            if ch == "#" and (i == 0 or raw[i - 1] in WORD_START):
                findings.append((lineno, raw[i:].strip()))
                break
            i += 1
    return findings


def findings_for(path, text):
    suffix = os.path.splitext(path)[1].lower()
    if suffix == ".py":
        return python_findings(text)
    if suffix in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
        return js_findings(text)
    if suffix == ".ps1":
        return hash_findings(text, "<#", "#>")
    if suffix == ".sh":
        return hash_findings(text)
    return []


def iter_files(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for f in files:
                    if f.lower().endswith(CODE_SUFFIXES):
                        yield os.path.join(root, f)
        elif p.lower().endswith(CODE_SUFFIXES) and os.path.isfile(p):
            yield p


def lint(paths):
    report = []
    for path in iter_files(paths):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        for line, body in findings_for(path, text):
            report.append(f"{path}:{line}: {body}")
    return report


def contract_check(paths):
    normalized = [p.replace("\\", "/") for p in paths]
    if not any("/contracts/" in p or "/data/samples/" in p for p in normalized):
        return []
    root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    script = os.path.join(root, "contracts", "validate.py")
    if not os.path.isfile(script):
        return []
    result = subprocess.run([sys.executable, script], capture_output=True, text=True, cwd=root)
    if result.returncode == 0:
        return []
    return ["contracts/validate.py failed:", result.stdout.strip(), result.stderr.strip()]


def hook_paths():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return []
    tool_input = payload.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("path")
    return [path] if path else []


def main(argv):
    hook = "--hook" in argv
    paths = hook_paths() if hook else [a for a in argv if not a.startswith("--")]
    report = lint(paths)
    if hook:
        report += contract_check(paths)
    if not report:
        return 0
    sys.stderr.write("Comments and docstrings are not allowed in code files; move the explanation to docs/ or the commit message.\n")
    sys.stderr.write("\n".join(r for r in report[:60] if r) + "\n")
    return 2 if hook else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
