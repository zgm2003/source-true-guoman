#!/usr/bin/env python3
"""Validate source-true-guoman storyboard contact-sheet manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.storyboard_generation_core import (
        STORYBOARD_OUTPUT_DIR,
        StoryboardGenerationError,
        StoryboardJob,
        load_storyboard_jobs_jsonl,
        prompt_hash,
        validate_storyboard_jobs,
    )
except ModuleNotFoundError:
    from storyboard_generation_core import (
        STORYBOARD_OUTPUT_DIR,
        StoryboardGenerationError,
        StoryboardJob,
        load_storyboard_jobs_jsonl,
        prompt_hash,
        validate_storyboard_jobs,
    )


def validate_storyboard_manifest(
    manifest: dict[str, Any],
    jobs: list[StoryboardJob],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    if "assets" not in manifest:
        return ["manifest assets is required"]
    assets = manifest["assets"]
    if not isinstance(assets, list):
        return ["manifest assets must be a list"]
    if not assets:
        return ["manifest assets must not be empty"]

    jobs_by_name = {job.job_id: job for job in jobs}
    seen_names: set[str] = set()
    for asset in assets:
        if not isinstance(asset, dict):
            errors.append("manifest asset entry must be an object")
            continue
        asset_name = str(asset.get("asset_name", "")).strip()
        asset_label = asset_name or "<missing asset_name>"
        path_text = str(asset.get("path", "")).strip()
        status = str(asset.get("status", "")).strip()

        if not asset_name:
            errors.append("asset_name is required")
        elif asset_name in seen_names:
            errors.append(f"duplicate asset_name: {asset_name}")
        if asset_name:
            seen_names.add(asset_name)

        job = jobs_by_name.get(asset_name)
        if job is None:
            errors.append(f"{asset_label}: manifest asset not present in jobs")
        else:
            if path_text != job.output_path.as_posix():
                errors.append(
                    f"{asset_label}: path must match job output {job.output_path.as_posix()}"
                )
            _validate_job_metadata(asset_label, asset, job, errors)

        if status not in {"done", "failed", "blocked"}:
            errors.append(f"{asset_label}: status must be done, failed, or blocked")
        if status in {"failed", "blocked"} and not str(asset.get("last_error", "")).strip():
            errors.append(f"{asset_label}: {status} storyboard must record last_error")

        image_path = _validate_storyboard_path(asset_label, path_text, workspace, errors)
        if status == "done" and image_path is not None and not image_path.is_file():
            errors.append(f"{asset_label}: done storyboard missing local file {path_text}")

    for job_id in jobs_by_name:
        if job_id not in seen_names:
            errors.append(f"{job_id}: missing from storyboard manifest")

    return errors


def _validate_job_metadata(
    asset_label: str,
    asset: dict[str, Any],
    job: StoryboardJob,
    errors: list[str],
) -> None:
    expected_values: dict[str, Any] = {
        "prompt_hash": prompt_hash(job.prompt),
        "model": job.model,
        "size": job.size,
        "line_start": job.line_start,
        "line_end": job.line_end,
        "line_count": job.line_count,
        "source_feed": job.source_feed,
        "references": [reference.to_dict() for reference in job.reference_images],
    }
    for field_name, expected_value in expected_values.items():
        if field_name not in asset:
            errors.append(f"{asset_label}: {field_name} is required")
            continue
        if asset.get(field_name) != expected_value:
            errors.append(f"{asset_label}: {field_name} must match current job")


def _validate_storyboard_path(
    asset_label: str,
    path_text: str,
    workspace: Path,
    errors: list[str],
) -> Path | None:
    if not path_text:
        errors.append(f"{asset_label}: generated storyboard path is required")
        return None
    path = Path(path_text)
    if _has_drive_prefix(path_text) or path.is_absolute():
        errors.append(f"{asset_label}: generated storyboard path must be relative")
        return None
    workspace_path = Path(workspace).resolve(strict=False)
    resolved_path = (workspace_path / path).resolve(strict=False)
    try:
        relative_path = resolved_path.relative_to(workspace_path)
    except ValueError:
        errors.append(f"{asset_label}: generated storyboard path must stay under workspace")
        return None
    if not relative_path.parts or relative_path.parts[0] != STORYBOARD_OUTPUT_DIR:
        errors.append(f"{asset_label}: path must start with {STORYBOARD_OUTPUT_DIR}")
    return resolved_path


def _has_drive_prefix(path: str) -> bool:
    return len(path) >= 2 and path[0].isalpha() and path[1] == ":"


def print_validation_errors(errors: list[str]) -> None:
    print("Storyboard manifest validation failed:")
    for error in errors:
        print(f"- {error}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate storyboard contact-sheet manifest files."
    )
    parser.add_argument("manifest")
    parser.add_argument("--jobs", required=True)
    parser.add_argument("--workspace", default=".")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    jobs_path = Path(args.jobs).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise StoryboardGenerationError("manifest must be a JSON object")
        jobs = load_storyboard_jobs_jsonl(jobs_path)
        validate_storyboard_jobs(jobs)
        errors = validate_storyboard_manifest(manifest, jobs, workspace)
    except FileNotFoundError as error:
        missing = Path(error.filename).name if error.filename else "input file"
        print_validation_errors([f"input file not found: {missing}"])
        return 1
    except json.JSONDecodeError as error:
        print_validation_errors(
            [f"manifest JSON is malformed at line {error.lineno} column {error.colno}"]
        )
        return 1
    except StoryboardGenerationError as error:
        print_validation_errors(str(error).split("; "))
        return 1

    if errors:
        print_validation_errors(errors)
        return 1

    print("Storyboard manifest validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
