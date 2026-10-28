from __future__ import annotations

import ast
import io
import subprocess
import tokenize
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]

_SCANNED_SUFFIXES = {
    ".py",
    ".toml",
    ".yaml",
    ".yml",
    ".tf",
    ".sh",
    ".ps1",
    ".json",
}
_SCANNED_NAMES = {"Dockerfile", ".env.example"}

_HASH_COMMENT_SUFFIXES = {".toml", ".yaml", ".yml", ".tf", ".sh", ".ps1"}
_HASH_COMMENT_NAMES = {"Dockerfile", ".env.example"}

_PLACEHOLDER_SECRET_KEYS = {
    "OPENROUTER_API_KEY",
    "QUERYN_API_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "LANGCHAIN_API_KEY",
}

_SECRET_MARKERS = ("sk-", "aws_", "AKIA")


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(_REPO_ROOT), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    staged = subprocess.run(
        ["git", "-C", str(_REPO_ROOT), "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
    )
    names = set(result.stdout.splitlines()) | set(staged.stdout.splitlines())
    paths: list[Path] = []
    for name in sorted(names):
        if not name:
            continue
        path = _REPO_ROOT / name
        if path.is_file():
            paths.append(path)
    return paths


def _should_scan(path: Path) -> bool:
    if path.name in _SCANNED_NAMES:
        return True
    return path.suffix in _SCANNED_SUFFIXES


def _python_violations(path: Path, text: str) -> list[str]:
    violations: list[str] = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError) as exc:
        return [f"{path}: could not tokenize ({exc})"]
    for token in tokens:
        if token.type == tokenize.COMMENT:
            violations.append(f"{path}:{token.start[0]}: python comment")
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return violations + [f"{path}: could not parse ({exc})"]
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                violations.append(f"{path}: docstring in {type(node).__name__}")
    return violations


def _hash_comment_violations(path: Path, text: str) -> list[str]:
    violations: list[str] = []
    allow_shebang = path.suffix == ".sh"
    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        if allow_shebang and lineno == 1 and stripped.startswith("#!"):
            continue
        if stripped.startswith("#"):
            violations.append(f"{path}:{lineno}: hash comment")
    return violations


def _json_comment_violations(path: Path, text: str) -> list[str]:
    violations: list[str] = []
    in_string = False
    escaped = False
    prev = ""
    for lineno, raw in enumerate(text.splitlines(), start=1):
        in_string = False
        escaped = False
        prev = ""
        for char in raw:
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            else:
                if char == '"':
                    in_string = True
                elif char == "/" and prev == "/":
                    violations.append(f"{path}:{lineno}: json comment")
                    break
                elif char == "#":
                    violations.append(f"{path}:{lineno}: json comment")
                    break
            prev = char
    return violations


def _scan_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        return _python_violations(path, text)
    if path.suffix == ".json":
        return _json_comment_violations(path, text)
    if path.suffix in _HASH_COMMENT_SUFFIXES or path.name in _HASH_COMMENT_NAMES:
        return _hash_comment_violations(path, text)
    return []


def test_no_comments_or_docstrings_in_committed_code() -> None:
    violations: list[str] = []
    for path in _tracked_files():
        if _should_scan(path):
            violations.extend(_scan_file(path))
    assert not violations, "comment/docstring violations:\n" + "\n".join(violations)


def test_env_example_contains_placeholder_values_only() -> None:
    env_path = _REPO_ROOT / ".env.example"
    assert env_path.is_file()
    offenders: list[str] = []
    for lineno, raw in enumerate(env_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if value == "":
            continue
        lowered = value.lower()
        if key.strip() in _PLACEHOLDER_SECRET_KEYS:
            offenders.append(f"{lineno}: {key.strip()} has a non-empty value")
            continue
        if any(marker.lower() in lowered for marker in _SECRET_MARKERS):
            offenders.append(f"{lineno}: {key.strip()} looks like a real credential")
    assert not offenders, "suspicious .env.example values:\n" + "\n".join(offenders)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
