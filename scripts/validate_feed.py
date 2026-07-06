#!/usr/bin/env python3
"""Validate lightweight source-true-guoman video feed structure."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


GLOBAL_REQUIREMENT = (
    "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】"
    "3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"
)

GROUP_PATTERNS = (
    re.compile(r"第\s*\d+\s*组"),
    re.compile(r"第\s*\d+\s*-\s*\d+\s*条"),
    re.compile(r"15\s*秒"),
)

READABLE_FORBIDDEN_TERMS = (
    "segment",
    "S01",
    "S02",
    "keyframe",
    "storyboard",
    "Storyboard",
    "首帧",
    "尾帧",
    "续接",
    "承接",
    "Canvas",
    "MP4",
)


def common_mojibake_variants(term: str) -> tuple[str, ...]:
    broken = term.encode("utf-8").decode("gbk", errors="replace")
    variants = (broken, broken.replace("\ufffd", "?"))
    return tuple(variant for variant in variants if variant != term)


FORBIDDEN_TERMS = tuple(
    dict.fromkeys(
        term
        for readable in READABLE_FORBIDDEN_TERMS
        for term in (readable, *common_mojibake_variants(readable))
    )
)

NUMBERED_LINE_RE = re.compile(r"^(\d+)\s+")
CAMERA_TAG_FILES = ("xiaoyunque-tags.md", "libtv-tags.md")


def load_camera_tags(root: Path) -> set[str]:
    tags: set[str] = set()
    for filename in CAMERA_TAG_FILES:
        tag_file = root / "references" / filename
        if not tag_file.exists():
            continue
        for line in tag_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("- "):
                tags.add(stripped[2:].strip())
    return tags


def line_camera_tags(line: str, tags: set[str]) -> list[str]:
    found_tags: list[str] = []
    for tag in sorted(tags, key=len, reverse=True):
        matches = re.findall(
            rf"(?<!\S)<{re.escape(tag)}>(?:（[^）]*）)?(?=\s|$)", line
        )
        found_tags.extend([tag] * len(matches))
    return found_tags


def unmarked_camera_tags(line: str, tags: set[str]) -> list[str]:
    line_without_marked_tags = re.sub(r"<[^>\n]+>(?:（[^）]*）)?", "", line)
    found_tags: list[str] = []
    for tag in sorted(tags, key=len, reverse=True):
        matches = re.findall(
            rf"(?<!\S){re.escape(tag)}(?:（[^）]*）)?(?=\s|$)",
            line_without_marked_tags,
        )
        found_tags.extend([tag] * len(matches))
    return found_tags


def validate_feed(path: Path, root: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tags = load_camera_tags(root)
    errors: list[str] = []

    if GLOBAL_REQUIREMENT not in text:
        errors.append("missing global requirement line")

    try:
        header_index = next(
            index for index, line in enumerate(lines) if line.strip() == "## 视频投喂块"
        )
    except StopIteration:
        errors.append("missing ## 视频投喂块 header")
    else:
        requirement_index = header_index + 1
        if (
            requirement_index >= len(lines)
            or lines[requirement_index].strip() != GLOBAL_REQUIREMENT
        ):
            errors.append(
                "global requirement line must immediately follow ## 视频投喂块"
            )

    expected_number = 1
    saw_numbered_line = False

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        if any(pattern.search(stripped) for pattern in GROUP_PATTERNS):
            errors.append(f"line {line_number}: group marker is not allowed")

        for forbidden in FORBIDDEN_TERMS:
            if forbidden in stripped:
                errors.append(f"line {line_number}: forbidden term `{forbidden}`")

        match = NUMBERED_LINE_RE.match(stripped)
        if not match:
            continue

        saw_numbered_line = True
        actual_number = int(match.group(1))
        if actual_number != expected_number:
            errors.append(
                f"line {line_number}: expected line {expected_number}, got {actual_number}"
            )
            expected_number = actual_number + 1
        else:
            expected_number += 1

        found_tags = line_camera_tags(stripped, tags)
        if len(found_tags) != 1:
            errors.append(
                f"line {line_number}: invalid camera tag count {len(found_tags)}"
            )
        unmarked_tags = unmarked_camera_tags(stripped, tags)
        if unmarked_tags:
            formatted_tags = ", ".join(dict.fromkeys(unmarked_tags))
            errors.append(
                f"line {line_number}: camera tag must be wrapped in angle brackets: {formatted_tags}"
            )

    if not saw_numbered_line:
        errors.append("no numbered video lines found")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate source-true-guoman feed files.")
    parser.add_argument("feed_file", help="Markdown or text file containing ## 视频投喂块")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    feed_path = Path(args.feed_file).expanduser().resolve()
    errors = validate_feed(feed_path, root)

    if errors:
        print("Feed validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Feed validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
