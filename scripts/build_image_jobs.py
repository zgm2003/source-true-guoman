#!/usr/bin/env python3
"""Build image generation jobs from source-true-guoman asset prompts."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    from scripts.image_generation_core import (
        ImageGenerationError,
        ImageJob,
        ReferenceImage,
        validate_jobs,
        write_jobs_jsonl,
    )
except ModuleNotFoundError:
    from image_generation_core import (
        ImageGenerationError,
        ImageJob,
        ReferenceImage,
        validate_jobs,
        write_jobs_jsonl,
    )


ASSET_BLOCK_RE = re.compile(r"^##\s+资产提示词\s*$")
HEADING_RE = re.compile(r"^###\s+图片\d+\s*=\s*(.+?)\s*$")
MARKDOWN_HEADING_RE = re.compile(r"^#{1,6}\s+")
REFERENCE_LINE_MARKER = "上传参考图"
REFERENCE_RE = re.compile(r"(.+?)\s*=\s*图片\d+\s*(?:（([^）]+)）|\(([^)]+)\))")

CHARACTER_OUTPUT_DIR = "人设资产"
SCENE_OUTPUT_DIR = "场景资产"
PROP_OUTPUT_DIR = "道具资产"
SCENE_STYLE_BASELINE_PURPOSE = "场景风格基准参考"
CHARACTER_STYLE_BASELINE_PURPOSE = "人设风格基准参考"

SECTION_ASSET_TYPES = {
    "character": ("character", CHARACTER_OUTPUT_DIR),
    "scene": ("scene", SCENE_OUTPUT_DIR),
    "prop": ("prop", PROP_OUTPUT_DIR),
}


def infer_asset_type(
    asset_name: str, prompt: str, section_kind: str | None = None
) -> tuple[str, str]:
    """Infer the image job asset type and output directory."""
    if section_kind in SECTION_ASSET_TYPES:
        return SECTION_ASSET_TYPES[section_kind]

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
    text: str,
    model: str,
    size: str,
    provider: str = "openai-compatible",
    style_stage: str = "confirmed",
) -> list[ImageJob]:
    if style_stage not in {"preview", "confirmed", "none"}:
        raise ImageGenerationError("style_stage must be preview, confirmed, or none")

    jobs: list[ImageJob] = []
    current_name: str | None = None
    current_lines: list[str] = []
    current_section_kind: str | None = None
    current_job_section_kind: str | None = None
    in_asset_block = False

    def flush_current() -> None:
        nonlocal current_name, current_lines, current_job_section_kind
        if current_name is None:
            return

        prompt = "\n".join(current_lines).strip()
        asset_type, output_dir = infer_asset_type(
            current_name,
            prompt,
            current_job_section_kind,
        )
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
        current_name = None
        current_lines = []
        current_job_section_kind = None

    for raw_line in text.splitlines():
        stripped = raw_line.strip()

        match = HEADING_RE.match(stripped)
        if match:
            flush_current()
            in_asset_block = True
            current_name = match.group(1).strip()
            current_lines = []
            current_job_section_kind = current_section_kind
            continue

        if ASSET_BLOCK_RE.match(stripped):
            flush_current()
            current_section_kind = None
            in_asset_block = True
            continue

        if current_name is not None and MARKDOWN_HEADING_RE.match(stripped):
            flush_current()
            current_section_kind = _section_kind(stripped)
            in_asset_block = current_section_kind is not None
            continue

        if current_name is None and MARKDOWN_HEADING_RE.match(stripped):
            current_section_kind = _section_kind(stripped)
            in_asset_block = current_section_kind is not None
            continue

        if not in_asset_block:
            continue
        if current_name is not None:
            current_lines.append(raw_line)

    flush_current()
    _resolve_reference_paths(jobs)
    if style_stage == "preview":
        jobs = _style_preview_jobs(jobs)
    elif style_stage == "confirmed":
        _apply_confirmed_style_baselines(jobs)
    validate_jobs(jobs)
    return jobs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build image jobs from asset prompts.")
    parser.add_argument("--asset-bible", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model", default="gpt-image-2")
    parser.add_argument("--size", default="16:9")
    parser.add_argument("--provider", default="openai-compatible")
    parser.add_argument(
        "--style-stage",
        choices=("preview", "confirmed", "none"),
        default="confirmed",
        help="preview writes only the first scene and first character for user style confirmation; confirmed writes the full job set with style references.",
    )
    args = parser.parse_args()

    asset_bible_path = Path(args.asset_bible).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    try:
        jobs = build_jobs_from_asset_text(
            asset_bible_path.read_text(encoding="utf-8"),
            model=args.model,
            size=args.size,
            provider=args.provider,
            style_stage=args.style_stage,
        )
        validate_jobs(jobs)
        write_jobs_jsonl(out_path, jobs)
    except (OSError, ImageGenerationError) as error:
        print("Image job build failed:")
        print(f"- {error}")
        return 1

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
    return any(marker in value for marker in ("母图", "空场景", "场景参考图"))


def _has_prop_marker(value: str) -> bool:
    return any(marker in value for marker in ("单体", "道具", "界面", "系统界面"))


def _section_kind(stripped_heading: str) -> str | None:
    heading_text = stripped_heading.lstrip("#").strip()
    if heading_text in {"Character Assets", "角色资产", "人设资产"}:
        return "character"
    if heading_text in {"Scene Assets", "场景资产"}:
        return "scene"
    if heading_text.startswith("Prop, Interface, Beast, Vehicle Assets"):
        return "prop"
    if heading_text in {"Prop Assets", "道具资产", "Interface Assets", "界面资产"}:
        return "prop"
    return None


def _resolve_reference_paths(jobs: list[ImageJob]) -> None:
    paths_by_asset = {job.asset_name: job.output_path.as_posix() for job in jobs}
    for job in jobs:
        for reference in job.reference_images:
            if not reference.path and reference.asset_name in paths_by_asset:
                reference.path = paths_by_asset[reference.asset_name]


def _style_preview_jobs(jobs: list[ImageJob]) -> list[ImageJob]:
    first_scene, first_character = _style_baseline_jobs(jobs)
    preview_jobs = [
        job
        for job in jobs
        if job is first_scene or job is first_character
    ]
    return preview_jobs


def _style_baseline_jobs(
    jobs: list[ImageJob],
) -> tuple[ImageJob | None, ImageJob | None]:
    first_scene = next((job for job in jobs if job.asset_type == "scene"), None)
    first_character = next((job for job in jobs if job.asset_type == "character"), None)
    return first_scene, first_character


def _apply_confirmed_style_baselines(jobs: list[ImageJob]) -> None:
    first_scene, first_character = _style_baseline_jobs(jobs)
    for job in jobs:
        if first_character is not None and job.asset_type == "character":
            if job is first_character:
                continue
            _prepend_reference(
                job,
                first_character,
                CHARACTER_STYLE_BASELINE_PURPOSE,
            )
            continue
        if first_scene is not None and job.asset_type in {"scene", "prop"}:
            if job is first_scene:
                continue
            _prepend_reference(
                job,
                first_scene,
                SCENE_STYLE_BASELINE_PURPOSE,
            )


def _prepend_reference(
    job: ImageJob,
    reference_job: ImageJob,
    purpose: str,
) -> None:
    if job.asset_name == reference_job.asset_name:
        return
    if reference_job.asset_name not in job.depends_on:
        job.depends_on.insert(0, reference_job.asset_name)
    reference_path = reference_job.output_path.as_posix()
    existing_reference = next(
        (
            reference
            for reference in job.reference_images
            if reference.asset_name == reference_job.asset_name
            and reference.purpose == purpose
        ),
        None,
    )
    if existing_reference is not None:
        existing_reference.path = existing_reference.path or reference_path
        return
    insert_index = 0
    while (
        insert_index < len(job.reference_images)
        and job.reference_images[insert_index].purpose
        in {
            SCENE_STYLE_BASELINE_PURPOSE,
            CHARACTER_STYLE_BASELINE_PURPOSE,
        }
    ):
        insert_index += 1
    job.reference_images.insert(
        insert_index,
        ReferenceImage(
            asset_name=reference_job.asset_name,
            path=reference_path,
            purpose=purpose,
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())
