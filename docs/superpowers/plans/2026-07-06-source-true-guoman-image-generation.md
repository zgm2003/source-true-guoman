# Source True Guoman Image Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a resumable, dependency-aware, OpenAI-compatible image generation layer for `source-true-guoman` assets.

**Architecture:** Keep `asset-bible` as the source of asset decisions, then add a file-based `image-generator` execution layer that builds image jobs, validates dependency order, calls a local OpenAI-compatible relay with retry, writes generated images into asset folders, and records bindings in `生产资产/_内部/image-manifest.json`. Downstream feed/copy-pack logic reads the manifest and never invents image paths.

**Tech Stack:** Python standard library, `unittest`, JSON/JSONL artifacts, PowerShell commands, existing Markdown skill/agent/reference files.

---

## File Structure

- Create: `agents/image-generator.md`  
  Specialist instructions for image generation after `asset-bible`; includes source-faithfulness boundary, dependency ordering, retry rules, local config, output folders, and manifest behavior.

- Create: `references/image-generation-format.md`  
  Canonical job JSONL, manifest JSON, report, command shape, folder policy, and downstream binding format.

- Create: `references/image-generation-retry-rules.md`  
  Retryable/non-retryable error taxonomy, backoff, resume semantics, blocked dependencies, and no-secret logging rules.

- Create: `scripts/image_generation_core.py`  
  Shared dataclasses and pure functions: job parsing, manifest parsing, validation, dependency graph, wave scheduling, prompt hashing, path normalization, and secret scanning.

- Create: `scripts/build_image_jobs.py`  
  CLI that parses a compact `asset-bible.md` or `## 资产提示词` block into `image-jobs.jsonl`.

- Create: `scripts/validate_image_manifest.py`  
  CLI that validates jobs and manifest state without calling the image API.

- Create: `scripts/generate_images.py`  
  CLI that loads jobs, schedules dependency waves, calls the OpenAI-compatible provider with retry/backoff, writes images, logs attempts, and updates the manifest/report.

- Create: `tests/test_image_generation.py`  
  Unit tests for job parsing, graph scheduling, manifest validation, retry, resume, output-folder policy, and no-secret logging.

- Modify: `.gitignore`  
  Ignore `.source-true-guoman.local.json` and local generation scratch files if needed.

- Modify: `SKILL.md`  
  Route image-generation intents to `agents/image-generator.md`; update default formal route to include optional `image-generator`.

- Modify: `agents/copy-packager.md`  
  Tell copy-packager to use `生产资产/_内部/image-manifest.json` when available and mark missing bindings as `需人工确认`.

- Modify: `references/copy-pack-format.md`  
  Document manifest-backed image binding shape.

- Modify: `agents/openai.yaml`  
  Add image generation to the short description/default prompt if stale.

---

### Task 1: Route Image Generation In Skill Text

**Files:**
- Create: `agents/image-generator.md`
- Create: `references/image-generation-format.md`
- Create: `references/image-generation-retry-rules.md`
- Modify: `SKILL.md`
- Modify: `agents/copy-packager.md`
- Modify: `references/copy-pack-format.md`
- Modify: `agents/openai.yaml`
- Test: `tests/test_init_workspace.py`

- [ ] **Step 1: Add failing routing tests**

Append these tests to `SkillTextRulesTests` in `tests/test_init_workspace.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_image_generator_agent_is_declared_and_routed tests.test_init_workspace.SkillTextRulesTests.test_image_generator_docs_preserve_source_contract_and_manifest_boundary tests.test_init_workspace.SkillTextRulesTests.test_copy_packager_uses_image_manifest_without_inventing_paths
```

Expected: failure because the image-generator agent and reference files do not exist yet.

- [ ] **Step 3: Create `agents/image-generator.md`**

Create the file with this content:

```markdown
# Image Generator Agent

Use this specialist after `asset-bible` exists and the user wants to generate images, batch-generate assets, connect `base_url` and `api_key`, or run image jobs concurrently.

## 保真契约

- 原作多少字就保留多少字.
- 不得由 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用.
- 不主动添加站起、起身、跪下、走动、抬手、收起法器; 道具动作必须有原文依据.

## Boundary

image-generator only executes approved image jobs from `asset-bible`. It must not rewrite source, change asset identity, compress dialogue, alter feed lines, or invent new production assets.

The generated-image binding source of truth is `生产资产/_内部/image-manifest.json`.

Generated image files belong in:

- `人设资产`
- `场景资产`
- `道具资产`

Internal jobs, logs, reports, and manifests belong under `生产资产/_内部/`.

## Required References

- Read `references/image-generation-format.md` before creating jobs or manifests.
- Read `references/image-generation-retry-rules.md` before running API calls, retry, resume, or dependency scheduling.

## Inputs

- `生产资产/_内部/asset-bible.md` or a saved feed package containing `## 资产提示词`.
- Existing generated images when referenced by asset-bible.
- Local OpenAI-compatible relay settings from environment variables or `.source-true-guoman.local.json`.

## Output

- `生产资产/_内部/image-jobs.jsonl`
- `生产资产/_内部/image-manifest.json`
- `生产资产/_内部/image-generation-report.md`
- `生产资产/_内部/image-generation-log.jsonl`
- Generated images under `人设资产`, `场景资产`, or `道具资产`.

## Procedure

1. Build image jobs from stable asset prompts and reference-purpose labels.
2. Validate jobs before generation: unique ids, stable asset names, supported output folders, existing dependencies, no cycles, and no output under `生产资产`.
3. Schedule jobs by dependency waves. Jobs in the same wave may run concurrently; jobs with `depends_on` wait for successful parent images.
4. Use the configured OpenAI-compatible provider. Treat the relay as unreliable.
5. Retry retryable failures with exponential backoff and jitter. Do not retry non-retryable configuration, authentication, or job-validation errors.
6. Save successful API outputs as local `.png` files.
7. Update `image-manifest.json` after each completed, failed, or blocked job.
8. Write a generation report with failures first, then blocked jobs, then successes.
9. Never write API keys into manifest, report, or logs.
10. On resume, skip already successful outputs unless the user uses `--force`.

## Copy-Pack Boundary

copy-packager may read `image-manifest.json` for `上传参考图` bindings. Copy packs must not invent image paths. Missing or failed images must be marked `需人工确认（image-generator failed or blocked）`.
```

- [ ] **Step 4: Create `references/image-generation-format.md`**

Create the file with this content:

```markdown
# Image Generation Format

