import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import generate_images as generate_images_module
from scripts.build_storyboard_jobs import build_storyboard_jobs
from scripts.generate_images import (
    ImageGenerationConfig,
    NonRetryableProviderError,
    openai_compatible_provider,
)
from scripts.generate_storyboards import (
    manifest_by_name,
    run_storyboard_generation,
    run_storyboard_job_with_retry,
    should_skip_storyboard_job,
    storyboard_output_path,
)
from scripts.storyboard_generation_core import (
    FULL_GROUP_INSTRUCTION,
    PARTIAL_GROUP_INSTRUCTION_TEMPLATE,
    STORYBOARD_OUTPUT_DIR,
    StoryboardGenerationError,
    StoryboardJob,
    StoryboardReference,
    extract_numbered_feed_lines,
    load_storyboard_jobs_jsonl,
    prompt_hash,
    validate_storyboard_jobs,
    write_storyboard_jobs_jsonl,
)
from scripts.validate_storyboard_manifest import validate_storyboard_manifest


class StoryboardCoreTests(unittest.TestCase):
    def make_job(self, name: str = "storyboard-001-lines-001-025") -> StoryboardJob:
        return StoryboardJob(
            job_id=name,
            group_index=1,
            line_start=1,
            line_end=25,
            line_count=25,
            source_feed="生产资产/feed.md",
            prompt="1 line\n生成5*5的分镜图，分镜图上不允许有台词。",
            output_dir=STORYBOARD_OUTPUT_DIR,
            output_file="storyboard-contact-sheet-001-lines-001-025.png",
            reference_images=[
                StoryboardReference(
                    asset_name="林夜_黑袍造型",
                    path="人设资产/林夜_黑袍造型.png",
                    purpose="人物身份参考",
                )
            ],
            provider="openai-compatible",
            model="gpt-image-2",
            size="16:9",
            status="pending",
        )

    def test_extract_numbered_feed_lines_preserves_original_text(self) -> None:
        text = "\n".join(
            [
                "# Feed",
                "## 视频投喂块",
                "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。",
                "1 日 内 大殿 林夜 坐着 <固定镜头> 无对白",
                "2 日 内 大殿 林夜 抬眼 <固定镜头> 林夜：来了？",
            ]
        )

        lines = extract_numbered_feed_lines(text)

        self.assertEqual(
            lines,
            [
                (1, "1 日 内 大殿 林夜 坐着 <固定镜头> 无对白"),
                (2, "2 日 内 大殿 林夜 抬眼 <固定镜头> 林夜：来了？"),
            ],
        )

    def test_validate_storyboard_jobs_rejects_non_storyboard_output_dir(self) -> None:
        job = self.make_job()
        job.output_dir = "生产资产"

        with self.assertRaises(StoryboardGenerationError) as context:
            validate_storyboard_jobs([job])

        self.assertIn("output_dir must be 分镜资产", str(context.exception))

    def test_validate_storyboard_jobs_rejects_missing_reference_fields(self) -> None:
        job = self.make_job()
        job.reference_images[0].path = ""

        with self.assertRaises(StoryboardGenerationError) as context:
            validate_storyboard_jobs([job])

        self.assertIn("reference path is required", str(context.exception))

    def test_validate_storyboard_jobs_requires_full_group_instruction(self) -> None:
        job = self.make_job()
        job.prompt = "1 line"

        with self.assertRaises(StoryboardGenerationError) as context:
            validate_storyboard_jobs([job])

        self.assertIn("missing full 25-line instruction", str(context.exception))

    def test_validate_storyboard_jobs_requires_partial_group_instruction(self) -> None:
        job = self.make_job("storyboard-002-lines-026-028")
        job.group_index = 2
        job.line_start = 26
        job.line_end = 28
        job.line_count = 3
        job.output_file = "storyboard-contact-sheet-002-lines-026-028.png"
        job.prompt = "26 line\n27 line\n28 line\n生成5*5的分镜图，分镜图上不允许有台词。"

        with self.assertRaises(StoryboardGenerationError) as context:
            validate_storyboard_jobs([job])

        self.assertIn("missing partial 3-panel instruction", str(context.exception))

    def test_storyboard_jobs_round_trip_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "storyboard-jobs.jsonl"
            job = self.make_job()

            write_storyboard_jobs_jsonl(path, [job])
            loaded = load_storyboard_jobs_jsonl(path)

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].job_id, job.job_id)
        self.assertEqual(loaded[0].reference_images[0].asset_name, "林夜_黑袍造型")
        self.assertEqual(prompt_hash("abc"), prompt_hash("abc"))
        self.assertTrue(prompt_hash("abc").startswith("sha256:"))

    def test_validate_storyboard_jobs_rejects_empty_job_list(self) -> None:
        with self.assertRaises(StoryboardGenerationError) as context:
            validate_storyboard_jobs([])

        self.assertIn("storyboard jobs must not be empty", str(context.exception))


