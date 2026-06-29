import tempfile
import unittest
from pathlib import Path

from scripts.init_workspace import ASSET_DIRS, init_workspace


class InitWorkspaceTests(unittest.TestCase):
    def test_init_workspace_creates_standard_asset_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            result = init_workspace(workspace)

            self.assertEqual([path.name for path in result.directories], list(ASSET_DIRS))
            for dirname in ASSET_DIRS:
                self.assertTrue((workspace / dirname).is_dir())

    def test_init_workspace_preserves_existing_asset_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            existing_dir = workspace / "场景资产"
            existing_dir.mkdir()
            marker = existing_dir / "existing.txt"
            marker.write_text("keep", encoding="utf-8")

            init_workspace(workspace)

            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_init_workspace_moves_root_script_file_to_script_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            script = workspace / "发布抖音仙界版，圣地老祖破防了，前十章"
            script.write_text("原始剧本", encoding="utf-8")

            result = init_workspace(workspace)

            archived = workspace / "剧本资产" / script.name
            self.assertFalse(script.exists())
            self.assertEqual(archived.read_text(encoding="utf-8"), "原始剧本")
            self.assertEqual(result.archived_scripts, [archived])

    def test_init_workspace_does_not_overwrite_archived_script(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            script_dir = workspace / "剧本资产"
            script_dir.mkdir()
            root_script = workspace / "第一章.txt"
            root_script.write_text("根目录版本", encoding="utf-8")
            archived_script = script_dir / root_script.name
            archived_script.write_text("已有归档版本", encoding="utf-8")

            result = init_workspace(workspace)

            self.assertTrue(root_script.exists())
            self.assertEqual(archived_script.read_text(encoding="utf-8"), "已有归档版本")
            self.assertEqual(result.archived_scripts, [])

    def test_init_workspace_does_not_archive_generated_working_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            index = workspace / "source-index.md"
            index.write_text("索引", encoding="utf-8")

            init_workspace(workspace)

            self.assertTrue(index.exists())
            self.assertFalse((workspace / "剧本资产" / index.name).exists())


class SkillTextRulesTests(unittest.TestCase):
    def test_dialogue_compression_forbids_orphan_lines(self) -> None:
        skill_text = Path(__file__).resolve().parents[1].joinpath("SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("孤句", skill_text)
        self.assertIn("前因", skill_text)
        self.assertIn("动作对象", skill_text)
        self.assertIn("结果", skill_text)

    def test_dialogue_rules_require_source_excerpt_not_rewrite(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, format_text):
            self.assertIn("对白必须从原文摘取", text)
            self.assertIn("不改写", text)
            self.assertIn("不补写", text)
            self.assertIn("不提前挪用", text)
            self.assertIn("太长就拆镜头", text)


if __name__ == "__main__":
    unittest.main()
