import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.recommend_next_steps import (
    RecommendationState,
    inspect_workspace,
    recommendation_block,
    recommend_next_steps,
)


class RecommendationEngineTests(unittest.TestCase):
    def test_pending_reconciliation_is_first_priority(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="done",
            storyboard="not_started",
            reconciliation="pending",
            recent_user_intent="continue",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "处理索引回填")
        self.assertIn("新章节证据改变了旧角色/资产判断", recommendation.options[0].reason)

    def test_missing_images_after_copy_packs_recommends_image_generation(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="missing",
            storyboard="not_started",
            reconciliation="none",
            recent_user_intent="",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "自动化生图")
        self.assertEqual(recommendation.options[0].command, "image-generator")

    def test_style_preview_done_requires_user_confirmation(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="style_preview_done",
            storyboard="not_started",
            reconciliation="none",
            recent_user_intent="",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "确认风格基准")
        self.assertIn("未确认前不跑全量依赖资产", recommendation.options[0].reason)

    def test_failed_images_block_storyboard_recommend_retry_first(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="failed",
            storyboard="not_started",
            reconciliation="none",
            recent_user_intent="分镜",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "续跑/修复失败图片")
        self.assertTrue(
            any("暂不建议分镜 QA" in blocked.reason for blocked in recommendation.blocked)
        )

    def test_done_images_recommend_storyboard_qa(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="done",
            storyboard="not_started",
            reconciliation="none",
            recent_user_intent="",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "分镜/站位 QA")
        self.assertEqual(recommendation.options[0].command, "storyboard-contact-sheet")

    def test_done_images_recommend_storyboard_before_cut_pressure(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="done",
            storyboard="not_started",
            reconciliation="none",
            recent_user_intent="平台时长太长，需要删减",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "分镜/站位 QA")

    def test_storyboard_needs_fix_recommends_video_or_asset_correction(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="done",
            storyboard="needs_fix",
            reconciliation="none",
            recent_user_intent="",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "视频增强或资产修正")
        self.assertIn("分镜 QA", recommendation.options[0].reason)

    def test_duration_intent_recommends_cut_safety(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="done",
            storyboard="done",
            reconciliation="none",
            recent_user_intent="平台时长太长，需要删减",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "安全剪辑")
        self.assertEqual(recommendation.options[0].command, "cut-safety")

    def test_recommendation_block_contains_status_and_three_options(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="missing",
            storyboard="not_started",
            reconciliation="none",
            recent_user_intent="",
        )

        block = recommendation_block(state, recommend_next_steps(state))

        self.assertIn("## 状态摘要", block)
        self.assertIn("下一步建议（3选1）：", block)
        self.assertEqual(block.count("\n1. "), 1)
        self.assertEqual(block.count("\n2. "), 1)
        self.assertEqual(block.count("\n3. "), 1)

    def test_migration_image_status_recommends_reconciliation_review(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="renamed",
            storyboard="not_started",
            reconciliation="none",
            recent_user_intent="",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "核对资产迁移")
        self.assertEqual(recommendation.options[0].command, "validate-reconciliation")


class RecommendationWorkspaceInspectionTests(unittest.TestCase):
    def test_inspect_workspace_reads_image_manifest_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            internal = workspace / "生产资产" / "_内部"
            internal.mkdir(parents=True)
            (workspace / "生产资产" / "feed.md").write_text("母稿", encoding="utf-8")
            (workspace / "生产资产" / "copy-packs.md").write_text("复制包", encoding="utf-8")
            (internal / "image-manifest.json").write_text(
                json.dumps(
                    {
                        "assets": [
                            {"asset_name": "a", "status": "done", "path": "人设资产/a.png"},
                            {"asset_name": "b", "status": "blocked", "path": "人设资产/b.png"},
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            state = inspect_workspace(workspace)

        self.assertEqual(state.mother_feed, "passed")
        self.assertEqual(state.copy_packs, "passed")
        self.assertEqual(state.images, "blocked")

    def test_inspect_workspace_reads_migration_manifest_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            internal = workspace / "生产资产" / "_内部"
            internal.mkdir(parents=True)
            (internal / "image-manifest.json").write_text(
                json.dumps(
                    {
                        "assets": [
                            {
                                "asset_name": "黑衣弟子_一次性造型",
                                "status": "renamed",
                                "replaced_by": "沈砚_青云宗内门弟子造型",
                                "migration_reason": "confirmed by chapter 6",
                                "evidence_anchor": "ch06-line12",
                            },
                            {
                                "asset_name": "沈砚_青云宗内门弟子造型",
                                "status": "done",
                                "path": "人设资产/沈砚_青云宗内门弟子造型.png",
                            },
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            state = inspect_workspace(workspace)

        self.assertEqual(state.images, "renamed")

    def test_inspect_workspace_reads_storyboard_needs_fix_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            internal = workspace / "生产资产" / "_内部"
            internal.mkdir(parents=True)
            (internal / "storyboard-manifest.json").write_text(
                json.dumps({"status": "needs_fix"}, ensure_ascii=False),
                encoding="utf-8",
            )

            state = inspect_workspace(workspace)

        self.assertEqual(state.storyboard, "needs_fix")

    def test_cli_prints_recommendation_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "recommend_next_steps.py"),
                    "--workspace",
                    str(workspace),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("## 状态摘要", result.stdout)
        self.assertIn("下一步建议（3选1）：", result.stdout)


if __name__ == "__main__":
    unittest.main()
