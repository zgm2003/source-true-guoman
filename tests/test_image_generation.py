import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import generate_images as generate_images_module
from scripts.image_generation_core import (
    ALLOWED_OUTPUT_DIRS,
    ImageGenerationError,
    ImageJob,
    build_dependency_waves,
    load_jobs_jsonl,
    prompt_hash,
    validate_manifest,
    validate_jobs,
)
from scripts.generate_images import (
    ImageGenerationConfig,
    NonRetryableProviderError,
    RetryableProviderError,
    _workspace_output_path,
    load_config_from_env,
    run_job_with_retry,
)
from scripts.build_image_jobs import build_jobs_from_asset_text


class ImageGenerationCoreTests(unittest.TestCase):
    def make_job(
        self,
        asset_name: str,
        output_dir: str = "人设资产",
        depends_on: list[str] | None = None,
    ) -> ImageJob:
        return ImageJob(
            job_id=f"job-{asset_name}",
            asset_name=asset_name,
            asset_type="character",
            prompt=f"prompt for {asset_name}",
            output_dir=output_dir,
            output_file=f"{asset_name}.png",
            depends_on=depends_on or [],
            reference_images=[],
            provider="openai-compatible",
            model="gpt-image-2",
            size="16:9",
            status="pending",
        )

    def test_load_jobs_jsonl_reads_required_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "image-jobs.jsonl"
            path.write_text(
                '{"job_id":"j1","asset_name":"林夜_黑袍造型","asset_type":"character","prompt":"p","output_dir":"人设资产","output_file":"林夜_黑袍造型.png","depends_on":[],"reference_images":[],"provider":"openai-compatible","model":"gpt-image-2","size":"16:9","status":"pending"}\n',
                encoding="utf-8",
            )

            jobs = load_jobs_jsonl(path)

            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0].asset_name, "林夜_黑袍造型")
            self.assertEqual(jobs[0].output_path, Path("人设资产") / "林夜_黑袍造型.png")

    def test_validate_jobs_rejects_missing_required_array_fields_from_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "image-jobs.jsonl"
            path.write_text(
                '{"job_id":"j1","asset_name":"missing_arrays","asset_type":"character","prompt":"p","output_dir":"人设资产","output_file":"missing_arrays.png","provider":"openai-compatible","model":"gpt-image-2","size":"16:9","status":"pending"}\n',
                encoding="utf-8",
            )

            jobs = load_jobs_jsonl(path)

            with self.assertRaises(ImageGenerationError) as context:
                validate_jobs(jobs)

            message = str(context.exception)
            self.assertIn("missing_arrays: depends_on is required", message)
            self.assertIn("missing_arrays: reference_images is required", message)

    def test_validate_jobs_rejects_duplicate_ids_and_production_output(self) -> None:
        jobs = [
            self.make_job("林夜_黑袍造型", output_dir="生产资产"),
            self.make_job("林夜_宗门礼服"),
        ]
        jobs[1].job_id = jobs[0].job_id

        with self.assertRaises(ImageGenerationError) as context:
            validate_jobs(jobs)

        message = str(context.exception)
        self.assertIn("duplicate job_id", message)
        self.assertIn("output_dir must be one of", message)

    def test_validate_jobs_rejects_missing_required_job_metadata_fields(self) -> None:
        job = self.make_job("metadata_asset")
        job.asset_type = ""
        job.provider = ""
        job.model = ""
        job.size = ""
        job.status = ""

        with self.assertRaises(ImageGenerationError) as context:
            validate_jobs([job])

        message = str(context.exception)
        self.assertIn("metadata_asset: asset_type is required", message)
        self.assertIn("metadata_asset: provider is required", message)
        self.assertIn("metadata_asset: model is required", message)
        self.assertIn("metadata_asset: size is required", message)
        self.assertIn("metadata_asset: status is required", message)

    def test_validate_jobs_rejects_output_file_paths(self) -> None:
        invalid_output_files = [
            "nested/asset.png",
            r"nested\asset.png",
            "/tmp/asset.png",
            r"C:\tmp\asset.png",
            "C:asset.png",
        ]

        for output_file in invalid_output_files:
            with self.subTest(output_file=output_file):
                job = self.make_job("path_asset")
                job.output_file = output_file

                with self.assertRaises(ImageGenerationError) as context:
                    validate_jobs([job])

                self.assertIn(
                    "path_asset: output_file must be a file name only",
                    str(context.exception),
                )

    def test_build_dependency_waves_orders_reference_dependencies(self) -> None:
        jobs = [
            self.make_job("林夜_黑袍造型"),
            self.make_job("鬼王宗宗门大殿_母图", output_dir="场景资产"),
            self.make_job("林夜_宗门礼服", depends_on=["林夜_黑袍造型"]),
            self.make_job("鬼王宗宗门大殿_左侧席位区", output_dir="场景资产", depends_on=["鬼王宗宗门大殿_母图"]),
        ]

        waves = build_dependency_waves(jobs)

        self.assertEqual(
            [[job.asset_name for job in wave] for wave in waves],
            [
                ["林夜_黑袍造型", "鬼王宗宗门大殿_母图"],
                ["林夜_宗门礼服", "鬼王宗宗门大殿_左侧席位区"],
            ],
        )

    def test_build_dependency_waves_rejects_cycles(self) -> None:
        jobs = [
            self.make_job("甲", depends_on=["乙"]),
            self.make_job("乙", depends_on=["甲"]),
        ]

        with self.assertRaises(ImageGenerationError) as context:
            build_dependency_waves(jobs)

        self.assertIn("cyclic dependencies", str(context.exception))

    def test_prompt_hash_is_stable_sha256(self) -> None:
        self.assertEqual(prompt_hash("abc"), prompt_hash("abc"))
        self.assertTrue(prompt_hash("abc").startswith("sha256:"))


