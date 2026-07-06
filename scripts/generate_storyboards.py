#!/usr/bin/env python3
"""Generate storyboard contact-sheet QA images."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from pathlib import Path
from typing import Any
from typing import Callable
from urllib.parse import urlsplit

try:
    from scripts.generate_images import (
        ImageGenerationError,
        ImageGenerationConfig,
        NonRetryableProviderError,
        RetryableProviderError,
        load_config_from_env,
        openai_compatible_provider,
        retry_delay,
    )
    from scripts.storyboard_generation_core import (
        STORYBOARD_OUTPUT_DIR,
        StoryboardGenerationError,
        StoryboardJob,
        load_storyboard_jobs_jsonl,
        prompt_hash,
        validate_storyboard_jobs,
    )
except ModuleNotFoundError:
    from generate_images import (
        ImageGenerationError,
        ImageGenerationConfig,
        NonRetryableProviderError,
        RetryableProviderError,
        load_config_from_env,
        openai_compatible_provider,
        retry_delay,
    )
    from storyboard_generation_core import (
        STORYBOARD_OUTPUT_DIR,
        StoryboardGenerationError,
        StoryboardJob,
        load_storyboard_jobs_jsonl,
        prompt_hash,
        validate_storyboard_jobs,
    )


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())
ProviderCallable = Callable[[StoryboardJob, ImageGenerationConfig], bytes]
SECRET_VALUE_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")


def storyboard_output_path(workspace: Path, job: StoryboardJob) -> Path:
    if job.output_dir != STORYBOARD_OUTPUT_DIR:
        raise NonRetryableProviderError(f"{job.job_id}: output_dir must be {STORYBOARD_OUTPUT_DIR}")
    if (
        "/" in job.output_file
        or "\\" in job.output_file
        or Path(job.output_file).is_absolute()
        or _has_drive_prefix(job.output_file)
    ):
        raise NonRetryableProviderError(f"{job.job_id}: output_file must be a file name only")

    workspace_path = Path(workspace).resolve(strict=False)
    output_path = (workspace_path / job.output_path).resolve(strict=False)
    try:
        output_path.relative_to(workspace_path)
    except ValueError as error:
        raise NonRetryableProviderError("output path must stay under workspace") from error
    return output_path


def run_storyboard_job_with_retry(
    job: StoryboardJob,
    config: ImageGenerationConfig,
    workspace: Path,
    provider: ProviderCallable = openai_compatible_provider,
) -> dict[str, Any]:
    attempts = 0
    try:
        output_path = storyboard_output_path(workspace, job)
        if job.reference_images and config.reference_mode != "data-url":
            raise NonRetryableProviderError(
                "storyboard references require SOURCE_TRUE_IMAGE_REFERENCE_MODE=data-url"
            )
    except NonRetryableProviderError as error:
        return _failed_result(job, config, attempts, _sanitize_error(str(error), config))

    while True:
        attempts += 1
        try:
            image_bytes = provider(job, config)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(image_bytes)
            return _result_base(job, config, attempts) | {"status": "done"}
        except NonRetryableProviderError as error:
            return _failed_result(job, config, attempts, _sanitize_error(str(error), config))
        except RetryableProviderError as error:
            last_error = _sanitize_error(str(error), config)
            if attempts > config.max_retries:
                return _failed_result(job, config, attempts, last_error)
            delay = retry_delay(config, attempts - 1)
            if delay > 0:
                time.sleep(delay)
        except Exception as error:
            return _failed_result(job, config, attempts, _sanitize_error(str(error), config))


def run_storyboard_generation(
    jobs: list[StoryboardJob],
    config: ImageGenerationConfig,
    workspace: Path,
    provider: ProviderCallable = openai_compatible_provider,
    existing_manifest: dict[str, Any] | None = None,
    resume: bool = False,
    on_manifest_update: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    validate_storyboard_jobs(jobs)
    _validate_reference_mode(jobs, config)
    existing = manifest_by_name(existing_manifest) if resume else {}
    results_by_name: dict[str, dict[str, Any]] = {}

    runnable: list[StoryboardJob] = []
    for job in jobs:
        if should_skip_storyboard_job(job, config, existing, workspace, resume):
            results_by_name[job.job_id] = _skipped_result(job, config, existing[job.job_id])
            _notify_manifest_update(jobs, results_by_name, on_manifest_update)
        else:
            runnable.append(job)

    if runnable:
        with ThreadPoolExecutor(max_workers=max(1, config.concurrency)) as executor:
            future_map = {
                executor.submit(
                    run_storyboard_job_with_retry,
                    job,
                    config,
                    workspace,
                    provider,
                ): job
                for job in runnable
            }
            for future in as_completed(future_map):
                job = future_map[future]
                try:
                    result = future.result()
                except Exception as error:
                    result = _failed_result(
                        job,
                        config,
                        0,
                        _sanitize_error(str(error), config),
                    )
                results_by_name[job.job_id] = result
                _notify_manifest_update(jobs, results_by_name, on_manifest_update)

    return _build_manifest(jobs, results_by_name)


def _validate_reference_mode(
    jobs: list[StoryboardJob],
    config: ImageGenerationConfig,
) -> None:
    if any(job.reference_images for job in jobs) and config.reference_mode != "data-url":
        raise StoryboardGenerationError(
            "storyboard references require SOURCE_TRUE_IMAGE_REFERENCE_MODE=data-url"
        )


def should_skip_storyboard_job(
    job: StoryboardJob,
    config: ImageGenerationConfig,
    existing: dict[str, dict[str, Any]],
    workspace: Path,
    resume: bool,
) -> bool:
    if not resume:
        return False
    asset = existing.get(job.job_id)
    if not asset or asset.get("status") != "done":
        return False
    path_text = str(asset.get("path", "")).strip()
    if path_text != job.output_path.as_posix():
        return False
    if asset.get("prompt_hash") != prompt_hash(job.prompt):
        return False
    if asset.get("model") != (job.model or config.model):
        return False
    if asset.get("size") != (job.size or config.size):
        return False
    if asset.get("references") != [reference.to_dict() for reference in job.reference_images]:
        return False
    return (Path(workspace) / path_text).is_file()


def manifest_by_name(manifest: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(manifest, dict):
        return {}
    assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        return {}
    return {
        str(asset.get("asset_name", "")).strip(): asset
        for asset in assets
        if isinstance(asset, dict) and str(asset.get("asset_name", "")).strip()
    }


def write_storyboard_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _write_text_atomic(path, text)


def write_storyboard_report(path: Path, manifest: dict[str, Any]) -> None:
    assets = [asset for asset in manifest.get("assets", []) if isinstance(asset, dict)]
    failed = [asset for asset in assets if asset.get("status") == "failed"]
    generated = [asset for asset in assets if asset.get("status") == "done"]
    lines = ["# Storyboard Contact Sheet Report", "", "## Failed"]
    lines.extend(
        [f"- {asset.get('asset_name')}: {asset.get('last_error')}" for asset in failed]
        or ["- None"]
    )
    lines.extend(["", "## Generated"])
    lines.extend(
        [f"- {asset.get('asset_name')}: {asset.get('path')}" for asset in generated]
        or ["- None"]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _notify_manifest_update(
    jobs: list[StoryboardJob],
    results_by_name: dict[str, dict[str, Any]],
    on_manifest_update: Callable[[dict[str, Any]], None] | None,
) -> None:
    if on_manifest_update is not None:
        on_manifest_update(_build_manifest(jobs, results_by_name))


def _build_manifest(
    jobs: list[StoryboardJob],
    results_by_name: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "version": 1,
        "provider": "openai-compatible",
        "base_url_label": "configured",
        "assets": [
            results_by_name[job.job_id]
            for job in jobs
            if job.job_id in results_by_name
        ],
    }


def _result_base(
    job: StoryboardJob,
    config: ImageGenerationConfig,
    attempts: int,
) -> dict[str, Any]:
    return {
        "asset_name": job.job_id,
        "asset_type": "storyboard_contact_sheet",
        "path": job.output_path.as_posix(),
        "prompt_hash": prompt_hash(job.prompt),
        "model": job.model or config.model,
        "size": job.size or config.size,
        "attempts": attempts,
        "line_start": job.line_start,
        "line_end": job.line_end,
        "line_count": job.line_count,
        "source_feed": job.source_feed,
        "references": [reference.to_dict() for reference in job.reference_images],
    }


def _failed_result(
    job: StoryboardJob,
    config: ImageGenerationConfig,
    attempts: int,
    last_error: str,
) -> dict[str, Any]:
    return _result_base(job, config, attempts) | {
        "status": "failed",
        "last_error": last_error,
    }


def _skipped_result(
    job: StoryboardJob,
    config: ImageGenerationConfig,
    existing_asset: dict[str, Any],
) -> dict[str, Any]:
    attempts = existing_asset.get("attempts", 0)
    if type(attempts) is not int or attempts < 0:
        attempts = 0
    return _result_base(job, config, attempts) | {"status": "done"}


def _sanitize_error(message: str, config: ImageGenerationConfig) -> str:
    sanitized = message
    parsed_base_url = urlsplit(config.base_url)
    for secret in {
        config.api_key,
        config.base_url,
        config.base_url.rstrip("/"),
        parsed_base_url.netloc,
        parsed_base_url.hostname or "",
    }:
        if secret:
            sanitized = sanitized.replace(secret, "[redacted]")
    return SECRET_VALUE_PATTERN.sub("[redacted]", sanitized) or "provider error"


def _write_text_atomic(path: Path, text: str) -> None:
    temp_path: Path | None = None
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temp_file:
        temp_file.write(text)
        temp_path = Path(temp_file.name)
    try:
        os.replace(temp_path, path)
    except OSError:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise


def _has_drive_prefix(path: str) -> bool:
    return len(path) >= 2 and path[0].isalpha() and path[1] == ":"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate storyboard contact-sheet QA images.")
    parser.add_argument("--jobs", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--report")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    jobs_path = Path(args.jobs).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()
    report_path = (
        Path(args.report).expanduser().resolve()
        if args.report
        else manifest_path.with_name("storyboard-report.md")
    )

    try:
        jobs = load_storyboard_jobs_jsonl(jobs_path)
        existing_manifest = None
        if args.resume and manifest_path.exists():
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(existing_manifest, dict):
                raise StoryboardGenerationError("existing manifest must be a JSON object")
        config = load_config_from_env()
        config.reference_workspace = str(workspace)

        def persist(current_manifest: dict[str, Any]) -> None:
            write_storyboard_manifest(manifest_path, current_manifest)
            write_storyboard_report(report_path, current_manifest)

        manifest = run_storyboard_generation(
            jobs,
            config,
            workspace,
            provider=openai_compatible_provider,
            existing_manifest=existing_manifest,
            resume=args.resume,
            on_manifest_update=persist,
        )
        write_storyboard_manifest(manifest_path, manifest)
        write_storyboard_report(report_path, manifest)
    except FileNotFoundError as error:
        missing = Path(error.filename).name if error.filename else "input file"
        print(f"Storyboard generation failed: input file not found: {missing}")
        return 1
    except (
        json.JSONDecodeError,
        OSError,
        ImageGenerationError,
        StoryboardGenerationError,
        NonRetryableProviderError,
        RetryableProviderError,
    ) as error:
        print(f"Storyboard generation failed: {error}")
        return 1

    print(
        "Storyboard generation wrote "
        f"{len(manifest.get('assets', []))} sheets to {manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
