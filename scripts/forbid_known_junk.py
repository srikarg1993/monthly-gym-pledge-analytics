"""Pre-commit guard: block known cache / scratch artifacts by name.

Belt-and-suspenders alongside ``.gitignore``. The ``.mutmut-cache`` incident
(commit 6fe2541) happened because the gitignore entry was removed before the
file was deleted, so a follow-up ``git add -A`` swept the binary in. A name-
based block at the pre-commit boundary makes that class of mistake impossible
regardless of gitignore state.

If you legitimately need to commit one of these names, edit ``ALLOWED`` below
and explain why in the commit message.
"""

from __future__ import annotations

import sys
from pathlib import PurePosixPath

# Exact filenames or path suffixes that should never be committed.
FORBIDDEN_NAMES: frozenset[str] = frozenset(
    {
        ".mutmut-cache",
        ".coverage",
        "coverage.xml",
        "mutmut-results.txt",
        ".DS_Store",
        "Thumbs.db",
    }
)

# Directory prefixes (POSIX-style) that should never be committed.
FORBIDDEN_PREFIXES: tuple[str, ...] = (
    ".scratch/",
    "scratch/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    "__pycache__/",
    "htmlcov/",
    ".venv/",
    "node_modules/",
)

# Suffix-based blocks (binary / generated artifacts).
FORBIDDEN_SUFFIXES: tuple[str, ...] = (
    ".pyc",
    ".pyo",
    ".scratch",
    ".tmp",
)

# Escape hatch for the rare legitimate exception. Keep this list short and
# justify each entry in the commit message that adds it.
ALLOWED: frozenset[str] = frozenset()


def is_forbidden(path: str) -> str | None:
    """Return a human-readable reason if ``path`` should be blocked, else None."""
    posix = PurePosixPath(path).as_posix()
    if posix in ALLOWED:
        return None
    name = PurePosixPath(posix).name
    if name in FORBIDDEN_NAMES:
        return f"forbidden filename: {name}"
    for prefix in FORBIDDEN_PREFIXES:
        if posix.startswith(prefix) or f"/{prefix}" in f"/{posix}":
            return f"forbidden path prefix: {prefix}"
    for suffix in FORBIDDEN_SUFFIXES:
        if name.endswith(suffix):
            return f"forbidden suffix: {suffix}"
    return None


def main(argv: list[str]) -> int:
    violations: list[tuple[str, str]] = []
    for path in argv[1:]:
        reason = is_forbidden(path)
        if reason is not None:
            violations.append((path, reason))
    if not violations:
        return 0
    print("blocked: cache / scratch / generated files in the diff:", file=sys.stderr)
    for path, reason in violations:
        print(f"  - {path}  ({reason})", file=sys.stderr)
    print(
        "\nIf this is intentional, add the path to ALLOWED in "
        "scripts/forbid_known_junk.py and explain in the commit message.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