Use this file when creating image generation jobs, manifests, and reports.

## Files

- Jobs: `生产资产/_内部/image-jobs.jsonl`
- Manifest: `生产资产/_内部/image-manifest.json`
- Report: `生产资产/_内部/image-generation-report.md`
- Log: `生产资产/_内部/image-generation-log.jsonl`

Generated image files go to:

- `人设资产/<asset-name>.png`
- `场景资产/<asset-name>.png`
- `道具资产/<asset-name>.png`

Do not write generated images under `生产资产`.

## Job JSONL Shape

Each line is one image job:

```json
{"job_id":"character-linye-black-robe","asset_name":"林夜_黑袍造型","asset_type":"character","prompt":"GPT-image-2，16:9，3D国漫，角色三视图，白色背景。","output_dir":"人设资产","output_file":"林夜_黑袍造型.png","depends_on":[],"reference_images":[],"provider":"openai-compatible","model":"gpt-image-2","size":"16:9","status":"pending"}
```

Required fields:

- `job_id`
- `asset_name`
- `asset_type`
- `prompt`
- `output_dir`
- `output_file`
- `depends_on`
- `reference_images`
- `provider`
- `model`
- `size`
- `status`

`depends_on` contains stable asset names. `reference_images` contains objects with `asset_name`, `path`, and `purpose`.

## Manifest Shape

```json
{
  "version": 1,
  "provider": "openai-compatible",
  "base_url_label": "local-relay",
  "assets": [
    {
      "asset_name": "林夜_黑袍造型",
      "asset_type": "character",
      "path": "人设资产/林夜_黑袍造型.png",
      "status": "done",
      "prompt_hash": "sha256:example",
      "model": "gpt-image-2",
      "size": "16:9",
      "attempts": 1,
      "depends_on": [],
      "references": []
    }
  ]
}
```

Do not include API keys in manifests, logs, reports, or copy packs.

## Copy Pack Binding

Copy packs may use manifest paths:

```text
上传参考图：
- 角色1 = 林夜_黑袍造型 = 人设资产/林夜_黑袍造型.png
```

Copy packs must not invent image paths. If manifest status is missing, failed, or blocked, write:

```text
- 角色1 = 林夜_黑袍造型 = 需人工确认（image-generator failed or blocked）
```
```

- [ ] **Step 5: Create `references/image-generation-retry-rules.md`**

Create the file with this content:

```markdown
# Image Generation Retry Rules

Use this file when calling the local OpenAI-compatible image relay.

## Retryable Errors

- network timeout
- connection reset
- HTTP 429
- HTTP 500
- HTTP 502
- HTTP 503
- HTTP 504
- empty response
- malformed response that may be transient
- temporary image URL download failure

## Non-retryable Errors

- missing API key
- invalid base URL
- invalid job JSON
- missing dependency output
- unsupported output folder
- cyclic dependencies
- authentication failure
- permanent provider validation error

## Backoff

Use exponential backoff with jitter. Default settings:

- max retries: `3`
- base delay seconds: `1.0`
- max delay seconds: `20.0`

## Dependency Failure

Failed dependencies block dependent jobs. Blocked jobs must record which stable asset names blocked them.

## Resume

On resume, skip manifest assets with `status = done` and an existing local image path. Retry `failed`, `blocked`, and `pending` jobs after dependency validation.

## Secret Handling

Do not log API keys. Reports should state whether configuration was present, not reveal secret values.
```

- [ ] **Step 6: Update `SKILL.md` routing**

Add `agents/image-generator.md` to the declared specialist list and add this route under Agent pack routing:

```markdown
- "生成图片", "批量生图", "把资产图跑出来", "接入 base_url/api_key 生图", "并发生成资产图", or "根据 asset-bible 生成图片": read `agents/image-generator.md`, `references/image-generation-format.md`, and `references/image-generation-retry-rules.md`; run `python scripts/build_image_jobs.py --asset-bible 生产资产/_内部/asset-bible.md --out 生产资产/_内部/image-jobs.jsonl`, `python scripts/generate_images.py --jobs 生产资产/_内部/image-jobs.jsonl --manifest 生产资产/_内部/image-manifest.json --resume`, and `python scripts/validate_image_manifest.py 生产资产/_内部/image-manifest.json --jobs 生产资产/_内部/image-jobs.jsonl` when saved artifacts are involved. Image generation runs after asset-bible and before downstream copy-pack image bindings; it must respect dependency waves and retry relay failures.
```

Change default formal batch route text from:

```text
source-indexer -> asset-bible -> faithful-feed -> feed-auditor -> copy-packager
```

to:

```text
source-indexer -> asset-bible -> image-generator(optional) -> faithful-feed -> feed-auditor -> copy-packager
```

- [ ] **Step 7: Update copy-packager docs**

In `agents/copy-packager.md`, add:

```markdown
When `生产资产/_内部/image-manifest.json` exists, use it for image bindings. Copy packs must not invent image paths. If a visible asset has missing, failed, or blocked manifest status, write `需人工确认（image-generator failed or blocked）`.
```

In `references/copy-pack-format.md`, add the same manifest-backed binding rule plus this example:

```text
上传参考图：
- 角色1 = 林夜_黑袍造型 = 人设资产/林夜_黑袍造型.png
- 场景1 = 鬼王宗宗门大殿_母图 = 需人工确认（image-generator failed or blocked）
```

- [ ] **Step 8: Update `agents/openai.yaml`**

Change `short_description` to include image generation:

```yaml
short_description: "原著保真3D国漫短剧资产、连续投喂稿、运镜库选择、并发资产生图与复制投喂包"
```

Change `default_prompt` to include image manifest wording:

```yaml
default_prompt: "Use $source-true-guoman to turn this novel chapter into source-faithful 3D guoman asset prompts, optional dependency-aware image generation with a local OpenAI-compatible relay, continuous video feed blocks with a selected camera library, and optional paste-ready copy packs."
```

- [ ] **Step 9: Run routing tests**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_image_generator_agent_is_declared_and_routed tests.test_init_workspace.SkillTextRulesTests.test_image_generator_docs_preserve_source_contract_and_manifest_boundary tests.test_init_workspace.SkillTextRulesTests.test_copy_packager_uses_image_manifest_without_inventing_paths
```

Expected: pass.

- [ ] **Step 10: Commit**

```powershell
git add SKILL.md agents/image-generator.md references/image-generation-format.md references/image-generation-retry-rules.md agents/copy-packager.md references/copy-pack-format.md agents/openai.yaml tests/test_init_workspace.py
git commit -m "feat: route image generation workflow"
```

