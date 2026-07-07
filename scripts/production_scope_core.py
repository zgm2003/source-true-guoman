#!/usr/bin/env python3
"""Production scope helpers for source-true-guoman."""

from __future__ import annotations

import re
from dataclasses import dataclass


SCOPE_GATE_PROMPT = (
    "生产范围缺失：检测到文本超过3章。建议先跑3章；你也可以指定 1-5 章、"
    "具体章节范围，或明确说全本分批。收到选择前，我不会生成连续投喂稿或复制包。"
)


@dataclass(frozen=True, order=True)
class ChapterRange:
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 1:
            raise ValueError("chapter range start must be at least 1")
        if self.end < self.start:
            raise ValueError("chapter range end must be greater than or equal to start")


@dataclass(frozen=True)
class ProductionScopeDecision:
    required: bool
    recommended_chapters: int
    prompt: str


def should_ask_scope_gate(
    total_chapters: int,
    explicit_output_range: ChapterRange | None,
    is_formal_production: bool,
) -> ProductionScopeDecision:
    if total_chapters < 0:
        raise ValueError("total_chapters must be zero or greater")
    required = (
        is_formal_production
        and total_chapters > 3
        and explicit_output_range is None
    )
    return ProductionScopeDecision(
        required=required,
        recommended_chapters=3,
        prompt=SCOPE_GATE_PROMPT if required else "",
    )


def parse_scope_choice(
    user_text: str,
    total_chapters: int,
    gate_was_shown: bool,
) -> ChapterRange:
    normalized = user_text.strip()
    if total_chapters < 1:
        raise ValueError("total_chapters must be at least 1")

    if gate_was_shown and normalized.casefold() in {"默认", "默認", "default"}:
        return ChapterRange(1, min(3, total_chapters))
    if "前三章" in normalized or "前3章" in normalized:
        return ChapterRange(1, min(3, total_chapters))
    if "全本分批" in normalized or "全书分批" in normalized:
        if not gate_was_shown:
            raise ValueError("full-book batching requires the production scope gate")
        return ChapterRange(1, min(3, total_chapters))
    if normalized in {"先试一章", "试一章", "先跑一章", "跑一章"}:
        return ChapterRange(1, 1)

    range_match = re.search(r"第?\s*(\d+)\s*[-~到至]\s*(\d+)\s*章", normalized)
    if range_match:
        start = int(range_match.group(1))
        end = min(int(range_match.group(2)), total_chapters)
        return ChapterRange(start, end)

    count_match = re.search(r"(?:先)?跑\s*(\d+)\s*章", normalized)
    if count_match:
        count = max(1, int(count_match.group(1)))
        return ChapterRange(1, min(count, total_chapters))

    single_match = re.search(r"第\s*(\d+)\s*章", normalized)
    if single_match:
        chapter = min(int(single_match.group(1)), total_chapters)
        return ChapterRange(chapter, chapter)

    raise ValueError("could not parse production scope choice")


def compute_forward_index_range(
    requested_output_range: ChapterRange,
    total_chapters: int,
    lookahead_chapters: int = 3,
) -> ChapterRange:
    if total_chapters < requested_output_range.start:
        raise ValueError("total_chapters must include requested range start")
    if lookahead_chapters < 0:
        raise ValueError("lookahead_chapters must be zero or greater")
    return ChapterRange(
        requested_output_range.start,
        min(total_chapters, requested_output_range.end + lookahead_chapters),
    )


def compute_required_cumulative_index_range(
    existing_index_range: ChapterRange | None,
    forward_index_range: ChapterRange,
) -> ChapterRange:
    if existing_index_range is None:
        return forward_index_range
    return ChapterRange(
        min(existing_index_range.start, forward_index_range.start),
        max(existing_index_range.end, forward_index_range.end),
    )