class ProviderRetryTests(unittest.TestCase):
    def make_job(self) -> ImageJob:
        return ImageJob(
            job_id="job-provider-asset",
            asset_name="provider_asset",
            asset_type="character",
            prompt="A production-ready character concept image.",
            output_dir="人设资产",
            output_file="provider_asset.png",
            depends_on=["base_asset"],
            reference_images=[],
            provider="openai-compatible",
            model="gpt-image-2",
            size="16:9",
            status="pending",
        )

    def make_config(self, max_retries: int = 2) -> ImageGenerationConfig:
        return ImageGenerationConfig(
            base_url="https://provider.example",
            api_key="sk-test-secret-1234567890",
            model="gpt-image-2",
            size="16:9",
            timeout_seconds=30.0,
            max_retries=max_retries,
            retry_base_seconds=0.0,
            retry_max_seconds=0.0,
            concurrency=1,
        )

    def test_transient_retry_succeeds_on_third_attempt_and_writes_image(self) -> None:
        job = self.make_job()
        config = self.make_config(max_retries=3)
        attempts = 0

        def provider(current_job: ImageJob, current_config: ImageGenerationConfig) -> bytes:
            nonlocal attempts
            attempts += 1
            self.assertIs(current_job, job)
            self.assertIs(current_config, config)
            if attempts < 3:
                raise RetryableProviderError("HTTP 429 rate limited")
            return b"image-bytes"

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            result = run_job_with_retry(job, config, workspace, provider=provider)

            self.assertEqual(result["status"], "done")
            self.assertEqual(result["attempts"], 3)
            self.assertEqual(result["path"], job.output_path.as_posix())
            self.assertEqual((workspace / job.output_path).read_bytes(), b"image-bytes")
            self.assertEqual(result["depends_on"], ["base_asset"])
            self.assertEqual(result["references"], [])

    def test_retry_budget_exhausted_returns_failed_result(self) -> None:
        job = self.make_job()
        config = self.make_config(max_retries=2)

        def provider(current_job: ImageJob, current_config: ImageGenerationConfig) -> bytes:
            raise RetryableProviderError("HTTP 504 upstream timeout")

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_job_with_retry(job, config, Path(temp_dir), provider=provider)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["attempts"], config.max_retries + 1)
        self.assertIn("HTTP 504", result["last_error"])
        self.assertEqual(result["depends_on"], ["base_asset"])
        self.assertEqual(result["references"], [])

    def test_non_retryable_provider_error_fails_after_one_attempt(self) -> None:
        job = self.make_job()
        config = self.make_config(max_retries=5)
        attempts = 0

        def provider(current_job: ImageJob, current_config: ImageGenerationConfig) -> bytes:
            nonlocal attempts
            attempts += 1
            raise NonRetryableProviderError("HTTP 401 authentication failed")

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_job_with_retry(job, config, Path(temp_dir), provider=provider)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(attempts, 1)
        self.assertIn("HTTP 401", result["last_error"])

    def test_result_dicts_do_not_include_api_key_or_base_url(self) -> None:
        job = self.make_job()
        config = self.make_config(max_retries=0)

        def provider(current_job: ImageJob, current_config: ImageGenerationConfig) -> bytes:
            raise RetryableProviderError(
                f"HTTP 429 from {current_config.base_url} using {current_config.api_key}"
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_job_with_retry(job, config, Path(temp_dir), provider=provider)

        result_text = json.dumps(result, ensure_ascii=False, sort_keys=True)
        self.assertEqual(result["status"], "failed")
        self.assertNotIn(config.api_key, result_text)
        self.assertNotIn(config.base_url, result_text)

    def test_output_path_escape_fails_before_provider_is_called(self) -> None:
        job = self.make_job()
        job.output_dir = ".."
        config = self.make_config(max_retries=3)
        provider_called = False

        def provider(current_job: ImageJob, current_config: ImageGenerationConfig) -> bytes:
            nonlocal provider_called
            provider_called = True
            return b"should-not-be-written"

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_job_with_retry(job, config, Path(temp_dir), provider=provider)

        self.assertFalse(provider_called)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["attempts"], 0)
        self.assertIn("output_dir", result["last_error"])

    def test_workspace_output_path_rejects_invalid_output_dir_directly(self) -> None:
        job = self.make_job()
        job.output_dir = "generated"

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(NonRetryableProviderError) as context:
                _workspace_output_path(Path(temp_dir), job)

        self.assertIn("output_dir", str(context.exception))

    def test_result_and_logs_redact_provider_host_and_api_key(self) -> None:
        job = self.make_job()
        config = self.make_config(max_retries=0)
        config.base_url = "https://relay.internal.example/openai"

        def provider(current_job: ImageJob, current_config: ImageGenerationConfig) -> bytes:
            raise RetryableProviderError(
                "HTTP 502 from relay.internal.example using sk-test-secret-1234567890"
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertLogs("scripts.generate_images", level="WARNING") as logs:
                result = run_job_with_retry(job, config, Path(temp_dir), provider=provider)

        result_text = json.dumps(result, ensure_ascii=False, sort_keys=True)
        log_text = "\n".join(logs.output)
        self.assertEqual(result["status"], "failed")
        self.assertNotIn("relay.internal.example", result_text)
        self.assertNotIn(config.api_key, result_text)
        self.assertNotIn("relay.internal.example", log_text)
        self.assertNotIn(config.api_key, log_text)

    def test_load_config_from_env_requires_credentials(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ImageGenerationError) as context:
                load_config_from_env()

        self.assertIn("SOURCE_TRUE_IMAGE_BASE_URL", str(context.exception))
        self.assertIn("SOURCE_TRUE_IMAGE_API_KEY", str(context.exception))

    def test_load_config_from_env_rejects_bad_int(self) -> None:
        env = {
            "SOURCE_TRUE_IMAGE_BASE_URL": "https://provider.example/",
            "SOURCE_TRUE_IMAGE_API_KEY": "sk-test-secret-1234567890",
            "SOURCE_TRUE_IMAGE_CONCURRENCY": "many",
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ImageGenerationError) as context:
                load_config_from_env()

        self.assertIn("SOURCE_TRUE_IMAGE_CONCURRENCY must be an integer", str(context.exception))

    def test_load_config_from_env_rejects_nan_float(self) -> None:
        env = {
            "SOURCE_TRUE_IMAGE_BASE_URL": "https://provider.example/",
            "SOURCE_TRUE_IMAGE_API_KEY": "sk-test-secret-1234567890",
            "SOURCE_TRUE_IMAGE_TIMEOUT_SECONDS": "nan",
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ImageGenerationError) as context:
                load_config_from_env()

        self.assertIn("SOURCE_TRUE_IMAGE_TIMEOUT_SECONDS must be finite", str(context.exception))

    def test_load_config_from_env_rejects_inf_float(self) -> None:
        env = {
            "SOURCE_TRUE_IMAGE_BASE_URL": "https://provider.example/",
            "SOURCE_TRUE_IMAGE_API_KEY": "sk-test-secret-1234567890",
            "SOURCE_TRUE_IMAGE_RETRY_MAX_SECONDS": "inf",
        }

        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(ImageGenerationError) as context:
                load_config_from_env()

        self.assertIn("SOURCE_TRUE_IMAGE_RETRY_MAX_SECONDS must be finite", str(context.exception))


class ImageGenerationRunnerTests(unittest.TestCase):
    def make_job(
        self,
        name: str,
        depends_on: list[str] | None = None,
    ) -> ImageJob:
        return ImageJob(
            job_id=f"job-{name}",
            asset_name=name,
            asset_type="character",
            prompt=f"prompt for {name}",
            output_dir=sorted(ALLOWED_OUTPUT_DIRS)[0],
            output_file=f"{name}.png",
            depends_on=depends_on or [],
            reference_images=[],
            provider="openai-compatible",
            model="gpt-image-2",
            size="16:9",
            status="pending",
        )

    def make_config(self, concurrency: int = 1) -> ImageGenerationConfig:
        return ImageGenerationConfig(
            base_url="https://provider.example/openai",
            api_key="sk-test-secret-1234567890",
            model="gpt-image-2",
            size="16:9",
            timeout_seconds=5.0,
            max_retries=0,
            retry_base_seconds=0.0,
            retry_max_seconds=0.0,
            concurrency=concurrency,
        )

    def test_run_generation_respects_dependency_order_and_resume(self) -> None:
        jobs = [
            self.make_job("parent"),
            self.make_job("child", depends_on=["parent"]),
        ]
        calls: list[str] = []

        def provider(job: ImageJob, config: ImageGenerationConfig) -> bytes:
            calls.append(job.asset_name)
            return f"image:{job.asset_name}".encode("utf-8")

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = self.make_config(concurrency=4)

            manifest = generate_images_module.run_generation(
                jobs,
                config,
                workspace,
                provider=provider,
            )
            second_manifest = generate_images_module.run_generation(
                jobs,
                config,
                workspace,
                provider=provider,
                existing_manifest=manifest,
                resume=True,
            )

        self.assertEqual(calls, ["parent", "child"])
        self.assertEqual(
            [asset["asset_name"] for asset in manifest["assets"]],
            ["parent", "child"],
        )
        self.assertEqual(
            [asset["status"] for asset in manifest["assets"]],
            ["done", "done"],
        )
        self.assertEqual(
            [asset["asset_name"] for asset in second_manifest["assets"]],
            ["parent", "child"],
        )
        self.assertEqual(
            [asset["status"] for asset in second_manifest["assets"]],
            ["done", "done"],
        )

    def test_sibling_jobs_in_same_dependency_wave_can_run_concurrently(self) -> None:
        jobs = [self.make_job("sibling_a"), self.make_job("sibling_b")]
        started = {
            "sibling_a": threading.Event(),
            "sibling_b": threading.Event(),
        }
        lock = threading.Lock()
        active = 0
        max_active = 0

        def provider(job: ImageJob, config: ImageGenerationConfig) -> bytes:
            nonlocal active, max_active
            other_name = "sibling_b" if job.asset_name == "sibling_a" else "sibling_a"
            with lock:
                active += 1
                max_active = max(max_active, active)
            try:
                started[job.asset_name].set()
                started[other_name].wait(timeout=1.0)
                time.sleep(0.02)
                return f"image:{job.asset_name}".encode("utf-8")
            finally:
                with lock:
                    active -= 1

        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = generate_images_module.run_generation(
                jobs,
                self.make_config(concurrency=2),
                Path(temp_dir),
                provider=provider,
            )

        self.assertEqual([asset["status"] for asset in manifest["assets"]], ["done", "done"])
        self.assertGreaterEqual(max_active, 2)

    def test_dependency_failure_blocks_dependent_jobs_without_provider_call(self) -> None:
        jobs = [
            self.make_job("parent"),
            self.make_job("child", depends_on=["parent"]),
        ]
        calls: list[str] = []

        def provider(job: ImageJob, config: ImageGenerationConfig) -> bytes:
            calls.append(job.asset_name)
            if job.asset_name == "parent":
                raise RetryableProviderError("HTTP 503 upstream")
            return b"child"

        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = generate_images_module.run_generation(
                jobs,
                self.make_config(concurrency=2),
                Path(temp_dir),
                provider=provider,
            )

        by_name = {asset["asset_name"]: asset for asset in manifest["assets"]}
        self.assertEqual(calls, ["parent"])
        self.assertEqual(by_name["parent"]["status"], "failed")
        self.assertEqual(by_name["child"]["status"], "blocked")
        self.assertEqual(by_name["child"]["attempts"], 0)
        self.assertIn("parent", by_name["child"]["last_error"])

    def test_manifest_asset_ordering_is_original_job_order(self) -> None:
        jobs = [self.make_job("slow"), self.make_job("fast")]
        fast_done = threading.Event()
        finish_order: list[str] = []
        lock = threading.Lock()

        def provider(job: ImageJob, config: ImageGenerationConfig) -> bytes:
            if job.asset_name == "fast":
                fast_done.set()
            else:
                fast_done.wait(timeout=1.0)
                time.sleep(0.05)
            with lock:
                finish_order.append(job.asset_name)
            return f"image:{job.asset_name}".encode("utf-8")

        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = generate_images_module.run_generation(
                jobs,
                self.make_config(concurrency=2),
                Path(temp_dir),
                provider=provider,
            )

        self.assertEqual(finish_order[0], "fast")
        self.assertEqual(
            [asset["asset_name"] for asset in manifest["assets"]],
            ["slow", "fast"],
        )

    def test_resume_does_not_skip_existing_manifest_path_outside_workspace(self) -> None:
        job = self.make_job("safe_asset")
        calls: list[str] = []

        def provider(current_job: ImageJob, config: ImageGenerationConfig) -> bytes:
            calls.append(current_job.asset_name)
            return b"replacement-image"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            (root / "outside.png").write_bytes(b"old-image")
            existing_manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [
                    {
                        "asset_name": "safe_asset",
                        "asset_type": "character",
                        "path": "../outside.png",
                        "status": "done",
                        "prompt_hash": prompt_hash(job.prompt),
                        "model": "gpt-image-2",
                        "size": "16:9",
                        "attempts": 1,
                        "depends_on": [],
                        "references": [],
                    }
                ],
            }

            manifest = generate_images_module.run_generation(
                [job],
                self.make_config(),
                workspace,
                provider=provider,
                existing_manifest=existing_manifest,
                resume=True,
            )

        self.assertEqual(calls, ["safe_asset"])
        self.assertEqual(manifest["assets"][0]["status"], "done")
        self.assertNotEqual(manifest["assets"][0]["path"], "../outside.png")

    def test_write_generation_report_orders_failed_blocked_generated_sections(self) -> None:
        manifest = {
            "version": 1,
            "provider": "openai-compatible",
            "assets": [
                {"asset_name": "generated_asset", "status": "done", "path": "out/generated.png"},
                {"asset_name": "blocked_asset", "status": "blocked", "last_error": "parent failed"},
                {"asset_name": "failed_asset", "status": "failed", "last_error": "provider failed"},
            ],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = Path(temp_dir) / "image-generation-report.md"

            generate_images_module.write_generation_report(report_path, manifest)

            text = report_path.read_text(encoding="utf-8")

        self.assertLess(text.index("## Failed"), text.index("## Blocked"))
        self.assertLess(text.index("## Blocked"), text.index("## Generated"))
        self.assertIn("- failed_asset: provider failed", text)
        self.assertIn("- blocked_asset: parent failed", text)
        self.assertIn("- generated_asset: out/generated.png", text)

    def test_main_writes_manifest_and_report_with_env_config_without_real_provider(self) -> None:
        job = self.make_job("cli_asset")
        calls: list[str] = []

        def provider(current_job: ImageJob, config: ImageGenerationConfig) -> bytes:
            calls.append(current_job.asset_name)
            self.assertEqual(config.model, "gpt-image-2")
            return b"cli-image"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            jobs_path = root / "image-jobs.jsonl"
            manifest_path = root / "image-manifest.json"
            report_path = root / "image-generation-report.md"
            jobs_path.write_text(
                json.dumps(job.to_dict(), ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            env = {
                "SOURCE_TRUE_IMAGE_BASE_URL": "https://provider.example/openai",
                "SOURCE_TRUE_IMAGE_API_KEY": "sk-test-secret-1234567890",
                "SOURCE_TRUE_IMAGE_MODEL": "gpt-image-2",
                "SOURCE_TRUE_IMAGE_SIZE": "16:9",
                "SOURCE_TRUE_IMAGE_TIMEOUT_SECONDS": "5",
                "SOURCE_TRUE_IMAGE_MAX_RETRIES": "0",
                "SOURCE_TRUE_IMAGE_RETRY_BASE_SECONDS": "0",
                "SOURCE_TRUE_IMAGE_RETRY_MAX_SECONDS": "0",
                "SOURCE_TRUE_IMAGE_CONCURRENCY": "1",
            }
            argv = [
                "generate_images.py",
                "--jobs",
                str(jobs_path),
                "--manifest",
                str(manifest_path),
                "--workspace",
                str(root),
                "--report",
                str(report_path),
            ]

            with patch.dict(os.environ, env, clear=True):
                with patch.object(sys, "argv", argv):
                    with patch.object(
                        generate_images_module,
                        "openai_compatible_provider",
                        provider,
                    ):
                        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                            exit_code = generate_images_module.main()

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            report_text = report_path.read_text(encoding="utf-8")
            manifest_text = json.dumps(manifest, ensure_ascii=False, sort_keys=True)

        self.assertEqual(exit_code, 0)
        self.assertIn("Image generation wrote 1 assets", stdout.getvalue())
        self.assertEqual(calls, ["cli_asset"])
        self.assertEqual(manifest["assets"][0]["status"], "done")
        self.assertIn("## Generated", report_text)
        self.assertNotIn("api_key", manifest_text)
        self.assertNotIn("sk-test-secret", manifest_text)
        self.assertNotIn("https://provider.example/openai", manifest_text)


class ImageManifestValidationTests(unittest.TestCase):
    def test_validate_manifest_rejects_done_asset_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            jobs = [
                ImageJob(
                    job_id="j1",
                    asset_name="林夜_黑袍造型",
                    asset_type="character",
                    prompt="prompt",
                    output_dir="人设资产",
                    output_file="林夜_黑袍造型.png",
                    depends_on=[],
                    reference_images=[],
                    provider="openai-compatible",
                    model="gpt-image-2",
                    size="16:9",
                    status="pending",
                )
            ]
            manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [
                    {
                        "asset_name": "林夜_黑袍造型",
                        "asset_type": "character",
                        "path": "人设资产/林夜_黑袍造型.png",
                        "status": "done",
                        "prompt_hash": "sha256:abc",
                        "model": "gpt-image-2",
                        "size": "16:9",
                        "attempts": 1,
                        "depends_on": [],
                        "references": [],
                    }
                ],
            }

            errors = validate_manifest(manifest, jobs, root)

            self.assertIn("done asset missing local file", "; ".join(errors))

    def test_validate_manifest_rejects_secret_values_and_production_image_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            jobs = []
            manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "api_key": "secret-value",
                "assets": [
                    {
                        "asset_name": "坏路径",
                        "asset_type": "scene",
                        "path": "生产资产/坏路径.png",
                        "status": "failed",
                        "last_error": "api_key leaked",
                    }
                ],
            }

            errors = validate_manifest(manifest, jobs, root)

            message = "; ".join(errors)
            self.assertIn("manifest must not contain secret key names", message)
            self.assertIn("generated image path must not be under 生产资产", message)

    def test_validate_image_manifest_cli_reports_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            jobs_path = root / "image-jobs.jsonl"
            manifest_path = root / "image-manifest.json"
            jobs_path.write_text("", encoding="utf-8")
            manifest_path.write_text(
                '{"version":1,"provider":"openai-compatible","api_key":"bad","assets":[]}',
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "validate_image_manifest.py"),
                    str(manifest_path),
                    "--jobs",
                    str(jobs_path),
                    "--workspace",
                    str(root),
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Image manifest validation failed", result.stdout)
            self.assertIn("manifest must not contain secret key names", result.stdout)

    def test_validate_manifest_rejects_normalized_production_paths_and_workspace_escapes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [
                    {
                        "asset_name": "normalized_production",
                        "path": "./\u751f\u4ea7\u8d44\u4ea7/foo.png",
                        "status": "pending",
                    },
                    {
                        "asset_name": "parent_production",
                        "path": "\u4eba\u8bbe\u8d44\u4ea7/../\u751f\u4ea7\u8d44\u4ea7/foo.png",
                        "status": "pending",
                    },
                    {
                        "asset_name": "parent_escape",
                        "path": "../outside.png",
                        "status": "pending",
                    },
                    {
                        "asset_name": "absolute_path",
                        "path": str(root / "asset.png"),
                        "status": "pending",
                    },
                    {
                        "asset_name": "drive_absolute",
                        "path": r"C:\tmp\x.png",
                        "status": "pending",
                    },
                    {
                        "asset_name": "drive_relative",
                        "path": r"C:tmp\x.png",
                        "status": "pending",
                    },
                ],
            }

            errors = validate_manifest(manifest, [], root)

            message = "; ".join(errors)
            self.assertGreaterEqual(
                message.count("generated image path must not be under"),
                2,
            )
            self.assertIn("generated image path must stay under workspace", message)
            self.assertIn("generated image path must be relative", message)
            self.assertIn("generated image path must not use a drive prefix", message)

    def test_validate_image_manifest_cli_fails_clearly_for_invalid_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            jobs_path = root / "image-jobs.jsonl"
            manifest_path = root / "image-manifest.json"
            jobs_path.write_text(
                '{"job_id":"j1","asset_name":"bad","asset_type":"character","prompt":"p",'
                '"output_dir":"\u751f\u4ea7\u8d44\u4ea7","output_file":"bad.png",'
                '"depends_on":[],"reference_images":[],"provider":"openai-compatible",'
                '"model":"gpt-image-2","size":"16:9","status":"pending"}' + "\n",
                encoding="utf-8",
            )
            manifest_path.write_text(
                '{"version":1,"provider":"openai-compatible","assets":[]}',
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "validate_image_manifest.py"),
                    str(manifest_path),
                    "--jobs",
                    str(jobs_path),
                    "--workspace",
                    str(root),
                ],
                text=True,
                capture_output=True,
            )

            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Image manifest validation failed", result.stdout)
            self.assertIn("output_dir must be one of", result.stdout)
            self.assertNotIn("Traceback", combined)

    def test_validate_image_manifest_cli_fails_clearly_for_missing_and_malformed_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            jobs_path = root / "image-jobs.jsonl"
            manifest_path = root / "image-manifest.json"
            jobs_path.write_text("", encoding="utf-8")
            manifest_path.write_text("{not json", encoding="utf-8")

            cases = [
                (root / "missing-manifest.json", jobs_path),
                (manifest_path, root / "missing-jobs.jsonl"),
                (manifest_path, jobs_path),
            ]

            for manifest_arg, jobs_arg in cases:
                with self.subTest(manifest=manifest_arg.name, jobs=jobs_arg.name):
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(Path(__file__).resolve().parents[1] / "scripts" / "validate_image_manifest.py"),
                            str(manifest_arg),
                            "--jobs",
                            str(jobs_arg),
                            "--workspace",
                            str(root),
                        ],
                        text=True,
                        capture_output=True,
                    )

                    combined = result.stdout + result.stderr
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Image manifest validation failed", result.stdout)
                    self.assertNotIn("Traceback", combined)

    def test_validate_manifest_rejects_obvious_secret_values(self) -> None:
        manifest = {
            "version": 1,
            "provider": "openai-compatible",
            "assets": [
                {
                    "asset_name": "secret_value",
                    "path": "\u4eba\u8bbe\u8d44\u4ea7/secret_value.png",
                    "status": "failed",
                    "last_error": "request used sk-test-1234567890",
                }
            ],
        }

        errors = validate_manifest(manifest, [], Path("."))

        self.assertIn("manifest must not contain secret key names", "; ".join(errors))


