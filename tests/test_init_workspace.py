import tempfile
import unittest
import subprocess
import sys
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
    def test_agent_pack_references_are_declared_and_routed_from_main_skill(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")

        expected_agent_refs = [
            "agents/source-indexer.md",
            "agents/asset-bible.md",
            "agents/faithful-feed.md",
            "agents/cut-safety.md",
            "agents/feed-auditor.md",
            "agents/visual-polish.md",
            "agents/production-runner.md",
        ]

        for relative_path in expected_agent_refs:
            with self.subTest(relative_path=relative_path):
                agent_path = root / relative_path
                self.assertTrue(agent_path.is_file())
                self.assertIn(relative_path, skill_text)

    def test_main_skill_routes_common_intents_to_specialists(self) -> None:
        root = Path(__file__).resolve().parents[1]
        route_lines = [
            line.strip()
            for line in root.joinpath("SKILL.md").read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("- ")
        ]

        route_contracts = [
            (
                ("New project directory or root script file",),
                ("scripts/init_workspace.py",),
            ),
            (
                ("Process these chapters", "turn this into feed"),
                ("source-indexer -> asset-bible -> faithful-feed -> feed-auditor",),
            ),
            (
                ("Make an index",),
                ("agents/source-indexer.md", "references/source-index-format.md"),
            ),
            (
                ("Make assets",),
                ("agents/asset-bible.md", "references/asset-bible-format.md"),
            ),
            (
                ("Write feed",),
                (
                    "agents/faithful-feed.md",
                    "references/format.md",
                    "references/xiaoyunque-tags.md",
                ),
            ),
            (
                ("Review",),
                (
                    "agents/feed-auditor.md",
                    "references/audit-checklist.md",
                    "scripts/validate_feed.py",
                ),
            ),
            (
                ("Can I delete",),
                ("agents/cut-safety.md", "references/cut-safety-rules.md"),
            ),
            (("Make it look better",), ("agents/visual-polish.md",)),
            (("Production order",), ("agents/production-runner.md",)),
        ]

        for intents, targets in route_contracts:
            with self.subTest(intents=intents):
                matching_lines = [
                    line for line in route_lines if all(intent in line for intent in intents)
                ]
                self.assertTrue(matching_lines, f"No route line found for {intents!r}")
                route_line = matching_lines[0]
                for target in targets:
                    self.assertIn(target, route_line)

    def test_optional_agents_are_guarded_by_prerequisites(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")

        guarded_phrases = [
            "cut-safety is a deletion-risk assistant, not a compression writer",
            "generic compression requests are refused as rewrites",
            "exact cut/source-span advice",
            "deletion-risk review and manual cut candidates",
            "Only use `cut-safety` after the user has chosen deletion targets or asks for cut-risk help",
            "Only use `visual-polish` after preserving source coverage",
            "Only use `production-runner` after assets and faithful feed lines exist",
        ]

        for phrase in guarded_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill_text)

    def test_agent_pack_keeps_source_faithfulness_as_non_overridable_contract(self) -> None:
        root = Path(__file__).resolve().parents[1]
        contract_phrases = [
            "不得由 AI 帮用户压缩",
            "对白必须从原文摘取",
            "不主动添加站起、起身、跪下、走动、抬手、收起法器",
            "原作多少字就保留多少字",
        ]

        for agent_file in root.joinpath("agents").glob("*.md"):
            if agent_file.name == "openai.yaml":
                continue
            text = agent_file.read_text(encoding="utf-8")
            with self.subTest(agent_file=agent_file.name):
                self.assertIn("保真契约", text)
                for phrase in contract_phrases:
                    self.assertIn(phrase, text)

    def test_workspace_storage_policy_puts_feed_text_in_production_assets(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        faithful_feed_text = root.joinpath("agents", "faithful-feed.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, faithful_feed_text):
            self.assertIn("投喂稿、source-index、asset-bible、审计报告、剪辑风险报告属于生产资产", text)
            self.assertIn("视频资产只放最终视频文件或渲染结果", text)

    def test_scope_modes_require_full_prescan_or_explicit_smoke_label(self) -> None:
        root = Path(__file__).resolve().parents[1]
        checked_files = [
            root.joinpath("SKILL.md"),
            root.joinpath("agents", "source-indexer.md"),
            root.joinpath("agents", "asset-bible.md"),
            root.joinpath("agents", "faithful-feed.md"),
        ]
        required_phrases = [
            "正式多章任务必须先预扫完整请求范围",
            "局部烟测必须显式标记已阅读范围",
            "局部烟测资产不得当作全局定稿",
        ]

        for path in checked_files:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                for phrase in required_phrases:
                    self.assertIn(phrase, text)

    def test_source_index_format_tracks_scope_status(self) -> None:
        root = Path(__file__).resolve().parents[1]
        format_text = root.joinpath("references", "source-index-format.md").read_text(
            encoding="utf-8"
        )

        for phrase in ("索引状态", "请求范围", "已阅读范围", "全范围预扫", "局部烟测"):
            self.assertIn(phrase, format_text)

    def test_validate_feed_rejects_grouped_feed_and_invalid_camera_tags(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_feed = Path(temp_dir) / "bad-feed.md"
            bad_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。",
                        "### 第1组",
                        "1 日 内 鬼王宗宗门大殿 林夜 坐在黑石王座上 中景 + 平视 慢慢推进 环境音：大殿低鸣",
                        "3 日 内 鬼王宗宗门大殿 骨灵教老者 正面半身开口 中近景 + 平视 镜头前推 骨灵教老者：宗主大人。",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(root / "scripts" / "validate_feed.py"), str(bad_feed)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("group marker", result.stdout)
            self.assertIn("invalid camera tag", result.stdout)
            self.assertIn("expected line 2", result.stdout)

    def test_validate_feed_accepts_continuous_feed_with_xiaoyunque_tags(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            good_feed = Path(temp_dir) / "good-feed.md"
            good_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。",
                        "1 日 内 鬼王宗宗门大殿 林夜 坐在黑石王座上 中景 + 平视 固定镜头 环境音：大殿低鸣",
                        "2 日 内 鬼王宗宗门大殿 骨灵教老者 正面半身开口 中近景 + 平视 镜头前推 骨灵教老者：宗主大人。",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(root / "scripts" / "validate_feed.py"), str(good_feed)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Feed validation passed", result.stdout)

    def test_validate_feed_rejects_missing_global_requirement_and_forbidden_terms(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_feed = Path(temp_dir) / "legacy-feed.md"
            bad_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        "segment S01",
                        "1 日 内 鬼王宗宗门大殿 林夜 首帧坐在黑石王座上 中景 + 平视 固定镜头 环境音：大殿低鸣",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(root / "scripts" / "validate_feed.py"), str(bad_feed)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing global requirement line", result.stdout)
            self.assertIn("forbidden term `segment`", result.stdout)
            self.assertIn("forbidden term `S01`", result.stdout)
            self.assertIn("forbidden term `首帧`", result.stdout)

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
            self.assertIn("原作多少字就保留多少字", text)
            self.assertIn("不删上下文", text)

    def test_long_scope_coverage_forbids_solving_dialogue_by_reducing_numbered_lines(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, format_text):
            self.assertIn("不得用减少编号行数解决对白变长", text)
            self.assertIn("多章覆盖审计", text)
            self.assertIn("十章不得压成十几行", text)

    def test_default_mode_preserves_source_content_for_manual_trimming_without_ai_compression(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, format_text):
            self.assertIn("原作多少字就保留多少字", text)
            self.assertIn("把删减权留给用户", text)
            self.assertIn("不得由 AI 帮用户压缩", text)
            self.assertIn("压缩请求只能输出原文切点", text)
            self.assertNotIn("may you intentionally trim", text)
            self.assertNotIn("只有用户明确要求压缩版", text)

    def test_video_feed_uses_continuous_numbering_without_ai_breathing_blocks(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, format_text):
            self.assertIn("把呼吸感交给用户", text)
            self.assertIn("Do not create 15-second groups", text)
            self.assertIn("do not enforce a 100-character spoken limit", text)
            self.assertNotIn("15秒对白字数上限100字", text)
            self.assertNotIn("超过100字就拆镜头或拆下一组", text)

        self.assertIn("number lines continuously from `1` to the end", skill_text)
        self.assertIn("Use continuous numbering only", format_text)

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

    def test_video_feed_starts_with_global_requirement_then_source_content(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, format_text):
            self.assertIn(
                "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。",
                text,
            )

        self.assertIn("Start `## 视频投喂块` with this exact line", skill_text)
        self.assertIn("The first line after `统一要求` should enter source content quickly", format_text)
        self.assertNotIn("### 第1组", format_text)
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
