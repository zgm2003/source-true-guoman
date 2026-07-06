#!/usr/bin/env python3
"""Core helpers for source-true-guoman image generation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any


ALLOWED_OUTPUT_DIRS = {"人设资产", "场景资产", "道具资产"}
SECRET_KEY_NAMES = {"api_key", "authorization", "bearer", "token"}


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
        references = [
            ReferenceImage.from_dict(item)
            for item in data.get("reference_images", [])
            if isinstance(item, dict)
        ]
        return cls(
            job_id=str(data.get("job_id", "")).strip(),
            asset_name=str(data.get("asset_name", "")).strip(),
            asset_type=str(data.get("asset_type", "")).strip(),
            prompt=str(data.get("prompt", "")).strip(),
            output_dir=str(data.get("output_dir", "")).strip(),
            output_file=str(data.get("output_file", "")).strip(),
            depends_on=[str(item).strip() for item in data.get("depends_on", [])],
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
        jobs.append(ImageJob.from_dict(data))
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
    return any(secret in lowered for secret in SECRET_KEY_NAMES)
