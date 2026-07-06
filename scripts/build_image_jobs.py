#!/usr/bin/env python3
"""Build image generation jobs from source-true-guoman asset prompts."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    from scripts.image_generation_core import (
        ImageJob,
        ReferenceImage,
        validate_jobs,
        write_jobs_jsonl,
    )
except ModuleNotFoundError:
    from image_generation_core import ImageJob, ReferenceImage, validate_jobs, write_jobs_jsonl


ASSET_BLOCK_RE = re.compile(r"^##\s+资产提示词\s*$")
HEADING_RE = re.compile(r"^###\s+图片\d+\s*=\s*(.+?)\s*$")
REFERENCE_LINE_MARKER = "上传参考图"
REFERENCE_RE = re.compile(r"(.+?)\s*=\s*图片\d+\s*(?:（([^）]+)）|\(([^)]+)\))")

CHARACTER_OUTPUT_DIR = "人设资产"
SCENE_OUTPUT_DIR = "场景资产"
PROP_OUTPUT_DIR = "道具资产"


def infer_asset_type(asset_name: str, prompt: str) -> tuple[str, str]:
    """Infer the image job asset type and output directory."""
    prompt_without_references = "\n".join(
        line for line in prompt.splitlines() if REFERENCE_LINE_MARKER not in line
    )

    if _has_prop_marker(asset_name):
        return "prop", PROP_OUTPUT_DIR
    if _has_scene_marker(asset_name):
        return "scene", SCENE_OUTPUT_DIR
    if _has_prop_marker(prompt_without_references):
        return "prop", PROP_OUTPUT_DIR
    if _has_scene_marker(prompt_without_references):
        return "scene", SCENE_OUTPUT_DIR
    return "character", CHARACTER_OUTPUT_DIR


def slug_job_id(asset_type: str, asset_name: str) -> str:
    cleaned_asset_name = re.sub(r"\s+", "-", asset_name.strip())
    return f"{asset_type}-{cleaned_asset_name}"


def extract_references(prompt: str) -> tuple[list[str], list[ReferenceImage]]:
    depends_on: list[str] = []
    reference_images: list[ReferenceImage] = []

    for line in prompt.splitlines():
        if REFERENCE_LINE_MARKER not in line:
            continue
        reference_text = _strip_reference_line_prefix(line)
        for part in re.split(r"[；;]", reference_text):
            match = REFERENCE_RE.search(part.strip())
            if not match:
                continue
            asset_name = match.group(1).strip(" ：:")
            purpose = (match.group(2) or match.group(3) or "").strip()
            if not asset_name:
                continue
            if asset_name not in depends_on:
                depends_on.append(asset_name)
            reference_images.append(
                ReferenceImage(asset_name=asset_name, path="", purpose=purpose)
            )

    return depends_on, reference_images


def build_jobs_from_asset_text(
    text: str, model: str, size: str, provider: str = "openai-compatible"
) -> list[ImageJob]:
    jobs: list[ImageJob] = []
    current_name: str | None = None
    current_lines: list[str] = []
    in_asset_block = False

    def flush_current() -> None:
        if current_name is None:
            return

        prompt = "\n".join(current_lines).strip()
        asset_type, output_dir = infer_asset_type(current_name, prompt)
        depends_on, references = extract_references(prompt)
        jobs.append(
            ImageJob(
                job_id=slug_job_id(asset_type, current_name),
                asset_name=current_name,
                asset_type=asset_type,
                prompt=prompt,
                output_dir=output_dir,
                output_file=f"{current_name}.png",
                depends_on=depends_on,
                reference_images=references,
                provider=provider,
                model=model,
                size=size,
                status="pending",
            )
        )

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if ASSET_BLOCK_RE.match(stripped):
            in_asset_block = True
            continue
        if not in_asset_block:
            continue

        match = HEADING_RE.match(stripped)
        if match:
            flush_current()
            current_name = match.group(1).strip()
            current_lines = []
            continue
        if current_name is not None:
            current_lines.append(raw_line)

    flush_current()
    validate_jobs(jobs)
    return jobs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build image jobs from asset prompts.")
    parser.add_argument("--asset-bible", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model", default="gpt-image-2")
    parser.add_argument("--size", default="16:9")
    parser.add_argument("--provider", default="openai-compatible")
    args = parser.parse_args()

    asset_bible_path = Path(args.asset_bible).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    jobs = build_jobs_from_asset_text(
        asset_bible_path.read_text(encoding="utf-8"),
        model=args.model,
        size=args.size,
        provider=args.provider,
    )
    validate_jobs(jobs)
    write_jobs_jsonl(out_path, jobs)
    print(f"Wrote {len(jobs)} image jobs to {out_path}")
    return 0


def _strip_reference_line_prefix(line: str) -> str:
    _, separator, remainder = line.partition("：")
    if separator:
        return remainder
    _, separator, remainder = line.partition(":")
    if separator:
        return remainder
    return line


def _has_scene_marker(value: str) -> bool:
    return any(marker in value for marker in ("母图", "场景", "空场景"))


def _has_prop_marker(value: str) -> bool:
    return any(marker in value for marker in ("单体", "道具", "界面", "系统界面"))


if __name__ == "__main__":
    raise SystemExit(main())