class StoryboardJobBuilderTests(unittest.TestCase):
    def write_feed(self, root: Path, count: int) -> Path:
        feed = root / "生产资产" / "seedance-all-reference-feed-production-ch01-03.md"
        feed.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Feed",
            "## 视频投喂块",
            "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。",
        ]
        for number in range(1, count + 1):
            if number % 2:
                lines.append(
                    f"{number} 日 内 鬼王宗宗门大殿 林夜 坐在王座上 <固定镜头> 无对白"
                )
            else:
                lines.append(
                    f"{number} 日 内 鬼王宗宗门大殿 骨灵教老者 坐在左席 <固定镜头> 骨灵教老者：宗主大人。"
                )
        feed.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return feed

    def write_manifest(self, root: Path) -> Path:
        manifest_path = root / "生产资产" / "_内部" / "image-manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        assets = [
            ("鬼王宗宗门大殿_母图", "scene", "场景资产/鬼王宗宗门大殿_母图.png"),
            ("林夜_黑袍造型", "character", "人设资产/林夜_黑袍造型.png"),
            ("骨灵教老者_骨纹法袍造型", "character", "人设资产/骨灵教老者_骨纹法袍造型.png"),
        ]
        for _, _, relative_path in assets:
            image_path = root / relative_path
            image_path.parent.mkdir(parents=True, exist_ok=True)
            image_path.write_bytes(b"image")
        manifest_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "provider": "openai-compatible",
                    "assets": [
                        {
                            "asset_name": name,
                            "asset_type": asset_type,
                            "path": path,
                            "status": "done",
                        }
                        for name, asset_type, path in assets
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return manifest_path

    def write_copy_packs(self, root: Path) -> Path:
        copy_pack = root / "生产资产" / "seedance-copy-packs-production-ch01-03.md"
        copy_pack.write_text(
            "\n".join(
                [
                    "# Copy Packs",
                    "### 投喂包 001｜原始行 1-25",
                    "上传参考图：",
                    "- 场景1 = 鬼王宗宗门大殿_母图 = 场景资产/鬼王宗宗门大殿_母图.png",
                    "- 角色1 = 林夜_黑袍造型 = 人设资产/林夜_黑袍造型.png",
                    "- 角色2 = 骨灵教老者_骨纹法袍造型 = 人设资产/骨灵教老者_骨纹法袍造型.png",
                    "### 投喂包 002｜原始行 26-28",
                    "上传参考图：",
                    "- 场景1 = 鬼王宗宗门大殿_母图 = 场景资产/鬼王宗宗门大殿_母图.png",
                    "- 角色1 = 林夜_黑袍造型 = 人设资产/林夜_黑袍造型.png",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return copy_pack

    def write_asset_bible(self, root: Path) -> Path:
        asset_bible = root / "生产资产" / "_内部" / "asset-bible.md"
        asset_bible.parent.mkdir(parents=True, exist_ok=True)
        asset_bible.write_text(
            "\n".join(
                [
                    "# Asset Bible",
                    "",
                    "## Scene Assets",
                    "- Asset name: 鬼王宗宗门大殿_母图",
                    "  - Asset class: scene",
                    "",
                    "## Character Assets",
                    "- Asset name: 林夜_黑袍造型",
                    "  - Asset class: character",
                    "- Asset name: 骨灵教老者_骨纹法袍造型",
                    "  - Asset class: character",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return asset_bible

    def test_build_storyboard_jobs_groups_feed_into_25_line_batches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feed = self.write_feed(root, 28)
            manifest = self.write_manifest(root)
            copy_packs = self.write_copy_packs(root)

            jobs = build_storyboard_jobs(
                feed_path=feed,
                manifest_path=manifest,
                workspace=root,
                copy_packs_path=copy_packs,
                model="gpt-image-2",
                size="16:9",
            )

        self.assertEqual(len(jobs), 2)
        self.assertEqual((jobs[0].line_start, jobs[0].line_end, jobs[0].line_count), (1, 25, 25))
        self.assertIn(FULL_GROUP_INSTRUCTION, jobs[0].prompt)
        self.assertEqual((jobs[1].line_start, jobs[1].line_end, jobs[1].line_count), (26, 28, 3))
        self.assertIn(PARTIAL_GROUP_INSTRUCTION_TEMPLATE.format(count=3), jobs[1].prompt)
        self.assertNotIn(FULL_GROUP_INSTRUCTION, jobs[1].prompt)
        self.assertEqual(jobs[0].output_dir, "分镜资产")
        self.assertEqual(len(jobs[0].reference_images), 3)

    def test_build_storyboard_jobs_rejects_failed_manifest_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feed = self.write_feed(root, 1)
            manifest = self.write_manifest(root)
            copy_packs = self.write_copy_packs(root)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["assets"][0]["status"] = "failed"
            data["assets"][0]["last_error"] = "provider rejected request"
            manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            with self.assertRaises(StoryboardGenerationError) as context:
                build_storyboard_jobs(
                    feed_path=feed,
                    manifest_path=manifest,
                    workspace=root,
                    copy_packs_path=copy_packs,
                    model="gpt-image-2",
                    size="16:9",
                )

        self.assertIn("not done", str(context.exception))

    def test_build_storyboard_jobs_rejects_missing_reference_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feed = self.write_feed(root, 1)
            manifest = self.write_manifest(root)
            copy_packs = self.write_copy_packs(root)
            (root / "场景资产" / "鬼王宗宗门大殿_母图.png").unlink()

            with self.assertRaises(StoryboardGenerationError) as context:
                build_storyboard_jobs(
                    feed_path=feed,
                    manifest_path=manifest,
                    workspace=root,
                    copy_packs_path=copy_packs,
                    model="gpt-image-2",
                    size="16:9",
                )

        self.assertIn("missing local file", str(context.exception))

    def test_build_storyboard_jobs_uses_asset_bible_when_copy_packs_are_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feed = self.write_feed(root, 2)
            manifest = self.write_manifest(root)
            asset_bible = self.write_asset_bible(root)

            jobs = build_storyboard_jobs(
                feed_path=feed,
                manifest_path=manifest,
                workspace=root,
                asset_bible_path=asset_bible,
                model="gpt-image-2",
                size="16:9",
            )

        self.assertEqual(len(jobs), 1)
        self.assertEqual(
            [reference.asset_name for reference in jobs[0].reference_images],
            ["鬼王宗宗门大殿_母图", "林夜_黑袍造型", "骨灵教老者_骨纹法袍造型"],
        )


class StoryboardRunnerTests(unittest.TestCase):
    def make_job(self) -> StoryboardJob:
        return StoryboardJob(
            job_id="storyboard-001-lines-001-025",
            group_index=1,
            line_start=1,
            line_end=25,
            line_count=25,
            source_feed="生产资产/feed.md",
            prompt="1 line\n生成5*5的分镜图，分镜图上不允许有台词。",
            output_dir="分镜资产",
            output_file="storyboard-contact-sheet-001-lines-001-025.png",
            reference_images=[
                StoryboardReference(
                    asset_name="林夜_黑袍造型",
                    path="人设资产/林夜_黑袍造型.png",
                    purpose="人物身份参考",
                )
            ],
            provider="openai-compatible",
            model="gpt-image-2",
            size="16:9",
            status="pending",
        )

    def make_config(self) -> ImageGenerationConfig:
        return ImageGenerationConfig(
            base_url="https://provider.example",
            api_key="sk-test-secret-1234567890",
            model="gpt-image-2",
            size="16:9",
            timeout_seconds=30.0,
            max_retries=2,
            retry_base_seconds=0.0,
            retry_max_seconds=0.0,
            concurrency=1,
            reference_mode="data-url",
        )

    def fake_image_response(self) -> object:
        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def read(self) -> bytes:
                return b'{"data":[{"b64_json":"aW1hZ2U="}]}'

        return FakeResponse()

    def test_storyboard_output_path_allows_only_storyboard_dir(self) -> None:
        job = self.make_job()
        with tempfile.TemporaryDirectory() as temp_dir:
            path = storyboard_output_path(Path(temp_dir), job)

        self.assertEqual(path.name, job.output_file)

        job.output_dir = "生产资产"
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(NonRetryableProviderError) as context:
                storyboard_output_path(Path(temp_dir), job)

        self.assertIn("output_dir must be 分镜资产", str(context.exception))

    def test_run_storyboard_job_writes_image_and_manifest_result(self) -> None:
        job = self.make_job()
        config = self.make_config()

        def provider(current_job: StoryboardJob, current_config: ImageGenerationConfig) -> bytes:
            self.assertIs(current_job, job)
            self.assertIs(current_config, config)
            return b"storyboard-image"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reference_path = root / "人设资产" / "林夜_黑袍造型.png"
            reference_path.parent.mkdir(parents=True, exist_ok=True)
            reference_path.write_bytes(b"reference")
            config.reference_workspace = str(root)

            result = run_storyboard_job_with_retry(job, config, root, provider=provider)

            self.assertEqual(result["status"], "done")
            self.assertEqual(result["path"], "分镜资产/storyboard-contact-sheet-001-lines-001-025.png")
            self.assertEqual((root / job.output_path).read_bytes(), b"storyboard-image")
            self.assertEqual(result["prompt_hash"], prompt_hash(job.prompt))
            self.assertNotIn(config.api_key, json.dumps(result, ensure_ascii=False))

    def test_run_storyboard_job_uses_data_url_references_with_provider(self) -> None:
        job = self.make_job()
        config = self.make_config()
        captured_payloads: list[dict[str, object]] = []

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reference_path = root / "人设资产" / "林夜_黑袍造型.png"
            reference_path.parent.mkdir(parents=True, exist_ok=True)
            reference_path.write_bytes(b"reference")
            config.reference_workspace = str(root)

            def fake_urlopen(request: object, timeout: float) -> object:
                self.assertEqual(timeout, config.timeout_seconds)
                captured_payloads.append(json.loads(getattr(request, "data").decode("utf-8")))
                return self.fake_image_response()

            with patch.object(
                generate_images_module.urllib.request,
                "urlopen",
                side_effect=fake_urlopen,
            ):
                result = run_storyboard_job_with_retry(
                    job,
                    config,
                    root,
                    provider=openai_compatible_provider,
                )

        self.assertEqual(result["status"], "done")
        self.assertEqual(
            captured_payloads[0]["reference_images"],
            [
                {
                    "asset_name": "林夜_黑袍造型",
                    "purpose": "人物身份参考",
                    "path": "人设资产/林夜_黑袍造型.png",
                    "data_url": "data:image/png;base64,cmVmZXJlbmNl",
                }
            ],
        )

    def test_run_storyboard_job_requires_data_url_reference_mode(self) -> None:
        job = self.make_job()
        config = self.make_config()
        config.reference_mode = "unsupported"
        provider_called = False

        def provider(current_job: StoryboardJob, current_config: ImageGenerationConfig) -> bytes:
            nonlocal provider_called
            provider_called = True
            return b"image"

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_storyboard_job_with_retry(job, config, Path(temp_dir), provider=provider)

        self.assertFalse(provider_called)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["attempts"], 0)
        self.assertIn("SOURCE_TRUE_IMAGE_REFERENCE_MODE=data-url", result["last_error"])

    def test_run_storyboard_generation_requires_data_url_reference_mode_before_jobs(
        self,
    ) -> None:
        job = self.make_job()
        config = self.make_config()
        config.reference_mode = "unsupported"
        provider_called = False

        def provider(current_job: StoryboardJob, current_config: ImageGenerationConfig) -> bytes:
            nonlocal provider_called
            provider_called = True
            return b"image"

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(StoryboardGenerationError) as context:
                run_storyboard_generation(
                    [job],
                    config,
                    Path(temp_dir),
                    provider=provider,
                )

        self.assertFalse(provider_called)
        self.assertIn("SOURCE_TRUE_IMAGE_REFERENCE_MODE=data-url", str(context.exception))

    def test_run_storyboard_generation_resume_skips_matching_done_output(self) -> None:
        job = self.make_job()
        config = self.make_config()
        existing_manifest = {
            "version": 1,
            "provider": "openai-compatible",
            "assets": [
                {
                    "asset_name": job.job_id,
                    "path": job.output_path.as_posix(),
                    "status": "done",
                    "prompt_hash": prompt_hash(job.prompt),
                    "model": job.model,
                    "size": job.size,
                    "attempts": 1,
                    "references": [reference.to_dict() for reference in job.reference_images],
                }
            ],
        }
        provider_called = False

        def provider(current_job: StoryboardJob, current_config: ImageGenerationConfig) -> bytes:
            nonlocal provider_called
            provider_called = True
            return b"new-image"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / job.output_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"existing-image")
            manifest = run_storyboard_generation(
                [job],
                config,
                root,
                provider=provider,
                existing_manifest=existing_manifest,
                resume=True,
            )
            can_skip = should_skip_storyboard_job(
                job,
                config,
                manifest_by_name(existing_manifest),
                root,
                True,
            )

        self.assertFalse(provider_called)
        self.assertEqual(manifest["assets"][0]["status"], "done")
        self.assertEqual(manifest["assets"][0]["attempts"], 1)
        self.assertTrue(can_skip)


class StoryboardManifestValidatorTests(unittest.TestCase):
    def make_job(self) -> StoryboardJob:
        return StoryboardRunnerTests().make_job()

    def test_validate_storyboard_manifest_accepts_done_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            job = self.make_job()
            output = root / job.output_path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"image")
            manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [
                    {
                        "asset_name": job.job_id,
                        "asset_type": "storyboard_contact_sheet",
                        "path": job.output_path.as_posix(),
                        "status": "done",
                        "prompt_hash": prompt_hash(job.prompt),
                        "model": job.model,
                        "size": job.size,
                        "line_start": job.line_start,
                        "line_end": job.line_end,
                        "line_count": job.line_count,
                        "source_feed": job.source_feed,
                        "references": [reference.to_dict() for reference in job.reference_images],
                    }
                ],
            }

            errors = validate_storyboard_manifest(manifest, [job], root)

        self.assertEqual(errors, [])

    def test_validate_storyboard_manifest_rejects_production_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            job = self.make_job()
            manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [
                    {
                        "asset_name": job.job_id,
                        "asset_type": "storyboard_contact_sheet",
                        "path": "生产资产/storyboard.png",
                        "status": "done",
                    }
                ],
            }

            errors = validate_storyboard_manifest(manifest, [job], root)

        self.assertTrue(any("path must start with 分镜资产" in error for error in errors))

    def test_validate_storyboard_manifest_rejects_missing_done_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            job = self.make_job()
            manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [
                    {
                        "asset_name": job.job_id,
                        "asset_type": "storyboard_contact_sheet",
                        "path": job.output_path.as_posix(),
                        "status": "done",
                    }
                ],
            }

            errors = validate_storyboard_manifest(manifest, [job], root)

        self.assertTrue(any("done storyboard missing local file" in error for error in errors))

    def test_validate_storyboard_manifest_requires_resume_critical_fields_for_done_assets(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            job = self.make_job()
            output = root / job.output_path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"image")
            manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [
                    {
                        "asset_name": job.job_id,
                        "asset_type": "storyboard_contact_sheet",
                        "path": job.output_path.as_posix(),
                        "status": "done",
                    }
                ],
            }

            errors = validate_storyboard_manifest(manifest, [job], root)

        message = "; ".join(errors)
        self.assertIn("prompt_hash is required", message)
        self.assertIn("model is required", message)
        self.assertIn("size is required", message)
        self.assertIn("line_start is required", message)
        self.assertIn("line_end is required", message)
        self.assertIn("line_count is required", message)
        self.assertIn("source_feed is required", message)
        self.assertIn("references is required", message)

    def test_validate_storyboard_manifest_rejects_missing_job_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            errors = validate_storyboard_manifest(
                {
                    "version": 1,
                    "provider": "openai-compatible",
                    "assets": [
                        {
                            "asset_name": "storyboard-999-lines-999-999",
                            "asset_type": "storyboard_contact_sheet",
                            "path": "分镜资产/other.png",
                            "status": "failed",
                            "last_error": "not generated",
                        }
                    ],
                },
                [self.make_job()],
                Path(temp_dir),
            )

        self.assertTrue(any("missing from storyboard manifest" in error for error in errors))

    def test_validate_storyboard_manifest_rejects_missing_assets_field(self) -> None:
        errors = validate_storyboard_manifest(
            {"version": 1, "provider": "openai-compatible"},
            [],
            Path("."),
        )

        self.assertEqual(errors, ["manifest assets is required"])

    def test_validate_storyboard_manifest_rejects_empty_assets_list(self) -> None:
        errors = validate_storyboard_manifest(
            {"version": 1, "provider": "openai-compatible", "assets": []},
            [],
            Path("."),
        )

        self.assertEqual(errors, ["manifest assets must not be empty"])


