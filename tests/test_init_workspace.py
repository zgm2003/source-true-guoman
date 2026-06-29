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

    def test_long_scope_coverage_forbids_solving_dialogue_by_reducing_groups(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, format_text):
            self.assertIn("不得用减少总组数解决对白变长", text)
            self.assertIn("多章覆盖审计", text)
            self.assertIn("十章不得压成十几组", text)

    def test_default_mode_preserves_source_content_for_manual_trimming(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, format_text):
            self.assertIn("默认不主动删减原文内容", text)
            self.assertIn("把删减权留给用户", text)
            self.assertIn("只有用户明确要求压缩版", text)

    def test_female_assets_allow_tasteful_leg_visibility(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, format_text):
            self.assertIn("成年女修可以适度露腿", text)
            self.assertIn("可露小腿、膝盖、膝上自然腿部线条", text)
            self.assertIn("正常双腿可见不算违规", text)
            self.assertIn("禁止低机位扫腿", text)
            self.assertNotIn("不靠露腿卖点", text)
            self.assertNotIn("同时露出双腿", text)
            self.assertNotIn("整条腿暴露", text)

    def test_shot_staging_must_not_invent_unsourced_blocking(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, format_text):
            self.assertIn("不主动添加站起、起身、跪下、走动、抬手、收起法器", text)
            self.assertIn("原文只写坐着就写坐着", text)
            self.assertIn("道具动作必须有原文依据", text)

        self.assertNotIn("站在左侧席位前", format_text)
        self.assertNotIn("法器在指节间轻晃", format_text)

    def test_dialogue_camera_keeps_speaker_and_space_without_invented_blocking(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, format_text):
            self.assertIn("谁说话，镜头优先给谁", text)
            self.assertIn("默认不要纯大脸特写", text)
            self.assertIn("对白行优先使用中近景、半身中景或中景", text)
            self.assertIn("保留说话人的身体姿态、所在席位/环境", text)
            self.assertIn("说话微表演", text)
            self.assertIn("不得把微动作升级成原文没有的站起、走动、跪下、抬手收法器", text)

    def test_dialogue_camera_defaults_to_front_half_body_not_side_template(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, format_text):
            self.assertIn("对白默认优先给说话人正面半身", text)
            self.assertIn("空间感放在背景纵深、席位关系和反应层次里", text)
            self.assertIn("不要把默认对白镜头写成半身侧面", text)

        self.assertIn("正面半身", format_text)
        self.assertNotIn("半身侧面 + 左侧席位 + 王座远处可见", format_text)

    def test_15_second_groups_must_advance_plot_not_empty_setup(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, format_text):
            self.assertIn("15秒组必须承载剧情推进", text)
            self.assertIn("不要整组只做空定场", text)
            self.assertIn("开场定场最多占1个短镜头", text)
            self.assertIn("第一组应尽快进入原文事件或对白", text)
            self.assertIn("不要用过低对白字数预算把一句完整汇报拆成多组", text)

        self.assertIn("鬼王宗大殿与骨灵教汇报", format_text)
        self.assertIn(
            "宗主大人，昨日我骨灵教内又发现了一名正道奸细，今日一早我就已经把他剥皮抽筋，将他的一身骨头炼制成了法器，神魂也收入到了万魂幡中。",
            format_text,
        )

    def test_character_assets_must_not_include_shot_staging(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, format_text):
            self.assertIn("人设资产只写身份、脸、体型、服装和气质", text)
            self.assertIn("不要把坐在左侧第二位、站在席位前、当前镜头姿态写进三视图人设", text)
            self.assertIn("席位、站位、坐姿、当前动作属于视频行", text)
            self.assertIn("骨灵教老者_骨纹法袍造型", text)
            self.assertNotIn("骨灵教老者_左侧第二席造型", text)


if __name__ == "__main__":
    unittest.main()
