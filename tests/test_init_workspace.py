import tempfile
import unittest
import subprocess
import sys
from pathlib import Path

from scripts.init_workspace import ASSET_DIRS, init_workspace


READABLE_TEXT_THAT_MUST_NOT_APPEAR_AS_MOJIBAKE = [
    "保真契约",
    "原作多少字就保留多少字",
    "不得由 AI 帮用户压缩",
    "不得用 AI 帮用户压缩",
    "对白必须从原文摘取",
    "不主动添加站起、起身、跪下、走动、抬手、收起法器",
    "生产资产",
    "资产提示词",
    "全范围预扫",
    "局部烟测",
    "正式多章任务必须先预扫完整请求范围",
    "局部烟测必须显式标记已阅读范围",
    "局部烟测资产不得当作全局定稿",
    "索引状态",
    "请求范围",
    "已阅读范围",
    "未阅读范围",
    "证据依据",
    "弟子/NPC/黑衣人/侍女/守卫/路人",
    "主角/高频配角",
    "命名低频角色",
    "群像模板",
    "一次性背景人",
    "人脸身份参考",
    "旧造型参考",
    "避撞脸参考",
    "同门服制参考",
    "场景母图参考",
    "局部场景参考",
    "材质风格参考",
    "界面风格参考",
    "首帧",
    "尾帧",
    "续接",
    "承接",
]


def common_mojibake_fragments() -> list[str]:
    fragments: set[str] = set()
    for phrase in READABLE_TEXT_THAT_MUST_NOT_APPEAR_AS_MOJIBAKE:
        broken = phrase.encode("utf-8").decode("gbk", errors="replace")
        fragments.add(broken)
        fragments.add(broken.replace("\ufffd", "?"))
    return sorted(fragment for fragment in fragments if len(fragment) >= 3)


