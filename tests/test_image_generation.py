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
    ReferenceImage,
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
    openai_compatible_provider,
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

    def fake_image_response(self) -> object:
        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def read(self) -> bytes:
                return b'{"data":[{"b64_json":"aW1hZ2U="}]}'

        return FakeResponse()

    def test_provider_rejects_reference_jobs_without_explicit_reference_mode(
        self,
    ) -> None:
        job = self.make_job()
        job.reference_images = [
            ReferenceImage(
                asset_name="base_asset",
                path="人设资产/base_asset.png",
                purpose="人脸身份参考",
            )
        ]
        config = self.make_config()

        with patch.object(
            generate_images_module.urllib.request,
            "urlopen",
            return_value=self.fake_image_response(),
        ):
            with self.assertRaises(NonRetryableProviderError) as context:
                openai_compatible_provider(job, config)

        self.assertIn(
            "SOURCE_TRUE_IMAGE_REFERENCE_MODE",
            str(context.exception),
        )

    def test_provider_payload_includes_reference_image_data_urls_when_enabled(
        self,
    ) -> None:
        job = self.make_job()
        captured_payloads: list[dict[str, object]] = []

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reference_path = root / "人设资产" / "base_asset.png"
            reference_path.parent.mkdir(parents=True, exist_ok=True)
            reference_path.write_bytes(b"reference-bytes")
            job.reference_images = [
                ReferenceImage(
                    asset_name="base_asset",
                    path="人设资产/base_asset.png",
                    purpose="人脸身份参考",
                )
            ]
            config = self.make_config()
            config.reference_mode = "data-url"
            config.reference_workspace = str(root)

            def fake_urlopen(request: object, timeout: float) -> object:
                self.assertEqual(timeout, config.timeout_seconds)
                data = getattr(request, "data")
                captured_payloads.append(json.loads(data.decode("utf-8")))
                return self.fake_image_response()

            with patch.object(
                generate_images_module.urllib.request,
                "urlopen",
                side_effect=fake_urlopen,
            ):
                image_bytes = openai_compatible_provider(job, config)

        self.assertEqual(image_bytes, b"image")
        self.assertEqual(len(captured_payloads), 1)
        reference_payload = captured_payloads[0]["reference_images"]
        self.assertEqual(
            reference_payload,
            [
                {
                    "asset_name": "base_asset",
                    "purpose": "人脸身份参考",
                    "path": "人设资产/base_asset.png",
                    "data_url": "data:image/png;base64,cmVmZXJlbmNlLWJ5dGVz",
                }
            ],
        )

    def test_run_job_blocks_style_dependent_assets_until_user_confirms_baseline(
        self,
    ) -> None:
        job = self.make_job()
        job.reference_images = [
            ReferenceImage(
                asset_name="林夜_黑袍造型",
                path="人设资产/林夜_黑袍造型.png",
                purpose="人设风格基准参考",
            )
        ]
        config = self.make_config()
        config.reference_mode = "data-url"
        provider_called = False

        def provider(current_job: ImageJob, current_config: ImageGenerationConfig) -> bytes:
            nonlocal provider_called
            provider_called = True
            return b"image"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reference_path = root / "人设资产" / "林夜_黑袍造型.png"
            reference_path.parent.mkdir(parents=True, exist_ok=True)
            reference_path.write_bytes(b"baseline")
            config.reference_workspace = str(root)

            result = run_job_with_retry(job, config, root, provider=provider)

        self.assertFalse(provider_called)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["attempts"], 0)
        self.assertIn("style baseline requires user confirmation", result["last_error"])

    def test_run_job_allows_style_dependent_assets_after_user_confirmation(
        self,
    ) -> None:
        job = self.make_job()
        job.reference_images = [
            ReferenceImage(
                asset_name="林夜_黑袍造型",
                path="人设资产/林夜_黑袍造型.png",
                purpose="人设风格基准参考",
            )
        ]
        config = self.make_config()
        config.reference_mode = "data-url"
        config.style_confirmed = True

        def provider(current_job: ImageJob, current_config: ImageGenerationConfig) -> bytes:
            return b"image"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reference_path = root / "人设资产" / "林夜_黑袍造型.png"
            reference_path.parent.mkdir(parents=True, exist_ok=True)
            reference_path.write_bytes(b"baseline")
            config.reference_workspace = str(root)

            result = run_job_with_retry(job, config, root, provider=provider)

        self.assertEqual(result["status"], "done")

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

    def test_workspace_output_path_accepts_windows_extended_prefix_equivalent_path(
        self,
    ) -> None:
        if os.name != "nt":
            self.skipTest("Windows extended-length prefix behavior is Windows-specific")

        job = self.make_job()

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            expected_workspace = workspace.resolve(strict=False)
            expected_output = (expected_workspace / job.output_path).resolve(
                strict=False
            )
            extended_output = Path("\\\\?\\" + str(expected_output))
            original_resolve = Path.resolve

            def resolve_with_extended_output(
                path: Path,
                *args: object,
                **kwargs: object,
            ) -> Path:
                resolved = original_resolve(path, *args, **kwargs)
                if resolved == expected_output:
                    return extended_output
                return resolved

            with patch.object(Path, "resolve", resolve_with_extended_output):
                output_path = _workspace_output_path(workspace, job)

        self.assertEqual(output_path, extended_output)

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

    def existing_done_asset(
        self,
        job: ImageJob,
        path: str | None = None,
        prompt_hash_value: str | None = None,
        model: str = "gpt-image-2",
        size: str = "16:9",
        attempts: object = 1,
        references: list[dict[str, str]] | None = None,
    ) -> dict[str, object]:
        return {
            "asset_name": job.asset_name,
            "asset_type": job.asset_type,
            "path": path or job.output_path.as_posix(),
            "status": "done",
            "prompt_hash": prompt_hash_value or prompt_hash(job.prompt),
            "model": model,
            "size": size,
            "attempts": attempts,
            "depends_on": list(job.depends_on),
            "references": references or [],
        }

    def run_generate_images_cli_with_job_data(
        self,
        job_data: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            jobs_path = root / "image-jobs.jsonl"
            manifest_path = root / "image-manifest.json"
            jobs_path.write_text(
                json.dumps(job_data, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            return subprocess.run(
                [
                    sys.executable,
                    str(
                        Path(__file__).resolve().parents[1]
                        / "scripts"
                        / "generate_images.py"
                    ),
                    "--jobs",
                    str(jobs_path),
                    "--manifest",
                    str(manifest_path),
                    "--workspace",
                    str(root),
                ],
                text=True,
                capture_output=True,
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

    def test_unexpected_same_wave_provider_error_fails_and_blocks_dependents(self) -> None:
        jobs = [
            self.make_job("bad_parent"),
            self.make_job("good_sibling"),
            self.make_job("child", depends_on=["bad_parent"]),
        ]
        calls: list[str] = []
        calls_lock = threading.Lock()
        config = self.make_config(concurrency=2)

        def provider(job: ImageJob, current_config: ImageGenerationConfig) -> bytes:
            with calls_lock:
                calls.append(job.asset_name)
            if job.asset_name == "bad_parent":
                raise RuntimeError(
                    f"boom from {current_config.base_url} with {current_config.api_key}"
                )
            return f"image:{job.asset_name}".encode("utf-8")

        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = generate_images_module.run_generation(
                jobs,
                config,
                Path(temp_dir),
                provider=provider,
            )

        by_name = {asset["asset_name"]: asset for asset in manifest["assets"]}
        manifest_text = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        self.assertEqual(by_name["bad_parent"]["status"], "failed")
        self.assertIn("boom from", by_name["bad_parent"]["last_error"])
        self.assertIn("with [redacted]", by_name["bad_parent"]["last_error"])
        self.assertEqual(by_name["good_sibling"]["status"], "done")
        self.assertEqual(by_name["child"]["status"], "blocked")
        self.assertEqual(by_name["child"]["attempts"], 0)
        self.assertIn("bad_parent", by_name["child"]["last_error"])
        self.assertNotIn(config.base_url, manifest_text)
        self.assertNotIn(config.api_key, manifest_text)
        with calls_lock:
            recorded_calls = sorted(calls)
        self.assertEqual(recorded_calls, ["bad_parent", "good_sibling"])

    def test_resume_in_workspace_wrong_path_does_not_skip(self) -> None:
        job = self.make_job("wrong_path_asset")
        calls: list[str] = []

        def provider(current_job: ImageJob, config: ImageGenerationConfig) -> bytes:
            calls.append(current_job.asset_name)
            return b"new-image"

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            wrong_path = job.output_path.with_name("wrong_path_asset_old.png")
            (workspace / wrong_path).parent.mkdir(parents=True, exist_ok=True)
            (workspace / wrong_path).write_bytes(b"old-image")
            existing_manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [
                    self.existing_done_asset(job, path=wrong_path.as_posix())
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

        self.assertEqual(calls, ["wrong_path_asset"])
        self.assertEqual(manifest["assets"][0]["path"], job.output_path.as_posix())
        self.assertEqual(manifest["assets"][0]["attempts"], 1)

    def test_resume_prompt_hash_mismatch_does_not_skip(self) -> None:
        job = self.make_job("changed_prompt_asset")
        calls: list[str] = []

        def provider(current_job: ImageJob, config: ImageGenerationConfig) -> bytes:
            calls.append(current_job.asset_name)
            return b"new-image"

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            output_path = workspace / job.output_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"old-image")
            existing_manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [
                    self.existing_done_asset(
                        job,
                        prompt_hash_value=prompt_hash("old prompt"),
                    )
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

            regenerated_bytes = output_path.read_bytes()

        self.assertEqual(calls, ["changed_prompt_asset"])
        self.assertEqual(regenerated_bytes, b"new-image")
        self.assertEqual(manifest["assets"][0]["prompt_hash"], prompt_hash(job.prompt))

    def test_resume_skip_rebuilds_manifest_row_without_old_allowed_field_secrets(self) -> None:
        job = self.make_job("clean_skip_asset")
        secret_reference = {
            "asset_name": "secret_ref",
            "path": "out/sk-test-secret-1234567890.png",
            "purpose": "secret reference",
        }

        def provider(current_job: ImageJob, config: ImageGenerationConfig) -> bytes:
            raise AssertionError("provider should not be called for valid resume skip")

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            output_path = workspace / job.output_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"existing-image")
            existing_manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [
                    self.existing_done_asset(
                        job,
                        attempts=3,
                        references=[secret_reference],
                    )
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

        manifest_text = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        self.assertEqual(manifest["assets"][0]["status"], "done")
        self.assertEqual(manifest["assets"][0]["attempts"], 3)
        self.assertEqual(manifest["assets"][0]["references"], [])
        self.assertNotIn("sk-test-secret", manifest_text)

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

    def test_main_persists_manifest_and_report_after_wave_before_interruption(self) -> None:
        parent = self.make_job("persisted_parent")
        child = self.make_job("interrupted_child", depends_on=["persisted_parent"])
        calls: list[str] = []

        def provider(current_job: ImageJob, config: ImageGenerationConfig) -> bytes:
            calls.append(current_job.asset_name)
            if current_job.asset_name == child.asset_name:
                raise KeyboardInterrupt("stop after parent wave")
            return b"parent-image"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            jobs_path = root / "image-jobs.jsonl"
            manifest_path = root / "image-manifest.json"
            report_path = root / "image-generation-report.md"
            jobs_path.write_text(
                "".join(
                    json.dumps(job.to_dict(), ensure_ascii=False) + "\n"
                    for job in [parent, child]
                ),
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
                        with self.assertRaises(KeyboardInterrupt):
                            generate_images_module.main()

            self.assertTrue(
                manifest_path.exists(),
                "manifest should be persisted before interruption",
            )
            self.assertTrue(
                report_path.exists(),
                "report should be persisted before interruption",
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            report_text = report_path.read_text(encoding="utf-8")
            persisted_text = (
                json.dumps(manifest, ensure_ascii=False, sort_keys=True)
                + report_text
            )

        self.assertEqual(calls, ["persisted_parent", "interrupted_child"])
        self.assertEqual(
            [asset["asset_name"] for asset in manifest["assets"]],
            ["persisted_parent"],
        )
        self.assertEqual(manifest["assets"][0]["status"], "done")
        self.assertIn("- persisted_parent:", report_text)
        self.assertNotIn("api_key", persisted_text)
        self.assertNotIn("sk-test-secret", persisted_text)
        self.assertNotIn("https://provider.example/openai", persisted_text)

    def test_cli_reports_malformed_depends_on_without_traceback(self) -> None:
        job_data = self.make_job("bad_depends_on").to_dict()
        job_data["depends_on"] = None

        result = self.run_generate_images_cli_with_job_data(job_data)

        combined = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Image generation failed:", result.stdout)
        self.assertIn("line 1", result.stdout)
        self.assertIn("depends_on", result.stdout)
        self.assertNotIn("Traceback", combined)

    def test_cli_reports_malformed_reference_images_without_traceback(self) -> None:
        job_data = self.make_job("bad_reference_images").to_dict()
        job_data["reference_images"] = None

        result = self.run_generate_images_cli_with_job_data(job_data)

        combined = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Image generation failed:", result.stdout)
        self.assertIn("line 1", result.stdout)
        self.assertIn("reference_images", result.stdout)
        self.assertNotIn("Traceback", combined)


class ImageManifestValidationTests(unittest.TestCase):
    def make_job(self, name: str = "manifest_asset") -> ImageJob:
        return ImageJob(
            job_id=f"job-{name}",
            asset_name=name,
            asset_type="character",
            prompt=f"prompt for {name}",
            output_dir=sorted(ALLOWED_OUTPUT_DIRS)[0],
            output_file=f"{name}.png",
            depends_on=[],
            reference_images=[],
            provider="openai-compatible",
            model="gpt-image-2",
            size="16:9",
            status="pending",
        )

    def manifest_asset(
        self,
        job: ImageJob | None = None,
        **overrides: object,
    ) -> dict[str, object]:
        if job is None:
            job = self.make_job()
        asset: dict[str, object] = {
            "asset_name": job.asset_name,
            "asset_type": job.asset_type,
            "path": job.output_path.as_posix(),
            "status": "failed",
            "last_error": "provider failed",
            "prompt_hash": prompt_hash(job.prompt),
            "model": job.model,
            "size": job.size,
            "attempts": 1,
            "depends_on": list(job.depends_on),
            "references": [],
        }
        asset.update(overrides)
        return asset

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

    def test_validate_manifest_rejects_paths_outside_allowed_output_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_path = root / "docs" / "foo.png"
            docs_path.parent.mkdir(parents=True, exist_ok=True)
            docs_path.write_bytes(b"image")
            asset = self.manifest_asset(
                path="docs/foo.png",
                status="done",
            )
            asset.pop("last_error")
            manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [asset],
            }

            errors = validate_manifest(manifest, [], root)

            self.assertIn(
                "generated image path must start with one of",
                "; ".join(errors),
            )

    def test_validate_manifest_rejects_unknown_status(self) -> None:
        manifest = {
            "version": 1,
            "provider": "openai-compatible",
            "assets": [self.manifest_asset(status="queued")],
        }

        errors = validate_manifest(manifest, [], Path("."))

        self.assertIn(
            "status must be one of",
            "; ".join(errors),
        )

    def test_validate_manifest_rejects_missing_required_asset_fields(self) -> None:
        required_fields = ["asset_name", "asset_type", "status"]

        for field_name in required_fields:
            with self.subTest(field_name=field_name):
                asset = self.manifest_asset()
                asset[field_name] = ""
                manifest = {
                    "version": 1,
                    "provider": "openai-compatible",
                    "assets": [asset],
                }

                errors = validate_manifest(manifest, [], Path("."))

                self.assertIn(
                    f"{field_name} is required",
                    "; ".join(errors),
                )

    def test_validate_manifest_rejects_duplicate_asset_names(self) -> None:
        asset = self.manifest_asset()
        manifest = {
            "version": 1,
            "provider": "openai-compatible",
            "assets": [asset, dict(asset)],
        }

        errors = validate_manifest(manifest, [], Path("."))

        self.assertIn("duplicate asset_name: manifest_asset", "; ".join(errors))

    def test_validate_manifest_rejects_done_path_that_differs_from_job_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            job = self.make_job("path_mismatch")
            wrong_path = Path(job.output_dir) / "wrong.png"
            output_path = root / wrong_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"image")
            asset = self.manifest_asset(
                job,
                path=wrong_path.as_posix(),
                status="done",
            )
            asset.pop("last_error")
            manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [asset],
            }

            errors = validate_manifest(manifest, [job], root)

            self.assertIn("path must match job output", "; ".join(errors))

    def test_validate_manifest_rejects_stale_job_metadata_when_present(self) -> None:
        job = self.make_job("stale_metadata")
        manifest = {
            "version": 1,
            "provider": "openai-compatible",
            "assets": [
                self.manifest_asset(
                    job,
                    prompt_hash=prompt_hash("old prompt"),
                    model="old-model",
                    size="1:1",
                )
            ],
        }

        errors = validate_manifest(manifest, [job], Path("."))

        message = "; ".join(errors)
        self.assertIn("prompt_hash must match current job prompt", message)
        self.assertIn("model must match current job model", message)
        self.assertIn("size must match current job size", message)

    def test_validate_jobs_rejects_reference_images_without_real_paths(self) -> None:
        job = self.make_job("missing_reference_path")
        job.reference_images = [
            ReferenceImage(
                asset_name="林夜_黑袍造型",
                path="",
                purpose="人脸身份参考",
            )
        ]

        with self.assertRaises(ImageGenerationError) as context:
            validate_jobs([job])

        self.assertIn("reference path is required", str(context.exception))

    def test_validate_manifest_rejects_bad_reference_entries_and_missing_files(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            child = self.make_job("林夜_宗门礼服")
            child.reference_images = [
                ReferenceImage(
                    asset_name="林夜_黑袍造型",
                    path="人设资产/林夜_黑袍造型.png",
                    purpose="人脸身份参考",
                )
            ]
            output_path = root / child.output_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"child-image")
            manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [
                    self.manifest_asset(
                        child,
                        status="done",
                        references=[
                            {
                                "asset_name": "林夜_黑袍造型",
                                "path": "",
                                "purpose": "人脸身份参考",
                            },
                            {
                                "asset_name": "鬼王宗宗门大殿_母图",
                                "path": "../outside.png",
                                "purpose": "场景母图参考",
                            },
                        ],
                    )
                ],
            }

            errors = validate_manifest(manifest, [child], root)

        message = "; ".join(errors)
        self.assertIn("reference path is required", message)
        self.assertIn("reference path must stay under workspace", message)
        self.assertIn("references must match current job references", message)

    def test_validate_manifest_requires_reference_files_to_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            child = self.make_job("林夜_宗门礼服")
            child.reference_images = [
                ReferenceImage(
                    asset_name="林夜_黑袍造型",
                    path="人设资产/林夜_黑袍造型.png",
                    purpose="人脸身份参考",
                )
            ]
            output_path = root / child.output_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"child-image")
            asset = self.manifest_asset(
                child,
                status="done",
                references=[
                    {
                        "asset_name": "林夜_黑袍造型",
                        "path": "人设资产/林夜_黑袍造型.png",
                        "purpose": "人脸身份参考",
                    }
                ],
            )
            asset.pop("last_error")
            manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [asset],
            }

            errors = validate_manifest(manifest, [child], root)

        self.assertIn("reference image missing local file", "; ".join(errors))


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
                ("林夜_黑袍造型", "人设风格基准参考"),
                ("林夜_黑袍造型", "人脸身份参考"),
                ("林夜_黑袍造型", "旧造型参考"),
                ("鬼王宗宗门大殿_母图", "场景母图参考"),
            ],
        )
        self.assertEqual(
            [ref.path for ref in variant.reference_images],
            [
                "人设资产/林夜_黑袍造型.png",
                "人设资产/林夜_黑袍造型.png",
                "人设资产/林夜_黑袍造型.png",
                "场景资产/鬼王宗宗门大殿_母图.png",
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

    def test_build_jobs_preserves_user_requested_q_style_without_hardcoded_guard(
        self,
    ) -> None:
        text = """
### 图片1 = 林夜_Q版黑袍造型
GPT-image-2，16:9，3D Q版国漫，二头身，可爱夸张，白色背景。
"""

        jobs = build_jobs_from_asset_text(text, model="gpt-image-2", size="16:9")

        self.assertIn("3D Q版国漫", jobs[0].prompt)
        self.assertNotIn("非Q版", jobs[0].prompt)
        self.assertNotIn("非玩具感", jobs[0].prompt)
        self.assertNotIn("非卡通低龄化", jobs[0].prompt)

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

    def test_build_jobs_uses_asset_bible_sections_before_keyword_guessing(
        self,
    ) -> None:
        text = """
# Asset Bible

## Character Assets
### 图片1 = 鬼财神_财神殿执掌者铁算盘造型
GPT-image-2，16:9，角色三视图，白色背景。肥胖中年男子，铁算盘是身份道具，人物资产，不要做成单独道具。

## Prop, Interface, Beast, Vehicle Assets
### 图片2 = 天机一型手机_三视图
GPT-image-2，16:9，道具三视图，正面屏幕、背面摄像头、侧面厚度。
"""

        jobs = build_jobs_from_asset_text(text, model="gpt-image-2", size="16:9")

        self.assertEqual(jobs[0].asset_name, "鬼财神_财神殿执掌者铁算盘造型")
        self.assertEqual(jobs[0].asset_type, "character")
        self.assertEqual(jobs[0].output_dir, "人设资产")
        self.assertEqual(jobs[1].asset_name, "天机一型手机_三视图")
        self.assertEqual(jobs[1].asset_type, "prop")
        self.assertEqual(jobs[1].output_dir, "道具资产")

    def test_build_jobs_resolves_phone_family_references_to_local_paths(
        self,
    ) -> None:
        text = """
## Prop, Interface, Beast, Vehicle Assets

### 图片1 = 天机一型手机_三视图
GPT-image-2，16:9，道具三视图，正面屏幕、背面摄像头、侧面厚度。

### 图片2 = 神级文娱系统界面_商城状态
上传参考图：天机一型手机_三视图 = 图片1（手机母资产参考）
GPT-image-2，16:9，手机屏幕 UI，商城卡片必须保持手机外形、边框、摄像头、屏幕比例一致。
"""

        jobs = build_jobs_from_asset_text(text, model="gpt-image-2", size="16:9")

        interface_job = jobs[1]
        self.assertEqual(interface_job.depends_on, ["天机一型手机_三视图"])
        self.assertEqual(len(interface_job.reference_images), 1)
        self.assertEqual(interface_job.reference_images[0].asset_name, "天机一型手机_三视图")
        self.assertEqual(interface_job.reference_images[0].purpose, "手机母资产参考")
        self.assertEqual(interface_job.reference_images[0].path, "道具资产/天机一型手机_三视图.png")

    def test_build_jobs_auto_binds_phone_family_interfaces_to_phone_mother_asset(
        self,
    ) -> None:
        text = """
## 资产提示词

### 图片8 = 神级文娱系统界面_商城
GPT-image-2，16:9，脑内系统商城界面参考图，抖音纯享版和天机一型手机商品突出。

### 图片9 = 天机一型手机_三视图
GPT-image-2，16:9，天机一型手机三视图参考图，正面为屏幕与音符图标，背面为近似水果手机的简洁机身，侧面有锁屏键。

### 图片10 = 抖音纯享版_主界面与拍摄界面
GPT-image-2，16:9，抖音纯享版界面参考图，绑定天机一型手机正面屏幕，屏幕正面朝镜头，保持手机机身比例、边框和材质一致。
"""

        jobs = build_jobs_from_asset_text(text, model="gpt-image-2", size="16:9")

        mall, phone, douyin = jobs
        self.assertEqual(phone.asset_name, "天机一型手机_三视图")
        for job in (mall, douyin):
            self.assertEqual(job.depends_on, ["天机一型手机_三视图"])
            self.assertEqual(
                [(ref.asset_name, ref.path, ref.purpose) for ref in job.reference_images],
                [
                    (
                        "天机一型手机_三视图",
                        "道具资产/天机一型手机_三视图.png",
                        "手机母资产参考",
                    )
                ],
            )

    def test_build_jobs_preview_stage_outputs_only_first_scene_and_first_character(
        self,
    ) -> None:
        text = """
## Scene Assets
### 图片1 = 鬼王宗财神殿_母图
GPT-image-2，16:9，场景母图，财神殿。

## Character Assets
### 图片2 = 林夜_黑袍造型
GPT-image-2，16:9，角色三视图，白色背景。

### 图片3 = 鬼财神_财神殿执掌者铁算盘造型
GPT-image-2，16:9，角色三视图，铁算盘是身份道具。

## Prop, Interface, Beast, Vehicle Assets
### 图片4 = 天机一型手机_三视图
GPT-image-2，16:9，道具三视图，手机。
"""

        jobs = build_jobs_from_asset_text(
            text,
            model="gpt-image-2",
            size="16:9",
            style_stage="preview",
        )

        self.assertEqual(
            [job.asset_name for job in jobs],
            ["鬼王宗财神殿_母图", "林夜_黑袍造型"],
        )
        self.assertEqual([job.asset_type for job in jobs], ["scene", "character"])
        self.assertEqual([job.reference_images for job in jobs], [[], []])

    def test_build_jobs_after_style_confirmation_references_first_scene_and_character(
        self,
    ) -> None:
        text = """
## Scene Assets
### 图片1 = 鬼王宗财神殿_母图
GPT-image-2，16:9，Q版暗黑财神殿，场景母图。

### 图片2 = 财神殿侧廊_局部
GPT-image-2，16:9，侧廊局部场景。

## Character Assets
### 图片3 = 林夜_Q版黑袍造型
GPT-image-2，16:9，3D Q版国漫，二头身，可爱夸张，白色背景。

### 图片4 = 鬼财神_财神殿执掌者铁算盘造型
GPT-image-2，16:9，角色三视图，铁算盘是身份道具。

## Prop, Interface, Beast, Vehicle Assets
### 图片5 = 天机一型手机_三视图
GPT-image-2，16:9，道具三视图，手机。

### 图片6 = 神级文娱系统界面_商城状态
上传参考图：天机一型手机_三视图 = 图片5（手机母资产参考）
GPT-image-2，16:9，手机屏幕 UI。
"""

        jobs = build_jobs_from_asset_text(
            text,
            model="gpt-image-2",
            size="16:9",
            style_stage="confirmed",
        )

        scene_variant = jobs[1]
        first_character = jobs[2]
        character_variant = jobs[3]
        phone = jobs[4]
        interface = jobs[5]

        self.assertEqual(scene_variant.depends_on, ["鬼王宗财神殿_母图"])
        self.assertEqual(
            [(ref.asset_name, ref.path, ref.purpose) for ref in scene_variant.reference_images],
            [("鬼王宗财神殿_母图", "场景资产/鬼王宗财神殿_母图.png", "场景风格基准参考")],
        )
        self.assertEqual(first_character.reference_images, [])
        self.assertEqual(
            [(ref.asset_name, ref.path, ref.purpose) for ref in character_variant.reference_images],
            [("林夜_Q版黑袍造型", "人设资产/林夜_Q版黑袍造型.png", "人设风格基准参考")],
        )
        self.assertEqual(
            [(ref.asset_name, ref.path, ref.purpose) for ref in phone.reference_images],
            [("鬼王宗财神殿_母图", "场景资产/鬼王宗财神殿_母图.png", "场景风格基准参考")],
        )
        self.assertEqual(
            [
                (ref.asset_name, ref.path, ref.purpose)
                for ref in interface.reference_images
            ],
            [
                ("鬼王宗财神殿_母图", "场景资产/鬼王宗财神殿_母图.png", "场景风格基准参考"),
                ("天机一型手机_三视图", "道具资产/天机一型手机_三视图.png", "手机母资产参考"),
            ],
        )
        for job in jobs:
            self.assertNotIn("非Q版", job.prompt)
            self.assertNotIn("非玩具感", job.prompt)
            self.assertNotIn("非卡通低龄化", job.prompt)


if __name__ == "__main__":
    unittest.main()
