#!/usr/bin/env python3
"""Validate source-true-guoman image generation manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.image_generation_core import load_jobs_jsonl, validate_manifest
except ModuleNotFoundError:
    from image_generation_core import load_jobs_jsonl, validate_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate image manifest files.")
    parser.add_argument("manifest", help="Path to image-manifest.json")
    parser.add_argument("--jobs", required=True, help="Path to image-jobs.jsonl")
    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace root used to resolve generated image paths.",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    jobs_path = Path(args.jobs).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    jobs = load_jobs_jsonl(jobs_path)
    errors = validate_manifest(manifest, jobs, workspace)

    if errors:
        print("Image manifest validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Image manifest validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
