#!/usr/bin/env python3
"""Validate source-true-guoman image generation manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.image_generation_core import (
        ImageGenerationError,
        load_jobs_jsonl,
        validate_jobs,
        validate_manifest,
    )
except ModuleNotFoundError:
    from image_generation_core import (
        ImageGenerationError,
        load_jobs_jsonl,
        validate_jobs,
        validate_manifest,
    )


def print_validation_errors(errors: list[str]) -> None:
    print("Image manifest validation failed:")
    for error in errors:
        print(f"- {error}")


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

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ImageGenerationError("manifest must be a JSON object")
        jobs = load_jobs_jsonl(jobs_path)
        validate_jobs(jobs)
        errors = validate_manifest(manifest, jobs, workspace)
    except FileNotFoundError as error:
        missing = Path(error.filename).name if error.filename else "input file"
        print_validation_errors([f"input file not found: {missing}"])
        return 1
    except json.JSONDecodeError as error:
        print_validation_errors(
            [f"manifest JSON is malformed at line {error.lineno} column {error.colno}"]
        )
        return 1
    except ImageGenerationError as error:
        print_validation_errors(str(error).split("; "))
        return 1

    if errors:
        print_validation_errors(errors)
        return 1

    print("Image manifest validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
