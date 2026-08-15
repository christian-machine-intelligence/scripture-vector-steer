"""Portable ``.env`` loading for the benchmark-authoring entry points.

These helpers previously searched a hard-coded list of directories on one
maintainer's laptop, which meant nobody else could supply an API key through a
file. Search order is now:

1. ``$VIRTUE_BENCH_ENV``, if set (an explicit path to an env file);
2. ``.env`` at the repository root;
3. ``.env`` in the current working directory.

Values already present in the environment always win, so exporting a key in the
shell overrides whatever a file says.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def env_file_candidates() -> list[Path]:
    candidates = []
    explicit = os.environ.get("VIRTUE_BENCH_ENV")
    if explicit:
        candidates.append(Path(explicit).expanduser())
    candidates.append(REPO_ROOT / ".env")
    candidates.append(Path.cwd() / ".env")
    seen, unique = set(), []
    for path in candidates:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def load_env_files() -> None:
    """Populate ``os.environ`` from the first-found ``.env`` files."""
    for env_path in env_file_candidates():
        if not env_path.is_file():
            continue
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if val and not os.environ.get(key):
                os.environ[key] = val


def require_api_key(name: str = "ANTHROPIC_API_KEY") -> str:
    """Load env files and return ``name``, or exit with a clear message."""
    load_env_files()
    value = os.environ.get(name)
    if not value:
        searched = "\n  ".join(str(p) for p in env_file_candidates())
        raise SystemExit(
            f"{name} not found.\n"
            f"Export it, or put it in one of:\n  {searched}\n"
            f"(or point $VIRTUE_BENCH_ENV at an env file)"
        )
    return value