class BuildImageJobsTests(unittest.TestCase):
    def test_build_jobs_from_asset_prompt_headings_preserves_order_and_infers_output_dirs(
        self,
    ) -> None:
        text = """
## 资产提示词

### 图片1 = 林夜_黑袍造型
GPT-image-2，16:9，3D国漫。角色三视图，白色背景。

### 图片2 = 鬼王宗宗门大殿_母图
GPT-image-2，16:9，3D国漫。空场景，宗门大殿，不要人物。

### 图片3 = 万魂幡_单体
GPT-image-2，16:9，道具名单体参考图，只生成一个完整主体。

### 图片4 = 系统界面_惩罚弹窗
GPT-image-2，16:9，界面风格参考图，正面屏幕。
"""

        jobs = build_jobs_from_asset_text(text, model="gpt-image-2", size="16:9")

        self.assertEqual(
            [job.asset_name for job in jobs],
            [
                "林夜_黑袍造型",
                "鬼王宗宗门大殿_母图",
                "万魂幡_单体",
                "系统界面_惩罚弹窗",
            ],
        )
        self.assertEqual(
            [job.asset_type for job in jobs],
            ["character", "scene", "prop", "prop"],
        )
        self.assertEqual(
            [job.output_dir for job in jobs],
            ["人设资产", "场景资产", "道具资产", "道具资产"],
        )
        self.assertEqual(jobs[0].output_file, "林夜_黑袍造型.png")

    def test_build_jobs_extracts_upload_reference_lines_and_dedupes_dependencies(
        self,
    ) -> None:
        text = """
## 资产提示词

### 图片1 = 林夜_黑袍造型
GPT-image-2，16:9，3D国漫。角色三视图，白色背景。

### 图片2 = 鬼王宗宗门大殿_母图
GPT-image-2，16:9，3D国漫。空场景，宗门大殿，不要人物。

### 图片3 = 林夜_宗门礼服
上传参考图：林夜_黑袍造型 = 图片1（人脸身份参考）；林夜_黑袍造型 = 图片1（旧造型参考）
上传参考图：鬼王宗宗门大殿_母图 = 图片2（场景母图参考）
GPT-image-2，16:9，3D国漫。保持同一张脸，换宗门礼服。
"""

        jobs = build_jobs_from_asset_text(text, model="gpt-image-2", size="16:9")

        variant = jobs[2]
        self.assertEqual(variant.depends_on, ["林夜_黑袍造型", "鬼王宗宗门大殿_母图"])
        self.assertEqual(
            [(ref.asset_name, ref.purpose) for ref in variant.reference_images],
            [
                ("林夜_黑袍造型", "人脸身份参考"),
                ("林夜_黑袍造型", "旧造型参考"),
                ("鬼王宗宗门大殿_母图", "场景母图参考"),
            ],
        )

    def test_build_image_jobs_cli_writes_jsonl_loadable_by_core(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            asset_bible = root / "asset-bible.md"
            jobs_path = root / "image-jobs.jsonl"
            asset_bible.write_text(
                "## 资产提示词\n\n"
                "### 图片1 = 万魂幡_单体\n"
                "GPT-image-2，16:9，道具名单体参考图，只生成一个完整主体。\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(
                        Path(__file__).resolve().parents[1]
                        / "scripts"
                        / "build_image_jobs.py"
                    ),
                    "--asset-bible",
                    str(asset_bible),
                    "--out",
                    str(jobs_path),
                    "--provider",
                    "openai-compatible",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Wrote 1 image jobs", result.stdout)
            jobs = load_jobs_jsonl(jobs_path)
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0].asset_name, "万魂幡_单体")
            self.assertEqual(jobs[0].output_dir, "道具资产")
            self.assertEqual(jobs[0].provider, "openai-compatible")

    def test_build_jobs_keeps_character_prompt_with_negative_scene_wording(self) -> None:
        text = """
### 图片1 = 林夜_黑袍造型
GPT-image-2，16:9，角色三视图，白色背景，不要复杂场景。
"""

        jobs = build_jobs_from_asset_text(text, model="gpt-image-2", size="16:9")

        self.assertEqual(jobs[0].asset_type, "character")
        self.assertEqual(jobs[0].output_dir, "人设资产")

    def test_build_image_jobs_cli_reports_missing_asset_bible_without_traceback(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = subprocess.run(
                [
                    sys.executable,
                    str(
                        Path(__file__).resolve().parents[1]
                        / "scripts"
                        / "build_image_jobs.py"
                    ),
                    "--asset-bible",
                    str(root / "missing-asset-bible.md"),
                    "--out",
                    str(root / "image-jobs.jsonl"),
                ],
                text=True,
                capture_output=True,
            )

            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Image job build failed:", result.stdout)
            self.assertNotIn("Traceback", combined)

    def test_build_image_jobs_cli_reports_invalid_generated_jobs_without_traceback(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            asset_bible = root / "asset-bible.md"
            asset_bible.write_text(
                "### 图片1 = 林夜_宗门礼服\n"
                "上传参考图：林夜_黑袍造型 = 图片99（人脸身份参考）\n"
                "GPT-image-2，16:9，保持同一张脸，换宗门礼服。\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(
                        Path(__file__).resolve().parents[1]
                        / "scripts"
                        / "build_image_jobs.py"
                    ),
                    "--asset-bible",
                    str(asset_bible),
                    "--out",
                    str(root / "image-jobs.jsonl"),
                ],
                text=True,
                capture_output=True,
            )

            combined = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Image job build failed:", result.stdout)
            self.assertIn("unknown dependency", result.stdout)
            self.assertNotIn("Traceback", combined)

    def test_build_jobs_stops_prompt_before_following_markdown_heading(self) -> None:
        text = """
## 资产提示词
### 图片1 = 林夜_黑袍造型
GPT-image-2 prompt for character concept.
## VIDEO FEED
1 This downstream section is not an image prompt.
"""

        jobs = build_jobs_from_asset_text(text, model="gpt-image-2", size="16:9")

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].prompt, "GPT-image-2 prompt for character concept.")
        self.assertNotIn("VIDEO FEED", jobs[0].prompt)
        self.assertNotIn("downstream section", jobs[0].prompt)

    def test_build_jobs_accepts_compact_image_sections_without_asset_block_heading(
        self,
    ) -> None:
        text = """
### 图片1 = 林夜_黑袍造型
GPT-image-2 prompt for character concept.
### 图片2 = 鬼王宗宗门大殿_母图
GPT-image-2 prompt for empty scene.
"""

        jobs = build_jobs_from_asset_text(text, model="gpt-image-2", size="16:9")

        self.assertEqual(
            [job.asset_name for job in jobs],
            ["林夜_黑袍造型", "鬼王宗宗门大殿_母图"],
        )
        self.assertEqual([job.output_dir for job in jobs], ["人设资产", "场景资产"])


if __name__ == "__main__":
    unittest.main()
