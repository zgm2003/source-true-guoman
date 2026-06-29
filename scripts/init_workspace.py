#!/usr/bin/env python3
"""Initialize a source-true-guoman project workspace."""

from __future__ import annotations

import argparse
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


def init_workspace(root: Path) -> list[Path]:
    """Create the standard asset directories under root and return them."""
    root.mkdir(parents=True, exist_ok=True)
    created_or_existing: list[Path] = []

    for dirname in ASSET_DIRS:
        directory = root / dirname
        directory.mkdir(exist_ok=True)
        created_or_existing.append(directory)

    return created_or_existing


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
    paths = init_workspace(root)

    print(f"Initialized: {root}")
    for path in paths:
        print(path.name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
