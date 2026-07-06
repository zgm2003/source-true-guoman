#!/usr/bin/env python3
"""Core helpers for source-true-guoman storyboard contact sheets."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any


STORYBOARD_OUTPUT_DIR = "分镜资产"
PRODUCTION_OUTPUT_DIR = "生产资产"
REFERENCE_OUTPUT_DIRS = {"人设资产", "场景资产", "道具资产"}
FULL_GROUP_SIZE = 25
FULL_GROUP_INSTRUCTION = "生成5*5的分镜图，分镜图上不允许有台词。"
PARTIAL_GROUP_INSTRUCTION_TEMPLATE = "生成{count}格分镜图，分镜图上不允许有台词。"
ALLOWED_STORYBOARD_STATUSES = {"pending", "done", "failed", "blocked"}
NUMBERED_LINE_RE = re.compile(r"^(\d+)\s+")
RAW_SECRET_VALUE_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")


class StoryboardGenerationError(ValueError):
    """Raised when storyboard job inputs or state are invalid."""


@dataclass
class StoryboardReference:
    asset_name: str
    path: str
    purpose: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StoryboardReference":
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
class StoryboardJob:
    job_id: str
    group_index: int
    line_start: int
    line_end: int
    line_count: int
    source_feed: str
    prompt: str
    output_dir: str
    output_file: str
    reference_images: list[StoryboardReference]
    provider: str
    model: str
    size: str
    status: str = "pending"
    _has_reference_images: bool = field(default=True, repr=False)

    @property
    def asset_name(self) -> str:
        return self.job_id

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir) / self.output_file

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StoryboardJob":
        raw_references = data.get("reference_images", [])
        if "reference_images" in data and not isinstance(raw_references, list):
            raise StoryboardGenerationError("reference_images must be a list")
        return cls(
            job_id=str(data.get("job_id", "")).strip(),
            group_index=int(data.get("group_index", 0)),
            line_start=int(data.get("line_start", 0)),
            line_end=int(data.get("line_end", 0)),
            line_count=int(data.get("line_count", 0)),
            source_feed=str(data.get("source_feed", "")).strip(),
            prompt=str(data.get("prompt", "")).strip(),
            output_dir=str(data.get("output_dir", "")).strip(),
            output_file=str(data.get("output_file", "")).strip(),
            reference_images=[
                StoryboardReference.from_dict(item)
                for item in raw_references
                if isinstance(item, dict)
            ],
            provider=str(data.get("provider", "")).strip(),
            model=str(data.get("model", "")).strip(),
            size=str(data.get("size", "")).strip(),
            status=str(data.get("status", "")).strip(),
            _has_reference_images="reference_images" in data,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "group_index": self.group_index,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "line_count": self.line_count,
            "source_feed": self.source_feed,
            "prompt": self.prompt,
            "output_dir": self.output_dir,
            "output_file": self.output_file,
            "reference_images": [reference.to_dict() for reference in self.reference_images],
            "provider": self.provider,
            "model": self.model,
            "size": self.size,
            "status": self.status,
        }


def prompt_hash(prompt: str) -> str:
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def extract_numbered_feed_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        match = NUMBERED_LINE_RE.match(stripped)
        if not match:
            continue
        lines.append((int(match.group(1)), stripped))
    return lines


def load_storyboard_jobs_jsonl(path: Path) -> list[StoryboardJob]:
    jobs: list[StoryboardJob] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as error:
            raise StoryboardGenerationError(f"line {line_number}: invalid JSON") from error
        if not isinstance(data, dict):
            raise StoryboardGenerationError(f"line {line_number}: job must be an object")
        try:
            jobs.append(StoryboardJob.from_dict(data))
        except (TypeError, ValueError) as error:
            raise StoryboardGenerationError(f"line {line_number}: {error}") from error
    return jobs


def write_storyboard_jobs_jsonl(path: Path, jobs: list[StoryboardJob]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(
        json.dumps(job.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
        for job in jobs
    )
    path.write_text(text, encoding="utf-8")


def validate_storyboard_jobs(jobs: list[StoryboardJob]) -> list[str]:
    errors: list[str] = []
    job_ids: set[str] = set()

    if not jobs:
        raise StoryboardGenerationError("storyboard jobs must not be empty")

    for job in jobs:
        label = job.job_id or "<missing job_id>"
        if not job.job_id:
            errors.append("job_id is required")
        elif job.job_id in job_ids:
            errors.append(f"duplicate job_id: {job.job_id}")
        job_ids.add(job.job_id)

        if job.group_index <= 0:
            errors.append(f"{label}: group_index must be greater than zero")
        if job.line_start <= 0:
            errors.append(f"{label}: line_start must be greater than zero")
        if job.line_end < job.line_start:
            errors.append(f"{label}: line_end must be greater than or equal to line_start")
        if job.line_count != job.line_end - job.line_start + 1:
            errors.append(f"{label}: line_count must match line_start and line_end")
        if job.line_count <= 0 or job.line_count > FULL_GROUP_SIZE:
            errors.append(f"{label}: line_count must be between 1 and {FULL_GROUP_SIZE}")
        if not job.source_feed:
            errors.append(f"{label}: source_feed is required")
        if not job.prompt:
            errors.append(f"{label}: prompt is required")
        if not job.provider:
            errors.append(f"{label}: provider is required")
        if not job.model:
            errors.append(f"{label}: model is required")
        if not job.size:
            errors.append(f"{label}: size is required")
        if job.status not in ALLOWED_STORYBOARD_STATUSES:
            errors.append(f"{label}: status must be one of {sorted(ALLOWED_STORYBOARD_STATUSES)}")
        if job.output_dir != STORYBOARD_OUTPUT_DIR:
            errors.append(f"{label}: output_dir must be {STORYBOARD_OUTPUT_DIR}")
        if not job.output_file.endswith(".png"):
            errors.append(f"{label}: output_file must end with .png")
        if (
            "/" in job.output_file
            or "\\" in job.output_file
            or Path(job.output_file).is_absolute()
            or _has_drive_prefix(job.output_file)
        ):
            errors.append(f"{label}: output_file must be a file name only")
        if not job._has_reference_images:
            errors.append(f"{label}: reference_images is required")
        if not job.reference_images:
            errors.append(f"{label}: at least one real reference image is required")
        for index, reference in enumerate(job.reference_images, start=1):
            _validate_reference_shape(label, index, reference, errors)
        _validate_prompt_instruction(job, errors)
        if contains_secret_text(job.prompt):
            errors.append(f"{label}: prompt must not contain secrets")

    if errors:
        raise StoryboardGenerationError("; ".join(errors))
    return errors


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise StoryboardGenerationError(
            f"{label} JSON is malformed at line {error.lineno} column {error.colno}"
        ) from error
    if not isinstance(data, dict):
        raise StoryboardGenerationError(f"{label} must be a JSON object")
    return data


def manifest_assets_by_name(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        raise StoryboardGenerationError("manifest assets must be a list")
    by_name: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            raise StoryboardGenerationError("manifest asset entry must be an object")
        asset_name = str(asset.get("asset_name", "")).strip()
        if asset_name:
            by_name[asset_name] = asset
    return by_name


def validate_reference_file(
    reference: StoryboardReference,
    workspace: Path,
    manifest_by_name: dict[str, dict[str, Any]],
) -> None:
    asset = manifest_by_name.get(reference.asset_name)
    if asset is None:
        raise StoryboardGenerationError(f"{reference.asset_name}: missing from image manifest")
    if str(asset.get("status", "")).strip() != "done":
        raise StoryboardGenerationError(f"{reference.asset_name}: manifest asset is not done")
    manifest_path = str(asset.get("path", "")).strip()
    if manifest_path != reference.path:
        raise StoryboardGenerationError(
            f"{reference.asset_name}: reference path must match manifest path {manifest_path}"
        )

    path_errors: list[str] = []
    _validate_reference_shape("reference-gate", 1, reference, path_errors)
    if path_errors:
        raise StoryboardGenerationError("; ".join(path_errors))

    workspace_path = Path(workspace).resolve(strict=False)
    resolved_path = (workspace_path / reference.path).resolve(strict=False)
    try:
        resolved_path.relative_to(workspace_path)
    except ValueError as error:
        raise StoryboardGenerationError(
            f"{reference.asset_name}: reference path must stay under workspace"
        ) from error
    if not resolved_path.is_file():
        raise StoryboardGenerationError(
            f"{reference.asset_name}: missing local file {reference.path}"
        )


def contains_secret_text(value: str) -> bool:
    return RAW_SECRET_VALUE_PATTERN.search(value) is not None


def _validate_prompt_instruction(job: StoryboardJob, errors: list[str]) -> None:
    if job.line_count == FULL_GROUP_SIZE:
        if FULL_GROUP_INSTRUCTION not in job.prompt:
            errors.append(f"{job.job_id}: missing full 25-line instruction")
        return

    expected = PARTIAL_GROUP_INSTRUCTION_TEMPLATE.format(count=job.line_count)
    if expected not in job.prompt:
        errors.append(f"{job.job_id}: missing partial {job.line_count}-panel instruction")
    if FULL_GROUP_INSTRUCTION in job.prompt:
        errors.append(f"{job.job_id}: partial group must not use full 25-line instruction")


def _validate_reference_shape(
    job_label: str,
    index: int,
    reference: StoryboardReference,
    errors: list[str],
) -> None:
    reference_label = f"{job_label}: reference {index}"
    if not reference.asset_name:
        errors.append(f"{reference_label}: reference asset_name is required")
    if not reference.path:
        errors.append(f"{reference_label}: reference path is required")
        return
    if not reference.purpose:
        errors.append(f"{reference_label}: reference purpose is required")

    path = Path(reference.path)
    if _has_drive_prefix(reference.path) or path.is_absolute():
        errors.append(f"{reference_label}: reference path must be relative")
        return
    if ".." in path.parts:
        errors.append(f"{reference_label}: reference path must stay under workspace")
    if not path.parts or path.parts[0] not in REFERENCE_OUTPUT_DIRS:
        errors.append(
            f"{reference_label}: reference path must start with one of "
            f"{sorted(REFERENCE_OUTPUT_DIRS)}"
        )
    if path.parts and path.parts[0] == PRODUCTION_OUTPUT_DIR:
        errors.append(f"{reference_label}: reference path must not be under {PRODUCTION_OUTPUT_DIR}")


def _has_drive_prefix(path: str) -> bool:
    return len(path) >= 2 and path[0].isalpha() and path[1] == ":"
