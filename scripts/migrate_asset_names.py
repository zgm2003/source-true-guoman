#!/usr/bin/env python3
"""Explicit asset-name migration helper for confirmed reconciliation cases."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def migrate_asset_name(
    manifest: dict[str, Any],
    workspace: Path,
    old_name: str,
    new_name: str,
    asset_dir: str,
    mode: str,
    migration_reason: str,
    evidence_anchor: str,
    apply: bool = False,
) -> dict[str, Any]:
    if mode not in {"rename", "deprecated"}:
        raise ValueError("mode must be rename or deprecated")
    if not old_name or not new_name:
        raise ValueError("old_name and new_name are required")
    _validate_asset_name(old_name)
    _validate_asset_name(new_name)
    if not migration_reason:
        raise ValueError("migration_reason is required")
    if not evidence_anchor:
        raise ValueError("evidence_anchor is required")

    workspace = Path(workspace)
    old_path = workspace / asset_dir / f"{old_name}.png"
    new_path = workspace / asset_dir / f"{new_name}.png"
    updated = deepcopy(manifest)
    assets = updated.setdefault("assets", [])
    if not isinstance(assets, list):
        raise ValueError("manifest assets must be a list")
    asset_type = _asset_type_for(assets, old_name, asset_dir)

    if mode == "rename":
        if apply:
            if new_path.exists():
                raise ValueError("target asset file already exists")
            if not old_path.exists():
                raise ValueError("source asset file missing")
            new_path.parent.mkdir(parents=True, exist_ok=True)
            old_path.rename(new_path)
        _mark_old_asset(
            assets,
            old_name,
            new_name,
            migration_reason,
            evidence_anchor,
            status="renamed",
            asset_type=asset_type,
        )
        _upsert_new_asset(
            assets,
            old_name=old_name,
            new_name=new_name,
            asset_dir=asset_dir,
            asset_type=asset_type,
            status="renamed",
            migration_reason=migration_reason,
            evidence_anchor=evidence_anchor,
        )
        return updated

    _mark_old_asset(
        assets,
        old_name,
        new_name,
        migration_reason,
        evidence_anchor,
        status="deprecated",
        asset_type=asset_type,
    )
    return updated


def _mark_old_asset(
    assets: list[Any],
    old_name: str,
    new_name: str,
    migration_reason: str,
    evidence_anchor: str,
    status: str,
    asset_type: str,
) -> None:
    asset = _find_asset(assets, old_name)
    if asset is None:
        asset = {"asset_name": old_name, "asset_type": asset_type}
        assets.append(asset)
    elif not str(asset.get("asset_type", "")).strip():
        asset["asset_type"] = asset_type
    asset["status"] = status
    asset["replaced_by"] = new_name
    asset["migration_reason"] = migration_reason
    asset["evidence_anchor"] = evidence_anchor


def _upsert_new_asset(
    assets: list[Any],
    old_name: str,
    new_name: str,
    asset_dir: str,
    asset_type: str,
    status: str,
    migration_reason: str,
    evidence_anchor: str,
) -> None:
    asset = _find_asset(assets, new_name)
    if asset is None:
        asset = {"asset_name": new_name, "asset_type": asset_type}
        assets.append(asset)
    elif not str(asset.get("asset_type", "")).strip():
        asset["asset_type"] = asset_type
    asset["status"] = status
    asset["path"] = f"{asset_dir}/{new_name}.png"
    asset["previous_asset_name"] = old_name
    aliases = asset.get("aliases", [])
    if not isinstance(aliases, list):
        aliases = []
    asset["aliases"] = sorted({*[str(alias) for alias in aliases], old_name})
    asset["migration_reason"] = migration_reason
    asset["evidence_anchor"] = evidence_anchor


def _find_asset(assets: list[Any], asset_name: str) -> dict[str, Any] | None:
    for asset in assets:
        if isinstance(asset, dict) and asset.get("asset_name") == asset_name:
            return asset
    return None


def _validate_asset_name(asset_name: str) -> None:
    if (
        "/" in asset_name
        or "\\" in asset_name
        or ".." in asset_name
        or Path(asset_name).is_absolute()
        or (len(asset_name) >= 2 and asset_name[1] == ":")
    ):
        raise ValueError("asset names must be file-safe names")


def _asset_type_for(assets: list[Any], old_name: str, asset_dir: str) -> str:
    existing = _find_asset(assets, old_name)
    if existing is not None:
        asset_type = str(existing.get("asset_type", "")).strip()
        if asset_type:
            return asset_type
    return {
        "人设资产": "character",
        "场景资产": "scene",
        "道具资产": "prop",
    }.get(asset_dir, "asset")


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate a confirmed asset name in image-manifest.json.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--old-name", required=True)
    parser.add_argument("--new-name", required=True)
    parser.add_argument("--asset-dir", required=True, choices=("人设资产", "场景资产", "道具资产"))
    parser.add_argument("--mode", required=True, choices=("rename", "deprecated"))
    parser.add_argument("--migration-reason", required=True)
    parser.add_argument("--evidence-anchor", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be a JSON object")
        updated = migrate_asset_name(
            manifest=manifest,
            workspace=Path(args.workspace).expanduser().resolve(),
            old_name=args.old_name,
            new_name=args.new_name,
            asset_dir=args.asset_dir,
            mode=args.mode,
            migration_reason=args.migration_reason,
            evidence_anchor=args.evidence_anchor,
            apply=args.apply,
        )
        if args.apply:
            manifest_path.write_text(
                json.dumps(updated, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Asset migration failed: {error}")
        return 1

    print(json.dumps(updated, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