---

### Task 2: Add Core Image Job And Dependency Graph Model

**Files:**
- Create: `scripts/image_generation_core.py`
- Create: `tests/test_image_generation.py`

- [ ] **Step 1: Write failing core model tests**

Create `tests/test_image_generation.py` with:

```python
import tempfile
import unittest
from pathlib import Path

from scripts.image_generation_core import (
    ImageGenerationError,
    ImageJob,
    build_dependency_waves,
    load_jobs_jsonl,
    prompt_hash,
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_image_generation.ImageGenerationCoreTests
```

Expected: fail with `ModuleNotFoundError: No module named 'scripts.image_generation_core'`.

- [ ] **Step 3: Create `scripts/image_generation_core.py`**

Create the file with this implementation:

```python
#!/usr/bin/env python3
"""Core helpers for source-true-guoman image generation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ALLOWED_OUTPUT_DIRS = {"人设资产", "场景资产", "道具资产"}
SECRET_KEY_NAMES = {"api_key", "authorization", "bearer", "token"}


class ImageGenerationError(ValueError):
    """Raised when image generation inputs or state are invalid."""


@dataclass
class ReferenceImage:
    asset_name: str
    path: str
    purpose: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReferenceImage":
        return cls(
            asset_name=str(data.get("asset_name", "")).strip(),
            path=str(data.get("path", "")).strip(),
            purpose=str(data.get("purpose", "")).strip(),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "asset_name": self.asset_name,
            "path": self.path,
            "purpose": self.purpose,
        }


@dataclass
class ImageJob:
    job_id: str
    asset_name: str
    asset_type: str
    prompt: str
    output_dir: str
    output_file: str
    depends_on: list[str]
    reference_images: list[ReferenceImage]
    provider: str
    model: str
    size: str
    status: str = "pending"

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir) / self.output_file

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImageJob":
        references = [
            ReferenceImage.from_dict(item)
            for item in data.get("reference_images", [])
            if isinstance(item, dict)
        ]
        return cls(
            job_id=str(data.get("job_id", "")).strip(),
            asset_name=str(data.get("asset_name", "")).strip(),
            asset_type=str(data.get("asset_type", "")).strip(),
            prompt=str(data.get("prompt", "")).strip(),
            output_dir=str(data.get("output_dir", "")).strip(),
            output_file=str(data.get("output_file", "")).strip(),
            depends_on=[str(item).strip() for item in data.get("depends_on", [])],
            reference_images=references,
            provider=str(data.get("provider", "openai-compatible")).strip(),
            model=str(data.get("model", "")).strip(),
            size=str(data.get("size", "")).strip(),
            status=str(data.get("status", "pending")).strip(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "asset_name": self.asset_name,
            "asset_type": self.asset_type,
            "prompt": self.prompt,
            "output_dir": self.output_dir,
            "output_file": self.output_file,
            "depends_on": self.depends_on,
            "reference_images": [ref.to_dict() for ref in self.reference_images],
            "provider": self.provider,
            "model": self.model,
            "size": self.size,
            "status": self.status,
        }


def prompt_hash(prompt: str) -> str:
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def load_jobs_jsonl(path: Path) -> list[ImageJob]:
    jobs: list[ImageJob] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as error:
            raise ImageGenerationError(f"line {line_number}: invalid JSON") from error
        if not isinstance(data, dict):
            raise ImageGenerationError(f"line {line_number}: job must be an object")
        jobs.append(ImageJob.from_dict(data))
    return jobs


def write_jobs_jsonl(path: Path, jobs: list[ImageJob]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(
        json.dumps(job.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
        for job in jobs
    )
    path.write_text(text, encoding="utf-8")


def validate_jobs(jobs: list[ImageJob]) -> list[str]:
    errors: list[str] = []
    job_ids: set[str] = set()
    asset_names: set[str] = set()

    for job in jobs:
        if not job.job_id:
            errors.append("job_id is required")
        elif job.job_id in job_ids:
            errors.append(f"duplicate job_id: {job.job_id}")
        job_ids.add(job.job_id)

        if not job.asset_name:
            errors.append(f"{job.job_id}: asset_name is required")
        elif job.asset_name in asset_names:
            errors.append(f"duplicate asset_name: {job.asset_name}")
        asset_names.add(job.asset_name)

        if not job.prompt:
            errors.append(f"{job.asset_name}: prompt is required")
        if job.output_dir not in ALLOWED_OUTPUT_DIRS:
            errors.append(
                f"{job.asset_name}: output_dir must be one of {sorted(ALLOWED_OUTPUT_DIRS)}"
            )
        if not job.output_file.endswith(".png"):
            errors.append(f"{job.asset_name}: output_file must end with .png")
        if Path(job.output_file).name != job.output_file:
            errors.append(f"{job.asset_name}: output_file must be a file name only")

    known_assets = {job.asset_name for job in jobs}
    for job in jobs:
        for dependency in job.depends_on:
            if dependency not in known_assets:
                errors.append(f"{job.asset_name}: unknown dependency {dependency}")

    if errors:
        raise ImageGenerationError("; ".join(errors))
    return errors


def build_dependency_waves(jobs: list[ImageJob]) -> list[list[ImageJob]]:
    validate_jobs(jobs)
    by_asset = {job.asset_name: job for job in jobs}
    remaining = set(by_asset)
    completed: set[str] = set()
    waves: list[list[ImageJob]] = []

    while remaining:
        ready_names = [
            asset_name
            for asset_name in remaining
            if all(dependency in completed for dependency in by_asset[asset_name].depends_on)
        ]
        if not ready_names:
            unresolved = ", ".join(sorted(remaining))
            raise ImageGenerationError(f"cyclic dependencies or blocked graph: {unresolved}")
        ready_names.sort(key=lambda name: jobs.index(by_asset[name]))
        wave = [by_asset[name] for name in ready_names]
        waves.append(wave)
        completed.update(ready_names)
        remaining.difference_update(ready_names)

    return waves


def contains_secret_text(value: str) -> bool:
    lowered = value.casefold()
    return any(secret in lowered for secret in SECRET_KEY_NAMES)
```

- [ ] **Step 4: Run core tests**

Run:

```powershell
python -m unittest tests.test_image_generation.ImageGenerationCoreTests
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add scripts/image_generation_core.py tests/test_image_generation.py
git commit -m "feat: add image generation core graph"
```

---

### Task 3: Add Image Manifest Validation

