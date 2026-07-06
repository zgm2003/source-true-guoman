#!/usr/bin/env python3
"""Build storyboard contact-sheet jobs from a source-true-guoman feed."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    from scripts.storyboard_generation_core import (
        FULL_GROUP_INSTRUCTION,
        FULL_GROUP_SIZE,
        PARTIAL_GROUP_INSTRUCTION_TEMPLATE,
        STORYBOARD_OUTPUT_DIR,
        StoryboardGenerationError,
        StoryboardJob,
        StoryboardReference,
        extract_numbered_feed_lines,
        load_json_object,
        manifest_assets_by_name,
        validate_reference_file,
        validate_storyboard_jobs,
        write_storyboard_jobs_jsonl,
    )
except ModuleNotFoundError:
    from storyboard_generation_core import (
        FULL_GROUP_INSTRUCTION,
        FULL_GROUP_SIZE,
        PARTIAL_GROUP_INSTRUCTION_TEMPLATE,
        STORYBOARD_OUTPUT_DIR,
        StoryboardGenerationError,
        StoryboardJob,
        StoryboardReference,
        extract_numbered_feed_lines,
        load_json_object,
        manifest_assets_by_name,
        validate_reference_file,
        validate_storyboard_jobs,
        write_storyboard_jobs_jsonl,
    )


COPY_PACK_HEADING_RE = re.compile(r"^### 投喂包 \d{3}｜原始行 (\d+)-(\d+)$")
REFERENCE_BINDING_RE = re.compile(
    r"^-\s*(?:场景|角色|道具|界面)\d+\s*=\s*(.+?)\s*=\s*(.+?)\s*$"
)
ASSET_BIBLE_NAME_RE = re.compile(
    r"^\s*(?:-\s*)?(?:Asset name|资产名|资产名称)\s*[:：]\s*(.+?)\s*$"
)
ASSET_BIBLE_IMAGE_HEADING_RE = re.compile(r"^###\s+图片\d+\s*=\s*(.+?)\s*$")


def build_storyboard_jobs(
    feed_path: Path,
    manifest_path: Path,
    workspace: Path,
    copy_packs_path: Path | None = None,
    asset_bible_path: Path | None = None,
    model: str = "gpt-image-2",
    size: str = "16:9",
    provider: str = "openai-compatible",
) -> list[StoryboardJob]:
    feed_text = feed_path.read_text(encoding="utf-8")
    numbered_lines = extract_numbered_feed_lines(feed_text)
    if not numbered_lines:
        raise StoryboardGenerationError("feed has no numbered video lines")
    _validate_continuous_lines(numbered_lines)

    manifest = load_json_object(manifest_path, "manifest")
    manifest_by_name = manifest_assets_by_name(manifest)
    copy_pack_refs = (
        parse_copy_pack_references(copy_packs_path.read_text(encoding="utf-8"))
        if copy_packs_path is not None
        else {}
    )
    asset_bible_refs = (
        parse_asset_bible_references(asset_bible_path.read_text(encoding="utf-8"), manifest_by_name)
        if asset_bible_path is not None
        else []
    )

    jobs: list[StoryboardJob] = []
    for group_index, start_index in enumerate(
        range(0, len(numbered_lines), FULL_GROUP_SIZE),
        start=1,
    ):
        group = numbered_lines[start_index : start_index + FULL_GROUP_SIZE]
        line_start = group[0][0]
        line_end = group[-1][0]
        references = references_for_group(
            group,
            copy_pack_refs,
            asset_bible_refs,
            manifest_by_name,
            workspace,
        )
        instruction = (
            FULL_GROUP_INSTRUCTION
            if len(group) == FULL_GROUP_SIZE
            else PARTIAL_GROUP_INSTRUCTION_TEMPLATE.format(count=len(group))
        )
        prompt = build_prompt(group, references, instruction)
        jobs.append(
            StoryboardJob(
                job_id=f"storyboard-{group_index:03d}-lines-{line_start:03d}-{line_end:03d}",
                group_index=group_index,
                line_start=line_start,
                line_end=line_end,
                line_count=len(group),
                source_feed=_relative_or_name(feed_path, workspace),
                prompt=prompt,
                output_dir=STORYBOARD_OUTPUT_DIR,
                output_file=(
                    f"storyboard-contact-sheet-{group_index:03d}-lines-"
                    f"{line_start:03d}-{line_end:03d}.png"
                ),
                reference_images=references,
                provider=provider,
                model=model,
                size=size,
                status="pending",
            )
        )

    validate_storyboard_jobs(jobs)
    return jobs


def parse_copy_pack_references(text: str) -> dict[tuple[int, int], list[StoryboardReference]]:
    bindings: dict[tuple[int, int], list[StoryboardReference]] = {}
    current_range: tuple[int, int] | None = None
    inside_upload_block = False

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        heading_match = COPY_PACK_HEADING_RE.match(stripped)
        if heading_match:
            current_range = (int(heading_match.group(1)), int(heading_match.group(2)))
            bindings.setdefault(current_range, [])
            inside_upload_block = False
            continue
        if stripped == "上传参考图：":
            inside_upload_block = current_range is not None
            continue
        if inside_upload_block and (stripped.startswith("### ") or stripped == "音色绑定："):
            inside_upload_block = False
        if not inside_upload_block or current_range is None:
            continue

        binding_match = REFERENCE_BINDING_RE.match(stripped)
        if not binding_match:
            continue
        asset_name = binding_match.group(1).strip()
        path = binding_match.group(2).strip()
        bindings[current_range].append(
            StoryboardReference(
                asset_name=asset_name,
                path=path,
                purpose=purpose_from_path(path),
            )
        )

    return bindings


def parse_asset_bible_references(
    text: str,
    manifest_by_name: dict[str, dict[str, object]],
) -> list[StoryboardReference]:
    references: list[StoryboardReference] = []
    seen: set[str] = set()

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        match = ASSET_BIBLE_NAME_RE.match(stripped)
        if match is None:
            match = ASSET_BIBLE_IMAGE_HEADING_RE.match(stripped)
        if match is None:
            continue
        asset_name = match.group(1).strip()
        if not asset_name or asset_name in seen:
            continue
        asset = manifest_by_name.get(asset_name)
        if asset is None:
            continue
        path = str(asset.get("path", "")).strip()
        references.append(
            StoryboardReference(
                asset_name=asset_name,
                path=path,
                purpose=purpose_from_path(path),
            )
        )
        seen.add(asset_name)

    return references


def references_for_group(
    group: list[tuple[int, str]],
    copy_pack_refs: dict[tuple[int, int], list[StoryboardReference]],
    asset_bible_refs: list[StoryboardReference],
    manifest_by_name: dict[str, dict[str, object]],
    workspace: Path,
) -> list[StoryboardReference]:
    line_numbers = {number for number, _ in group}
    references: list[StoryboardReference] = []
    for (start, end), pack_refs in copy_pack_refs.items():
        if line_numbers.intersection(range(start, end + 1)):
            references.extend(pack_refs)

    if not references:
        references = references_from_asset_bible(group, asset_bible_refs)

    if not references:
        group_text = "\n".join(text for _, text in group)
        for asset_name, asset in manifest_by_name.items():
            if asset_name in group_text:
                path = str(asset.get("path", "")).strip()
                references.append(
                    StoryboardReference(
                        asset_name=asset_name,
                        path=path,
                        purpose=purpose_from_path(path),
                    )
                )

    deduped: list[StoryboardReference] = []
    seen: set[tuple[str, str]] = set()
    for reference in references:
        key = (reference.asset_name, reference.path)
        if key in seen:
            continue
        seen.add(key)
        validate_reference_file(reference, workspace, manifest_by_name)
        deduped.append(reference)

    if not deduped:
        start = group[0][0]
        end = group[-1][0]
        raise StoryboardGenerationError(f"lines {start}-{end}: no resolved image references")
    return deduped


def references_from_asset_bible(
    group: list[tuple[int, str]],
    asset_bible_refs: list[StoryboardReference],
) -> list[StoryboardReference]:
    group_text = "\n".join(text for _, text in group)
    references: list[StoryboardReference] = []
    for reference in asset_bible_refs:
        if any(alias and alias in group_text for alias in asset_aliases(reference.asset_name)):
            references.append(reference)
    return references


def asset_aliases(asset_name: str) -> list[str]:
    aliases: list[str] = [asset_name]
    for separator in ("_", "｜", "|"):
        if separator in asset_name:
            aliases.append(asset_name.split(separator, 1)[0])
            break
    return [alias.strip() for alias in aliases if alias.strip()]


def purpose_from_path(path: str) -> str:
    first_part = Path(path).parts[0] if Path(path).parts else ""
    if first_part == "场景资产":
        return "场景空间参考"
    if first_part == "人设资产":
        return "人物身份参考"
    return "道具界面参考"


def build_prompt(
    group: list[tuple[int, str]],
    references: list[StoryboardReference],
    instruction: str,
) -> str:
    lines = [
        "这是 post-asset visual QA 联系表，用于检查站位、人物身份、空间关系、道具连续性和尺度关系。",
        "生成图本身不要出现台词、字幕、气泡、标题、编号或任何可读文字。",
        "",
        "上传参考图：",
    ]
    for index, reference in enumerate(references, start=1):
        lines.append(
            f"- 参考图{index} = {reference.asset_name} = {reference.path}（{reference.purpose}）"
        )
    lines.extend(["", "原始视频行："])
    lines.extend(text for _, text in group)
    lines.extend(["", instruction])
    return "\n".join(lines)


def _validate_continuous_lines(numbered_lines: list[tuple[int, str]]) -> None:
    expected = 1
    for actual_number, _ in numbered_lines:
        if actual_number != expected:
            raise StoryboardGenerationError(
                f"feed numbered lines must be continuous; expected {expected}, got {actual_number}"
            )
        expected += 1


def _relative_or_name(path: Path, workspace: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(
            workspace.resolve(strict=False)
        ).as_posix()
    except ValueError:
        return path.name


def main() -> int:
    parser = argparse.ArgumentParser(description="Build storyboard contact-sheet jobs.")
    parser.add_argument("--feed", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--copy-packs")
    parser.add_argument("--asset-bible")
    parser.add_argument("--model", default="gpt-image-2")
    parser.add_argument("--size", default="16:9")
    parser.add_argument("--provider", default="openai-compatible")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    try:
        jobs = build_storyboard_jobs(
            feed_path=Path(args.feed).expanduser().resolve(),
            manifest_path=Path(args.manifest).expanduser().resolve(),
            workspace=workspace,
            copy_packs_path=Path(args.copy_packs).expanduser().resolve()
            if args.copy_packs
            else None,
            asset_bible_path=Path(args.asset_bible).expanduser().resolve()
            if args.asset_bible
            else None,
            model=args.model,
            size=args.size,
            provider=args.provider,
        )
        write_storyboard_jobs_jsonl(Path(args.out).expanduser().resolve(), jobs)
    except (OSError, StoryboardGenerationError) as error:
        print("Storyboard job build failed:")
        print(f"- {error}")
        return 1

    print(f"Wrote {len(jobs)} storyboard jobs to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
