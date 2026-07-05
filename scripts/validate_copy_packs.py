#!/usr/bin/env python3
"""Validate source-true-guoman copy-pack wrapper files."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

try:
    from scripts.validate_feed import (
        FORBIDDEN_TERMS,
        GLOBAL_REQUIREMENT,
        GROUP_PATTERNS,
        NUMBERED_LINE_RE,
        line_camera_tags,
        load_camera_tags,
    )
except ModuleNotFoundError:
    from validate_feed import (
        FORBIDDEN_TERMS,
        GLOBAL_REQUIREMENT,
        GROUP_PATTERNS,
        NUMBERED_LINE_RE,
        line_camera_tags,
        load_camera_tags,
    )


HEADING_RE = re.compile(r"^### 投喂包 (\d{3})｜原始行 (\d+)-(\d+)$")
HEADING_PREFIX_RE = re.compile(r"^###\s*投喂包")
VOICE_UPLOAD_TERMS = ("音色", "配音", "声音")
VOICE_UPLOAD_LOWER_TERMS = ("voice", "audio", ".mp3", ".wav", ".m4a", ".flac")


@dataclass
class CopyPack:
    line_number: int
    index: int
    start: int
    end: int
    lines: list[tuple[int, str]]


def split_packs(lines: list[str], errors: list[str]) -> list[CopyPack]:
    packs: list[CopyPack] = []
    current_pack: CopyPack | None = None

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        heading_match = HEADING_RE.match(stripped)
        if heading_match:
            if current_pack is not None:
                packs.append(current_pack)
            current_pack = CopyPack(
                line_number=line_number,
                index=int(heading_match.group(1)),
                start=int(heading_match.group(2)),
                end=int(heading_match.group(3)),
                lines=[],
            )
            continue

        if HEADING_PREFIX_RE.match(stripped):
            errors.append(f"line {line_number}: invalid copy-pack heading")

        if current_pack is not None:
            current_pack.lines.append((line_number, line))
        elif NUMBERED_LINE_RE.match(stripped):
            errors.append(f"line {line_number}: numbered line outside copy pack")

    if current_pack is not None:
        packs.append(current_pack)

    return packs


def numbered_lines(pack: CopyPack) -> list[tuple[int, int, str]]:
    lines: list[tuple[int, int, str]] = []
    for line_number, line in pack.lines:
        stripped = line.strip()
        match = NUMBERED_LINE_RE.match(stripped)
        if match:
            lines.append((line_number, int(match.group(1)), stripped))
    return lines


def format_numbers(numbers: list[int]) -> str:
    if not numbers:
        return "none"
    return ",".join(str(number) for number in numbers)


def check_forbidden_terms(lines: list[str], errors: list[str]) -> None:
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        if any(pattern.search(stripped) for pattern in GROUP_PATTERNS):
            errors.append(f"line {line_number}: group marker is not allowed")

        for forbidden in FORBIDDEN_TERMS:
            if forbidden in stripped:
                errors.append(f"line {line_number}: forbidden term `{forbidden}`")


def check_upload_blocks(lines: list[str], errors: list[str]) -> None:
    inside_upload_block = False

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped == "上传参考图：":
            inside_upload_block = True
            continue

        if inside_upload_block and (
            stripped == "音色绑定："
            or stripped.startswith("##")
            or NUMBERED_LINE_RE.match(stripped)
        ):
            inside_upload_block = False

        lowered = stripped.casefold()
        if inside_upload_block and (
            any(term in stripped for term in VOICE_UPLOAD_TERMS)
            or any(term in lowered for term in VOICE_UPLOAD_LOWER_TERMS)
        ):
            errors.append(f"line {line_number}: voice binding belongs under 音色绑定")


def check_pack_indexes(packs: list[CopyPack], errors: list[str]) -> None:
    for expected_index, pack in enumerate(packs, start=1):
        if pack.index != expected_index:
            errors.append(
                f"line {pack.line_number}: expected pack index {expected_index:03d}, got {pack.index:03d}"
            )


def check_pack_content(
    packs: list[CopyPack], pack_size: int, tags: set[str], errors: list[str]
) -> list[tuple[int, int, str]]:
    all_numbered_lines: list[tuple[int, int, str]] = []

    for pack_position, pack in enumerate(packs):
        if not any(line.strip() == GLOBAL_REQUIREMENT for _, line in pack.lines):
            errors.append(f"pack {pack.index:03d} missing global requirement line")

        if pack.start > pack.end:
            errors.append(f"line {pack.line_number}: invalid copy-pack heading range")

        copied_lines = numbered_lines(pack)
        all_numbered_lines.extend(copied_lines)
        actual_numbers = [number for _, number, _ in copied_lines]
        expected_numbers = list(range(pack.start, pack.end + 1))

        if actual_numbers != expected_numbers:
            errors.append(
                f"pack {pack.index:03d} heading range {pack.start}-{pack.end} "
                f"does not match numbered lines {format_numbers(actual_numbers)}"
            )

        for missing_number in expected_numbers:
            if missing_number not in actual_numbers:
                errors.append(f"pack {pack.index:03d} missing original line {missing_number}")

        for line_number, number, text in copied_lines:
            found_tags = line_camera_tags(text, tags)
            if len(found_tags) != 1:
                errors.append(
                    f"line {line_number}: invalid camera tag count {len(found_tags)}"
                )

        is_final_pack = pack_position == len(packs) - 1
        if not is_final_pack and len(copied_lines) != pack_size:
            errors.append(
                f"pack {pack.index:03d} must contain exactly {pack_size} numbered lines"
            )
        if is_final_pack and len(copied_lines) > pack_size:
            errors.append(
                f"pack {pack.index:03d} final pack exceeds pack size {pack_size}"
            )

    return all_numbered_lines


def check_continuous_numbers(
    copied_lines: list[tuple[int, int, str]], errors: list[str]
) -> None:
    expected_number = 1
    seen_numbers: set[int] = set()

    for line_number, actual_number, _ in copied_lines:
        if actual_number in seen_numbers:
            errors.append(f"line {line_number}: duplicate original line {actual_number}")

        if actual_number != expected_number:
            errors.append(
                f"line {line_number}: expected original line {expected_number}, got {actual_number}"
            )
            if actual_number > expected_number:
                for missing_number in range(expected_number, actual_number):
                    errors.append(f"missing original line {missing_number}")
                expected_number = actual_number + 1
        else:
            expected_number += 1

        seen_numbers.add(actual_number)


def load_source_feed_numbered_lines(path: Path) -> dict[int, str]:
    source_lines: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        match = NUMBERED_LINE_RE.match(stripped)
        if match:
            source_lines[int(match.group(1))] = stripped
    return source_lines


def check_source_feed(
    copied_lines: list[tuple[int, int, str]],
    source_feed: Path,
    errors: list[str],
) -> None:
    source_lines = load_source_feed_numbered_lines(source_feed)
    source_numbers = sorted(source_lines)
    copied_numbers = [original_number for _, original_number, _ in copied_lines]
    if source_numbers != copied_numbers:
        errors.append(
            "copied line numbers do not match source feed; "
            f"source {format_numbers(source_numbers)}; copied {format_numbers(copied_numbers)}"
        )

    for line_number, original_number, text in copied_lines:
        source_text = source_lines.get(original_number)
        if source_text is None:
            errors.append(
                f"line {line_number}: source feed missing original line {original_number}"
            )
        elif source_text != text:
            errors.append(
                f"line {line_number}: copied line {original_number} differs from source feed"
            )


def validate_copy_packs(
    path: Path, root: Path, pack_size: int, source_feed: Path | None = None
) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tags = load_camera_tags(root)
    errors: list[str] = []

    check_forbidden_terms(lines, errors)
    check_upload_blocks(lines, errors)

    packs = split_packs(lines, errors)
    if not packs:
        errors.append("no copy-pack headings found")
        return errors

    check_pack_indexes(packs, errors)
    copied_lines = check_pack_content(packs, pack_size, tags, errors)
    check_continuous_numbers(copied_lines, errors)

    if source_feed is not None:
        check_source_feed(copied_lines, source_feed, errors)

    return errors


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("pack size must be a positive integer") from error

    if number <= 0:
        raise argparse.ArgumentTypeError("pack size must be a positive integer")
    return number


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate source-true-guoman copy-pack files."
    )
    parser.add_argument("copy_pack_file", help="Markdown file containing copy packs")
    parser.add_argument("--source-feed", help="Optional source feed to compare against")
    parser.add_argument("--pack-size", type=positive_int, default=5)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    copy_pack_path = Path(args.copy_pack_file).expanduser().resolve()
    source_feed_path = (
        Path(args.source_feed).expanduser().resolve() if args.source_feed else None
    )
    errors = validate_copy_packs(
        copy_pack_path,
        root=root,
        pack_size=args.pack_size,
        source_feed=source_feed_path,
    )

    if errors:
        print("Copy-pack validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Copy-pack validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
