#!/usr/bin/env python3
"""Initialize a source-true-guoman project workspace."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


ASSET_DIRS = (
    "场景资产",
    "道具资产",
    "剧本资产",
    "人设资产",
    "生产资产",
    "视频资产",
    "音色资产",
)

SCRIPT_ASSET_DIR = "剧本资产"
ROOT_SCRIPT_SKIP_NAMES = {
    ".gitignore",
    "source-index.md",
}
ROOT_SCRIPT_SKIP_SUFFIXES = {
    ".py",
    ".pyc",
    ".ps1",
    ".sh",
    ".md",
    ".json",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class InitResult:
    directories: list[Path]
    archived_scripts: list[Path]


def _is_root_script_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.name.startswith("."):
        return False
    if path.name in ROOT_SCRIPT_SKIP_NAMES:
        return False
    if path.suffix.lower() in ROOT_SCRIPT_SKIP_SUFFIXES:
        return False
    return True


def _archive_root_scripts(root: Path) -> list[Path]:
    script_dir = root / SCRIPT_ASSET_DIR
    archived: list[Path] = []

    for candidate in root.iterdir():
        if not _is_root_script_file(candidate):
            continue

        destination = script_dir / candidate.name
        if destination.exists():
            continue

        candidate.replace(destination)
        archived.append(destination)

    return archived


def init_workspace(root: Path) -> InitResult:
    """Create the standard workspace and archive root-level script files."""
    root.mkdir(parents=True, exist_ok=True)
    created_or_existing: list[Path] = []

    for dirname in ASSET_DIRS:
        directory = root / dirname
        directory.mkdir(exist_ok=True)
        created_or_existing.append(directory)

    archived_scripts = _archive_root_scripts(root)

    return InitResult(
        directories=created_or_existing,
        archived_scripts=archived_scripts,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create standard source-true-guoman workspace folders."
    )
    parser.add_argument(
        "workspace",
        nargs="?",
        default=".",
        help="Workspace root to initialize. Defaults to the current directory.",
    )
    args = parser.parse_args()

    root = Path(args.workspace).expanduser().resolve()
    result = init_workspace(root)

    print(f"Initialized: {root}")
    for path in result.directories:
        print(path.name)
    for path in result.archived_scripts:
        print(f"Archived script: {path.relative_to(root)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
