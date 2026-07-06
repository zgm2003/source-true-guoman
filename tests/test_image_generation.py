import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.image_generation_core import (
    ImageGenerationError,
    ImageJob,
    build_dependency_waves,
    load_jobs_jsonl,
    prompt_hash,
    validate_manifest,
    validate_jobs,
)


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


if __name__ == "__main__":
    unittest.main()
