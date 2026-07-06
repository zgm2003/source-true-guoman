#!/usr/bin/env python3
"""Core helpers for source-true-guoman image generation."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any


ALLOWED_OUTPUT_DIRS = {"人设资产", "场景资产", "道具资产"}
ALLOWED_MANIFEST_STATUSES = {"done", "failed", "blocked"}
PRODUCTION_OUTPUT_DIR = "生产资产"
SECRET_KEY_NAMES = {"api_key", "authorization", "bearer", "token"}
RAW_SECRET_VALUE_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")


class ImageGenerationError(ValueError):
    """Raised when image generation inputs or state are invalid."""


@dataclass
class ReferenceImage:
    asset_name: str
    path: str
    purpose: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReferenceImage":
        return cls(
            asset_name=str(data.get("asset_name", "")).strip(),
            path=str(data.get("path", "")).strip(),
            purpose=str(data.get("purpose", "")).strip(),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "asset_name": self.asset_name,
            "path": self.path,
            "purpose": self.purpose,
        }


@dataclass
class ImageJob:
    job_id: str
    asset_name: str
    asset_type: str
    prompt: str
    output_dir: str
    output_file: str
    depends_on: list[str]
    reference_images: list[ReferenceImage]
    provider: str
    model: str
    size: str
    status: str = "pending"
    _has_depends_on: bool = field(default=True, repr=False)
    _has_reference_images: bool = field(default=True, repr=False)

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir) / self.output_file

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImageJob":
        raw_depends_on = data.get("depends_on", [])
        raw_reference_images = data.get("reference_images", [])
        if "depends_on" in data and not isinstance(raw_depends_on, list):
            raise ImageGenerationError("depends_on must be a list")
        if "reference_images" in data and not isinstance(raw_reference_images, list):
            raise ImageGenerationError("reference_images must be a list")

        references = [
            ReferenceImage.from_dict(item)
            for item in raw_reference_images
            if isinstance(item, dict)
        ]
        return cls(
            job_id=str(data.get("job_id", "")).strip(),
            asset_name=str(data.get("asset_name", "")).strip(),
            asset_type=str(data.get("asset_type", "")).strip(),
            prompt=str(data.get("prompt", "")).strip(),
            output_dir=str(data.get("output_dir", "")).strip(),
            output_file=str(data.get("output_file", "")).strip(),
            depends_on=[str(item).strip() for item in raw_depends_on],
            reference_images=references,
            provider=str(data.get("provider", "")).strip(),
            model=str(data.get("model", "")).strip(),
            size=str(data.get("size", "")).strip(),
            status=str(data.get("status", "")).strip(),
            _has_depends_on="depends_on" in data,
            _has_reference_images="reference_images" in data,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "asset_name": self.asset_name,
            "asset_type": self.asset_type,
            "prompt": self.prompt,
            "output_dir": self.output_dir,
            "output_file": self.output_file,
            "depends_on": self.depends_on,
            "reference_images": [ref.to_dict() for ref in self.reference_images],
            "provider": self.provider,
            "model": self.model,
            "size": self.size,
            "status": self.status,
        }


def prompt_hash(prompt: str) -> str:
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def load_jobs_jsonl(path: Path) -> list[ImageJob]:
    jobs: list[ImageJob] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as error:
            raise ImageGenerationError(f"line {line_number}: invalid JSON") from error
        if not isinstance(data, dict):
            raise ImageGenerationError(f"line {line_number}: job must be an object")
        try:
            jobs.append(ImageJob.from_dict(data))
        except ImageGenerationError as error:
            raise ImageGenerationError(f"line {line_number}: {error}") from error
    return jobs


def write_jobs_jsonl(path: Path, jobs: list[ImageJob]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(
        json.dumps(job.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
        for job in jobs
    )
    path.write_text(text, encoding="utf-8")


def validate_jobs(jobs: list[ImageJob]) -> list[str]:
    errors: list[str] = []
    job_ids: set[str] = set()
    asset_names: set[str] = set()

    for job in jobs:
        if not job.job_id:
            errors.append("job_id is required")
        elif job.job_id in job_ids:
            errors.append(f"duplicate job_id: {job.job_id}")
        job_ids.add(job.job_id)

        if not job.asset_name:
            errors.append(f"{job.job_id}: asset_name is required")
        elif job.asset_name in asset_names:
            errors.append(f"duplicate asset_name: {job.asset_name}")
        asset_names.add(job.asset_name)

        if not job.asset_type:
            errors.append(f"{job.asset_name}: asset_type is required")
        if not job.prompt:
            errors.append(f"{job.asset_name}: prompt is required")
        if not job.provider:
            errors.append(f"{job.asset_name}: provider is required")
        if not job.model:
            errors.append(f"{job.asset_name}: model is required")
        if not job.size:
            errors.append(f"{job.asset_name}: size is required")
        if not job.status:
            errors.append(f"{job.asset_name}: status is required")
        if not job._has_depends_on:
            errors.append(f"{job.asset_name}: depends_on is required")
        if not job._has_reference_images:
            errors.append(f"{job.asset_name}: reference_images is required")
        for index, reference in enumerate(job.reference_images, start=1):
            reference_label = f"{job.asset_name}: reference {index}"
            if not reference.asset_name:
                errors.append(f"{reference_label}: reference asset_name is required")
            if not reference.path:
                errors.append(f"{reference_label}: reference path is required")
            if not reference.purpose:
                errors.append(f"{reference_label}: reference purpose is required")
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

    known_assets = {job.asset_name for job in jobs}
    for job in jobs:
        for dependency in job.depends_on:
            if dependency not in known_assets:
                errors.append(f"{job.asset_name}: unknown dependency {dependency}")

    if errors:
        raise ImageGenerationError("; ".join(errors))
    return errors


def _has_drive_prefix(path: str) -> bool:
    return len(path) >= 2 and path[0].isalpha() and path[1] == ":"


def build_dependency_waves(jobs: list[ImageJob]) -> list[list[ImageJob]]:
    validate_jobs(jobs)
    by_asset = {job.asset_name: job for job in jobs}
    remaining = set(by_asset)
    completed: set[str] = set()
    waves: list[list[ImageJob]] = []

    while remaining:
        ready_names = [
            asset_name
            for asset_name in remaining
            if all(dependency in completed for dependency in by_asset[asset_name].depends_on)
        ]
        if not ready_names:
            unresolved = ", ".join(sorted(remaining))
            raise ImageGenerationError(f"cyclic dependencies or blocked graph: {unresolved}")
        ready_names.sort(key=lambda name: jobs.index(by_asset[name]))
        wave = [by_asset[name] for name in ready_names]
        waves.append(wave)
        completed.update(ready_names)
        remaining.difference_update(ready_names)

    return waves


def contains_secret_text(value: str) -> bool:
    lowered = value.casefold()
    return (
        any(secret in lowered for secret in SECRET_KEY_NAMES)
        or RAW_SECRET_VALUE_PATTERN.search(value) is not None
    )


def _walk_json_values(value: Any) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if contains_secret_text(str(key)):
                found.append((str(key), str(child)))
            found.extend(_walk_json_values(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_json_values(child))
    elif isinstance(value, str) and contains_secret_text(value):
        found.append(("value", value))
    return found


def validate_manifest(
    manifest: dict[str, Any], jobs: list[ImageJob], workspace: Path
) -> list[str]:
    errors: list[str] = []
    if _walk_json_values(manifest):
        errors.append("manifest must not contain secret key names")

    assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        return ["manifest assets must be a list"]

    jobs_by_name = {job.asset_name: job for job in jobs}
    seen_asset_names: set[str] = set()
    for asset in assets:
        if not isinstance(asset, dict):
            errors.append("manifest asset entry must be an object")
            continue
        asset_name = str(asset.get("asset_name", "")).strip()
        asset_label = asset_name or "<missing asset_name>"
        asset_type = str(asset.get("asset_type", "")).strip()
        path_text = str(asset.get("path", "")).strip()
        status = str(asset.get("status", "")).strip()

        if not asset_name:
            errors.append("asset_name is required")
        elif asset_name in seen_asset_names:
            errors.append(f"duplicate asset_name: {asset_name}")
        if asset_name:
            seen_asset_names.add(asset_name)
        if not asset_type:
            errors.append(f"{asset_label}: asset_type is required")
        if not status:
            errors.append(f"{asset_label}: status is required")
        elif status not in ALLOWED_MANIFEST_STATUSES:
            errors.append(
                f"{asset_label}: status must be one of {sorted(ALLOWED_MANIFEST_STATUSES)}"
            )

        path_errors, image_path = _validate_manifest_image_path(
            asset_label, path_text, workspace
        )

        job = jobs_by_name.get(asset_name)
        if jobs_by_name and asset_name and job is None:
            errors.append(f"{asset_name}: manifest asset not present in jobs")
        elif job is not None:
            expected_path = job.output_path.as_posix()
            if path_text != expected_path:
                errors.append(
                    f"{asset_name}: path must match job output {expected_path}"
                )
            expected_prompt_hash = prompt_hash(job.prompt)
            if "prompt_hash" in asset and asset.get("prompt_hash") != expected_prompt_hash:
                errors.append(
                    f"{asset_name}: prompt_hash must match current job prompt"
                )
            if "model" in asset and asset.get("model") != job.model:
                errors.append(f"{asset_name}: model must match current job model")
            if "size" in asset and asset.get("size") != job.size:
                errors.append(f"{asset_name}: size must match current job size")

        errors.extend(path_errors)
        reference_errors, normalized_references = _validate_manifest_references(
            asset_label,
            asset.get("references"),
            workspace,
        )
        errors.extend(reference_errors)
        if job is not None:
            expected_references = [
                reference.to_dict() for reference in job.reference_images
            ]
            if normalized_references != expected_references:
                errors.append(
                    f"{asset_label}: references must match current job references"
                )
        if status == "done" and image_path is not None:
            if not image_path.is_file():
                errors.append(f"{asset_label}: done asset missing local file {path_text}")
        if status in {"failed", "blocked"} and not str(asset.get("last_error", "")).strip():
            errors.append(f"{asset_label}: {status} asset must record last_error")

    return errors


def _validate_manifest_references(
    asset_name: str,
    references_value: Any,
    workspace: Path,
) -> tuple[list[str], list[dict[str, str]]]:
    errors: list[str] = []
    normalized_references: list[dict[str, str]] = []

    if references_value is None:
        return errors, normalized_references
    if not isinstance(references_value, list):
        return [f"{asset_name}: references must be a list"], normalized_references

    for index, reference in enumerate(references_value, start=1):
        reference_label = f"{asset_name}: reference {index}"
        if not isinstance(reference, dict):
            errors.append(f"{reference_label}: reference entry must be an object")
            continue

        reference_asset_name = str(reference.get("asset_name", "")).strip()
        path_text = str(reference.get("path", "")).strip()
        purpose = str(reference.get("purpose", "")).strip()
        if not reference_asset_name:
            errors.append(f"{reference_label}: reference asset_name is required")
        if not purpose:
            errors.append(f"{reference_label}: reference purpose is required")

        path_errors, reference_path = _validate_reference_image_path(
            reference_label,
            path_text,
            workspace,
        )
        errors.extend(path_errors)
        if reference_path is not None and not reference_path.is_file():
            errors.append(
                f"{reference_label}: reference image missing local file {path_text}"
            )

        normalized_references.append(
            {
                "asset_name": reference_asset_name,
                "path": path_text,
                "purpose": purpose,
            }
        )

    return errors, normalized_references


def _validate_reference_image_path(
    reference_label: str, path_text: str, workspace: Path
) -> tuple[list[str], Path | None]:
    errors: list[str] = []
    path = Path(path_text)

    if not path_text:
        errors.append(f"{reference_label}: reference path is required")
        return errors, None
    if _has_drive_prefix(path_text):
        errors.append(f"{reference_label}: reference path must not use a drive prefix")
    if path.is_absolute():
        errors.append(f"{reference_label}: reference path must be relative")
    if errors:
        return errors, None

    workspace_path = workspace.resolve(strict=False)
    resolved_path = (workspace_path / path).resolve(strict=False)
    try:
        relative_path = resolved_path.relative_to(workspace_path)
    except ValueError:
        errors.append(f"{reference_label}: reference path must stay under workspace")
        return errors, None

    if relative_path.parts and relative_path.parts[0] == PRODUCTION_OUTPUT_DIR:
        errors.append(
            f"{reference_label}: reference path must not be under {PRODUCTION_OUTPUT_DIR}"
        )
    if not relative_path.parts or relative_path.parts[0] not in ALLOWED_OUTPUT_DIRS:
        errors.append(
            f"{reference_label}: reference path must start with one of "
            f"{sorted(ALLOWED_OUTPUT_DIRS)}"
        )

    return errors, resolved_path


def _validate_manifest_image_path(
    asset_name: str, path_text: str, workspace: Path
) -> tuple[list[str], Path | None]:
    errors: list[str] = []
    path = Path(path_text)

    if not path_text:
        errors.append(f"{asset_name}: generated image path is required")
        return errors, None
    if _has_drive_prefix(path_text):
        errors.append(f"{asset_name}: generated image path must not use a drive prefix")
    if path.is_absolute():
        errors.append(f"{asset_name}: generated image path must be relative")
    if errors:
        return errors, None

    workspace_path = workspace.resolve(strict=False)
    resolved_path = (workspace_path / path).resolve(strict=False)
    try:
        relative_path = resolved_path.relative_to(workspace_path)
    except ValueError:
        errors.append(f"{asset_name}: generated image path must stay under workspace")
        return errors, None

    if relative_path.parts and relative_path.parts[0] == PRODUCTION_OUTPUT_DIR:
        errors.append(
            f"{asset_name}: generated image path must not be under {PRODUCTION_OUTPUT_DIR}"
        )
    if not relative_path.parts or relative_path.parts[0] not in ALLOWED_OUTPUT_DIRS:
        errors.append(
            f"{asset_name}: generated image path must start with one of "
            f"{sorted(ALLOWED_OUTPUT_DIRS)}"
        )

    return errors, resolved_path