class StoryboardCliTests(unittest.TestCase):
    def test_build_storyboard_jobs_cli_writes_jsonl(self) -> None:
        builder = StoryboardJobBuilderTests()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feed = builder.write_feed(root, 2)
            manifest = builder.write_manifest(root)
            copy_packs = builder.write_copy_packs(root)
            out = root / "生产资产" / "_内部" / "storyboard-jobs.jsonl"

            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "build_storyboard_jobs.py"),
                    "--feed",
                    str(feed),
                    "--manifest",
                    str(manifest),
                    "--copy-packs",
                    str(copy_packs),
                    "--workspace",
                    str(root),
                    "--out",
                    str(out),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Wrote 1 storyboard jobs", result.stdout)

    def test_build_storyboard_jobs_cli_accepts_asset_bible_fallback(self) -> None:
        builder = StoryboardJobBuilderTests()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            feed = builder.write_feed(root, 2)
            manifest = builder.write_manifest(root)
            asset_bible = builder.write_asset_bible(root)
            out = root / "生产资产" / "_内部" / "storyboard-jobs.jsonl"

            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "build_storyboard_jobs.py"),
                    "--feed",
                    str(feed),
                    "--manifest",
                    str(manifest),
                    "--asset-bible",
                    str(asset_bible),
                    "--workspace",
                    str(root),
                    "--out",
                    str(out),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Wrote 1 storyboard jobs", result.stdout)

    def test_validate_storyboard_manifest_cli_reports_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            job = StoryboardRunnerTests().make_job()
            jobs_path = root / "生产资产" / "_内部" / "storyboard-jobs.jsonl"
            write_storyboard_jobs_jsonl(jobs_path, [job])
            output = root / job.output_path
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"image")
            manifest_path = root / "生产资产" / "_内部" / "storyboard-manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "provider": "openai-compatible",
                        "assets": [
                            {
                                "asset_name": job.job_id,
                                "asset_type": "storyboard_contact_sheet",
                                "path": job.output_path.as_posix(),
                                "status": "done",
                                "prompt_hash": prompt_hash(job.prompt),
                                "model": job.model,
                                "size": job.size,
                                "line_start": job.line_start,
                                "line_end": job.line_end,
                                "line_count": job.line_count,
                                "source_feed": job.source_feed,
                                "references": [reference.to_dict() for reference in job.reference_images],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "validate_storyboard_manifest.py"),
                    str(manifest_path),
                    "--jobs",
                    str(jobs_path),
                    "--workspace",
                    str(root),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Storyboard manifest validation passed", result.stdout)

    def test_generate_storyboards_cli_rejects_missing_reference_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            job = StoryboardRunnerTests().make_job()
            jobs_path = root / "生产资产" / "_内部" / "storyboard-jobs.jsonl"
            write_storyboard_jobs_jsonl(jobs_path, [job])
            manifest_path = root / "生产资产" / "_内部" / "storyboard-manifest.json"
            env = os.environ.copy()
            env["SOURCE_TRUE_IMAGE_BASE_URL"] = "https://provider.example"
            env["SOURCE_TRUE_IMAGE_API_KEY"] = "sk-test-secret-1234567890"
            env.pop("SOURCE_TRUE_IMAGE_REFERENCE_MODE", None)

            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "generate_storyboards.py"),
                    "--jobs",
                    str(jobs_path),
                    "--manifest",
                    str(manifest_path),
                    "--workspace",
                    str(root),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SOURCE_TRUE_IMAGE_REFERENCE_MODE=data-url", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_generate_storyboards_cli_reports_missing_provider_config_without_traceback(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            job = StoryboardRunnerTests().make_job()
            jobs_path = root / "生产资产" / "_内部" / "storyboard-jobs.jsonl"
            write_storyboard_jobs_jsonl(jobs_path, [job])
            manifest_path = root / "生产资产" / "_内部" / "storyboard-manifest.json"
            env = os.environ.copy()
            env.pop("SOURCE_TRUE_IMAGE_BASE_URL", None)
            env.pop("SOURCE_TRUE_IMAGE_API_KEY", None)

            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "generate_storyboards.py"),
                    "--jobs",
                    str(jobs_path),
                    "--manifest",
                    str(manifest_path),
                    "--workspace",
                    str(root),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SOURCE_TRUE_IMAGE_BASE_URL and SOURCE_TRUE_IMAGE_API_KEY", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
