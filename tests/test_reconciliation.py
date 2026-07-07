import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.image_generation_core import ImageJob, validate_manifest
from scripts.migrate_asset_names import migrate_asset_name
from scripts.validate_reconciliation import (
    ReconciliationInputs,
    extract_reconciliation_upgrades,
    validate_reconciliation,
)


SOURCE_INDEX_WITH_CONFIRMED_UPGRADE = """
# Source Index

## Reconciliation Ledger
- Canonical name: 沈砚_青云宗内门弟子造型
  - Former temporary names: 黑衣弟子_一次性造型
  - Upgrade status: confirmed
  - Migration action: rename
  - Evidence anchors: ch06-line12
  - Affected prior artifacts: 生产资产/feed.md, 生产资产/copy-packs.md, 人设资产/黑衣弟子_一次性造型.png
"""


class ReconciliationValidationTests(unittest.TestCase):
    def test_extract_confirmed_upgrade_from_source_index(self) -> None:
        upgrades = extract_reconciliation_upgrades(SOURCE_INDEX_WITH_CONFIRMED_UPGRADE)

        self.assertEqual(len(upgrades), 1)
        self.assertEqual(upgrades[0].canonical_name, "沈砚_青云宗内门弟子造型")
        self.assertEqual(upgrades[0].former_names, ["黑衣弟子_一次性造型"])
        self.assertEqual(upgrades[0].status, "confirmed")
        self.assertEqual(upgrades[0].migration_action, "rename")
        self.assertIn("feed.md", upgrades[0].affected_artifacts)

    def test_extraction_stops_at_next_source_index_section(self) -> None:
        source_index = SOURCE_INDEX_WITH_CONFIRMED_UPGRADE + """

## Asset Index
- Asset name: unrelated
  - Migration action: none
"""

        upgrades = extract_reconciliation_upgrades(source_index)

        self.assertEqual(upgrades[0].migration_action, "rename")

    def test_confirmed_upgrade_fails_when_old_name_remains_in_feed(self) -> None:
        inputs = ReconciliationInputs(
            source_index_text=SOURCE_INDEX_WITH_CONFIRMED_UPGRADE,
            asset_bible_text=(
                "### 图片1 = 沈砚_青云宗内门弟子造型\n"
                "- Migration action: rename\n"
                "- Source-index evidence: ch06-line12\n"
            ),
            mother_feed_text="1 白天 大殿 黑衣弟子_一次性造型 低头站着 <固定镜头> 无对白",
            copy_pack_text="1 白天 大殿 沈砚_青云宗内门弟子造型 低头站着 <固定镜头> 无对白",
            image_manifest={
                "assets": [
                    {
                        "asset_name": "黑衣弟子_一次性造型",
                        "status": "renamed",
                        "replaced_by": "沈砚_青云宗内门弟子造型",
                    }
                ]
            },
        )

        errors = validate_reconciliation(inputs)

        self.assertTrue(any("mother feed still contains former name" in error for error in errors))

    def test_confirmed_upgrade_requires_manifest_migration(self) -> None:
        inputs = ReconciliationInputs(
            source_index_text=SOURCE_INDEX_WITH_CONFIRMED_UPGRADE,
            asset_bible_text=(
                "### 图片1 = 沈砚_青云宗内门弟子造型\n"
                "- Migration action: rename\n"
                "- Source-index evidence: ch06-line12\n"
            ),
            mother_feed_text="1 白天 大殿 沈砚_青云宗内门弟子造型 低头站着 <固定镜头> 无对白",
            copy_pack_text="1 白天 大殿 沈砚_青云宗内门弟子造型 低头站着 <固定镜头> 无对白",
            image_manifest={
                "assets": [
                    {
                        "asset_name": "黑衣弟子_一次性造型",
                        "status": "done",
                        "path": "人设资产/黑衣弟子_一次性造型.png",
                    }
                ]
            },
        )

        errors = validate_reconciliation(inputs)

        self.assertTrue(
            any("manifest former asset must be renamed or deprecated" in error for error in errors)
        )

    def test_confirmed_upgrade_requires_asset_bible_fields_in_canonical_block(self) -> None:
        inputs = ReconciliationInputs(
            source_index_text=SOURCE_INDEX_WITH_CONFIRMED_UPGRADE,
            asset_bible_text=(
                "### 图片1 = 旁人_错误造型\n"
                "- Migration action: rename\n"
                "- Source-index evidence: ch06-line12\n\n"
                "### 图片2 = 沈砚_青云宗内门弟子造型\n"
                "- Source evidence: ch06-line12\n"
            ),
            mother_feed_text="1 白天 大殿 沈砚_青云宗内门弟子造型 低头站着 <固定镜头> 无对白",
            copy_pack_text="1 白天 大殿 沈砚_青云宗内门弟子造型 低头站着 <固定镜头> 无对白",
            image_manifest={
                "assets": [
                    {
                        "asset_name": "黑衣弟子_一次性造型",
                        "status": "renamed",
                        "replaced_by": "沈砚_青云宗内门弟子造型",
                        "migration_reason": "confirmed source evidence",
                        "evidence_anchor": "ch06-line12",
                    }
                ]
            },
            reconciliation_log_text=(
                "沈砚_青云宗内门弟子造型 <- 黑衣弟子_一次性造型, ch06-line12"
            ),
        )

        errors = validate_reconciliation(inputs)

        joined = "; ".join(errors)
        self.assertIn("asset-bible missing Migration action", joined)
        self.assertIn("asset-bible missing Source-index evidence", joined)

    def test_documented_character_index_upgrade_shape_is_validated(self) -> None:
        source_index = """
# Source Index

## Character Index
- Name: 沈砚_青云宗内门弟子造型
  - confirmed anonymous-to-named upgrade:
    - Former temporary names: 黑衣弟子_一次性造型
    - Upgrade status: confirmed
    - Asset migration status: rename
    - Evidence anchors: ch06-line12
    - Affected prior artifacts: 生产资产/feed.md, 生产资产/copy-packs.md
"""
        inputs = ReconciliationInputs(
            source_index_text=source_index,
            asset_bible_text=(
                "### 图片1 = 沈砚_青云宗内门弟子造型\n"
                "- Migration action: rename\n"
                "- Source-index evidence: ch06-line12\n"
            ),
            mother_feed_text="1 大殿 黑衣弟子_一次性造型 低头站着 <固定镜头> 无对白",
            copy_pack_text="1 大殿 黑衣弟子_一次性造型 低头站着 <固定镜头> 无对白",
            image_manifest={
                "assets": [
                    {
                        "asset_name": "黑衣弟子_一次性造型",
                        "status": "done",
                        "path": "人设资产/黑衣弟子_一次性造型.png",
                    }
                ]
            },
            reconciliation_log_text=(
                "沈砚_青云宗内门弟子造型 <- 黑衣弟子_一次性造型, ch06-line12"
            ),
        )

        errors = validate_reconciliation(inputs)

        joined = "; ".join(errors)
        self.assertIn("mother feed still contains former name 黑衣弟子_一次性造型", joined)
        self.assertIn("copy packs still contain former name 黑衣弟子_一次性造型", joined)
        self.assertIn("manifest former asset must be renamed or deprecated", joined)

    def test_confirmed_upgrade_requires_affected_artifacts_and_log_entry(self) -> None:
        source_index = """
# Source Index

## Reconciliation Ledger
- Canonical name: 沈砚_青云宗内门弟子造型
  - Former temporary names: 黑衣弟子_一次性造型
  - Upgrade status: confirmed
  - Migration action: rename
  - Evidence anchors: ch06-line12
"""
        inputs = ReconciliationInputs(
            source_index_text=source_index,
            asset_bible_text=(
                "### 图片1 = 沈砚_青云宗内门弟子造型\n"
                "- Migration action: rename\n"
                "- Source-index evidence: ch06-line12\n"
            ),
            mother_feed_text="1 白天 大殿 沈砚_青云宗内门弟子造型 低头站着 <固定镜头> 无对白",
            copy_pack_text="1 白天 大殿 沈砚_青云宗内门弟子造型 低头站着 <固定镜头> 无对白",
            image_manifest={"assets": []},
            reconciliation_log_text="",
        )

        errors = validate_reconciliation(inputs)

        joined = "; ".join(errors)
        self.assertIn("confirmed upgrade requires affected artifacts", joined)
        self.assertIn("reconciliation-log missing canonical upgrade entry", joined)

    def test_inline_reconciliation_log_entry_satisfies_log_requirement(self) -> None:
        source_index = """
# Source Index

## Reconciliation Ledger
- Canonical name: 沈砚_青云宗内门弟子造型
  - Former temporary names: 黑衣弟子_一次性造型
  - Upgrade status: confirmed
  - Migration action: rename
  - Evidence anchors: ch06-line12
  - Affected prior artifacts: 生产资产/feed.md, 生产资产/copy-packs.md
  - reconciliation-log: 沈砚_青云宗内门弟子造型 <- 黑衣弟子_一次性造型, ch06-line12
"""
        inputs = ReconciliationInputs(
            source_index_text=source_index,
            asset_bible_text=(
                "### 图片1 = 沈砚_青云宗内门弟子造型\n"
                "- Migration action: rename\n"
                "- Source-index evidence: ch06-line12\n"
            ),
            mother_feed_text="1 白天 大殿 沈砚_青云宗内门弟子造型 低头站着 <固定镜头> 无对白",
            copy_pack_text="1 白天 大殿 沈砚_青云宗内门弟子造型 低头站着 <固定镜头> 无对白",
            image_manifest={
                "assets": [
                    {
                        "asset_name": "黑衣弟子_一次性造型",
                        "status": "renamed",
                        "replaced_by": "沈砚_青云宗内门弟子造型",
                    }
                ]
            },
            reconciliation_log_text="",
        )

        errors = validate_reconciliation(inputs)

        self.assertNotIn(
            "reconciliation-log missing canonical upgrade entry",
            "; ".join(errors),
        )

    def test_suspected_upgrade_does_not_force_migration(self) -> None:
        source_index = SOURCE_INDEX_WITH_CONFIRMED_UPGRADE.replace(
            "Upgrade status: confirmed",
            "Upgrade status: suspected",
        )
        inputs = ReconciliationInputs(
            source_index_text=source_index,
            asset_bible_text="### 图片1 = 黑衣弟子_一次性造型\n",
            mother_feed_text="1 白天 大殿 黑衣弟子_一次性造型 低头站着 <固定镜头> 无对白",
            copy_pack_text="1 白天 大殿 黑衣弟子_一次性造型 低头站着 <固定镜头> 无对白",
            image_manifest={"assets": []},
            reconciliation_log_text="",
        )

        errors = validate_reconciliation(inputs)

        self.assertEqual(errors, [])

    def test_cli_reports_validation_errors_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            internal = workspace / "生产资产" / "_内部"
            internal.mkdir(parents=True)
            feed = workspace / "生产资产" / "feed.md"
            copy_pack = workspace / "生产资产" / "copy-packs.md"
            source_index = internal / "source-index.md"
            asset_bible = internal / "asset-bible.md"
            manifest = internal / "image-manifest.json"
            source_index.write_text(SOURCE_INDEX_WITH_CONFIRMED_UPGRADE, encoding="utf-8")
            asset_bible.write_text(
                "### 图片1 = 沈砚_青云宗内门弟子造型\n- Migration action: rename\n",
                encoding="utf-8",
            )
            feed.write_text("1 黑衣弟子_一次性造型 <固定镜头>", encoding="utf-8")
            copy_pack.write_text("1 沈砚_青云宗内门弟子造型 <固定镜头>", encoding="utf-8")
            manifest.write_text(json.dumps({"assets": []}, ensure_ascii=False), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "validate_reconciliation.py"),
                    "--source-index",
                    str(source_index),
                    "--asset-bible",
                    str(asset_bible),
                    "--mother-feed",
                    str(feed),
                    "--copy-packs",
                    str(copy_pack),
                    "--image-manifest",
                    str(manifest),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Reconciliation validation failed:", result.stdout)
        self.assertIn("mother feed still contains former name", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


class AssetMigrationTests(unittest.TestCase):
    def new_job(self, asset_name: str, asset_type: str = "character", output_dir: str = "人设资产") -> ImageJob:
        return ImageJob(
            job_id=f"job-{asset_name}",
            asset_name=asset_name,
            asset_type=asset_type,
            prompt=f"prompt for {asset_name}",
            output_dir=output_dir,
            output_file=f"{asset_name}.png",
            depends_on=[],
            reference_images=[],
            provider="openai-compatible",
            model="gpt-image-2",
            size="16:9",
            status="pending",
        )

    def test_migrate_asset_name_renames_file_and_updates_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            asset_dir = workspace / "人设资产"
            asset_dir.mkdir()
            old_file = asset_dir / "黑衣弟子_一次性造型.png"
            old_file.write_bytes(b"image")
            manifest = {
                "version": 1,
                "assets": [
                    {
                        "asset_name": "黑衣弟子_一次性造型",
                        "asset_type": "character",
                        "status": "done",
                        "path": "人设资产/黑衣弟子_一次性造型.png",
                    }
                ],
            }

            updated = migrate_asset_name(
                manifest=manifest,
                workspace=workspace,
                old_name="黑衣弟子_一次性造型",
                new_name="沈砚_青云宗内门弟子造型",
                asset_dir="人设资产",
                mode="rename",
                migration_reason="ch06 reveals the early black-clothed disciple is 沈砚",
                evidence_anchor="ch06-line12",
                apply=True,
            )

            new_file = asset_dir / "沈砚_青云宗内门弟子造型.png"
            self.assertFalse(old_file.exists())
            self.assertTrue(new_file.is_file())
        assets = {asset["asset_name"]: asset for asset in updated["assets"]}
        self.assertEqual(assets["黑衣弟子_一次性造型"]["status"], "renamed")
        self.assertEqual(assets["黑衣弟子_一次性造型"]["replaced_by"], "沈砚_青云宗内门弟子造型")
        self.assertEqual(assets["沈砚_青云宗内门弟子造型"]["status"], "renamed")
        self.assertEqual(assets["沈砚_青云宗内门弟子造型"]["previous_asset_name"], "黑衣弟子_一次性造型")

    def test_migrated_manifest_validates_against_current_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            asset_dir = workspace / "人设资产"
            asset_dir.mkdir()
            (asset_dir / "黑衣弟子_一次性造型.png").write_bytes(b"image")
            manifest = {
                "assets": [
                    {
                        "asset_name": "黑衣弟子_一次性造型",
                        "asset_type": "character",
                        "status": "done",
                        "path": "人设资产/黑衣弟子_一次性造型.png",
                    }
                ]
            }

            updated = migrate_asset_name(
                manifest=manifest,
                workspace=workspace,
                old_name="黑衣弟子_一次性造型",
                new_name="沈砚_青云宗内门弟子造型",
                asset_dir="人设资产",
                mode="rename",
                migration_reason="confirmed by chapter 6",
                evidence_anchor="ch06-line12",
                apply=True,
            )
            errors = validate_manifest(
                updated,
                [self.new_job("沈砚_青云宗内门弟子造型")],
                workspace,
            )

        self.assertEqual(errors, [])

    def test_migrate_asset_name_deprecates_old_asset_without_renaming_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            asset_dir = workspace / "人设资产"
            asset_dir.mkdir()
            old_file = asset_dir / "黑衣弟子_一次性造型.png"
            old_file.write_bytes(b"image")
            manifest = {
                "assets": [
                    {
                        "asset_name": "黑衣弟子_一次性造型",
                        "asset_type": "character",
                        "status": "done",
                    }
                ]
            }

            updated = migrate_asset_name(
                manifest=manifest,
                workspace=workspace,
                old_name="黑衣弟子_一次性造型",
                new_name="沈砚_青云宗内门弟子造型",
                asset_dir="人设资产",
                mode="deprecated",
                migration_reason="old face cannot represent confirmed source identity",
                evidence_anchor="ch06-line12",
                apply=True,
            )

            self.assertTrue(old_file.is_file())
        assets = {asset["asset_name"]: asset for asset in updated["assets"]}
        self.assertEqual(assets["黑衣弟子_一次性造型"]["status"], "deprecated")
        self.assertEqual(assets["黑衣弟子_一次性造型"]["replaced_by"], "沈砚_青云宗内门弟子造型")

    def test_migrate_asset_name_refuses_to_overwrite_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            asset_dir = workspace / "人设资产"
            asset_dir.mkdir()
            (asset_dir / "黑衣弟子_一次性造型.png").write_bytes(b"old")
            (asset_dir / "沈砚_青云宗内门弟子造型.png").write_bytes(b"new")

            with self.assertRaises(ValueError) as context:
                migrate_asset_name(
                    manifest={"assets": []},
                    workspace=workspace,
                    old_name="黑衣弟子_一次性造型",
                    new_name="沈砚_青云宗内门弟子造型",
                    asset_dir="人设资产",
                    mode="rename",
                    migration_reason="confirmed source evidence",
                    evidence_anchor="ch06-line12",
                    apply=True,
                )

        self.assertIn("target asset file already exists", str(context.exception))

    def test_migrate_asset_name_rejects_path_like_asset_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            with self.assertRaises(ValueError) as context:
                migrate_asset_name(
                    manifest={"assets": []},
                    workspace=workspace,
                    old_name="../黑衣弟子",
                    new_name="沈砚_青云宗内门弟子造型",
                    asset_dir="人设资产",
                    mode="rename",
                    migration_reason="confirmed source evidence",
                    evidence_anchor="ch06-line12",
                    apply=True,
                )

        self.assertIn("asset names must be file-safe names", str(context.exception))

    def test_migrate_asset_name_refuses_missing_source_file_when_applying_rename(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "人设资产").mkdir()

            with self.assertRaises(ValueError) as context:
                migrate_asset_name(
                    manifest={"assets": []},
                    workspace=workspace,
                    old_name="黑衣弟子_一次性造型",
                    new_name="沈砚_青云宗内门弟子造型",
                    asset_dir="人设资产",
                    mode="rename",
                    migration_reason="confirmed source evidence",
                    evidence_anchor="ch06-line12",
                    apply=True,
                )

        self.assertIn("source asset file missing", str(context.exception))

    def test_migrate_asset_name_preserves_non_character_asset_type(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            asset_dir = workspace / "场景资产"
            asset_dir.mkdir()
            (asset_dir / "青云宗主殿_旧母图.png").write_bytes(b"image")
            manifest = {
                "assets": [
                    {
                        "asset_name": "青云宗主殿_旧母图",
                        "asset_type": "scene",
                        "status": "done",
                        "path": "场景资产/青云宗主殿_旧母图.png",
                    }
                ]
            }

            updated = migrate_asset_name(
                manifest=manifest,
                workspace=workspace,
                old_name="青云宗主殿_旧母图",
                new_name="青云宗主殿_母图",
                asset_dir="场景资产",
                mode="rename",
                migration_reason="standardized scene mother name",
                evidence_anchor="ch02-scene01",
                apply=True,
            )

        assets = {asset["asset_name"]: asset for asset in updated["assets"]}
        self.assertEqual(assets["青云宗主殿_母图"]["asset_type"], "scene")

    def test_migrate_asset_names_cli_writes_manifest_when_applied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            asset_dir = workspace / "人设资产"
            internal = workspace / "生产资产" / "_内部"
            asset_dir.mkdir(parents=True)
            internal.mkdir(parents=True)
            (asset_dir / "黑衣弟子_一次性造型.png").write_bytes(b"image")
            manifest_path = internal / "image-manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "assets": [
                            {
                                "asset_name": "黑衣弟子_一次性造型",
                                "asset_type": "character",
                                "status": "done",
                                "path": "人设资产/黑衣弟子_一次性造型.png",
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "migrate_asset_names.py"),
                    "--manifest",
                    str(manifest_path),
                    "--workspace",
                    str(workspace),
                    "--old-name",
                    "黑衣弟子_一次性造型",
                    "--new-name",
                    "沈砚_青云宗内门弟子造型",
                    "--asset-dir",
                    "人设资产",
                    "--mode",
                    "rename",
                    "--migration-reason",
                    "confirmed by chapter 6",
                    "--evidence-anchor",
                    "ch06-line12",
                    "--apply",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            updated = json.loads(manifest_path.read_text(encoding="utf-8"))

            self.assertTrue((asset_dir / "沈砚_青云宗内门弟子造型.png").is_file())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(
            any(asset["asset_name"] == "沈砚_青云宗内门弟子造型" for asset in updated["assets"])
        )


if __name__ == "__main__":
    unittest.main()
