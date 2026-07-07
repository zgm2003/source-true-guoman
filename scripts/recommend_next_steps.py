#!/usr/bin/env python3
"""Stage-aware next-step recommendations for source-true-guoman workspaces."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATUS_LABELS = {
    "mother_feed": {
        "passed": "已通过",
        "missing": "未生成",
        "needs_fix": "需修正",
    },
    "copy_packs": {
        "passed": "已通过",
        "missing": "未生成",
        "needs_regeneration": "需重生",
    },
    "images": {
        "missing": "未生成",
        "style_preview_done": "风格待确认",
        "failed": "部分失败",
        "blocked": "部分失败",
        "done": "已完成",
        "deprecated": "需迁移",
        "renamed": "需复核",
    },
    "storyboard": {
        "not_started": "未开始",
        "done": "已完成",
        "needs_fix": "需修正",
    },
    "reconciliation": {
        "none": "无待处理",
        "pending": "有待处理",
        "needs_user_confirmation": "需用户确认",
    },
}


@dataclass(frozen=True)
class RecommendationState:
    mother_feed: str
    copy_packs: str
    images: str
    storyboard: str
    reconciliation: str
    recent_user_intent: str = ""


@dataclass(frozen=True)
class RecommendationOption:
    action: str
    reason: str
    command: str = ""


@dataclass(frozen=True)
class BlockedAction:
    action: str
    reason: str


@dataclass(frozen=True)
class Recommendation:
    options: list[RecommendationOption]
    blocked: list[BlockedAction]


def recommend_next_steps(state: RecommendationState) -> Recommendation:
    if state.reconciliation in {"pending", "needs_user_confirmation"}:
        return Recommendation(
            options=[
                RecommendationOption(
                    "处理索引回填",
                    "新章节证据改变了旧角色/资产判断，先修正索引、母稿、复制包和 manifest。",
                    "validate-reconciliation",
                ),
                RecommendationOption(
                    "暂停并人工确认疑似身份",
                    "存在不能自动合并的疑似同一角色或旧图沿用判断。",
                ),
                RecommendationOption(
                    "查看 reconciliation-log",
                    "先看证据锚点和受影响文件，再决定 rename/deprecated/regenerate。",
                ),
            ],
            blocked=[
                BlockedAction("继续下一批章节", "索引回填未处理前继续生产会沿用错误身份。")
            ],
        )

    if state.images == "style_preview_done":
        return Recommendation(
            options=[
                RecommendationOption(
                    "确认风格基准",
                    "请先看第一个人设和第一个场景；未确认前不跑全量依赖资产。",
                    "image-generator",
                ),
                RecommendationOption("调整人设风格", "如果人设基准不对，先改提示词再重跑预览。"),
                RecommendationOption("调整场景风格", "如果场景基准不对，先改提示词再重跑预览。"),
            ],
            blocked=[
                BlockedAction("全量生图", "风格基准未确认。"),
                BlockedAction("分镜 QA", "真实图片资产还没有全量生成。"),
            ],
        )

    if state.images in {"failed", "blocked"}:
        return Recommendation(
            options=[
                RecommendationOption(
                    "续跑/修复失败图片",
                    "分镜 QA 需要真实图片引用；当前仍有 failed 或 blocked 图片资产。",
                    "image-generator --resume",
                ),
                RecommendationOption("查看失败报告", "先定位失败资产、依赖资产或供应商错误。"),
                RecommendationOption("人工标记跳过并继续文本流程", "只适合确认该资产暂时不影响当前交付时使用。"),
            ],
            blocked=[BlockedAction("分镜 QA", "暂不建议分镜 QA：图片资产还没有全部生成并验证。")],
        )

    if state.images in {"renamed", "deprecated"}:
        return Recommendation(
            options=[
                RecommendationOption(
                    "核对资产迁移",
                    "image-manifest 存在 renamed/deprecated 迁移记录，先确认旧名、canonical 名、证据锚点和受影响产物都已闭环。",
                    "validate-reconciliation",
                ),
                RecommendationOption(
                    "查看 reconciliation-log",
                    "先看证据锚点和受影响文件，再决定是否继续 rename/deprecated/regenerate。",
                ),
                RecommendationOption(
                    "重跑复制包绑定",
                    "迁移确认后，让复制包绑定 canonical 图片路径，避免继续引用旧资产名。",
                    "copy-packager",
                ),
            ],
            blocked=[BlockedAction("分镜 QA", "资产迁移复核前，分镜 QA 可能继续引用旧图或旧名。")],
        )

    if (
        state.mother_feed == "passed"
        and state.copy_packs == "passed"
        and state.images == "missing"
    ):
        return Recommendation(
            options=[
                RecommendationOption(
                    "自动化生图",
                    "当前已有母稿、asset-bible 和复制包，但还没有本地图片资产。",
                    "image-generator",
                ),
                RecommendationOption("安全剪辑", "如有时长或删减压力，可先做删减风险报告。", "cut-safety"),
                RecommendationOption("视频增强", "如需加强镜头表现，先改母稿、再审计、再重生复制包。", "visual-polish"),
            ],
            blocked=[BlockedAction("分镜 QA", "图片资产未生成。")],
        )

    if state.mother_feed == "passed" and state.images == "done" and state.storyboard == "not_started":
        return Recommendation(
            options=[
                RecommendationOption(
                    "分镜/站位 QA",
                    "图片资产已经齐了，下一步检查角色、场景、道具在真实镜头里的站位和连续性。",
                    "storyboard-contact-sheet",
                ),
                RecommendationOption("复制包绑定图片路径", "如果复制包还没有绑定 manifest，可先补绑定。", "copy-packager"),
                RecommendationOption("继续下一批章节", "当前批次文本和图片都通过后可进入下一批。"),
            ],
            blocked=[],
        )

    if state.storyboard == "needs_fix":
        return Recommendation(
            options=[
                RecommendationOption(
                    "视频增强或资产修正",
                    "分镜 QA 已暴露具体画面问题，先修正母稿镜头或资产绑定，再审计并重生复制包。",
                    "visual-polish",
                ),
                RecommendationOption("重跑分镜 QA", "修正后再生成 contact sheet 验证站位和连续性。", "storyboard-contact-sheet"),
                RecommendationOption("处理索引回填", "如果问题来自身份误判，先回填 source-index 和 asset-bible。", "validate-reconciliation"),
            ],
            blocked=[],
        )

    if _mentions_cut_pressure(state.recent_user_intent):
        return Recommendation(
            options=[
                RecommendationOption(
                    "安全剪辑",
                    "你提到时长/删减/平台压力，先按连续行号和原文跨度给删减风险。",
                    "cut-safety",
                ),
                RecommendationOption("视频增强", "如果不是删减问题，可增强镜头表现但不能改写剧情。", "visual-polish"),
                RecommendationOption("继续下一批章节", "当前批次闭环后再进入下一批。"),
            ],
            blocked=[],
        )

    if (
        state.mother_feed == "passed"
        and state.copy_packs == "passed"
        and state.images == "done"
        and state.storyboard == "done"
    ):
        return Recommendation(
            options=[
                RecommendationOption(
                    "继续下一批章节",
                    "当前批次文本、图片、分镜 QA 都已闭环，可以进入下一批并执行累积索引回填。",
                ),
                RecommendationOption("安全剪辑", "如果要控时长，先做删减风险报告。", "cut-safety"),
                RecommendationOption("视频增强", "如果要加强画面表现，先改母稿、再审计、再重生复制包。", "visual-polish"),
            ],
            blocked=[],
        )

    return Recommendation(
        options=[
            RecommendationOption(
                "补齐正式生产链路",
                "先完成 source-index、asset-bible、faithful-feed、feed-auditor、copy-packager。",
            ),
            RecommendationOption("自动化生图", "母稿和 asset-bible 通过后再运行。", "image-generator"),
            RecommendationOption("处理索引回填", "如果后续证据改变旧角色判断，先回填再继续。", "validate-reconciliation"),
        ],
        blocked=[],
    )


def recommendation_block(state: RecommendationState, recommendation: Recommendation) -> str:
    lines = [
        "## 状态摘要",
        f"- 母稿：{_label('mother_feed', state.mother_feed)}",
        f"- 复制包：{_label('copy_packs', state.copy_packs)}",
        f"- 图片资产：{_label('images', state.images)}",
        f"- 分镜QA：{_label('storyboard', state.storyboard)}",
        f"- 索引回填：{_label('reconciliation', state.reconciliation)}",
        "",
        "下一步建议（3选1）：",
    ]
    for index, option in enumerate(_three_options(recommendation.options), start=1):
        command = f" - run `{option.command}`" if option.command else ""
        lines.append(f"{index}. {option.action}{command}：{option.reason}")
    for blocked in recommendation.blocked:
        lines.append(f"暂不建议{blocked.action}：{blocked.reason}")
    return "\n".join(lines)


def inspect_workspace(workspace: Path, recent_user_intent: str = "") -> RecommendationState:
    workspace = Path(workspace)
    production_dir = workspace / "生产资产"
    internal_dir = production_dir / "_内部"
    manifest_path = internal_dir / "image-manifest.json"
    reconciliation_log = internal_dir / "reconciliation-log.md"

    return RecommendationState(
        mother_feed="passed" if _has_file(production_dir, ("feed", "母稿", "投喂")) else "missing",
        copy_packs="passed" if _has_file(production_dir, ("copy", "复制包", "投喂包")) else "missing",
        images=_image_state(manifest_path, internal_dir),
        storyboard=_storyboard_state(internal_dir / "storyboard-manifest.json"),
        reconciliation=_reconciliation_state(reconciliation_log),
        recent_user_intent=recent_user_intent,
    )


def _has_file(directory: Path, markers: tuple[str, ...]) -> bool:
    if not directory.is_dir():
        return False
    for path in directory.glob("*.md"):
        lowered = path.name.casefold()
        if any(marker.casefold() in lowered for marker in markers):
            return True
    return False


def _image_state(manifest_path: Path, internal_dir: Path) -> str:
    preview_jobs = internal_dir / "image-jobs-style-preview.jsonl"
    if not manifest_path.is_file():
        return "style_preview_done" if preview_jobs.is_file() else "missing"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "failed"
    assets = manifest.get("assets", [])
    if not isinstance(assets, list) or not assets:
        return "missing"
    statuses = {
        str(asset.get("status", "")).strip()
        for asset in assets
        if isinstance(asset, dict)
    }
    for status in ("failed", "blocked", "deprecated", "renamed"):
        if status in statuses:
            return status
    if statuses == {"done"}:
        return "done"
    return "missing"


def _storyboard_state(manifest_path: Path) -> str:
    if not manifest_path.is_file():
        return "not_started"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "needs_fix"
    if not isinstance(manifest, dict):
        return "needs_fix"
    status = str(manifest.get("status", "")).strip()
    if status in {"not_started", "done", "needs_fix"}:
        return status
    if manifest.get("issues") or manifest.get("failed_panels"):
        return "needs_fix"
    return "done"


def _reconciliation_state(log_path: Path) -> str:
    if not log_path.is_file():
        return "none"
    try:
        text = log_path.read_text(encoding="utf-8")
    except OSError:
        return "pending"
    if "Reconciliation status: pending" in text or "Upgrade status: confirmed" in text:
        return "pending"
    if "needs user confirmation" in text:
        return "needs_user_confirmation"
    return "none"


def _mentions_cut_pressure(text: str) -> bool:
    return any(
        marker in text
        for marker in ("时长", "删减", "剪短", "节奏", "平台", "投放", "太长", "压缩")
    )


def _three_options(options: list[RecommendationOption]) -> list[RecommendationOption]:
    padded = list(options)
    while len(padded) < 3:
        padded.append(RecommendationOption("继续当前生产链路", "先补齐缺失产物再进入下一阶段。"))
    return padded[:3]


def _label(group: str, value: str) -> str:
    return STATUS_LABELS.get(group, {}).get(value, value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Recommend next source-true-guoman production steps.")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--recent-user-intent", default="")
    args = parser.parse_args()

    state = inspect_workspace(Path(args.workspace), recent_user_intent=args.recent_user_intent)
    print(recommendation_block(state, recommend_next_steps(state)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
