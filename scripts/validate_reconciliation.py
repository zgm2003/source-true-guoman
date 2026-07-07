#!/usr/bin/env python3
"""Validate source-index reconciliation against downstream artifacts."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReconciliationUpgrade:
    canonical_name: str
    former_names: list[str]
    status: str
    migration_action: str
    evidence_anchors: str
    affected_artifacts: str
    reconciliation_log: str


@dataclass(frozen=True)
class ReconciliationInputs:
    source_index_text: str
    asset_bible_text: str
    mother_feed_text: str
    copy_pack_text: str
    image_manifest: dict[str, Any]
    reconciliation_log_text: str = ""
    prior_feed_texts: tuple[str, ...] = ()


@dataclass(frozen=True)
class AssetPrompt:
    label: str
    asset_name: str
    block_text: str


def extract_reconciliation_upgrades(source_index_text: str) -> list[ReconciliationUpgrade]:
    upgrades: list[ReconciliationUpgrade] = []
    current: dict[str, str] | None = None

    for raw_line in source_index_text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            if current is not None:
                upgrades.append(_upgrade_from_fields(current))
                current = None
            continue
        if stripped.startswith("- Canonical name:") or stripped.startswith("- Name:"):
            if current is not None:
                upgrades.append(_upgrade_from_fields(current))
            key, _, value = stripped[2:].partition(":")
            normalized_key = key.strip().casefold().replace(" ", "_")
            current = {normalized_key: value.strip()}
            continue
        if current is None or not stripped.startswith("- "):
            continue
        key, separator, value = stripped[2:].partition(":")
        if not separator:
            continue
        normalized_key = key.strip().casefold().replace(" ", "_").replace("-", "_")
        current[normalized_key] = value.strip()

    if current is not None:
        upgrades.append(_upgrade_from_fields(current))
    return [upgrade for upgrade in upgrades if upgrade.canonical_name]


def validate_reconciliation(inputs: ReconciliationInputs) -> list[str]:
    errors: list[str] = []
    upgrades = extract_reconciliation_upgrades(inputs.source_index_text)
    manifest_assets = _manifest_assets_by_name(inputs.image_manifest)
    errors.extend(_validate_prior_asset_reuse(inputs.prior_feed_texts, inputs.mother_feed_text))

    for upgrade in upgrades:
        if upgrade.status != "confirmed":
            continue
        label = upgrade.canonical_name
        if not upgrade.evidence_anchors:
            errors.append(f"{label}: confirmed upgrade requires evidence anchors")
        if not upgrade.affected_artifacts:
            errors.append(f"{label}: confirmed upgrade requires affected artifacts")
        if upgrade.migration_action not in {"rename", "deprecated", "regenerate"}:
            errors.append(
                f"{label}: confirmed upgrade requires rename, deprecated, or regenerate migration action"
            )
        reconciliation_log = "\n".join(
            part for part in (inputs.reconciliation_log_text, upgrade.reconciliation_log) if part
        )
        if not _log_contains_upgrade(reconciliation_log, upgrade):
            errors.append(f"{label}: reconciliation-log missing canonical upgrade entry")
        if label not in inputs.asset_bible_text:
            errors.append(f"{label}: asset-bible missing canonical asset name")
        asset_bible_block = _asset_bible_block(inputs.asset_bible_text, label)
        if "Migration action:" not in asset_bible_block:
            errors.append(f"{label}: asset-bible missing Migration action")
        if "Source-index evidence:" not in asset_bible_block:
            errors.append(f"{label}: asset-bible missing Source-index evidence")

        for former_name in upgrade.former_names:
            if former_name and former_name in inputs.mother_feed_text:
                errors.append(f"{label}: mother feed still contains former name {former_name}")
            if former_name and former_name in inputs.copy_pack_text:
                errors.append(f"{label}: copy packs still contain former name {former_name}")
            for prior_feed_text in inputs.prior_feed_texts:
                if former_name and former_name in prior_feed_text:
                    errors.append(f"{label}: prior feed still contains former name {former_name}")
            former_asset = manifest_assets.get(former_name)
            if former_asset is not None:
                status = str(former_asset.get("status", "")).strip()
                replaced_by = str(former_asset.get("replaced_by", "")).strip()
                if status not in {"renamed", "deprecated"} or replaced_by != label:
                    errors.append(
                        f"{label}: manifest former asset must be renamed or deprecated with replaced_by {label}"
                    )

    return errors


def _upgrade_from_fields(fields: dict[str, str]) -> ReconciliationUpgrade:
    return ReconciliationUpgrade(
        canonical_name=(
            fields.get("canonical_name", "")
            or fields.get("canonical_asset_name", "")
            or fields.get("name", "")
        ).strip(),
        former_names=_split_names(fields.get("former_temporary_names", "")),
        status=fields.get("upgrade_status", "none").strip(),
        migration_action=(
            fields.get("migration_action", "") or fields.get("asset_migration_status", "none")
        ).strip(),
        evidence_anchors=fields.get("evidence_anchors", "").strip(),
        affected_artifacts=(
            fields.get("affected_prior_artifacts", "") or fields.get("affected_artifacts", "")
        ).strip(),
        reconciliation_log=fields.get("reconciliation_log", "").strip(),
    )


def _split_names(value: str) -> list[str]:
    names: list[str] = []
    for item in value.replace("，", ",").replace("、", ",").split(","):
        stripped = item.strip()
        if stripped:
            names.append(stripped)
    return names


def _log_contains_upgrade(log_text: str, upgrade: ReconciliationUpgrade) -> bool:
    if not log_text.strip() or upgrade.canonical_name not in log_text:
        return False
    evidence_tokens = _split_names(upgrade.evidence_anchors)
    has_evidence = any(token and token in log_text for token in evidence_tokens)
    has_former_name = any(
        former_name and former_name in log_text for former_name in upgrade.former_names
    )
    return has_evidence or has_former_name


def _manifest_assets_by_name(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        asset_name = str(asset.get("asset_name", "")).strip()
        if asset_name:
            result[asset_name] = asset
    return result


def _asset_bible_block(asset_bible_text: str, canonical_name: str) -> str:
    start = asset_bible_text.find(canonical_name)
    if start < 0:
        return ""
    next_markers = [
        index
        for marker in ("\n### ", "\n## ")
        if (index := asset_bible_text.find(marker, start + len(canonical_name))) >= 0
    ]
    end = min(next_markers) if next_markers else len(asset_bible_text)
    return asset_bible_text[start:end]


def _validate_prior_asset_reuse(prior_feed_texts: tuple[str, ...], mother_feed_text: str) -> list[str]:
    prior_assets: dict[str, AssetPrompt] = {}
    for prior_feed_text in prior_feed_texts:
        for prompt in _extract_asset_prompts(prior_feed_text):
            prior_assets.setdefault(prompt.asset_name, prompt)
    if not prior_assets:
        return []

    errors: list[str] = []
    for prompt in _extract_asset_prompts(mother_feed_text):
        if prompt.asset_name in prior_assets and _is_full_asset_prompt(prompt):
            errors.append(
                f"{prompt.asset_name}: current batch re-emits full prompt for prior asset "
                f"{prompt.asset_name}; use 沿用第XX-XX章 图片N = {prompt.asset_name} or bind the "
                "existing manifest path instead"
            )
    return errors


def _extract_asset_prompts(feed_text: str) -> list[AssetPrompt]:
    section = _asset_prompt_section(feed_text)
    if not section:
        return []
    matches = list(re.finditer(r"^### 图片\d+\s*=\s*(.+?)\s*$", section, flags=re.MULTILINE))
    prompts: list[AssetPrompt] = []
    for index, match in enumerate(matches):
        block_start = match.start()
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        label = match.group(1).strip()
        prompts.append(
            AssetPrompt(
                label=label,
                asset_name=_asset_name_from_label(label),
                block_text=section[block_start:block_end].strip(),
            )
        )
    return prompts


def _asset_prompt_section(feed_text: str) -> str:
    start_marker = "## 资产提示词"
    start = feed_text.find(start_marker)
    if start < 0:
        return ""
    end = feed_text.find("\n## 视频投喂块", start + len(start_marker))
    return feed_text[start:end if end >= 0 else len(feed_text)]


def _asset_name_from_label(label: str) -> str:
    if "沿用" in label and "=" in label:
        return label.rsplit("=", 1)[1].strip()
    return label.strip()


def _is_full_asset_prompt(prompt: AssetPrompt) -> bool:
    body = "\n".join(prompt.block_text.splitlines()[1:]).strip()
    if not body:
        return False
    return "GPT-image" in body or "4K画质" in body or "三视图生成模板" in body


def _read_text(path_text: str) -> str:
    return Path(path_text).expanduser().resolve().read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate source-true-guoman reconciliation state.")
    parser.add_argument("--source-index", required=True)
    parser.add_argument("--asset-bible", required=True)
    parser.add_argument("--mother-feed", required=True)
    parser.add_argument("--copy-packs", required=True)
    parser.add_argument("--image-manifest", required=True)
    parser.add_argument("--reconciliation-log")
    parser.add_argument(
        "--prior-feed",
        action="append",
        default=[],
        help="Prior canonical feed to validate cross-batch asset reuse; may be passed more than once.",
    )
    args = parser.parse_args()

    try:
        manifest = json.loads(_read_text(args.image_manifest))
        if not isinstance(manifest, dict):
            raise ValueError("image manifest must be a JSON object")
        inputs = ReconciliationInputs(
            source_index_text=_read_text(args.source_index),
            asset_bible_text=_read_text(args.asset_bible),
            mother_feed_text=_read_text(args.mother_feed),
            copy_pack_text=_read_text(args.copy_packs),
            image_manifest=manifest,
            reconciliation_log_text=_read_text(args.reconciliation_log)
            if args.reconciliation_log
            else "",
            prior_feed_texts=tuple(_read_text(path) for path in args.prior_feed),
        )
        errors = validate_reconciliation(inputs)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        errors = [str(error)]

    if errors:
        print("Reconciliation validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Reconciliation validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
