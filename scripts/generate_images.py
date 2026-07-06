#!/usr/bin/env python3
"""OpenAI-compatible image provider and per-job retry helpers."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import logging
import math
import os
import random
import re
import socket
import time
import urllib.error
from urllib.parse import urlsplit
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Callable

try:
    from scripts.image_generation_core import ALLOWED_OUTPUT_DIRS
    from scripts.image_generation_core import ImageGenerationError
    from scripts.image_generation_core import ImageJob
    from scripts.image_generation_core import build_dependency_waves
    from scripts.image_generation_core import load_jobs_jsonl
    from scripts.image_generation_core import prompt_hash
except ModuleNotFoundError:
    from image_generation_core import ALLOWED_OUTPUT_DIRS
    from image_generation_core import ImageGenerationError
    from image_generation_core import ImageJob
    from image_generation_core import build_dependency_waves
    from image_generation_core import load_jobs_jsonl
    from image_generation_core import prompt_hash


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())
SECRET_VALUE_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")
SECRET_NAME_PATTERN = re.compile(
    r"\b(api[_ -]?key|authorization|bearer|token)\b",
    re.IGNORECASE,
)


class RetryableProviderError(RuntimeError):
    """Raised when a provider failure may succeed on a later attempt."""


class NonRetryableProviderError(RuntimeError):
    """Raised when retrying the provider request should not help."""


@dataclass
class ImageGenerationConfig:
    base_url: str
    api_key: str
    model: str
    size: str
    timeout_seconds: float
    max_retries: int
    retry_base_seconds: float
    retry_max_seconds: float
    concurrency: int


ProviderCallable = Callable[[ImageJob, ImageGenerationConfig], bytes]


def load_config_from_env() -> ImageGenerationConfig:
    base_url = os.environ.get("SOURCE_TRUE_IMAGE_BASE_URL", "").strip().rstrip("/")
    api_key = os.environ.get("SOURCE_TRUE_IMAGE_API_KEY", "").strip()
    if not base_url or not api_key:
        raise ImageGenerationError(
            "SOURCE_TRUE_IMAGE_BASE_URL and SOURCE_TRUE_IMAGE_API_KEY are required"
        )

    config = ImageGenerationConfig(
        base_url=base_url,
        api_key=api_key,
        model=os.environ.get("SOURCE_TRUE_IMAGE_MODEL", "gpt-image-2").strip()
        or "gpt-image-2",
        size=os.environ.get("SOURCE_TRUE_IMAGE_SIZE", "16:9").strip() or "16:9",
        timeout_seconds=_float_env("SOURCE_TRUE_IMAGE_TIMEOUT_SECONDS", 120.0),
        max_retries=_int_env("SOURCE_TRUE_IMAGE_MAX_RETRIES", 3),
        retry_base_seconds=_float_env("SOURCE_TRUE_IMAGE_RETRY_BASE_SECONDS", 1.0),
        retry_max_seconds=_float_env("SOURCE_TRUE_IMAGE_RETRY_MAX_SECONDS", 30.0),
        concurrency=_int_env("SOURCE_TRUE_IMAGE_CONCURRENCY", 1),
    )
    _validate_config(config)
    return config


def retry_delay(config: ImageGenerationConfig, attempt_index: int) -> float:
    if config.retry_base_seconds <= 0 or config.retry_max_seconds <= 0:
        return 0.0
    exponential_delay = config.retry_base_seconds * (2 ** max(0, attempt_index))
    capped_delay = min(config.retry_max_seconds, exponential_delay)
    return random.uniform(0.0, capped_delay)


def openai_compatible_provider(job: ImageJob, config: ImageGenerationConfig) -> bytes:
    endpoint = f"{config.base_url}/v1/images/generations"
    payload = {
        "model": _job_model(job, config),
        "prompt": job.prompt,
        "size": _job_size(job, config),
    }

    try:
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
            body = response.read()
    except urllib.error.HTTPError as error:
        raise _provider_error_from_http(error, config) from error
    except ValueError as error:
        raise NonRetryableProviderError("provider base URL is invalid") from error
    except (TimeoutError, socket.timeout, urllib.error.URLError, OSError) as error:
        raise RetryableProviderError("provider connection failed or timed out") from error

    if not body:
        raise RetryableProviderError("provider response was empty")
    return _image_bytes_from_response(body, config)


def download_image(url: str, timeout_seconds: float) -> bytes:
    request = urllib.request.Request(url, headers={"Accept": "image/*"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read()
    except urllib.error.HTTPError as error:
        status = error.code
        if status == 429 or 500 <= status <= 599:
            raise RetryableProviderError(f"image download failed with HTTP {status}") from error
        raise NonRetryableProviderError(
            f"image download failed with HTTP {status}"
        ) from error
    except (ValueError, TimeoutError, socket.timeout, urllib.error.URLError, OSError) as error:
        raise RetryableProviderError("image download failed or timed out") from error

    if not body:
        raise RetryableProviderError("image download response was empty")
    return body


def run_job_with_retry(
    job: ImageJob,
    config: ImageGenerationConfig,
    workspace: Path,
    provider: ProviderCallable = openai_compatible_provider,
) -> dict[str, Any]:
    attempts = 0
    try:
        output_path = _workspace_output_path(workspace, job)
    except NonRetryableProviderError as error:
        last_error = _sanitize_error(str(error), config)
        LOGGER.warning(
            "Image asset %s failed before provider call: %s",
            job.asset_name,
            last_error,
        )
        return _failed_result(job, config, attempts, last_error)

    while True:
        attempts += 1
        LOGGER.info("Generating image asset %s, attempt %s", job.asset_name, attempts)
        try:
            image_bytes = provider(job, config)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(image_bytes)
            return _result_base(job, config, attempts) | {"status": "done"}
        except NonRetryableProviderError as error:
            last_error = _sanitize_error(str(error), config)
            LOGGER.warning(
                "Image asset %s failed without retry: %s",
                job.asset_name,
                last_error,
            )
            return _failed_result(job, config, attempts, last_error)
        except RetryableProviderError as error:
            last_error = _sanitize_error(str(error), config)
            if attempts > config.max_retries:
                LOGGER.warning(
                    "Image asset %s exhausted retries: %s",
                    job.asset_name,
                    last_error,
                )
                return _failed_result(job, config, attempts, last_error)
            delay = retry_delay(config, attempts - 1)
            LOGGER.info(
                "Image asset %s retrying after %.2fs: %s",
                job.asset_name,
                delay,
                last_error,
            )
            if delay > 0:
                time.sleep(delay)
        except Exception as error:
            last_error = _sanitize_error(str(error), config)
            LOGGER.warning(
                "Image asset %s failed with unexpected error: %s",
                job.asset_name,
                last_error,
            )
            return _failed_result(job, config, attempts, last_error)


def manifest_by_name(manifest: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(manifest, dict):
        return {}
    assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        return {}

    by_name: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        asset_name = str(asset.get("asset_name", "")).strip()
        if asset_name:
            by_name[asset_name] = asset
    return by_name


def should_skip_job(
    job: ImageJob,
    config: ImageGenerationConfig,
    existing: dict[str, dict[str, Any]],
    workspace: Path,
    resume: bool,
) -> bool:
    if not resume:
        return False
    asset = existing.get(job.asset_name)
    if not asset or asset.get("status") != "done":
        return False
    existing_path = _existing_asset_path(asset, workspace)
    if existing_path is None or not existing_path.is_file():
        return False

    expected_path = _current_job_output_path(job, workspace)
    if expected_path is None or existing_path != expected_path:
        return False
    if asset.get("prompt_hash") != prompt_hash(job.prompt):
        return False
    if asset.get("model") != _job_model(job, config):
        return False
    if asset.get("size") != _job_size(job, config):
        return False
    return True


def run_generation(
    jobs: list[ImageJob],
    config: ImageGenerationConfig,
    workspace: Path,
    provider: ProviderCallable = openai_compatible_provider,
    existing_manifest: dict[str, Any] | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    workspace = Path(workspace)
    waves = build_dependency_waves(jobs)
    existing = manifest_by_name(existing_manifest) if resume else {}
    done_assets: set[str] = set()
    results_by_name: dict[str, dict[str, Any]] = {}

    for wave in waves:
        runnable: list[ImageJob] = []
        for job in wave:
            missing_dependencies = [
                dependency for dependency in job.depends_on if dependency not in done_assets
            ]
            if missing_dependencies:
                result = _blocked_result(job, config, missing_dependencies)
                results_by_name[job.asset_name] = result
                LOGGER.warning(
                    "Image asset %s blocked: %s",
                    job.asset_name,
                    result["last_error"],
                )
                continue

            if should_skip_job(job, config, existing, workspace, resume):
                results_by_name[job.asset_name] = _skipped_result(
                    job,
                    config,
                    existing[job.asset_name],
                )
                done_assets.add(job.asset_name)
                LOGGER.info("Skipping image asset %s on resume", job.asset_name)
                continue

            runnable.append(job)

        completed_results: dict[str, dict[str, Any]] = {}
        if runnable:
            with ThreadPoolExecutor(max_workers=max(1, config.concurrency)) as executor:
                future_map = {
                    executor.submit(
                        run_job_with_retry,
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
                        completed_results[job.asset_name] = future.result()
                    except Exception as error:
                        last_error = _sanitize_error(str(error), config)
                        LOGGER.warning(
                            "Image asset %s failed with unexpected worker error: %s",
                            job.asset_name,
                            last_error,
                        )
                        completed_results[job.asset_name] = _failed_result(
                            job,
                            config,
                            0,
                            last_error,
                        )

        for job in runnable:
            result = completed_results[job.asset_name]
            results_by_name[job.asset_name] = result
            if result.get("status") == "done":
                done_assets.add(job.asset_name)

    return {
        "version": 1,
        "provider": "openai-compatible",
        "base_url_label": "configured",
        "assets": [
            results_by_name[job.asset_name]
            for job in jobs
            if job.asset_name in results_by_name
        ],
    }


def write_generation_report(path: Path, manifest: dict[str, Any]) -> None:
    assets = [
        asset
        for asset in manifest.get("assets", [])
        if isinstance(asset, dict)
    ]
    failed = [asset for asset in assets if asset.get("status") == "failed"]
    blocked = [asset for asset in assets if asset.get("status") == "blocked"]
    generated = [asset for asset in assets if asset.get("status") == "done"]

    lines = ["# Image Generation Report", ""]
    _append_report_section(lines, "Failed", failed, "last_error")
    _append_report_section(lines, "Blocked", blocked, "last_error")
    _append_report_section(lines, "Generated", generated, "path")

    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _float_env(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    try:
        parsed = float(value)
    except ValueError as error:
        raise ImageGenerationError(f"{name} must be a number") from error
    if not math.isfinite(parsed):
        raise ImageGenerationError(f"{name} must be finite")
    return parsed


def _int_env(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as error:
        raise ImageGenerationError(f"{name} must be an integer") from error


def _validate_config(config: ImageGenerationConfig) -> None:
    errors: list[str] = []
    if not math.isfinite(config.timeout_seconds):
        errors.append("SOURCE_TRUE_IMAGE_TIMEOUT_SECONDS must be finite")
    elif config.timeout_seconds <= 0:
        errors.append("SOURCE_TRUE_IMAGE_TIMEOUT_SECONDS must be greater than zero")
    if config.max_retries < 0:
        errors.append("SOURCE_TRUE_IMAGE_MAX_RETRIES must be zero or greater")
    if not math.isfinite(config.retry_base_seconds):
        errors.append("SOURCE_TRUE_IMAGE_RETRY_BASE_SECONDS must be finite")
    elif config.retry_base_seconds < 0:
        errors.append("SOURCE_TRUE_IMAGE_RETRY_BASE_SECONDS must be zero or greater")
    if not math.isfinite(config.retry_max_seconds):
        errors.append("SOURCE_TRUE_IMAGE_RETRY_MAX_SECONDS must be finite")
    elif config.retry_max_seconds < 0:
        errors.append("SOURCE_TRUE_IMAGE_RETRY_MAX_SECONDS must be zero or greater")
    if config.concurrency < 1:
        errors.append("SOURCE_TRUE_IMAGE_CONCURRENCY must be at least one")
    if errors:
        raise ImageGenerationError("; ".join(errors))


def _provider_error_from_http(
    error: urllib.error.HTTPError,
    config: ImageGenerationConfig,
) -> RuntimeError:
    status = error.code
    if status == 429 or 500 <= status <= 599:
        return RetryableProviderError(f"HTTP {status}: {_safe_error_body(error, config)}")
    if status in {401, 403}:
        return NonRetryableProviderError(f"HTTP {status}: authentication failed")
    body = _safe_error_body(error, config)
    if body:
        return NonRetryableProviderError(f"HTTP {status}: {body}")
    return NonRetryableProviderError(f"HTTP {status}: provider rejected request")


def _safe_error_body(
    error: urllib.error.HTTPError,
    config: ImageGenerationConfig,
) -> str:
    try:
        body = error.read(2048).decode("utf-8", errors="replace").strip()
    except OSError:
        return ""
    return _sanitize_error(body, config)


def _image_bytes_from_response(body: bytes, config: ImageGenerationConfig) -> bytes:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RetryableProviderError("provider response was malformed JSON") from error

    if not isinstance(payload, dict):
        raise RetryableProviderError("provider response was not a JSON object")
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise RetryableProviderError("provider response did not include image data")

    first_image = data[0]
    if not isinstance(first_image, dict):
        raise RetryableProviderError("provider image response was malformed")

    b64_json = first_image.get("b64_json")
    if isinstance(b64_json, str) and b64_json.strip():
        try:
            return base64.b64decode(b64_json, validate=True)
        except (binascii.Error, ValueError) as error:
            raise RetryableProviderError("provider image b64_json was malformed") from error

    url = first_image.get("url")
    if isinstance(url, str) and url.strip():
        return download_image(url.strip(), config.timeout_seconds)

    raise RetryableProviderError("provider response did not include image bytes or URL")


def _workspace_output_path(workspace: Path, job: ImageJob) -> Path:
    _validate_job_output_policy(job)
    workspace_path = workspace.resolve(strict=False)
    output_path = (workspace_path / job.output_path).resolve(strict=False)
    try:
        output_path.relative_to(workspace_path)
    except ValueError as error:
        raise NonRetryableProviderError("output path must stay under workspace") from error
    return output_path


def _validate_job_output_policy(job: ImageJob) -> None:
    errors: list[str] = []
    if job.output_dir not in ALLOWED_OUTPUT_DIRS:
        errors.append(
            f"{job.asset_name}: output_dir must be one of {sorted(ALLOWED_OUTPUT_DIRS)}"
        )
    if not job.output_file.endswith(".png"):
        errors.append(f"{job.asset_name}: output_file must end with .png")
    if (
        "/" in job.output_file
        or "\\" in job.output_file
        or Path(job.output_file).is_absolute()
        or _has_drive_prefix(job.output_file)
    ):
        errors.append(f"{job.asset_name}: output_file must be a file name only")
    if errors:
        raise NonRetryableProviderError("; ".join(errors))


def _has_drive_prefix(path: str) -> bool:
    return len(path) >= 2 and path[0].isalpha() and path[1] == ":"


def _result_base(
    job: ImageJob,
    config: ImageGenerationConfig,
    attempts: int,
) -> dict[str, Any]:
    return {
        "asset_name": job.asset_name,
        "asset_type": job.asset_type,
        "path": job.output_path.as_posix(),
        "prompt_hash": prompt_hash(job.prompt),
        "model": _job_model(job, config),
        "size": _job_size(job, config),
        "attempts": attempts,
        "depends_on": list(job.depends_on),
        "references": _references(job),
    }


def _failed_result(
    job: ImageJob,
    config: ImageGenerationConfig,
    attempts: int,
    last_error: str,
) -> dict[str, Any]:
    return _result_base(job, config, attempts) | {
        "status": "failed",
        "last_error": last_error,
    }


def _blocked_result(
    job: ImageJob,
    config: ImageGenerationConfig,
    missing_dependencies: list[str],
) -> dict[str, Any]:
    dependency_text = ", ".join(missing_dependencies)
    return _result_base(job, config, 0) | {
        "status": "blocked",
        "last_error": f"blocked by failed or missing dependencies: {dependency_text}",
    }


def _existing_asset_path(asset: dict[str, Any], workspace: Path) -> Path | None:
    path_text = str(asset.get("path", "")).strip()
    if not path_text or _has_drive_prefix(path_text):
        return None

    path = Path(path_text)
    if path.is_absolute():
        return None

    workspace_path = Path(workspace).resolve(strict=False)
    resolved_path = (workspace_path / path).resolve(strict=False)
    try:
        resolved_path.relative_to(workspace_path)
    except ValueError:
        return None
    return resolved_path


def _current_job_output_path(job: ImageJob, workspace: Path) -> Path | None:
    try:
        return _workspace_output_path(workspace, job)
    except NonRetryableProviderError:
        return None


def _skipped_result(
    job: ImageJob,
    config: ImageGenerationConfig,
    existing_asset: dict[str, Any],
) -> dict[str, Any]:
    attempts = existing_asset.get("attempts", 0)
    if type(attempts) is not int or attempts < 0:
        attempts = 0
    return _result_base(job, config, attempts) | {"status": "done"}


def _append_report_section(
    lines: list[str],
    title: str,
    assets: list[dict[str, Any]],
    detail_field: str,
) -> None:
    lines.append(f"## {title}")
    if assets:
        for asset in assets:
            detail = asset.get(detail_field, "")
            lines.append(f"- {asset.get('asset_name')}: {detail}")
    else:
        lines.append("- None")
    lines.append("")


def _references(job: ImageJob) -> list[dict[str, str]]:
    return [reference.to_dict() for reference in job.reference_images]


def _job_model(job: ImageJob, config: ImageGenerationConfig) -> str:
    return job.model or config.model


def _job_size(job: ImageJob, config: ImageGenerationConfig) -> str:
    return job.size or config.size


def _sanitize_error(message: str, config: ImageGenerationConfig) -> str:
    sanitized = message
    parsed_base_url = urlsplit(config.base_url)
    secret_fragments = {
        config.api_key,
        config.base_url,
        config.base_url.rstrip("/"),
        parsed_base_url.netloc,
        parsed_base_url.hostname or "",
    }
    for secret in secret_fragments:
        if secret:
            sanitized = sanitized.replace(secret, "[redacted]")
    sanitized = SECRET_VALUE_PATTERN.sub("[redacted]", sanitized)
    sanitized = SECRET_NAME_PATTERN.sub("credential", sanitized)
    return sanitized or "provider error"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate source-true-guoman image assets."
    )
    parser.add_argument("--jobs", required=True, help="Path to image-jobs.jsonl")
    parser.add_argument("--manifest", required=True, help="Path to image-manifest.json")
    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace root used to resolve generated image paths.",
    )
    parser.add_argument("--report", help="Path to image-generation-report.md")
    parser.add_argument("--resume", action="store_true", help="Skip completed outputs")
    args = parser.parse_args()

    jobs_path = Path(args.jobs).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()
    report_path = (
        Path(args.report).expanduser().resolve()
        if args.report
        else manifest_path.with_name("image-generation-report.md")
    )

    try:
        jobs = load_jobs_jsonl(jobs_path)
        existing_manifest = None
        if args.resume and manifest_path.exists():
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(existing_manifest, dict):
                raise ImageGenerationError("existing manifest must be a JSON object")

        config = load_config_from_env()
        manifest = run_generation(
            jobs,
            config,
            workspace,
            provider=openai_compatible_provider,
            existing_manifest=existing_manifest,
            resume=args.resume,
        )

        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        write_generation_report(report_path, manifest)
    except FileNotFoundError as error:
        missing = Path(error.filename).name if error.filename else "input file"
        print(f"Image generation failed: input file not found: {missing}")
        return 1
    except json.JSONDecodeError as error:
        print(
            "Image generation failed: manifest JSON is malformed "
            f"at line {error.lineno} column {error.colno}"
        )
        return 1
    except (OSError, ImageGenerationError, RetryableProviderError, NonRetryableProviderError) as error:
        print(f"Image generation failed: {error}")
        return 1

    print(
        "Image generation wrote "
        f"{len(manifest.get('assets', []))} assets to {manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
