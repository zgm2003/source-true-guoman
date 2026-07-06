#!/usr/bin/env python3
"""OpenAI-compatible image provider and per-job retry helpers."""

from __future__ import annotations

import base64
import binascii
import json
import logging
import os
import random
import re
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Callable

try:
    from scripts.image_generation_core import ImageGenerationError
    from scripts.image_generation_core import ImageJob
    from scripts.image_generation_core import prompt_hash
except ModuleNotFoundError:
    from image_generation_core import ImageGenerationError
    from image_generation_core import ImageJob
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
    last_error = ""

    while True:
        attempts += 1
        LOGGER.info("Generating image asset %s, attempt %s", job.asset_name, attempts)
        try:
            image_bytes = provider(job, config)
            output_path = _workspace_output_path(workspace, job)
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


def _float_env(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    try:
        return float(value)
    except ValueError as error:
        raise ImageGenerationError(f"{name} must be a number") from error


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
    if config.timeout_seconds <= 0:
        errors.append("SOURCE_TRUE_IMAGE_TIMEOUT_SECONDS must be greater than zero")
    if config.max_retries < 0:
        errors.append("SOURCE_TRUE_IMAGE_MAX_RETRIES must be zero or greater")
    if config.retry_base_seconds < 0:
        errors.append("SOURCE_TRUE_IMAGE_RETRY_BASE_SECONDS must be zero or greater")
    if config.retry_max_seconds < 0:
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
    workspace_path = workspace.resolve(strict=False)
    output_path = (workspace_path / job.output_path).resolve(strict=False)
    try:
        output_path.relative_to(workspace_path)
    except ValueError as error:
        raise NonRetryableProviderError("output path must stay under workspace") from error
    return output_path


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


def _references(job: ImageJob) -> list[dict[str, str]]:
    return [reference.to_dict() for reference in job.reference_images]


def _job_model(job: ImageJob, config: ImageGenerationConfig) -> str:
    return job.model or config.model


def _job_size(job: ImageJob, config: ImageGenerationConfig) -> str:
    return job.size or config.size


def _sanitize_error(message: str, config: ImageGenerationConfig) -> str:
    sanitized = message
    for secret in {config.api_key, config.base_url, config.base_url.rstrip("/")}:
        if secret:
            sanitized = sanitized.replace(secret, "[redacted]")
    sanitized = SECRET_VALUE_PATTERN.sub("[redacted]", sanitized)
    sanitized = SECRET_NAME_PATTERN.sub("credential", sanitized)
    return sanitized or "provider error"
