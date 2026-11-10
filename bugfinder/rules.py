from __future__ import annotations

import ast
import os
import re
from pathlib import Path

from bugfinder.models import Finding

EXTENSIONS = {
    ".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".java", ".c",
    ".h", ".cpp", ".hpp", ".cc", ".cs", ".php", ".go", ".rs", ".rb",
    ".html", ".htm", ".css", ".sql", ".json", ".yaml", ".yml",
}
IGNORED = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build", "target", "vendor",
}
MAX_BYTES = 1_500_000

RULES = [
    ("BFSEC001", "Possible hard-coded credential", "high", "medium",
     re.compile(r"""(?i)\b(?:api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*["'][^"'\s]{8,}["']"""),
     "A value resembling a credential is assigned directly in source code.",
     "Move the secret to a protected environment variable or secret manager. Rotate it if it was real."),
    ("BFSEC002", "Use of eval-like dynamic execution", "high", "medium",
     re.compile(r"\b(?:eval|exec)\s*\("),
     "Dynamic execution can run input as code and may create an injection risk.",
     "Avoid dynamic execution. Use a parser or explicit allow-listed operations instead."),
    ("BFSEC003", "Possible SQL string construction", "medium", "low",
     re.compile(r"(?i)\b(?:execute|executemany)\s*\([^)]*(?:\+|%s\s*%)"),
     "SQL may be assembled through string concatenation or interpolation.",
     "Use parameterized queries and pass values separately from the SQL statement."),
    ("BFSEC004", "TLS certificate verification disabled", "high", "medium",
     re.compile(r"(?i)(?:verify\s*=\s*False|CERT_NONE|rejectUnauthorized\s*:\s*false)"),
     "Certificate verification appears to be disabled.",
     "Keep certificate verification enabled and configure trusted certificates correctly."),
    ("BFSEC005", "Potentially unsafe HTML insertion", "medium", "low",
     re.compile(r"\.innerHTML\s*="),
     "HTML is assigned directly; untrusted content could create a cross-site scripting risk.",
     "Prefer textContent or safely sanitize and validate HTML before insertion."),
    ("BFSEC006", "Wildcard CORS configuration", "low", "low",
     re.compile(r"""(?i)(?:Access-Control-Allow-Origin\s*[:=]\s*["']\*["']|cors\s*\(\s*\{\s*origin\s*:\s*["']\*["'])"""),
     "A wildcard CORS origin appears in the code.",
     "Restrict cross-origin access to the specific origins that need it."),
    ("BFPERF001", "Potentially broad SQL query", "low", "low",
     re.compile(r"(?i)\bSELECT\s+\*\s+FROM\b"),
     "A SELECT * query may fetch more data than the caller needs.",
     "Select only required columns and consider pagination for large result sets."),
    ("BFQUAL001", "Debug print statement", "info", "low",
     re.compile(r"(?<![\w.])print\s*\("),
     "A print statement may be leftover debugging output.",
     "Use the project's logging system or remove the statement if it is not needed."),
]

def _make(rule, path, line, column=1):
    rid, title, severity, confidence, _, message, fix = rule
    return Finding(rid, title, severity, confidence, message, fix, str(path), line, column)

def scan_text(path: Path, text: str) -> list[Finding]:
    findings = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for rule in RULES:
            match = rule[4].search(line)
            if match:
                findings.append(_make(rule, path, line_no, match.start() + 1))
    if path.suffix.lower() == ".py":
        findings.extend(_scan_python(path, text))
    return findings

def _scan_python(path, text):
    found = []
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        found.append(Finding(
            "BFPY001", "Python syntax error", "high", "high",
            exc.msg or "Python syntax error.",
            "Correct the syntax at this location, then run the scan again.",
            str(path), max(1, exc.lineno or 1), max(1, exc.offset or 1)))
        return found
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec"}:
                found.append(Finding(
                    "BFPY002", "Dynamic Python code execution", "high", "high",
                    f"{node.func.id}() executes dynamically supplied code.",
                    "Replace dynamic execution with explicit parsing or allow-listed logic.",
                    str(path), node.lineno, node.col_offset + 1))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "Popen" and any(
                isinstance(k, ast.keyword) and k.arg == "shell"
                and isinstance(k.value, ast.Constant) and k.value.value is True
                for k in node.keywords
            ):
                found.append(Finding(
                    "BFPY003", "Shell execution enabled", "medium", "medium",
                    "subprocess.Popen appears to enable shell execution.",
                    "Prefer argument lists with shell=False; validate inputs if shell use is unavoidable.",
                    str(path), node.lineno, node.col_offset + 1))
    return found

def iter_source_files(root: Path):
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in IGNORED]
        for name in names:
            candidate = Path(current) / name
            try:
                if candidate.is_symlink() or candidate.suffix.lower() not in EXTENSIONS:
                    continue
                if candidate.stat().st_size > MAX_BYTES:
                    continue
            except OSError:
                continue
            yield candidate

def scan_project(root: Path):
    root = root.resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Project directory does not exist: {root}")
    results = []
    for path in iter_source_files(root):
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            results.extend(scan_text(path.relative_to(root), source))
        except OSError:
            continue
    return results