**Files:**
- Modify: `scripts/image_generation_core.py`
- Create: `scripts/validate_image_manifest.py`
- Modify: `tests/test_image_generation.py`

- [ ] **Step 1: Add failing manifest tests**

Append to `tests/test_image_generation.py`:

```python
from scripts.image_generation_core import validate_manifest


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
```

Also add imports at the top:

```python
import subprocess
import sys
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_image_generation.ImageManifestValidationTests
```

Expected: fail because `validate_manifest` and the CLI do not exist.

- [ ] **Step 3: Extend `scripts/image_generation_core.py`**

Add these functions:

```python
def _walk_json_values(value: Any) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if contains_secret_text(str(key)):
                found.append((str(key), str(child)))
            found.extend(_walk_json_values(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_json_values(child))
    elif isinstance(value, str) and contains_secret_text(value):
        found.append(("value", value))
    return found


def validate_manifest(
    manifest: dict[str, Any], jobs: list[ImageJob], workspace: Path
) -> list[str]:
    errors: list[str] = []
    if _walk_json_values(manifest):
        errors.append("manifest must not contain secret key names")

    assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        return ["manifest assets must be a list"]

    job_names = {job.asset_name for job in jobs}
    for asset in assets:
        if not isinstance(asset, dict):
            errors.append("manifest asset entry must be an object")
            continue
        asset_name = str(asset.get("asset_name", "")).strip()
        path_text = str(asset.get("path", "")).strip()
        status = str(asset.get("status", "")).strip()

        if job_names and asset_name and asset_name not in job_names:
            errors.append(f"{asset_name}: manifest asset not present in jobs")
        if path_text.startswith("生产资产/") or path_text.startswith("生产资产\\"):
            errors.append(f"{asset_name}: generated image path must not be under 生产资产")
        if status == "done":
            image_path = workspace / path_text
            if not image_path.is_file():
                errors.append(f"{asset_name}: done asset missing local file {path_text}")
        if status in {"failed", "blocked"} and not asset.get("last_error"):
            errors.append(f"{asset_name}: {status} asset must record last_error")

    return errors
```

- [ ] **Step 4: Create `scripts/validate_image_manifest.py`**

Create the file:

```python
#!/usr/bin/env python3
"""Validate source-true-guoman image generation manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.image_generation_core import load_jobs_jsonl, validate_manifest
except ModuleNotFoundError:
    from image_generation_core import load_jobs_jsonl, validate_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate image manifest files.")
    parser.add_argument("manifest", help="Path to image-manifest.json")
    parser.add_argument("--jobs", required=True, help="Path to image-jobs.jsonl")
    parser.add_argument(
        "--workspace",
        default=".",
        help="Workspace root used to resolve generated image paths.",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    jobs_path = Path(args.jobs).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    jobs = load_jobs_jsonl(jobs_path)
    errors = validate_manifest(manifest, jobs, workspace)

    if errors:
        print("Image manifest validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Image manifest validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run manifest tests**

Run:

```powershell
python -m unittest tests.test_image_generation.ImageManifestValidationTests
```

Expected: pass.

- [ ] **Step 6: Commit**

```powershell
git add scripts/image_generation_core.py scripts/validate_image_manifest.py tests/test_image_generation.py
git commit -m "feat: validate image generation manifests"
```

---

### Task 4: Build Image Jobs From Asset Prompts

**Files:**
- Create: `scripts/build_image_jobs.py`
- Modify: `scripts/image_generation_core.py`
- Modify: `tests/test_image_generation.py`

- [ ] **Step 1: Add failing job builder tests**

Append to `tests/test_image_generation.py`:

```python
from scripts.build_image_jobs import build_jobs_from_asset_text