COMMON_MOJIBAKE_FRAGMENTS = common_mojibake_fragments()


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
    def assertNoKnownMojibake(self, text: str) -> None:
        self.assertNotIn("\ufffd", text)
        for fragment in COMMON_MOJIBAKE_FRAGMENTS:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, text)

    def test_agent_pack_references_are_declared_and_routed_from_main_skill(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")

        expected_agent_refs = [
            "agents/source-indexer.md",
            "agents/asset-bible.md",
            "agents/image-generator.md",
            "agents/faithful-feed.md",
            "agents/copy-packager.md",
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

    def test_formal_production_aspect_ratio_options_are_limited(self) -> None:
        root = Path(__file__).resolve().parents[1]
        files = [
            root.joinpath("SKILL.md"),
            root.joinpath("references", "format.md"),
            root.joinpath("references", "copy-pack-format.md"),
            root.joinpath("agents", "faithful-feed.md"),
            root.joinpath("agents", "copy-packager.md"),
        ]

        for path in files:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIn("9:16（竖屏）", text)
                self.assertIn("16:9（横屏）", text)
                self.assertIn("21:9（电影）", text)
                self.assertIn("默认 16:9", text)
                self.assertNotIn("1:1 方屏", text)
                self.assertNotIn("4:5 信息流", text)

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
                (
                    "source-indexer -> asset-bible -> image-generator(optional) -> faithful-feed -> feed-auditor",
                ),
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
                    "references/libtv-tags.md",
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
            (
                ("复制包", "投喂包"),
                ("agents/copy-packager.md", "references/copy-pack-format.md"),
            ),
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
            "run `copy-packager` after source index, asset bible, faithful feed, and feed audit exist; keep copy packs in a separate `生产资产` artifact",
            "Only use `copy-packager` after source index, asset bible, faithful feed, and feed audit exist",
            "copy-packager creates paste-ready wrappers, not pacing groups",
        ]

        for phrase in guarded_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill_text)

    def test_copy_packager_contract_preserves_non_compression_and_wrapper_boundary(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_path = root.joinpath("agents", "copy-packager.md")

        self.assertTrue(agent_path.is_file())
        agent_text = agent_path.read_text(encoding="utf-8")

        required_phrases = [
            "保真契约",
            "原作多少字就保留多少字",
            "不得由 AI 帮用户压缩",
            "对白必须从原文摘取",
            "复制投喂包",
            "delivery wrapper",
            "not pacing groups",
            "preserve original continuous line numbers",
            "do not renumber each pack from 1",
            "default pack size is 5",
            "do not invent references",
            "references/copy-pack-format.md",
            "scripts/validate_copy_packs.py",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agent_text)

    def test_copy_packager_routes_to_copy_pack_validator(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        agent_text = root.joinpath("agents", "copy-packager.md").read_text(
            encoding="utf-8"
        )
        validator_path = root.joinpath("scripts", "validate_copy_packs.py")

        self.assertTrue(validator_path.is_file())
        for text in (skill_text, agent_text):
            self.assertIn("scripts/validate_copy_packs.py", text)
            self.assertIn("--source-feed", text)
            self.assertIn("--pack-size", text)

    def test_copy_pack_format_defines_paste_ready_wrapper_shape(self) -> None:
        root = Path(__file__).resolve().parents[1]
        reference_path = root.joinpath("references", "copy-pack-format.md")

        self.assertTrue(reference_path.is_file())
        reference_text = reference_path.read_text(encoding="utf-8")

        required_phrases = [
            "# Copy Pack Format",
            "复制投喂包",
            "delivery wrapper",
            "not pacing groups",
            "Pack size: 5",
            "### 投喂包 {NNN}｜原始行 {start}-{end}",
            "### 投喂包 001｜原始行 1-5",
            "zero-padded to three digits",
            "separator is full-width `｜`",
            "range must match copied original line numbers",
            "preserve original continuous line numbers",
            "do not renumber from 1 inside each pack",
            "上传参考图：",
            "音色绑定：",
            "场景1 =",
            "角色1 =",
            "音色1 =",
            "需人工确认",
            "Do not invent references",
            "Voice assets belong under `音色绑定：`",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, reference_text)

    def test_copy_pack_format_separates_image_uploads_from_voice_bindings(self) -> None:
        root = Path(__file__).resolve().parents[1]
        reference_text = root.joinpath("references", "copy-pack-format.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("上传参考图：", reference_text)
        self.assertIn("音色绑定：", reference_text)
        upload_block = reference_text.split("上传参考图：", 1)[1].split(
            "音色绑定：", 1
        )[0]
        voice_block = reference_text.split("音色绑定：", 1)[1].split(
            "1 日 内", 1
        )[0]

        self.assertIn("场景1 =", upload_block)
        self.assertIn("角色1 =", upload_block)
        self.assertIn("道具1 =", upload_block)
        self.assertNotIn("音色1 =", upload_block)
        self.assertNotIn("音色2 =", upload_block)
        self.assertIn("音色1 =", voice_block)
        self.assertIn("音色2 =", voice_block)

    def test_canonical_format_keeps_copy_packs_out_of_video_feed(self) -> None:
        root = Path(__file__).resolve().parents[1]
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )
        runner_text = root.joinpath("agents", "production-runner.md").read_text(
            encoding="utf-8"
        )

        for phrase in [
            "canonical continuous feed",
            "Copy packs are separate paste-ready artifacts",
            "references/copy-pack-format.md",
            "Do not put `复制投喂包` inside `## 视频投喂块`",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, format_text)

        for phrase in [
            "copy-packager",
            "fixed pack sizes such as `每5条一包`",
            "paste-ready wrappers",
            "not by arbitrary 15-second pacing",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, runner_text)
        self.assertNotIn("fixed copy counts", runner_text)

    def test_cut_safety_outputs_risk_notes_not_rewritten_compression(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_text = root.joinpath("agents", "cut-safety.md").read_text(
            encoding="utf-8"
        )
        rules_text = root.joinpath("references", "cut-safety-rules.md").read_text(
            encoding="utf-8"
        )

        for text in (agent_text, rules_text):
            self.assertIn("not a rewritten compressed story", text)
            self.assertIn("exact feed line numbers", text)
            self.assertIn("exact source spans", text)
            self.assertIn("lost setup", text)
            self.assertIn("dangling reaction", text)

    def test_visual_polish_and_production_runner_keep_existing_boundaries(self) -> None:
        root = Path(__file__).resolve().parents[1]
        visual_text = root.joinpath("agents", "visual-polish.md").read_text(
            encoding="utf-8"
        )
        runner_text = root.joinpath("agents", "production-runner.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("requires an existing faithful feed", visual_text)
        self.assertIn(
            "must not remove, shorten, reorder, or rewrite source dialogue",
            visual_text,
        )
        self.assertIn("dependency checklist", runner_text)
        self.assertIn("no Canvas package", runner_text)
        self.assertIn("no storyboard folder", runner_text)
        self.assertIn("no MP4 claim", runner_text)

    def test_canonical_feed_controls_copy_pack_regeneration_for_downstream_tools(
        self,
    ) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )
        copy_format_text = root.joinpath("references", "copy-pack-format.md").read_text(
            encoding="utf-8"
        )
        cut_text = root.joinpath("agents", "cut-safety.md").read_text(encoding="utf-8")
        visual_text = root.joinpath("agents", "visual-polish.md").read_text(
            encoding="utf-8"
        )
        runner_text = root.joinpath("agents", "production-runner.md").read_text(
            encoding="utf-8"
        )

        canonical_phrases = [
            "连续投喂稿 is the canonical mother feed",
            "复制投喂包 is a derived paste wrapper",
            "Any operation that changes video line text, line numbers, or asset bindings must update the canonical continuous feed first, then re-run feed audit and regenerate copy packs",
            "Do not edit copy packs as the source of truth",
        ]

        for text in (skill_text, format_text, copy_format_text):
            for phrase in canonical_phrases:
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, text)

        for phrase in [
            "Cut-safety writes a separate risk report",
            "does not directly modify the canonical feed or copy packs",
            "If the user approves cuts, create a revised canonical feed first, then audit it and regenerate copy packs",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, cut_text)

        for phrase in [
            "Visual-polish may return notes without editing files",
            "If applying polish changes video line text, update the canonical feed first",
            "then re-run feed audit and regenerate copy packs",
            "Never patch copy packs directly",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, visual_text)

        for phrase in [
            "Production-runner writes a dependency checklist",
            "does not modify the canonical feed or copy packs",
            "Reference line ranges from the canonical feed and copy packs without changing them",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, runner_text)

    def test_image_generator_agent_is_declared_and_routed(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        agent_path = root.joinpath("agents", "image-generator.md")
        format_path = root.joinpath("references", "image-generation-format.md")
        retry_path = root.joinpath("references", "image-generation-retry-rules.md")

        self.assertTrue(agent_path.is_file())
        self.assertTrue(format_path.is_file())
        self.assertTrue(retry_path.is_file())

        route_line = next(
            line.strip()
            for line in skill_text.splitlines()
            if "生成图片" in line and "agents/image-generator.md" in line
        )
        self.assertIn("references/image-generation-format.md", route_line)
        self.assertIn("references/image-generation-retry-rules.md", route_line)
        self.assertIn("scripts/generate_images.py", route_line)

    def test_image_generator_docs_preserve_source_contract_and_manifest_boundary(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_text = root.joinpath("agents", "image-generator.md").read_text(
            encoding="utf-8"
        )
        format_text = root.joinpath(
            "references", "image-generation-format.md"
        ).read_text(encoding="utf-8")
        retry_text = root.joinpath(
            "references", "image-generation-retry-rules.md"
        ).read_text(encoding="utf-8")

        required_agent_phrases = [
            "保真契约",
            "不得由 AI 帮用户压缩",
            "image-generator only executes approved image jobs",
            "生产资产/_内部/image-manifest.json",
            "人设资产",
            "场景资产",
            "道具资产",
            "dependency waves",
            "OpenAI-compatible",
            "retry",
            "resume",
            "must not rewrite source",
        ]
        for phrase in required_agent_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agent_text)

        required_format_phrases = [
            "image-jobs.jsonl",
            "image-manifest.json",
            "image-generation-report.md",
            "stable asset name",
            "depends_on",
            "reference_images",
            "Copy packs must not invent image paths",
        ]
        for phrase in required_format_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, format_text)

        required_retry_phrases = [
            "Retryable errors",
            "Non-retryable errors",
            "exponential backoff",
            "Failed dependencies block dependent jobs",
            "Do not log API keys",
        ]
        for phrase in required_retry_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, retry_text)

    def test_image_generation_scripts_are_documented_and_no_secret_logging_is_required(
        self,
    ) -> None:
        root = Path(__file__).resolve().parents[1]
        format_text = root.joinpath(
            "references", "image-generation-format.md"
        ).read_text(encoding="utf-8")
        retry_text = root.joinpath(
            "references", "image-generation-retry-rules.md"
        ).read_text(encoding="utf-8")

        script_paths = [
            "scripts/build_image_jobs.py",
            "scripts/generate_images.py",
            "scripts/validate_image_manifest.py",
        ]

        for relative_path in script_paths:
            with self.subTest(relative_path=relative_path):
                self.assertTrue(root.joinpath(relative_path).is_file())
                self.assertIn(relative_path, format_text)

        self.assertIn("Do not log API keys", retry_text)
        self.assertIn("Failed dependencies block dependent jobs", retry_text)
        self.assertIn("resume", format_text)

    def test_copy_packager_uses_image_manifest_without_inventing_paths(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_text = root.joinpath("agents", "copy-packager.md").read_text(
            encoding="utf-8"
        )
        format_text = root.joinpath("references", "copy-pack-format.md").read_text(
            encoding="utf-8"
        )

        for text in (agent_text, format_text):
            self.assertIn("image-manifest.json", text)
            self.assertIn("Copy packs must not invent image paths", text)
            self.assertIn("需人工确认（image-generator failed or blocked）", text)

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

    def test_agent_and_reference_docs_do_not_contain_known_mojibake(self) -> None:
        root = Path(__file__).resolve().parents[1]
        checked_paths = [
            root.joinpath("SKILL.md"),
            *root.joinpath("agents").glob("*.md"),
            *root.joinpath("references").glob("*.md"),
        ]

        for path in checked_paths:
            with self.subTest(path=path.relative_to(root).as_posix()):
                self.assertNoKnownMojibake(path.read_text(encoding="utf-8"))

    def test_plan_docs_do_not_contain_known_mojibake(self) -> None:
        root = Path(__file__).resolve().parents[1]
        checked_paths = root.joinpath("docs", "superpowers").rglob("*.md")

        for path in checked_paths:
            with self.subTest(path=path.relative_to(root).as_posix()):
                self.assertNoKnownMojibake(path.read_text(encoding="utf-8"))

    def test_skill_baseline_mentions_xianjie_only_as_regression_sample(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")

        self.assertIn(
            "Use `E:\\xianjie` only as a regression sample unless the user explicitly asks to produce its chapters",
            skill_text,
        )
        self.assertIn(
            "do not generate the full five-chapter feed as part of baseline implementation",
            skill_text,
        )

    def test_workspace_storage_policy_puts_feed_text_in_production_assets(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        faithful_feed_text = root.joinpath("agents", "faithful-feed.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, faithful_feed_text):
            self.assertIn("投喂稿、source-index、asset-bible、审计报告、剪辑风险报告属于生产资产", text)
            self.assertIn("视频资产只放最终视频文件或渲染结果", text)
        self.assertIn("生产资产/source-index.md", skill_text)
        self.assertNotIn("working-directory source index", skill_text)
        self.assertNotIn("Keep the index in the working directory", skill_text)

    def test_faithful_feed_requires_index_assets_and_coverage_audit(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_text = root.joinpath("agents", "faithful-feed.md").read_text(
            encoding="utf-8"
        )

        required_phrases = [
            "formal multi-chapter output requires either a `全范围预扫` source index or an explicit full requested-scope pre-scan",
            "Formal multi-chapter output requires either a `全范围预扫` source index or an explicit full requested-scope pre-scan.",
            "private chapter beat ledger",
            "coverage audit before delivery",
            "Check `source-index` for names, aliases, event order, scene hierarchy, posture facts, and unresolved doubts.",
            "Check `asset-bible` for stable asset names, existing references, outfit variants, scene mother images, and voice roles.",
            "do not reduce coverage by reducing line count",
            "11. Do not reduce coverage by reducing line count.",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agent_text)

    def test_format_reference_declares_only_two_output_blocks(self) -> None:
        root = Path(__file__).resolve().parents[1]
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        required_phrases = [
            "Emit only these two user-facing blocks",
            "## 资产提示词",
            "## 视频投喂块",
            "one visible action target",
            "one main beat",
            "one selected-library camera tag",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, format_text)

        package_heading = format_text.index("## Package shape")
        output_paragraph = format_text.index("Emit only these two user-facing blocks")
        first_copyable_example = format_text.index("```text", package_heading)
        self.assertLess(package_heading, output_paragraph)
        self.assertLess(output_paragraph, first_copyable_example)

    def test_format_reference_video_block_example_matches_validator_header_order(self) -> None:
        root = Path(__file__).resolve().parents[1]
        format_lines = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        ).splitlines()
        header_index = format_lines.index("## 视频投喂块")

        self.assertTrue(format_lines[header_index + 1].startswith("统一要求："))

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

        for phrase in (
            "Index status:",
            "Requested range:",
            "Read range:",
            "Unread range:",
            "Evidence basis:",
            "全范围预扫",
            "局部烟测",
        ):
            self.assertIn(phrase, format_text)

    def test_source_index_agent_requires_evidence_backed_entries(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_text = root.joinpath("agents", "source-indexer.md").read_text(
            encoding="utf-8"
        )

        required_phrases = [
            "formal multi-chapter work must pre-scan the whole requested scope",
            "every merge, correction, relationship claim, reveal handling, face reference, scene reference, or reusable asset decision",
            "anonymous-to-named upgrade",
            "suspected same asset",
            "do not output a synopsis replacement",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agent_text)

    def test_source_index_format_contains_all_baseline_sections(self) -> None:
        root = Path(__file__).resolve().parents[1]
        format_text = root.joinpath("references", "source-index-format.md").read_text(
            encoding="utf-8"
        )

        required_sections = [
            "## Scope Status",
            "## Character Index",
            "## Scene Index",
            "## Asset Index",
            "## Term Index",
            "## Doubt Index",
            "## Evidence Anchors",
        ]
        required_fields = [
            "Requested range:",
            "Read range:",
            "Unread range:",
            "Evidence basis:",
            "Posture facts:",
            "Parent scene:",
            "Suspected same asset:",
            "Do not promote smoke-test assets to global final decisions.",
        ]

        for phrase in required_sections + required_fields:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, format_text)

    def test_source_index_agent_uses_readable_scope_labels(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_text = root.joinpath("agents", "source-indexer.md").read_text(
            encoding="utf-8"
        )

        required_phrases = [
            "生产资产/source-index.md",
            "全范围预扫",
            "局部烟测",
            "索引状态",
            "请求范围",
            "已阅读范围",
            "未阅读范围",
            "证据依据",
            "正式多章任务必须先预扫完整请求范围",
            "局部烟测必须显式标记已阅读范围",
            "局部烟测资产不得当作全局定稿",
            "弟子/NPC/黑衣人/侍女/守卫/路人",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agent_text)

    def test_source_index_format_uses_readable_scope_status(self) -> None:
        root = Path(__file__).resolve().parents[1]
        format_text = root.joinpath("references", "source-index-format.md").read_text(
            encoding="utf-8"
        )

        required_phrases = [
            "Index status: 全范围预扫 / 局部烟测",
            "Scope statement: 正式多章任务必须先预扫完整请求范围；局部烟测必须显式标记已阅读范围；局部烟测资产不得当作全局定稿。",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, format_text)

    def test_source_index_format_contains_no_mojibake_compatibility_anchors(self) -> None:
        root = Path(__file__).resolve().parents[1]
        format_text = root.joinpath("references", "source-index-format.md").read_text(
            encoding="utf-8"
        )

        template_start = format_text.index("```text")
        template_body_start = format_text.index("\n", template_start) + 1
        template_end = format_text.index("```", template_body_start)
        template_text = format_text[template_body_start:template_end]

        self.assertNotIn("## Compatibility Anchors", format_text)
        self.assertNoKnownMojibake(template_text)

    def test_asset_bible_agent_requires_full_scope_or_slice_labels(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_text = root.joinpath("agents", "asset-bible.md").read_text(
            encoding="utf-8"
        )

        required_phrases = [
            "final asset decisions require `全范围预扫`",
            "label every asset as slice-limited",
            "tri-view assets",
            "derived outfit/state",
            "same sect, same uniform, same gender/age band, or similar protagonist styling",
            "voice assets for speaking roles",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agent_text)

    def test_asset_bible_agent_contains_no_mojibake_compatibility_anchors(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_text = root.joinpath("agents", "asset-bible.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("## 保真契约", agent_text)
        self.assertNotIn("## Compatibility Anchors", agent_text)
        self.assertNoKnownMojibake(agent_text)

    def test_asset_bible_format_tracks_references_and_dependencies(self) -> None:
        root = Path(__file__).resolve().parents[1]
        format_text = root.joinpath("references", "asset-bible-format.md").read_text(
            encoding="utf-8"
        )

        required_phrases = [
            "## Scope Status",
            "## Character Assets",
            "Tier: 主角/高频配角 / 命名低频角色 / 群像模板 / 一次性背景人",
            "Tri-view requirement:",
            "Derived from previous asset:",
            "Reference uploads:",
            "人脸身份参考",
            "避撞脸参考",
            "同门服制参考",
            "场景母图参考",
            "## Production Dependencies",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, format_text)

    def test_asset_bible_format_keeps_compatibility_anchors_out_of_template(self) -> None:
        root = Path(__file__).resolve().parents[1]
        format_text = root.joinpath("references", "asset-bible-format.md").read_text(
            encoding="utf-8"
        )

        template_start = format_text.index("```text")
        template_body_start = format_text.index("\n", template_start) + 1
        template_end = format_text.index("```", template_body_start)
        template_text = format_text[template_body_start:template_end]

        self.assertNotIn(
            "## Compatibility Anchors (do not copy into asset-bible.md output)",
            template_text,
        )
        self.assertNoKnownMojibake(template_text)

    def test_feed_auditor_splits_script_checks_from_source_fidelity_review(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_text = root.joinpath("agents", "feed-auditor.md").read_text(
            encoding="utf-8"
        )
        checklist_text = root.joinpath("references", "audit-checklist.md").read_text(
            encoding="utf-8"
        )

        for text in (agent_text, checklist_text):
            self.assertIn("Blocking issues first", text)
            self.assertIn("file/line references", text)
            self.assertIn("script-deterministic checks", text)
            self.assertIn("human/agent source-fidelity checks", text)
            self.assertIn(
                "scope status is explicit when the artifact is a smoke test", text
            )

    def test_validate_feed_rejects_duplicate_camera_tags_and_storyboard_terms(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_feed = Path(temp_dir) / "bad-feed.md"
            bad_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。",
                        "1 日 内 大殿 林夜 坐在王座中 中景 + 平视 <固定镜头> <镜头前推> 环境音：低鸣",
                        "2 日 内 大殿 林夜 坐在王座中 中景 + 平视 <固定镜头> storyboard folder 环境音：低鸣",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "validate_feed.py"),
                    str(bad_feed),
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid camera tag count 2", result.stdout)
            self.assertIn("forbidden term `storyboard`", result.stdout)

    def test_validate_feed_rejects_repeated_same_camera_tag(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_feed = Path(temp_dir) / "bad-feed.md"
            bad_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。",
                        "1 日 内 大殿 林夜 坐在王座中 中景 + 平视 <固定镜头> <固定镜头> 环境音：低鸣",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "validate_feed.py"),
                    str(bad_feed),
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid camera tag count 2", result.stdout)

    def test_validate_feed_requires_global_requirement_immediately_after_header(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_feed = Path(temp_dir) / "bad-feed.md"
            bad_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        "这里不应该出现说明文字",
                        "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。",
                        "1 日 内 大殿 林夜 坐在王座中 中景 + 平视 <固定镜头> 环境音：低鸣",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "validate_feed.py"),
                    str(bad_feed),
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "global requirement line must immediately follow ## 视频投喂块",
                result.stdout,
            )

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
                        "3 日 内 鬼王宗宗门大殿 骨灵教老者 正面半身开口 中近景 + 平视 <镜头前推> 骨灵教老者：宗主大人。",
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

    def test_validate_feed_accepts_continuous_feed_with_marked_xiaoyunque_tags(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            good_feed = Path(temp_dir) / "good-feed.md"
            good_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。",
                        "1 日 内 鬼王宗宗门大殿 林夜 坐在黑石王座上 中景 + 平视 <固定镜头> 环境音：大殿低鸣",
                        "2 日 内 鬼王宗宗门大殿 骨灵教老者 正面半身开口 中近景 + 平视 <镜头前推> 骨灵教老者：宗主大人。",
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

    def test_validate_feed_accepts_continuous_feed_with_marked_libtv_tags(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            good_feed = Path(temp_dir) / "good-libtv-feed.md"
            good_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。",
                        "1 日 外 赛博街区 女主 站在雨夜街道中抬头看向高楼 中景 + 平视 <构变焦焦> 环境音：雨声、霓虹电流声，无对白",
                        "2 日 外 赛博街区 女主 侧身穿过湿冷街口，银色长发被风带起 中景 + 侧向空间 <滚筒旋转> 环境音：脚步溅水声，无对白",
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

    def test_validate_feed_rejects_unmarked_camera_tag(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_feed = Path(temp_dir) / "unmarked-feed.md"
            bad_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。",
                        "1 日 内 大殿 林夜 坐在王座上 中景 + 平视 固定镜头 环境音：低鸣",
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
            self.assertIn("invalid camera tag count 0", result.stdout)
            self.assertIn("camera tag must be wrapped in angle brackets: 固定镜头", result.stdout)

    def test_validate_feed_accepts_supported_aspect_ratios(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            for aspect_ratio in ("9:16", "16:9", "21:9"):
                with self.subTest(aspect_ratio=aspect_ratio):
                    feed = Path(temp_dir) / f"feed-{aspect_ratio.replace(':', '-')}.md"
                    feed.write_text(
                        "\n".join(
                            [
                                "## 视频投喂块",
                                f"统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，{aspect_ratio}。",
                                "1 日 内 大殿 林夜 坐在王座上 中景 + 平视 <固定镜头> 环境音：低鸣",
                            ]
                        ),
                        encoding="utf-8",
                    )

                    result = subprocess.run(
                        [sys.executable, str(root / "scripts" / "validate_feed.py"), str(feed)],
                        cwd=root,
                        text=True,
                        capture_output=True,
                        check=False,
                    )

                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validate_feed_rejects_unsupported_aspect_ratio(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_feed = Path(temp_dir) / "unsupported-aspect-feed.md"
            bad_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，1:1。",
                        "1 日 内 大殿 林夜 坐在王座上 中景 + 平视 <固定镜头> 环境音：低鸣",
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
            self.assertIn("global requirement line must immediately follow ## 视频投喂块", result.stdout)

    def test_validate_copy_packs_accepts_valid_five_line_pack_file(self) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_pack = Path(temp_dir) / "copy-packs.md"
            copy_pack.write_text(
                "\n".join(
                    [
                        "# Seedance Copy Packs - ch01",
                        "## Pack Settings",
                        "- Pack size: 5",
                        "### 投喂包 001｜原始行 1-5",
                        requirement,
                        "上传参考图：",
                        "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                        "- 角色1 = 林夜_黑袍造型 = 图片1",
                        "音色绑定：",
                        "- 音色1 = 林夜.mp3",
                        "1 日 内 鬼王宗宗门大殿 林夜 坐在黑石王座上 中景 + 平视 <固定镜头> 环境音：低鸣",
                        "2 日 内 鬼王宗宗门大殿 骨灵教老者 正面半身开口 中近景 + 平视 <镜头前推> 骨灵教老者：宗主大人。",
                        "3 日 内 鬼王宗宗门大殿 骨灵教老者 不改变坐姿继续说话 中近景 + 正面半身 <固定镜头> 骨灵教老者：明日一早。",
                        "4 日 内 鬼王宗宗门大殿 林夜 眼皮轻跳 近景 + 正面半身 <急速变焦> 音效：心跳一顿",
                        "5 日 内 鬼王宗宗门大殿 林夜 压住反差表情 中近景 + 正面半身 <固定镜头> 环境音：冷雾低鸣",
                        "### 投喂包 002｜原始行 6-7",
                        requirement,
                        "上传参考图：",
                        "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                        "音色绑定：",
                        "- 音色1 = 林夜.mp3",
                        "6 日 内 鬼王宗宗门大殿 林夜 抬眼看向殿中 中景 + 平视 <镜头前推> 环境音：衣袖轻响",
                        "7 日 内 鬼王宗宗门大殿 群魔 殿内众人压低视线 远景 + 两侧席位 <固定镜头> 环境音：大殿低鸣",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "validate_copy_packs.py"),
                    str(copy_pack),
                    "--pack-size",
                    "5",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Copy-pack validation passed", result.stdout)

    def test_validate_copy_packs_accepts_supported_aspect_ratios(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            for aspect_ratio in ("9:16", "16:9", "21:9"):
                with self.subTest(aspect_ratio=aspect_ratio):
                    requirement = f"统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，{aspect_ratio}。"
                    copy_pack = Path(temp_dir) / f"copy-packs-{aspect_ratio.replace(':', '-')}.md"
                    copy_pack.write_text(
                        "\n".join(
                            [
                                "# Seedance Copy Packs - ch01",
                                "## Pack Settings",
                                "- Pack size: 1",
                                f"- Aspect ratio: {aspect_ratio}",
                                "### 投喂包 001｜原始行 1-1",
                                requirement,
                                "上传参考图：",
                                "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                                "音色绑定：",
                                "- 音色1 = 林夜.mp3",
                                "1 日 内 鬼王宗宗门大殿 林夜 坐在黑石王座上 中景 + 平视 <固定镜头> 环境音：低鸣",
                            ]
                        ),
                        encoding="utf-8",
                    )

                    result = subprocess.run(
                        [
                            sys.executable,
                            str(root / "scripts" / "validate_copy_packs.py"),
                            str(copy_pack),
                            "--pack-size",
                            "1",
                        ],
                        cwd=root,
                        text=True,
                        capture_output=True,
                        check=False,
                    )

                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validate_copy_packs_rejects_missing_requirement_per_pack(self) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_pack = Path(temp_dir) / "missing-requirement-copy-packs.md"
            copy_pack.write_text(
                "\n".join(
                    [
                        "# Seedance Copy Packs - ch01",
                        "## Pack Settings",
                        "- Pack size: 2",
                        "### 投喂包 001｜原始行 1-2",
                        requirement,
                        "上传参考图：",
                        "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                        "音色绑定：",
                        "- 音色1 = 林夜.mp3",
                        "1 日 内 鬼王宗宗门大殿 林夜 坐在王座上 中景 + 平视 <固定镜头> 环境音：低鸣",
                        "2 日 内 鬼王宗宗门大殿 骨灵教老者 正面半身开口 中近景 + 平视 <镜头前推> 骨灵教老者：宗主大人。",
                        "### 投喂包 002｜原始行 3-4",
                        "上传参考图：",
                        "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                        "音色绑定：",
                        "- 音色1 = 林夜.mp3",
                        "3 日 内 鬼王宗宗门大殿 骨灵教老者 继续说话 中近景 + 正面半身 <固定镜头> 骨灵教老者：明日一早。",
                        "4 日 内 鬼王宗宗门大殿 林夜 眼皮轻跳 近景 + 正面半身 <急速变焦> 音效：心跳一顿",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "validate_copy_packs.py"),
                    str(copy_pack),
                    "--pack-size",
                    "2",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Copy-pack validation failed:", result.stdout)
            self.assertIn("pack 002 missing global requirement line", result.stdout)

    def test_validate_copy_packs_rejects_reset_duplicate_or_missing_numbers(self) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"

        def numbered_line(number: int) -> str:
            return f"{number} 日 内 鬼王宗宗门大殿 林夜 编号测试动作{number} 中景 + 平视 <固定镜头> 环境音：低鸣"

        def pack_lines(pack_index: int, start: int, end: int, numbers: list[int]) -> list[str]:
            return [
                f"### 投喂包 {pack_index:03d}｜原始行 {start}-{end}",
                requirement,
                "上传参考图：",
                "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                "音色绑定：",
                "- 音色1 = 林夜.mp3",
                *[numbered_line(number) for number in numbers],
            ]

        cases = [
            (
                "reset",
                [
                    "# Seedance Copy Packs - ch01",
                    *pack_lines(1, 1, 2, [1, 2]),
                    *pack_lines(2, 3, 4, [1, 4]),
                ],
                [
                    "heading range 3-4 does not match numbered lines 1,4",
                    "duplicate original line 1",
                    "expected original line 3, got 1",
                ],
            ),
            (
                "duplicate",
                [
                    "# Seedance Copy Packs - ch01",
                    *pack_lines(1, 1, 3, [1, 2, 2]),
                ],
                ["duplicate original line 2"],
            ),
            (
                "missing",
                [
                    "# Seedance Copy Packs - ch01",
                    *pack_lines(1, 1, 3, [1, 3]),
                ],
                ["missing original line 2"],
            ),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for case_name, lines, expected_errors in cases:
                with self.subTest(case_name=case_name):
                    copy_pack = Path(temp_dir) / f"{case_name}-copy-packs.md"
                    copy_pack.write_text("\n".join(lines), encoding="utf-8")

                    result = subprocess.run(
                        [
                            sys.executable,
                            str(root / "scripts" / "validate_copy_packs.py"),
                            str(copy_pack),
                            "--pack-size",
                            "2",
                        ],
                        cwd=root,
                        text=True,
                        capture_output=True,
                        check=False,
                    )

                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Copy-pack validation failed:", result.stdout)
                    for expected_error in expected_errors:
                        self.assertIn(expected_error, result.stdout)

    def test_validate_copy_packs_rejects_voice_binding_in_upload_block(self) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_pack = Path(temp_dir) / "voice-in-upload-copy-packs.md"
            copy_pack.write_text(
                "\n".join(
                    [
                        "# Seedance Copy Packs - ch01",
                        "### 投喂包 001｜原始行 1-1",
                        requirement,
                        "上传参考图：",
                        "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                        "- 音色1 = 林夜.mp3",
                        "音色绑定：",
                        "- 音色1 = 林夜.mp3",
                        "1 日 内 鬼王宗宗门大殿 林夜 坐在王座上 中景 + 平视 <固定镜头> 环境音：低鸣",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "validate_copy_packs.py"),
                    str(copy_pack),
                    "--pack-size",
                    "5",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("voice binding belongs under 音色绑定", result.stdout)

    def test_validate_copy_packs_compares_against_source_feed_when_provided(
        self,
    ) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"
        source_line_1 = "1 日 内 鬼王宗宗门大殿 林夜 坐在王座上 中景 + 平视 <固定镜头> 环境音：低鸣"
        source_line_2 = "2 日 内 鬼王宗宗门大殿 骨灵教老者 正面半身开口 中近景 + 平视 <镜头前推> 骨灵教老者：宗主大人。"
        copied_line_2 = "2 日 内 鬼王宗宗门大殿 骨灵教老者 被改写成错误动作 中近景 + 平视 <镜头前推> 骨灵教老者：宗主大人。"

        with tempfile.TemporaryDirectory() as temp_dir:
            source_feed = Path(temp_dir) / "source-feed.md"
            source_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        requirement,
                        source_line_1,
                        source_line_2,
                    ]
                ),
                encoding="utf-8",
            )
            copy_pack = Path(temp_dir) / "copy-packs.md"
            copy_pack.write_text(
                "\n".join(
                    [
                        "# Seedance Copy Packs - ch01",
                        "### 投喂包 001｜原始行 1-2",
                        requirement,
                        "上传参考图：",
                        "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                        "音色绑定：",
                        "- 音色1 = 林夜.mp3",
                        source_line_1,
                        copied_line_2,
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "validate_copy_packs.py"),
                    str(copy_pack),
                    "--source-feed",
                    str(source_feed),
                    "--pack-size",
                    "2",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("copied line 2 differs from source feed", result.stdout)

    def test_validate_copy_packs_source_feed_rejects_missing_copied_line(self) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"
        source_line_1 = "1 日 内 鬼王宗宗门大殿 林夜 坐在王座上 中景 + 平视 <固定镜头> 环境音：低鸣"
        source_line_2 = "2 日 内 鬼王宗宗门大殿 骨灵教老者 正面半身开口 中近景 + 平视 <镜头前推> 骨灵教老者：宗主大人。"

        with tempfile.TemporaryDirectory() as temp_dir:
            source_feed = Path(temp_dir) / "source-feed.md"
            source_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        requirement,
                        source_line_1,
                        source_line_2,
                    ]
                ),
                encoding="utf-8",
            )
            copy_pack = Path(temp_dir) / "copy-packs.md"
            copy_pack.write_text(
                "\n".join(
                    [
                        "# Seedance Copy Packs - ch01",
                        "### 投喂包 001｜原始行 1-1",
                        requirement,
                        "上传参考图：",
                        "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                        "音色绑定：",
                        "- 音色1 = 林夜.mp3",
                        source_line_1,
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "validate_copy_packs.py"),
                    str(copy_pack),
                    "--source-feed",
                    str(source_feed),
                    "--pack-size",
                    "5",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("copied line numbers do not match source feed", result.stdout)

    def test_validate_copy_packs_rejects_legacy_group_and_workflow_terms(self) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_pack = Path(temp_dir) / "legacy-copy-packs.md"
            copy_pack.write_text(
                "\n".join(
                    [
                        "# Seedance Copy Packs - ch01",
                        "### 第1组",
                        "### 投喂包 001｜原始行 1-2",
                        requirement,
                        "上传参考图：",
                        "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                        "音色绑定：",
                        "- 音色1 = 林夜.mp3",
                        "segment S01 15秒 Canvas MP4 首帧 尾帧 续接 承接",
                        "1 日 内 鬼王宗宗门大殿 林夜 坐在王座上 中景 + 平视 <固定镜头> 环境音：低鸣",
                        "2 日 内 鬼王宗宗门大殿 骨灵教老者 正面半身开口 中近景 + 平视 <镜头前推> 骨灵教老者：宗主大人。",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "validate_copy_packs.py"),
                    str(copy_pack),
                    "--pack-size",
                    "2",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("group marker is not allowed", result.stdout)
            self.assertIn("forbidden term `segment`", result.stdout)
            self.assertIn("forbidden term `S01`", result.stdout)
            self.assertIn("forbidden term `Canvas`", result.stdout)
            self.assertIn("forbidden term `MP4`", result.stdout)
            self.assertIn("forbidden term `首帧`", result.stdout)
            self.assertIn("forbidden term `尾帧`", result.stdout)
            self.assertIn("forbidden term `续接`", result.stdout)
            self.assertIn("forbidden term `承接`", result.stdout)

    def test_validate_copy_packs_rejects_numbered_line_outside_pack(self) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"
        copied_line = "1 日 内 鬼王宗宗门大殿 林夜 坐在王座上 中景 + 平视 <固定镜头> 环境音：低鸣"

        with tempfile.TemporaryDirectory() as temp_dir:
            copy_pack = Path(temp_dir) / "outside-line-copy-packs.md"
            copy_pack.write_text(
                "\n".join(
                    [
                        "# Seedance Copy Packs - ch01",
                        copied_line,
                        "### 投喂包 001｜原始行 1-1",
                        requirement,
                        "上传参考图：",
                        "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                        "音色绑定：",
                        "- 音色1 = 林夜.mp3",
                        copied_line,
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "validate_copy_packs.py"),
                    str(copy_pack),
                    "--pack-size",
                    "5",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("numbered line outside copy pack", result.stdout)

    def test_validate_copy_packs_rejects_voice_binding_after_blank_upload_line(self) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"

        with tempfile.TemporaryDirectory() as temp_dir:
            copy_pack = Path(temp_dir) / "voice-after-blank-copy-packs.md"
            copy_pack.write_text(
                "\n".join(
                    [
                        "# Seedance Copy Packs - ch01",
                        "### 投喂包 001｜原始行 1-1",
                        requirement,
                        "上传参考图：",
                        "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                        "",
                        "- 音色1 = 林夜.mp3",
                        "1 日 内 鬼王宗宗门大殿 林夜 坐在王座上 中景 + 平视 <固定镜头> 环境音：低鸣",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "validate_copy_packs.py"),
                    str(copy_pack),
                    "--pack-size",
                    "5",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("voice binding belongs under 音色绑定", result.stdout)

    def test_validate_copy_packs_rejects_audio_file_in_upload_block(self) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"

        with tempfile.TemporaryDirectory() as temp_dir:
            copy_pack = Path(temp_dir) / "audio-file-upload-copy-packs.md"
            copy_pack.write_text(
                "\n".join(
                    [
                        "# Seedance Copy Packs - ch01",
                        "### 投喂包 001｜原始行 1-1",
                        requirement,
                        "上传参考图：",
                        "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                        "- 林夜.mp3",
                        "1 日 内 鬼王宗宗门大殿 林夜 坐在王座上 中景 + 平视 <固定镜头> 环境音：低鸣",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "validate_copy_packs.py"),
                    str(copy_pack),
                    "--pack-size",
                    "5",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("voice binding belongs under 音色绑定", result.stdout)

    def test_validate_feed_rejects_missing_global_requirement_and_forbidden_terms(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_feed = Path(temp_dir) / "legacy-feed.md"
            bad_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        "segment S01",
                        "1 日 内 鬼王宗宗门大殿 林夜 首帧坐在黑石王座上 中景 + 平视 <固定镜头> 环境音：大殿低鸣",
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

    def test_validate_feed_rejects_legacy_mojibake_workflow_terms(self) -> None:
        root = Path(__file__).resolve().parents[1]
        legacy_first_frame = "首帧".encode("utf-8").decode("gbk", errors="replace")
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_feed = Path(temp_dir) / "legacy-mojibake-feed.md"
            bad_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。",
                        f"1 日 内 鬼王宗宗门大殿 林夜 {legacy_first_frame}坐在黑石王座上 中景 + 平视 <固定镜头> 环境音：大殿低鸣",
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
            self.assertIn(f"forbidden term `{legacy_first_frame}`", result.stdout)

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

    def test_single_speaker_dialogue_avoids_named_background_characters(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )

        for text in (skill_text, format_text):
            self.assertIn("单人对白镜头不要点名另一个重要角色做后景", text)
            self.assertIn("blurred pillars, seat edge, cold fog, lamps, or robe details", text)

        self.assertIn("画面只显示说话人", format_text)
        self.assertIn("后景虚化暗柱和席位边缘", format_text)
        self.assertNotIn("背景保留林夜所在上首方向", format_text)
        self.assertNotIn("林夜在王座方向眼皮轻跳", format_text)

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

        self.assertIn("Start `## 视频投喂块` with the selected-ratio global `统一要求` line", skill_text)
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


    def test_commercial_upgrade_identity_period_reference_is_routed(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_text = root.joinpath("agents", "source-indexer.md").read_text(
            encoding="utf-8"
        )
        format_text = root.joinpath("references", "source-index-format.md").read_text(
            encoding="utf-8"
        )
        reference_path = root.joinpath("references", "identity-period-rules.md")

        self.assertTrue(reference_path.is_file())
        reference_text = reference_path.read_text(encoding="utf-8")
        self.assertIn("references/identity-period-rules.md", agent_text)

        agent_phrases = [
            "canonical source name",
            "standard-name basis",
            "alias mapping",
            "period/state trigger",
            "period/state decisions are slice-limited",
            "evidence anchor",
        ]
        format_phrases = [
            "Standard name basis:",
            "Alias evidence:",
            "Period/state variants:",
            "Period/state trigger:",
            "Slice limitation:",
        ]
        reference_phrases = [
            "Canonical name is an evidence-backed source identity",
            "Aliases are evidence, not production names",
            "Generic-role upgrade",
            "Role tier",
            "first-person labels",
            "Period/state trigger",
            "Smoke-test limitation",
        ]

        for phrase in agent_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agent_text)
        for phrase in format_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, format_text)
        for phrase in reference_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, reference_text)

    def test_commercial_upgrade_asset_continuity_reference_is_routed(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_text = root.joinpath("agents", "asset-bible.md").read_text(
            encoding="utf-8"
        )
        format_text = root.joinpath("references", "asset-bible-format.md").read_text(
            encoding="utf-8"
        )
        reference_path = root.joinpath("references", "asset-continuity-rules.md")

        self.assertTrue(reference_path.is_file())
        reference_text = reference_path.read_text(encoding="utf-8")
        self.assertIn("references/asset-continuity-rules.md", agent_text)

        agent_phrases = [
            "prop/interface double gate",
            "both value and dependency",
            "character variant matrix",
            "derived variant",
            "face/identity reference",
            "scene mother reference",
            "similar-character separation",
            "voice asset trigger",
        ]
        format_phrases = [
            "Canonical source identity:",
            "Value gate:",
            "Dependency gate:",
            "Character variant matrix:",
            "Variant type:",
            "Face/identity reference:",
            "Parent reference purpose:",
            "Scene mother reference:",
            "Voice asset trigger:",
        ]
        reference_phrases = [
            "Character variant matrix",
            "Prop/interface double gate",
            "both value and dependency",
            "Scene mother and sub-scene dependencies",
            "Reference purpose labels",
        ]

        for phrase in agent_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agent_text)
        for phrase in format_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, format_text)
        for phrase in reference_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, reference_text)

    def test_prop_assets_default_to_single_subject_and_require_labeled_triviews(
        self,
    ) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        agent_text = root.joinpath("agents", "asset-bible.md").read_text(
            encoding="utf-8"
        )
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )
        bible_format_text = root.joinpath("references", "asset-bible-format.md").read_text(
            encoding="utf-8"
        )
        continuity_text = root.joinpath("references", "asset-continuity-rules.md").read_text(
            encoding="utf-8"
        )

        required_phrases = [
            "道具默认生成单体参考图",
            "只生成一个完整主体",
            "生产需要三视图的道具必须显式标注正面、背面、侧面",
            "手机等需要前后侧信息的道具可以使用道具三视图",
            "不要把普通一次性道具升级成三视图",
        ]

        for text in (skill_text, agent_text, format_text, continuity_text):
            for phrase in required_phrases:
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, text)

        for phrase in [
            "View requirement: single-subject / prop tri-view",
            "Required labeled views: 正面 / 背面 / 侧面",
            "Front/back/side notes:",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, bible_format_text)

    def test_commercial_upgrade_feed_alignment_reference_is_routed(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_text = root.joinpath("agents", "faithful-feed.md").read_text(
            encoding="utf-8"
        )
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )
        reference_path = root.joinpath("references", "feed-alignment-rules.md")

        self.assertTrue(reference_path.is_file())
        reference_text = reference_path.read_text(encoding="utf-8")
        self.assertIn("references/feed-alignment-rules.md", agent_text)

        agent_phrases = [
            "source-span alignment",
            "private line/span plan",
            "local continuity check",
            "previous visible state",
            "speaker as the primary subject",
            "Do not import fixed-second timelines",
        ]
        reference_phrases = [
            "Source-span alignment",
            "Private line/span plan",
            "Coverage ledger",
            "Local continuity check",
            "Dialogue alignment",
            "Do not import fixed-second timelines",
        ]
        format_phrases = [
            "source-span alignment",
            "local continuity check",
            "previous visible state",
        ]

        for phrase in agent_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agent_text)
        for phrase in reference_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, reference_text)
        for phrase in format_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, format_text)

    def test_commercial_upgrade_physicalization_reference_is_routed(self) -> None:
        root = Path(__file__).resolve().parents[1]
        visual_text = root.joinpath("agents", "visual-polish.md").read_text(
            encoding="utf-8"
        )
        feed_text = root.joinpath("agents", "faithful-feed.md").read_text(
            encoding="utf-8"
        )
        reference_path = root.joinpath("references", "source-safe-physicalization.md")

        self.assertTrue(reference_path.is_file())
        reference_text = reference_path.read_text(encoding="utf-8")
        self.assertIn("references/source-safe-physicalization.md", visual_text)

        required_phrases = [
            "source-safe physicalization",
            "main motion requires source support",
            "secondary animation must be consequence",
            "facial micro-performance",
            "breath/cloth/hair/environment",
            "unsafe motion escalation",
            "must not add standing, walking, kneeling, bowing, weapon drawing, attacks, prop raising, prop putting away, seat changes, or exits",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, visual_text)
                self.assertIn(phrase, reference_text)

        self.assertIn("source-safe physicalization", feed_text)

    def test_commercial_upgrade_audit_reference_is_routed(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_text = root.joinpath("agents", "feed-auditor.md").read_text(
            encoding="utf-8"
        )
        checklist_text = root.joinpath("references", "audit-checklist.md").read_text(
            encoding="utf-8"
        )
        reference_path = root.joinpath("references", "commercial-upgrade-audit.md")

        self.assertTrue(reference_path.is_file())
        reference_text = reference_path.read_text(encoding="utf-8")
        self.assertIn("references/commercial-upgrade-audit.md", agent_text)

        required_phrases = [
            "commercial-upgrade audit",
            "identity drift",
            "standard-name drift",
            "period/state drift",
            "source-span coverage",
            "local continuity",
            "physicalization safety",
            "prompt contamination",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agent_text)
                self.assertIn(phrase, checklist_text)
                self.assertIn(phrase, reference_text)

    def test_skill_docs_do_not_copy_commercial_prompt_contamination_terms(self) -> None:
        root = Path(__file__).resolve().parents[1]
        checked_paths = [
            root.joinpath("SKILL.md"),
            *root.joinpath("agents").glob("*.md"),
            *root.joinpath("references").glob("*.md"),
        ]
        contamination_terms = [
            "隐藏" + "游戏",
            "Prompt " + "Injection",
            "D" + "ALL",
            "异常" + "指令",
            "欢迎" + "参加",
        ]

        for path in checked_paths:
            text = path.read_text(encoding="utf-8")
            for term in contamination_terms:
                with self.subTest(path=path.relative_to(root).as_posix(), term=term):
                    self.assertNotIn(term, text)


if __name__ == "__main__":
    unittest.main()