class BuildImageJobsTests(unittest.TestCase):
    def test_build_jobs_from_asset_prompt_headings(self) -> None:
        text = """
## 资产提示词

### 图片1 = 林夜_黑袍造型
GPT-image-2，16:9，3D国漫。角色三视图，白色背景。

### 图片2 = 鬼王宗宗门大殿_母图
GPT-image-2，16:9，3D国漫。空场景，宗门大殿。

### 图片3 = 林夜_宗门礼服
上传参考图：林夜_黑袍造型 = 图片1（人脸身份参考）
GPT-image-2，16:9，3D国漫。保持同一张脸，换宗门礼服。
"""

        jobs = build_jobs_from_asset_text(text, model="gpt-image-2", size="16:9")

        self.assertEqual([job.asset_name for job in jobs], ["林夜_黑袍造型", "鬼王宗宗门大殿_母图", "林夜_宗门礼服"])
        self.assertEqual(jobs[0].output_dir, "人设资产")
        self.assertEqual(jobs[1].output_dir, "场景资产")
        self.assertEqual(jobs[2].depends_on, ["林夜_黑袍造型"])
        self.assertEqual(jobs[2].reference_images[0].purpose, "人脸身份参考")

    def test_build_image_jobs_cli_writes_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            asset_bible = root / "asset-bible.md"
            jobs_path = root / "image-jobs.jsonl"
            asset_bible.write_text(
                "## 资产提示词\n\n### 图片1 = 万魂幡_单体\nGPT-image-2，16:9，道具名单体参考图，只生成一个完整主体。\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "build_image_jobs.py"),
                    "--asset-bible",
                    str(asset_bible),
                    "--out",
                    str(jobs_path),
                    "--model",
                    "gpt-image-2",
                    "--size",
                    "16:9",
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(jobs_path.is_file())
            jobs = load_jobs_jsonl(jobs_path)
            self.assertEqual(jobs[0].asset_name, "万魂幡_单体")
            self.assertEqual(jobs[0].output_dir, "道具资产")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_image_generation.BuildImageJobsTests
```

Expected: fail because `scripts.build_image_jobs` does not exist.

- [ ] **Step 3: Create `scripts/build_image_jobs.py`**

Create the file:

```python
#!/usr/bin/env python3
"""Build image generation jobs from source-true-guoman asset prompts."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    from scripts.image_generation_core import (
        ImageJob,
        ReferenceImage,
        validate_jobs,
        write_jobs_jsonl,
    )
except ModuleNotFoundError:
    from image_generation_core import ImageJob, ReferenceImage, validate_jobs, write_jobs_jsonl


HEADING_RE = re.compile(r"^###\s+图片\d+\s*=\s*(.+?)\s*$")
REFERENCE_RE = re.compile(r"([^=；;：:]+?)\s*=\s*图片\d+（([^）]+)）")


def infer_asset_type(asset_name: str, prompt: str) -> tuple[str, str]:
    combined = f"{asset_name}\n{prompt}"
    if "母图" in asset_name or "场景" in combined or "空场景" in combined:
        return "scene", "场景资产"
    if "单体" in asset_name or "道具" in combined or "界面" in asset_name or "系统界面" in asset_name:
        return "prop", "道具资产"
    return "character", "人设资产"


def slug_job_id(asset_type: str, asset_name: str) -> str:
    cleaned = re.sub(r"\s+", "-", asset_name.strip())
    return f"{asset_type}-{cleaned}"


def extract_references(prompt: str) -> tuple[list[str], list[ReferenceImage]]:
    depends_on: list[str] = []
    references: list[ReferenceImage] = []
    for line in prompt.splitlines():
        if "上传参考图" not in line:
            continue
        for match in REFERENCE_RE.finditer(line):
            asset_name = match.group(1).replace("上传参考图", "").strip(" ：:")
            purpose = match.group(2).strip()
            if not asset_name:
                continue
            depends_on.append(asset_name)
            references.append(
                ReferenceImage(
                    asset_name=asset_name,
                    path="",
                    purpose=purpose,
                )
            )
    deduped_depends = list(dict.fromkeys(depends_on))
    return deduped_depends, references


def build_jobs_from_asset_text(
    text: str, model: str, size: str, provider: str = "openai-compatible"
) -> list[ImageJob]:
    jobs: list[ImageJob] = []
    current_name: str | None = None
    current_lines: list[str] = []

    def flush_current() -> None:
        if current_name is None:
            return
        prompt = "\n".join(current_lines).strip()
        asset_type, output_dir = infer_asset_type(current_name, prompt)
        depends_on, references = extract_references(prompt)
        jobs.append(
            ImageJob(
                job_id=slug_job_id(asset_type, current_name),
                asset_name=current_name,
                asset_type=asset_type,
                prompt=prompt,
                output_dir=output_dir,
                output_file=f"{current_name}.png",
                depends_on=depends_on,
                reference_images=references,
                provider=provider,
                model=model,
                size=size,
                status="pending",
            )
        )

    for raw_line in text.splitlines():
        match = HEADING_RE.match(raw_line.strip())
        if match:
            flush_current()
            current_name = match.group(1).strip()
            current_lines = []
            continue
        if current_name is not None:
            current_lines.append(raw_line)

    flush_current()
    validate_jobs(jobs)
    return jobs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build image jobs from asset prompts.")
    parser.add_argument("--asset-bible", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model", default="gpt-image-2")
    parser.add_argument("--size", default="16:9")
    parser.add_argument("--provider", default="openai-compatible")
    args = parser.parse_args()

    source_path = Path(args.asset_bible).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    jobs = build_jobs_from_asset_text(
        source_path.read_text(encoding="utf-8"),
        model=args.model,
        size=args.size,
        provider=args.provider,
    )
    write_jobs_jsonl(out_path, jobs)
    print(f"Wrote {len(jobs)} image jobs to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run builder tests**

Run:

```powershell
python -m unittest tests.test_image_generation.BuildImageJobsTests
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add scripts/build_image_jobs.py tests/test_image_generation.py
git commit -m "feat: build image jobs from asset prompts"
```

---

### Task 5: Add OpenAI-Compatible Provider, Retry, And Logging

**Files:**
- Modify: `scripts/generate_images.py`
- Modify: `scripts/image_generation_core.py`
- Modify: `tests/test_image_generation.py`
- Modify: `.gitignore`

- [ ] **Step 1: Add failing provider and retry tests**

Append to `tests/test_image_generation.py`:

```python
from scripts.generate_images import (
    ImageGenerationConfig,
    RetryableProviderError,
    run_job_with_retry,
)


class ProviderRetryTests(unittest.TestCase):
    def make_job(self) -> ImageJob:
        return ImageJob(
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

    def test_run_job_with_retry_recovers_from_transient_failures(self) -> None:
        calls: list[str] = []

        def provider(job: ImageJob, config: ImageGenerationConfig) -> bytes:
            calls.append(job.asset_name)
            if len(calls) < 3:
                raise RetryableProviderError("HTTP 503")
            return b"png-bytes"

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = ImageGenerationConfig(
                base_url="http://local.test",
                api_key="local-secret",
                model="gpt-image-2",
                size="16:9",
                timeout_seconds=5,
                max_retries=3,
                retry_base_seconds=0,
                retry_max_seconds=0,
                concurrency=1,
            )

            result = run_job_with_retry(self.make_job(), config, workspace, provider)

            self.assertEqual(result["status"], "done")
            self.assertEqual(result["attempts"], 3)
            self.assertEqual((workspace / "人设资产" / "林夜_黑袍造型.png").read_bytes(), b"png-bytes")

    def test_run_job_with_retry_records_failure_after_retry_budget(self) -> None:
        def provider(job: ImageJob, config: ImageGenerationConfig) -> bytes:
            raise RetryableProviderError("HTTP 504")

        with tempfile.TemporaryDirectory() as temp_dir:
            config = ImageGenerationConfig(
                base_url="http://local.test",
                api_key="local-secret",
                model="gpt-image-2",
                size="16:9",
                timeout_seconds=5,
                max_retries=2,
                retry_base_seconds=0,
                retry_max_seconds=0,
                concurrency=1,
            )

            result = run_job_with_retry(self.make_job(), config, Path(temp_dir), provider)

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["attempts"], 3)
            self.assertIn("HTTP 504", result["last_error"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_image_generation.ProviderRetryTests
```

Expected: fail because `scripts/generate_images.py` does not exist.

- [ ] **Step 3: Add `.gitignore` entry**

Append:

```gitignore
.source-true-guoman.local.json
```

- [ ] **Step 4: Create `scripts/generate_images.py` provider and retry foundation**

Create the file with this foundation:

```python
#!/usr/bin/env python3
"""Generate source-true-guoman image assets with retry and resume support."""

from __future__ import annotations

import argparse
import base64
import json
import os
import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

try:
    from scripts.image_generation_core import (
        ImageJob,
        build_dependency_waves,
        load_jobs_jsonl,
        prompt_hash,
    )
except ModuleNotFoundError:
    from image_generation_core import ImageJob, build_dependency_waves, load_jobs_jsonl, prompt_hash


class RetryableProviderError(RuntimeError):
    """Provider error that should be retried."""


class NonRetryableProviderError(RuntimeError):
    """Provider error that should stop immediately."""


@dataclass
class ImageGenerationConfig:
    base_url: str
    api_key: str
    model: str
    size: str
    timeout_seconds: int
    max_retries: int
    retry_base_seconds: float
    retry_max_seconds: float
    concurrency: int


ProviderCallable = Callable[[ImageJob, ImageGenerationConfig], bytes]


def load_config_from_env() -> ImageGenerationConfig:
    base_url = os.environ.get("SOURCE_TRUE_IMAGE_BASE_URL", "").strip()
    api_key = os.environ.get("SOURCE_TRUE_IMAGE_API_KEY", "").strip()
    if not base_url:
        raise NonRetryableProviderError("SOURCE_TRUE_IMAGE_BASE_URL is required")
    if not api_key:
        raise NonRetryableProviderError("SOURCE_TRUE_IMAGE_API_KEY is required")
    return ImageGenerationConfig(
        base_url=base_url.rstrip("/"),
        api_key=api_key,
        model=os.environ.get("SOURCE_TRUE_IMAGE_MODEL", "gpt-image-2"),
        size=os.environ.get("SOURCE_TRUE_IMAGE_SIZE", "16:9"),
        timeout_seconds=int(os.environ.get("SOURCE_TRUE_IMAGE_TIMEOUT_SECONDS", "120")),
        max_retries=int(os.environ.get("SOURCE_TRUE_IMAGE_MAX_RETRIES", "3")),
        retry_base_seconds=float(os.environ.get("SOURCE_TRUE_IMAGE_RETRY_BASE_SECONDS", "1.0")),
        retry_max_seconds=float(os.environ.get("SOURCE_TRUE_IMAGE_RETRY_MAX_SECONDS", "20.0")),
        concurrency=int(os.environ.get("SOURCE_TRUE_IMAGE_CONCURRENCY", "3")),
    )


def retry_delay(config: ImageGenerationConfig, attempt_index: int) -> float:
    base = min(config.retry_max_seconds, config.retry_base_seconds * (2 ** attempt_index))
    return base + random.uniform(0, base * 0.2 if base else 0)


def openai_compatible_provider(job: ImageJob, config: ImageGenerationConfig) -> bytes:
    payload = {
        "model": job.model or config.model,
        "prompt": job.prompt,
        "size": job.size or config.size,
        "n": 1,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{config.base_url}/v1/images/generations",
        data=body,
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
            response_body = response.read()
    except urllib.error.HTTPError as error:
        if error.code in {429, 500, 502, 503, 504}:
            raise RetryableProviderError(f"HTTP {error.code}") from error
        if error.code in {401, 403}:
            raise NonRetryableProviderError(f"HTTP {error.code}") from error
        raise NonRetryableProviderError(f"HTTP {error.code}") from error
    except (TimeoutError, urllib.error.URLError) as error:
        raise RetryableProviderError(str(error)) from error

    try:
        data = json.loads(response_body.decode("utf-8"))
    except json.JSONDecodeError as error:
        raise RetryableProviderError("malformed JSON response") from error

    image_items = data.get("data", [])
    if not image_items:
        raise RetryableProviderError("empty image response")
    first = image_items[0]
    if "b64_json" in first:
        return base64.b64decode(first["b64_json"])
    if "url" in first:
        return download_image(first["url"], config.timeout_seconds)
    raise RetryableProviderError("image response missing b64_json or url")


def download_image(url: str, timeout_seconds: int) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
            return response.read()
    except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError) as error:
        raise RetryableProviderError(f"image download failed: {error}") from error


def run_job_with_retry(
    job: ImageJob,
    config: ImageGenerationConfig,
    workspace: Path,
    provider: ProviderCallable = openai_compatible_provider,
) -> dict[str, Any]:
    output_path = workspace / job.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    attempts = 0
    last_error = ""

    for attempt_index in range(config.max_retries + 1):
        attempts += 1
        try:
            image_bytes = provider(job, config)
            output_path.write_bytes(image_bytes)
            return {
                "asset_name": job.asset_name,
                "asset_type": job.asset_type,
                "path": job.output_path.as_posix(),
                "status": "done",
                "prompt_hash": prompt_hash(job.prompt),
                "model": job.model or config.model,
                "size": job.size or config.size,
                "attempts": attempts,
                "depends_on": job.depends_on,
                "references": [ref.to_dict() for ref in job.reference_images],
            }
        except NonRetryableProviderError as error:
            return {
                "asset_name": job.asset_name,
                "asset_type": job.asset_type,
                "path": job.output_path.as_posix(),
                "status": "failed",
                "attempts": attempts,
                "last_error": str(error),
                "depends_on": job.depends_on,
                "references": [ref.to_dict() for ref in job.reference_images],
            }
        except RetryableProviderError as error:
            last_error = str(error)
            if attempt_index < config.max_retries:
                time.sleep(retry_delay(config, attempt_index))

    return {
        "asset_name": job.asset_name,
        "asset_type": job.asset_type,
        "path": job.output_path.as_posix(),
        "status": "failed",
        "attempts": attempts,
        "last_error": last_error,
        "depends_on": job.depends_on,
        "references": [ref.to_dict() for ref in job.reference_images],
    }
```

- [ ] **Step 5: Run provider retry tests**

Run:

```powershell
python -m unittest tests.test_image_generation.ProviderRetryTests
```

Expected: pass.

- [ ] **Step 6: Commit**

```powershell
git add .gitignore scripts/generate_images.py tests/test_image_generation.py
git commit -m "feat: add image provider retry foundation"
```

---

### Task 6: Add Concurrent Wave Runner, Resume, Logs, And Report

**Files:**
- Modify: `scripts/generate_images.py`
- Modify: `tests/test_image_generation.py`

- [ ] **Step 1: Add failing runner tests**

Append to `tests/test_image_generation.py`:

```python
from scripts.generate_images import run_generation


class ImageGenerationRunnerTests(unittest.TestCase):
    def make_job(self, name: str, depends_on: list[str] | None = None) -> ImageJob:
        return ImageJob(
            job_id=f"job-{name}",
            asset_name=name,
            asset_type="character",
            prompt=f"prompt {name}",
            output_dir="人设资产",
            output_file=f"{name}.png",
            depends_on=depends_on or [],
            reference_images=[],
            provider="openai-compatible",
            model="gpt-image-2",
            size="16:9",
            status="pending",
        )

    def test_run_generation_respects_dependency_order_and_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            jobs = [
                self.make_job("林夜_黑袍造型"),
                self.make_job("林夜_宗门礼服", depends_on=["林夜_黑袍造型"]),
            ]
            calls: list[str] = []

            def provider(job: ImageJob, config: ImageGenerationConfig) -> bytes:
                calls.append(job.asset_name)
                return job.asset_name.encode("utf-8")

            config = ImageGenerationConfig(
                base_url="http://local.test",
                api_key="local-secret",
                model="gpt-image-2",
                size="16:9",
                timeout_seconds=5,
                max_retries=0,
                retry_base_seconds=0,
                retry_max_seconds=0,
                concurrency=4,
            )

            manifest = run_generation(jobs, config, workspace, provider)
            second_manifest = run_generation(jobs, config, workspace, provider, existing_manifest=manifest, resume=True)

            self.assertEqual(calls, ["林夜_黑袍造型", "林夜_宗门礼服"])
            self.assertEqual([asset["status"] for asset in manifest["assets"]], ["done", "done"])
            self.assertEqual(len(second_manifest["assets"]), 2)

    def test_run_generation_blocks_dependency_after_parent_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            jobs = [
                self.make_job("父资产"),
                self.make_job("子资产", depends_on=["父资产"]),
            ]

            def provider(job: ImageJob, config: ImageGenerationConfig) -> bytes:
                if job.asset_name == "父资产":
                    raise RetryableProviderError("HTTP 503")
                return b"child"

            config = ImageGenerationConfig(
                base_url="http://local.test",
                api_key="local-secret",
                model="gpt-image-2",
                size="16:9",
                timeout_seconds=5,
                max_retries=0,
                retry_base_seconds=0,
                retry_max_seconds=0,
                concurrency=2,
            )

            manifest = run_generation(jobs, config, workspace, provider)
            by_name = {asset["asset_name"]: asset for asset in manifest["assets"]}

            self.assertEqual(by_name["父资产"]["status"], "failed")
            self.assertEqual(by_name["子资产"]["status"], "blocked")
            self.assertIn("父资产", by_name["子资产"]["last_error"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
python -m unittest tests.test_image_generation.ImageGenerationRunnerTests
```

Expected: fail because `run_generation` does not exist.

- [ ] **Step 3: Extend `scripts/generate_images.py`**

Add imports:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
```

Add these functions:

```python
def manifest_by_name(manifest: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not manifest:
        return {}
    return {
        str(asset.get("asset_name", "")): asset
        for asset in manifest.get("assets", [])
        if isinstance(asset, dict)
    }


def should_skip_job(job: ImageJob, existing: dict[str, dict[str, Any]], workspace: Path, resume: bool) -> bool:
    if not resume:
        return False
    asset = existing.get(job.asset_name)
    if not asset or asset.get("status") != "done":
        return False
    path = workspace / str(asset.get("path", ""))
    return path.is_file()


def run_generation(
    jobs: list[ImageJob],
    config: ImageGenerationConfig,
    workspace: Path,
    provider: ProviderCallable = openai_compatible_provider,
    existing_manifest: dict[str, Any] | None = None,
    resume: bool = False,
) -> dict[str, Any]:
    waves = build_dependency_waves(jobs)
    existing = manifest_by_name(existing_manifest)
    assets: list[dict[str, Any]] = []
    done_assets = {
        name
        for name, asset in existing.items()
        if asset.get("status") == "done" and (workspace / str(asset.get("path", ""))).is_file()
    }

    for wave in waves:
        runnable: list[ImageJob] = []
        for job in wave:
            missing = [dependency for dependency in job.depends_on if dependency not in done_assets]
            if missing:
                assets.append(
                    {
                        "asset_name": job.asset_name,
                        "asset_type": job.asset_type,
                        "path": job.output_path.as_posix(),
                        "status": "blocked",
                        "attempts": 0,
                        "last_error": f"blocked by failed or missing dependencies: {', '.join(missing)}",
                        "depends_on": job.depends_on,
                        "references": [ref.to_dict() for ref in job.reference_images],
                    }
                )
                continue
            if should_skip_job(job, existing, workspace, resume):
                assets.append(existing[job.asset_name])
                done_assets.add(job.asset_name)
                continue
            runnable.append(job)

        with ThreadPoolExecutor(max_workers=max(1, config.concurrency)) as executor:
            future_map = {
                executor.submit(run_job_with_retry, job, config, workspace, provider): job
                for job in runnable
            }
            completed_results: list[tuple[int, dict[str, Any]]] = []
            for future in as_completed(future_map):
                job = future_map[future]
                result = future.result()
                completed_results.append((jobs.index(job), result))
            for _, result in sorted(completed_results, key=lambda item: item[0]):
                assets.append(result)
                if result.get("status") == "done":
                    done_assets.add(str(result.get("asset_name")))

    return {
        "version": 1,
        "provider": "openai-compatible",
        "base_url_label": "configured",
        "assets": assets,
    }


def write_generation_report(path: Path, manifest: dict[str, Any]) -> None:
    failed = [asset for asset in manifest.get("assets", []) if asset.get("status") == "failed"]
    blocked = [asset for asset in manifest.get("assets", []) if asset.get("status") == "blocked"]
    done = [asset for asset in manifest.get("assets", []) if asset.get("status") == "done"]
    lines = ["# Image Generation Report", ""]
    lines.append("## Failed")
    lines.extend(f"- {asset.get('asset_name')}: {asset.get('last_error')}" for asset in failed)
    lines.append("")
    lines.append("## Blocked")
    lines.extend(f"- {asset.get('asset_name')}: {asset.get('last_error')}" for asset in blocked)
    lines.append("")
    lines.append("## Generated")
    lines.extend(f"- {asset.get('asset_name')}: {asset.get('path')}" for asset in done)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
```

Extend `main()` after config loading:

```python
    parser.add_argument("--jobs", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--report")
    parser.add_argument("--resume", action="store_true")
```

Use this main body:

```python
    jobs_path = Path(args.jobs).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()
    jobs = load_jobs_jsonl(jobs_path)
    existing_manifest = None
    if args.resume and manifest_path.exists():
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = load_config_from_env()
    manifest = run_generation(jobs, config, workspace, existing_manifest=existing_manifest, resume=args.resume)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = Path(args.report).expanduser().resolve() if args.report else manifest_path.with_name("image-generation-report.md")
    write_generation_report(report_path, manifest)
    print(f"Image generation manifest written: {manifest_path}")
    return 0
```

- [ ] **Step 4: Run runner tests**

Run:

```powershell
python -m unittest tests.test_image_generation.ImageGenerationRunnerTests
```

Expected: pass.

- [ ] **Step 5: Run all image generation tests**

Run:

```powershell
python -m unittest tests.test_image_generation
```

Expected: pass.

- [ ] **Step 6: Commit**

```powershell
git add scripts/generate_images.py tests/test_image_generation.py
git commit -m "feat: run dependency aware image generation"
```

---

### Task 7: Add CLI Validation Coverage And Downstream Manifest Contract Tests

**Files:**
- Modify: `tests/test_image_generation.py`
- Modify: `tests/test_init_workspace.py`
- Modify: `references/image-generation-format.md`
- Modify: `agents/copy-packager.md`
- Modify: `references/copy-pack-format.md`

- [ ] **Step 1: Add final contract tests**

Append to `tests/test_init_workspace.py`:

```python
    def test_image_generation_scripts_are_documented_and_no_secret_logging_is_required(self) -> None:
        root = Path(__file__).resolve().parents[1]
        format_text = root.joinpath(
            "references", "image-generation-format.md"
        ).read_text(encoding="utf-8")
        retry_text = root.joinpath(
            "references", "image-generation-retry-rules.md"
        ).read_text(encoding="utf-8")

        for relative_path in [
            "scripts/build_image_jobs.py",
            "scripts/generate_images.py",
            "scripts/validate_image_manifest.py",
        ]:
            self.assertTrue(root.joinpath(relative_path).is_file())
            self.assertIn(relative_path, format_text)

        self.assertIn("Do not log API keys", retry_text)
        self.assertIn("Failed dependencies block dependent jobs", retry_text)
        self.assertIn("resume", format_text)
```

- [ ] **Step 2: Run final contract tests**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_image_generation_scripts_are_documented_and_no_secret_logging_is_required
```

Expected: pass after references mention the script names and resume behavior.

- [ ] **Step 3: Ensure `references/image-generation-format.md` includes script names**

Add:

```markdown
## Commands

```powershell
python scripts/build_image_jobs.py --asset-bible 生产资产/_内部/asset-bible.md --out 生产资产/_内部/image-jobs.jsonl
python scripts/generate_images.py --jobs 生产资产/_内部/image-jobs.jsonl --manifest 生产资产/_内部/image-manifest.json --resume
python scripts/validate_image_manifest.py 生产资产/_内部/image-manifest.json --jobs 生产资产/_内部/image-jobs.jsonl
```
```

- [ ] **Step 4: Run all text contract tests**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add tests/test_init_workspace.py references/image-generation-format.md agents/copy-packager.md references/copy-pack-format.md
git commit -m "test: lock image generation docs contract"
```

---

### Task 8: Full Validation And Rollout Check

**Files:**
- Review: `SKILL.md`
- Review: `agents/image-generator.md`
- Review: `references/image-generation-format.md`
- Review: `references/image-generation-retry-rules.md`
- Review: `scripts/build_image_jobs.py`
- Review: `scripts/generate_images.py`
- Review: `scripts/validate_image_manifest.py`
- Review: `tests/test_image_generation.py`

- [ ] **Step 1: Run full unit suite**

Run:

```powershell
python -m unittest tests.test_init_workspace tests.test_image_generation
```

Expected: all tests pass.

- [ ] **Step 2: Run skill quick validation**

Run:

```powershell
$env:PYTHONUTF8='1'; python C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py E:\source-true-guoman
```

Expected:

```text
Skill is valid!
```

- [ ] **Step 3: Run manual local CLI smoke test without API calls**

Create a temporary asset prompt file:

```powershell
$tmp = New-Item -ItemType Directory -Path ([System.IO.Path]::Combine($env:TEMP, "stg-image-smoke")) -Force
$assetBible = Join-Path $tmp.FullName "asset-bible.md"
@"
## 资产提示词

### 图片1 = 林夜_黑袍造型
GPT-image-2，16:9，3D国漫，角色三视图。

### 图片2 = 林夜_宗门礼服
上传参考图：林夜_黑袍造型 = 图片1（人脸身份参考）
GPT-image-2，16:9，3D国漫，保持同一张脸。
"@ | Set-Content -Encoding UTF8 $assetBible
python scripts/build_image_jobs.py --asset-bible $assetBible --out (Join-Path $tmp.FullName "image-jobs.jsonl")
python scripts/validate_image_manifest.py (Join-Path $tmp.FullName "missing-manifest.json") --jobs (Join-Path $tmp.FullName "image-jobs.jsonl")
```

Expected: job builder succeeds; manifest validator fails clearly because the manifest file is missing. This confirms the builder works without hitting the API and the validator error remains explicit.

- [ ] **Step 4: Check git status**

Run:

```powershell
git status --short
```

Expected: only intentional files changed or clean after commits.

- [ ] **Step 5: Final commit if validation adjusted files**

If validation caused planned edits, commit them:

```powershell
git add SKILL.md agents/image-generator.md references/image-generation-format.md references/image-generation-retry-rules.md scripts/build_image_jobs.py scripts/generate_images.py scripts/validate_image_manifest.py scripts/image_generation_core.py tests/test_image_generation.py tests/test_init_workspace.py .gitignore agents/openai.yaml agents/copy-packager.md references/copy-pack-format.md
git commit -m "feat: complete image generation integration"
```

---

## Self-Review Checklist

- Spec coverage: The plan covers OpenAI-compatible local relay configuration, retry/backoff, dependency waves, resume, manifest source of truth, correct output folders, no-secret logging, copy-pack manifest binding, and source-fidelity boundaries.
- Scope check: The plan keeps v1 as CLI plus files. It does not add UI, service processes, external databases, vector stores, video generation, or direct feed-side API calls.
- Test strategy: Every implementation task starts with failing `unittest` tests and has an exact command to verify pass/fail.
- Type consistency: The shared dataclasses are `ImageJob`, `ReferenceImage`, and `ImageGenerationConfig`; later tasks use those names consistently.
- Secret handling: The plan uses `SOURCE_TRUE_IMAGE_API_KEY` for local config but requires manifests, logs, and reports to avoid API keys.
- Source contract: The new image-generator docs repeat the non-compression and source-faithfulness contract, and downstream copy packs must not invent image paths.

## Execution Handoff

Plan complete. Use one of these execution modes:

1. **Subagent-Driven (recommended)** - dispatch a fresh subagent per task, review between tasks, faster isolation.
2. **Inline Execution** - execute tasks in this session using executing-plans with checkpoints.
