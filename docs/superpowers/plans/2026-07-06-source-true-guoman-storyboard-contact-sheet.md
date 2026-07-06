# Source True Guoman Storyboard Contact Sheet Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a post-asset storyboard contact-sheet QA agent that groups canonical feed lines by 25, uploads real generated asset references, and writes visual QA sheets under `分镜资产`.

**Architecture:** Keep storyboard QA separate from reusable image asset generation. Add a dedicated storyboard job model, builder, runner, validator, agent document, and routing rules so `分镜资产` is a narrow post-asset QA exception instead of weakening the existing no-storyboard-feed contract.

**Tech Stack:** Python standard library, `unittest`, existing `scripts.generate_images` OpenAI-compatible provider helpers, Markdown skill/agent files, file-based JSONL and JSON manifests.

---

## File Structure

- Create: `agents/storyboard-contact-sheet.md`
  - Specialist instructions for the new post-asset QA agent.
- Create: `scripts/storyboard_generation_core.py`
  - Dataclasses, JSONL helpers, validation, feed parsing, reference validation, manifest validation, and output path policy for storyboard jobs.
- Create: `scripts/build_storyboard_jobs.py`
  - CLI and helper functions that build 25-line storyboard jobs from a canonical feed plus manifest and optional copy-pack bindings.
- Create: `scripts/generate_storyboards.py`
  - CLI and runner that reuses the OpenAI-compatible provider path but enforces `分镜资产` output policy.
- Create: `scripts/validate_storyboard_manifest.py`
  - CLI validator for storyboard manifests and their source jobs.
- Create: `tests/test_storyboard_generation.py`
  - Focused tests for job grouping, reference gates, runner behavior, resume behavior, and manifest validation.
- Modify: `scripts/init_workspace.py`
  - Add `分镜资产` as a standard top-level workspace folder.
- Modify: `tests/test_init_workspace.py`
  - Add routing and documentation assertions for `storyboard-contact-sheet`.
- Modify: `SKILL.md`
  - Add route, workflow note, narrow `分镜资产` exception, and workspace folder list entry.
- Modify: installed skill copy under `C:\Users\Administrator\.codex\skills\source-true-guoman`
  - Sync the changed skill files after all tests pass.

---

### Task 1: Add Failing Routing And Workspace Tests

**Files:**
- Modify: `tests/test_init_workspace.py`
- Test command: `python -m unittest tests.test_init_workspace.InitWorkspaceTests tests.test_init_workspace.SkillTextRulesTests`

- [ ] **Step 1: Write failing workspace and routing tests**

Add these test methods to `tests/test_init_workspace.py`.

```python
    def test_init_workspace_creates_storyboard_asset_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            init_workspace(workspace)

            self.assertIn("分镜资产", ASSET_DIRS)
            self.assertTrue((workspace / "分镜资产").is_dir())

    def test_storyboard_contact_sheet_agent_is_declared_and_routed(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        agent_path = root.joinpath("agents", "storyboard-contact-sheet.md")

        self.assertTrue(agent_path.is_file())
        self.assertIn("agents/storyboard-contact-sheet.md", skill_text)
        self.assertIn("分镜资产", skill_text)
        self.assertIn("站位QA", skill_text)
        self.assertIn("生成5*5的分镜图，分镜图上不允许有台词。", skill_text)

    def test_storyboard_contact_sheet_is_post_asset_qa_exception_not_old_workflow(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        agent_text = root.joinpath("agents", "storyboard-contact-sheet.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("post-asset visual QA", agent_text)
        self.assertIn("must not modify the canonical feed or copy packs", agent_text)
        self.assertIn("分镜资产 is a narrow post-asset QA exception", skill_text)
        self.assertIn("Canvas", agent_text)
        self.assertIn("keyframe", agent_text)
        self.assertIn("MP4", agent_text)
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_init_workspace.InitWorkspaceTests tests.test_init_workspace.SkillTextRulesTests
```

Expected: FAIL because `分镜资产` is not in `ASSET_DIRS`, `agents/storyboard-contact-sheet.md` does not exist, and `SKILL.md` has no storyboard QA route.

- [ ] **Step 3: Commit only the failing tests**

```powershell
git add tests/test_init_workspace.py
git commit -m "test: cover storyboard contact sheet routing"
```

---

### Task 2: Implement Workspace Directory, Agent Doc, And Skill Route

**Files:**
- Modify: `scripts/init_workspace.py`
- Create: `agents/storyboard-contact-sheet.md`
- Modify: `SKILL.md`
- Test command: `python -m unittest tests.test_init_workspace.InitWorkspaceTests tests.test_init_workspace.SkillTextRulesTests`

- [ ] **Step 1: Add `分镜资产` to workspace initialization**

Modify `ASSET_DIRS` in `scripts/init_workspace.py` to include `分镜资产` after `生产资产` and before `视频资产`.

```python
ASSET_DIRS = (
    "场景资产",
    "道具资产",
    "剧本资产",
    "人设资产",
    "生产资产",
    "分镜资产",
    "视频资产",
    "音色资产",
)
```

- [ ] **Step 2: Create the storyboard agent document**

Create `agents/storyboard-contact-sheet.md` with this content.

```markdown
# Storyboard Contact Sheet Agent

Use this specialist only after generated image assets are complete and the user wants `分镜资产`, `分镜图`, `站位检查`, `站位QA`, `生成5*5的分镜图`, `storyboard contact sheet`, or `blocking QA`.

## 保真契约

- 原作多少字就保留多少字.
- 不得由 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用.
- 不主动添加站起、起身、跪下、走动、抬手、收起法器; 道具动作必须有原文依据.

## Boundary

This agent creates post-asset visual QA contact sheets. It must not modify the canonical feed or copy packs.

`分镜资产` is a narrow post-asset QA exception to the general ban on old storyboard image folders. It is not a Canvas, keyframe, first-frame, last-frame, segment, continuation, or MP4 workflow.

## Required Gate

Before building or running jobs, confirm:

- The canonical production feed exists.
- `生产资产/_内部/image-manifest.json` exists.
- Required generated image assets have `done` status.
- Required local image files exist.
- Reference paths are relative workspace paths under `人设资产`, `场景资产`, or `道具资产`.
- `SOURCE_TRUE_IMAGE_REFERENCE_MODE=data-url` is configured before provider generation.

If any required reference is missing, failed, blocked, ambiguous, or not found on disk, stop and report the exact missing binding. Do not generate weaker prompt-only contact sheets.

## Inputs

- Canonical production feed, such as `生产资产/seedance-all-reference-feed-production-ch01-03.md`.
- `生产资产/_内部/image-manifest.json`.
- Optional copy-pack bindings, such as `生产资产/seedance-copy-packs-production-ch01-03.md`.
- Optional `生产资产/_内部/asset-bible.md` for fallback stable asset names.

## Outputs

- Generated QA sheets under `分镜资产/`.
- `生产资产/_内部/storyboard-jobs.jsonl`.
- `生产资产/_内部/storyboard-manifest.json`.
- `生产资产/_内部/storyboard-report.md`.

## Procedure

1. Build jobs with `python scripts/build_storyboard_jobs.py --feed <feed> --manifest 生产资产/_内部/image-manifest.json --out 生产资产/_内部/storyboard-jobs.jsonl`.
2. Generate sheets with `python scripts/generate_storyboards.py --jobs 生产资产/_内部/storyboard-jobs.jsonl --manifest 生产资产/_内部/storyboard-manifest.json --resume`.
3. Validate with `python scripts/validate_storyboard_manifest.py 生产资产/_内部/storyboard-manifest.json --jobs 生产资产/_内部/storyboard-jobs.jsonl`.

## Prompt Rule

Every full 25-line job must append exactly:

```text
生成5*5的分镜图，分镜图上不允许有台词。
```

The final partial job must append `生成N格分镜图，分镜图上不允许有台词。`, where `N` is the actual number of remaining feed lines.

The prompt may include original feed dialogue as guidance. The generated image must not contain dialogue, subtitles, speech bubbles, captions, panel labels, or visible text.
```

- [ ] **Step 3: Update `SKILL.md` route and workspace wording**

Make these targeted text edits in `SKILL.md`:

- In the hard-ban section, keep the old ban but add the exception sentence:

```text
`分镜资产` is a narrow post-asset QA exception only for storyboard contact sheets after all required image assets are generated and validated; it is not the old Canvas/keyframe/storyboard workflow.
```

- In workflow initialization, add `分镜资产` to the folder list.
- In agent pack routing, add:

```text
- "分镜资产", "分镜图", "站位检查", "站位QA", "生成5*5的分镜图", "storyboard contact sheet", or "blocking QA": read `agents/storyboard-contact-sheet.md` only after generated image assets and a valid canonical feed exist. It creates post-asset visual QA contact sheets under `分镜资产` and must not modify the canonical feed or copy packs.
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```powershell
python -m unittest tests.test_init_workspace.InitWorkspaceTests tests.test_init_workspace.SkillTextRulesTests
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add scripts/init_workspace.py agents/storyboard-contact-sheet.md SKILL.md
git commit -m "feat: route storyboard contact sheet agent"
```

---

### Task 3: Add Failing Storyboard Core Tests

**Files:**
- Create: `tests/test_storyboard_generation.py`
- Test command: `python -m unittest tests.test_storyboard_generation.StoryboardCoreTests`

- [ ] **Step 1: Create core tests**

Create `tests/test_storyboard_generation.py` with imports and this first test class.

```python
import json
import tempfile
import unittest
from pathlib import Path

from scripts.storyboard_generation_core import (
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
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_storyboard_generation.StoryboardCoreTests
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.storyboard_generation_core'`.

- [ ] **Step 3: Commit the failing tests**

```powershell
git add tests/test_storyboard_generation.py
git commit -m "test: cover storyboard core model"
```

---

### Task 4: Implement Storyboard Core

**Files:**
- Create: `scripts/storyboard_generation_core.py`
- Test command: `python -m unittest tests.test_storyboard_generation.StoryboardCoreTests`

- [ ] **Step 1: Create core module**

Create `scripts/storyboard_generation_core.py` with these definitions. Keep the module independent from `ImageJob` so `分镜资产` does not enter `ALLOWED_OUTPUT_DIRS`.

```python
#!/usr/bin/env python3
"""Core helpers for source-true-guoman storyboard contact sheets."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any


STORYBOARD_OUTPUT_DIR = "分镜资产"
PRODUCTION_OUTPUT_DIR = "生产资产"
REFERENCE_OUTPUT_DIRS = {"人设资产", "场景资产", "道具资产"}
FULL_GROUP_SIZE = 25
FULL_GROUP_INSTRUCTION = "生成5*5的分镜图，分镜图上不允许有台词。"
PARTIAL_GROUP_INSTRUCTION_TEMPLATE = "生成{count}格分镜图，分镜图上不允许有台词。"
ALLOWED_STORYBOARD_STATUSES = {"pending", "done", "failed", "blocked"}
NUMBERED_LINE_RE = re.compile(r"^(\d+)\s+")
RAW_SECRET_VALUE_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")


class StoryboardGenerationError(ValueError):
    """Raised when storyboard job inputs or state are invalid."""


@dataclass
class StoryboardReference:
    asset_name: str
    path: str
    purpose: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StoryboardReference":
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
class StoryboardJob:
    job_id: str
    group_index: int
    line_start: int
    line_end: int
    line_count: int
    source_feed: str
    prompt: str
    output_dir: str
    output_file: str
    reference_images: list[StoryboardReference]
    provider: str
    model: str
    size: str
    status: str = "pending"
    _has_reference_images: bool = field(default=True, repr=False)

    @property
    def asset_name(self) -> str:
        return self.job_id

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir) / self.output_file

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StoryboardJob":
        raw_references = data.get("reference_images", [])
        if "reference_images" in data and not isinstance(raw_references, list):
            raise StoryboardGenerationError("reference_images must be a list")
        return cls(
            job_id=str(data.get("job_id", "")).strip(),
            group_index=int(data.get("group_index", 0)),
            line_start=int(data.get("line_start", 0)),
            line_end=int(data.get("line_end", 0)),
            line_count=int(data.get("line_count", 0)),
            source_feed=str(data.get("source_feed", "")).strip(),
            prompt=str(data.get("prompt", "")).strip(),
            output_dir=str(data.get("output_dir", "")).strip(),
            output_file=str(data.get("output_file", "")).strip(),
            reference_images=[
                StoryboardReference.from_dict(item)
                for item in raw_references
                if isinstance(item, dict)
            ],
            provider=str(data.get("provider", "")).strip(),
            model=str(data.get("model", "")).strip(),
            size=str(data.get("size", "")).strip(),
            status=str(data.get("status", "")).strip(),
            _has_reference_images="reference_images" in data,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "group_index": self.group_index,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "line_count": self.line_count,
            "source_feed": self.source_feed,
            "prompt": self.prompt,
            "output_dir": self.output_dir,
            "output_file": self.output_file,
            "reference_images": [reference.to_dict() for reference in self.reference_images],
            "provider": self.provider,
            "model": self.model,
            "size": self.size,
            "status": self.status,
        }


def prompt_hash(prompt: str) -> str:
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def extract_numbered_feed_lines(text: str) -> list[tuple[int, str]]:
    numbered: list[tuple[int, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        match = NUMBERED_LINE_RE.match(stripped)
        if match:
            numbered.append((int(match.group(1)), stripped))
    return numbered


def load_storyboard_jobs_jsonl(path: Path) -> list[StoryboardJob]:
    jobs: list[StoryboardJob] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as error:
            raise StoryboardGenerationError(f"line {line_number}: invalid JSON") from error
        if not isinstance(data, dict):
            raise StoryboardGenerationError(f"line {line_number}: job must be an object")
        try:
            jobs.append(StoryboardJob.from_dict(data))
        except (TypeError, ValueError, StoryboardGenerationError) as error:
            raise StoryboardGenerationError(f"line {line_number}: {error}") from error
    return jobs


def write_storyboard_jobs_jsonl(path: Path, jobs: list[StoryboardJob]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(
        json.dumps(job.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
        for job in jobs
    )
    path.write_text(text, encoding="utf-8")


def validate_storyboard_jobs(jobs: list[StoryboardJob]) -> list[str]:
    errors: list[str] = []
    seen_job_ids: set[str] = set()

    for job in jobs:
        if not job.job_id:
            errors.append("job_id is required")
        elif job.job_id in seen_job_ids:
            errors.append(f"duplicate job_id: {job.job_id}")
        seen_job_ids.add(job.job_id)

        if job.group_index < 1:
            errors.append(f"{job.job_id}: group_index must be positive")
        if job.line_start < 1:
            errors.append(f"{job.job_id}: line_start must be positive")
        if job.line_end < job.line_start:
            errors.append(f"{job.job_id}: line_end must be greater than or equal to line_start")
        if job.line_count != job.line_end - job.line_start + 1:
            errors.append(f"{job.job_id}: line_count must match line range")
        if not job.source_feed:
            errors.append(f"{job.job_id}: source_feed is required")
        if not job.prompt:
            errors.append(f"{job.job_id}: prompt is required")
        if job.output_dir != STORYBOARD_OUTPUT_DIR:
            errors.append(f"{job.job_id}: output_dir must be {STORYBOARD_OUTPUT_DIR}")
        if not job.output_file.endswith(".png"):
            errors.append(f"{job.job_id}: output_file must end with .png")
        if "/" in job.output_file or "\\" in job.output_file or Path(job.output_file).is_absolute() or _has_drive_prefix(job.output_file):
            errors.append(f"{job.job_id}: output_file must be a file name only")
        if not job._has_reference_images:
            errors.append(f"{job.job_id}: reference_images is required")
        if not job.reference_images:
            errors.append(f"{job.job_id}: reference_images must not be empty")
        if not job.provider:
            errors.append(f"{job.job_id}: provider is required")
        if not job.model:
            errors.append(f"{job.job_id}: model is required")
        if not job.size:
            errors.append(f"{job.job_id}: size is required")
        if job.status not in ALLOWED_STORYBOARD_STATUSES:
            errors.append(f"{job.job_id}: status must be one of {sorted(ALLOWED_STORYBOARD_STATUSES)}")

        _validate_prompt_instruction(job, errors)
        for index, reference in enumerate(job.reference_images, start=1):
            _validate_reference_shape(job.job_id, index, reference, errors)

    if errors:
        raise StoryboardGenerationError("; ".join(errors))
    return errors


def _validate_prompt_instruction(job: StoryboardJob, errors: list[str]) -> None:
    if job.line_count == FULL_GROUP_SIZE:
        if FULL_GROUP_INSTRUCTION not in job.prompt:
            errors.append(f"{job.job_id}: missing full 25-line instruction")
        return
    expected = PARTIAL_GROUP_INSTRUCTION_TEMPLATE.format(count=job.line_count)
    if expected not in job.prompt:
        errors.append(f"{job.job_id}: missing partial {job.line_count}-panel instruction")


def _validate_reference_shape(
    job_id: str,
    index: int,
    reference: StoryboardReference,
    errors: list[str],
) -> None:
    label = f"{job_id}: reference {index}"
    if not reference.asset_name:
        errors.append(f"{label}: reference asset_name is required")
    if not reference.path:
        errors.append(f"{label}: reference path is required")
        return
    if not reference.purpose:
        errors.append(f"{label}: reference purpose is required")
    path = Path(reference.path)
    if _has_drive_prefix(reference.path) or path.is_absolute():
        errors.append(f"{label}: reference path must be relative")
    if path.parts and path.parts[0] == PRODUCTION_OUTPUT_DIR:
        errors.append(f"{label}: reference path must not be under {PRODUCTION_OUTPUT_DIR}")
    if not path.parts or path.parts[0] not in REFERENCE_OUTPUT_DIRS:
        errors.append(f"{label}: reference path must start with one of {sorted(REFERENCE_OUTPUT_DIRS)}")


def _has_drive_prefix(path: str) -> bool:
    return len(path) >= 2 and path[0].isalpha() and path[1] == ":"
```

- [ ] **Step 2: Run core tests**

Run:

```powershell
python -m unittest tests.test_storyboard_generation.StoryboardCoreTests
```

Expected: PASS.

- [ ] **Step 3: Commit**

```powershell
git add scripts/storyboard_generation_core.py
git commit -m "feat: add storyboard job core"
```

---

### Task 5: Add Failing Storyboard Job Builder Tests

**Files:**
- Modify: `tests/test_storyboard_generation.py`
- Test command: `python -m unittest tests.test_storyboard_generation.StoryboardJobBuilderTests`

- [ ] **Step 1: Add builder imports**

Extend imports in `tests/test_storyboard_generation.py`.

```python
from scripts.build_storyboard_jobs import build_storyboard_jobs
```

- [ ] **Step 2: Add builder test class**

Append this class to `tests/test_storyboard_generation.py`.

```python
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
                lines.append(f"{number} 日 内 鬼王宗宗门大殿 林夜 坐在王座上 <固定镜头> 无对白")
            else:
                lines.append(f"{number} 日 内 鬼王宗宗门大殿 骨灵教老者 坐在左席 <固定镜头> 骨灵教老者：宗主大人。")
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
        self.assertIn("生成5*5的分镜图，分镜图上不允许有台词。", jobs[0].prompt)
        self.assertEqual((jobs[1].line_start, jobs[1].line_end, jobs[1].line_count), (26, 28, 3))
        self.assertIn("生成3格分镜图，分镜图上不允许有台词。", jobs[1].prompt)
        self.assertNotIn("生成5*5的分镜图，分镜图上不允许有台词。", jobs[1].prompt)
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
```

- [ ] **Step 3: Run tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_storyboard_generation.StoryboardJobBuilderTests
```

Expected: FAIL because `scripts/build_storyboard_jobs.py` does not exist.

- [ ] **Step 4: Commit failing tests**

```powershell
git add tests/test_storyboard_generation.py
git commit -m "test: cover storyboard job builder"
```

---

### Task 6: Implement Storyboard Job Builder

**Files:**
- Create: `scripts/build_storyboard_jobs.py`
- Modify: `scripts/storyboard_generation_core.py`
- Test command: `python -m unittest tests.test_storyboard_generation.StoryboardCoreTests tests.test_storyboard_generation.StoryboardJobBuilderTests`

- [ ] **Step 1: Add manifest and path helpers to core**

Add these helpers to `scripts/storyboard_generation_core.py`.

```python
def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise StoryboardGenerationError(
            f"{label} JSON is malformed at line {error.lineno} column {error.colno}"
        ) from error
    if not isinstance(data, dict):
        raise StoryboardGenerationError(f"{label} must be a JSON object")
    return data


def manifest_assets_by_name(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        raise StoryboardGenerationError("manifest assets must be a list")
    by_name: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            raise StoryboardGenerationError("manifest asset entry must be an object")
        asset_name = str(asset.get("asset_name", "")).strip()
        if asset_name:
            by_name[asset_name] = asset
    return by_name


def validate_reference_file(
    reference: StoryboardReference,
    workspace: Path,
    manifest_by_name: dict[str, dict[str, Any]],
) -> None:
    asset = manifest_by_name.get(reference.asset_name)
    if asset is None:
        raise StoryboardGenerationError(f"{reference.asset_name}: missing from image manifest")
    if str(asset.get("status", "")).strip() != "done":
        raise StoryboardGenerationError(f"{reference.asset_name}: manifest asset is not done")
    manifest_path = str(asset.get("path", "")).strip()
    if manifest_path != reference.path:
        raise StoryboardGenerationError(
            f"{reference.asset_name}: reference path must match manifest path {manifest_path}"
        )

    path_errors = []
    _validate_reference_shape("reference-gate", 1, reference, path_errors)
    if path_errors:
        raise StoryboardGenerationError("; ".join(path_errors))

    workspace_path = Path(workspace).resolve(strict=False)
    resolved_path = (workspace_path / reference.path).resolve(strict=False)
    try:
        resolved_path.relative_to(workspace_path)
    except ValueError as error:
        raise StoryboardGenerationError(
            f"{reference.asset_name}: reference path must stay under workspace"
        ) from error
    if not resolved_path.is_file():
        raise StoryboardGenerationError(
            f"{reference.asset_name}: missing local file {reference.path}"
        )
```

- [ ] **Step 2: Create builder script**

Create `scripts/build_storyboard_jobs.py` with these functions and CLI.

```python
#!/usr/bin/env python3
"""Build storyboard contact-sheet jobs from a source-true-guoman feed."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    from scripts.storyboard_generation_core import (
        FULL_GROUP_INSTRUCTION,
        FULL_GROUP_SIZE,
        PARTIAL_GROUP_INSTRUCTION_TEMPLATE,
        STORYBOARD_OUTPUT_DIR,
        StoryboardGenerationError,
        StoryboardJob,
        StoryboardReference,
        extract_numbered_feed_lines,
        load_json_object,
        manifest_assets_by_name,
        validate_reference_file,
        validate_storyboard_jobs,
        write_storyboard_jobs_jsonl,
    )
except ModuleNotFoundError:
    from storyboard_generation_core import (
        FULL_GROUP_INSTRUCTION,
        FULL_GROUP_SIZE,
        PARTIAL_GROUP_INSTRUCTION_TEMPLATE,
        STORYBOARD_OUTPUT_DIR,
        StoryboardGenerationError,
        StoryboardJob,
        StoryboardReference,
        extract_numbered_feed_lines,
        load_json_object,
        manifest_assets_by_name,
        validate_reference_file,
        validate_storyboard_jobs,
        write_storyboard_jobs_jsonl,
    )


COPY_PACK_HEADING_RE = re.compile(r"^### 投喂包 \d{3}｜原始行 (\d+)-(\d+)$")
REFERENCE_BINDING_RE = re.compile(
    r"^-\s*(?:场景|角色|道具|界面)\d+\s*=\s*(.+?)\s*=\s*(.+?)\s*$"
)


def build_storyboard_jobs(
    feed_path: Path,
    manifest_path: Path,
    workspace: Path,
    copy_packs_path: Path | None = None,
    model: str = "gpt-image-2",
    size: str = "16:9",
    provider: str = "openai-compatible",
) -> list[StoryboardJob]:
    feed_text = feed_path.read_text(encoding="utf-8")
    numbered_lines = extract_numbered_feed_lines(feed_text)
    if not numbered_lines:
        raise StoryboardGenerationError("feed has no numbered video lines")

    expected = 1
    for actual_number, _ in numbered_lines:
        if actual_number != expected:
            raise StoryboardGenerationError(
                f"feed numbered lines must be continuous; expected {expected}, got {actual_number}"
            )
        expected += 1

    manifest = load_json_object(manifest_path, "manifest")
    manifest_by_name = manifest_assets_by_name(manifest)
    copy_pack_refs = (
        parse_copy_pack_references(copy_packs_path.read_text(encoding="utf-8"))
        if copy_packs_path is not None
        else {}
    )

    jobs: list[StoryboardJob] = []
    for group_index, start_index in enumerate(range(0, len(numbered_lines), FULL_GROUP_SIZE), start=1):
        group = numbered_lines[start_index : start_index + FULL_GROUP_SIZE]
        line_start = group[0][0]
        line_end = group[-1][0]
        references = references_for_group(group, copy_pack_refs, manifest_by_name, workspace)
        instruction = (
            FULL_GROUP_INSTRUCTION
            if len(group) == FULL_GROUP_SIZE
            else PARTIAL_GROUP_INSTRUCTION_TEMPLATE.format(count=len(group))
        )
        prompt = build_prompt(group, references, instruction)
        jobs.append(
            StoryboardJob(
                job_id=f"storyboard-{group_index:03d}-lines-{line_start:03d}-{line_end:03d}",
                group_index=group_index,
                line_start=line_start,
                line_end=line_end,
                line_count=len(group),
                source_feed=_relative_or_name(feed_path, workspace),
                prompt=prompt,
                output_dir=STORYBOARD_OUTPUT_DIR,
                output_file=f"storyboard-contact-sheet-{group_index:03d}-lines-{line_start:03d}-{line_end:03d}.png",
                reference_images=references,
                provider=provider,
                model=model,
                size=size,
                status="pending",
            )
        )

    validate_storyboard_jobs(jobs)
    return jobs


def parse_copy_pack_references(text: str) -> dict[tuple[int, int], list[StoryboardReference]]:
    bindings: dict[tuple[int, int], list[StoryboardReference]] = {}
    current_range: tuple[int, int] | None = None
    inside_upload_block = False

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        heading_match = COPY_PACK_HEADING_RE.match(stripped)
        if heading_match:
            current_range = (int(heading_match.group(1)), int(heading_match.group(2)))
            bindings.setdefault(current_range, [])
            inside_upload_block = False
            continue
        if stripped == "上传参考图：":
            inside_upload_block = current_range is not None
            continue
        if inside_upload_block and (stripped.startswith("### ") or stripped == "音色绑定："):
            inside_upload_block = False
        if not inside_upload_block or current_range is None:
            continue

        binding_match = REFERENCE_BINDING_RE.match(stripped)
        if not binding_match:
            continue
        asset_name = binding_match.group(1).strip()
        path = binding_match.group(2).strip()
        purpose = purpose_from_path(path)
        bindings[current_range].append(
            StoryboardReference(asset_name=asset_name, path=path, purpose=purpose)
        )

    return bindings


def references_for_group(
    group: list[tuple[int, str]],
    copy_pack_refs: dict[tuple[int, int], list[StoryboardReference]],
    manifest_by_name: dict[str, dict[str, object]],
    workspace: Path,
) -> list[StoryboardReference]:
    line_numbers = {number for number, _ in group}
    references: list[StoryboardReference] = []
    for (start, end), pack_refs in copy_pack_refs.items():
        if line_numbers.intersection(range(start, end + 1)):
            references.extend(pack_refs)

    if not references:
        group_text = "\n".join(text for _, text in group)
        for asset_name, asset in manifest_by_name.items():
            if asset_name in group_text:
                path = str(asset.get("path", "")).strip()
                references.append(
                    StoryboardReference(
                        asset_name=asset_name,
                        path=path,
                        purpose=purpose_from_path(path),
                    )
                )

    deduped: list[StoryboardReference] = []
    seen: set[tuple[str, str]] = set()
    for reference in references:
        key = (reference.asset_name, reference.path)
        if key in seen:
            continue
        seen.add(key)
        validate_reference_file(reference, workspace, manifest_by_name)
        deduped.append(reference)

    if not deduped:
        start = group[0][0]
        end = group[-1][0]
        raise StoryboardGenerationError(f"lines {start}-{end}: no resolved image references")
    return deduped


def purpose_from_path(path: str) -> str:
    first_part = Path(path).parts[0] if Path(path).parts else ""
    if first_part == "场景资产":
        return "场景空间参考"
    if first_part == "人设资产":
        return "人物身份参考"
    return "道具界面参考"


def build_prompt(
    group: list[tuple[int, str]],
    references: list[StoryboardReference],
    instruction: str,
) -> str:
    lines = [
        "这是 post-asset visual QA 联系表，用于检查站位、人物身份、空间关系、道具连续性和尺度关系。",
        "生成图本身不要出现台词、字幕、气泡、标题、编号或任何可读文字。",
        "",
        "上传参考图：",
    ]
    for index, reference in enumerate(references, start=1):
        lines.append(f"- 参考图{index} = {reference.asset_name} = {reference.path}（{reference.purpose}）")
    lines.extend(["", "原始视频行："])
    lines.extend(text for _, text in group)
    lines.extend(["", instruction])
    return "\n".join(lines)


def _relative_or_name(path: Path, workspace: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(workspace.resolve(strict=False)).as_posix()
    except ValueError:
        return path.name


def main() -> int:
    parser = argparse.ArgumentParser(description="Build storyboard contact-sheet jobs.")
    parser.add_argument("--feed", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--copy-packs")
    parser.add_argument("--model", default="gpt-image-2")
    parser.add_argument("--size", default="16:9")
    parser.add_argument("--provider", default="openai-compatible")
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    try:
        jobs = build_storyboard_jobs(
            feed_path=Path(args.feed).expanduser().resolve(),
            manifest_path=Path(args.manifest).expanduser().resolve(),
            workspace=workspace,
            copy_packs_path=Path(args.copy_packs).expanduser().resolve() if args.copy_packs else None,
            model=args.model,
            size=args.size,
            provider=args.provider,
        )
        write_storyboard_jobs_jsonl(Path(args.out).expanduser().resolve(), jobs)
    except (OSError, StoryboardGenerationError) as error:
        print("Storyboard job build failed:")
        print(f"- {error}")
        return 1

    print(f"Wrote {len(jobs)} storyboard jobs to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Run builder tests**

Run:

```powershell
python -m unittest tests.test_storyboard_generation.StoryboardCoreTests tests.test_storyboard_generation.StoryboardJobBuilderTests
```

Expected: PASS.

- [ ] **Step 4: Commit**

```powershell
git add scripts/storyboard_generation_core.py scripts/build_storyboard_jobs.py
git commit -m "feat: build storyboard contact sheet jobs"
```

---

### Task 7: Add Failing Storyboard Runner Tests

**Files:**
- Modify: `tests/test_storyboard_generation.py`
- Test command: `python -m unittest tests.test_storyboard_generation.StoryboardRunnerTests`

- [ ] **Step 1: Add runner imports**

Extend imports in `tests/test_storyboard_generation.py`.

```python
from scripts.generate_images import ImageGenerationConfig, NonRetryableProviderError, RetryableProviderError
from scripts.generate_storyboards import (
    run_storyboard_generation,
    run_storyboard_job_with_retry,
    should_skip_storyboard_job,
    storyboard_output_path,
)
```

- [ ] **Step 2: Add runner test class**

Append this class to `tests/test_storyboard_generation.py`.

```python
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

        self.assertFalse(provider_called)
        self.assertEqual(manifest["assets"][0]["status"], "done")
        self.assertEqual(manifest["assets"][0]["attempts"], 1)
```

- [ ] **Step 3: Run tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_storyboard_generation.StoryboardRunnerTests
```

Expected: FAIL because `scripts/generate_storyboards.py` does not exist.

- [ ] **Step 4: Commit failing tests**

```powershell
git add tests/test_storyboard_generation.py
git commit -m "test: cover storyboard generation runner"
```

---

### Task 8: Implement Storyboard Generation Runner

**Files:**
- Create: `scripts/generate_storyboards.py`
- Test command: `python -m unittest tests.test_storyboard_generation.StoryboardRunnerTests`

- [ ] **Step 1: Create runner script**

Create `scripts/generate_storyboards.py`. Reuse provider and retry error classes from `generate_images.py`, but use storyboard-specific output validation.

```python
#!/usr/bin/env python3
"""Generate storyboard contact-sheet QA images."""

from __future__ import annotations

import argparse
import json
import logging
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from pathlib import Path
from typing import Any
from typing import Callable

try:
    from scripts.generate_images import (
        ImageGenerationConfig,
        NonRetryableProviderError,
        RetryableProviderError,
        load_config_from_env,
        openai_compatible_provider,
        retry_delay,
    )
    from scripts.storyboard_generation_core import (
        STORYBOARD_OUTPUT_DIR,
        StoryboardGenerationError,
        StoryboardJob,
        load_storyboard_jobs_jsonl,
        prompt_hash,
        validate_storyboard_jobs,
    )
except ModuleNotFoundError:
    from generate_images import (
        ImageGenerationConfig,
        NonRetryableProviderError,
        RetryableProviderError,
        load_config_from_env,
        openai_compatible_provider,
        retry_delay,
    )
    from storyboard_generation_core import (
        STORYBOARD_OUTPUT_DIR,
        StoryboardGenerationError,
        StoryboardJob,
        load_storyboard_jobs_jsonl,
        prompt_hash,
        validate_storyboard_jobs,
    )


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())
ProviderCallable = Callable[[StoryboardJob, ImageGenerationConfig], bytes]


def storyboard_output_path(workspace: Path, job: StoryboardJob) -> Path:
    if job.output_dir != STORYBOARD_OUTPUT_DIR:
        raise NonRetryableProviderError(f"{job.job_id}: output_dir must be {STORYBOARD_OUTPUT_DIR}")
    if "/" in job.output_file or "\\" in job.output_file or Path(job.output_file).is_absolute() or _has_drive_prefix(job.output_file):
        raise NonRetryableProviderError(f"{job.job_id}: output_file must be a file name only")

    workspace_path = Path(workspace).resolve(strict=False)
    output_path = (workspace_path / job.output_path).resolve(strict=False)
    try:
        output_path.relative_to(workspace_path)
    except ValueError as error:
        raise NonRetryableProviderError("output path must stay under workspace") from error
    return output_path


def run_storyboard_job_with_retry(
    job: StoryboardJob,
    config: ImageGenerationConfig,
    workspace: Path,
    provider: ProviderCallable = openai_compatible_provider,
) -> dict[str, Any]:
    attempts = 0
    try:
        output_path = storyboard_output_path(workspace, job)
        if job.reference_images and config.reference_mode != "data-url":
            raise NonRetryableProviderError(
                "storyboard references require SOURCE_TRUE_IMAGE_REFERENCE_MODE=data-url"
            )
    except NonRetryableProviderError as error:
        return _failed_result(job, config, attempts, _sanitize_error(str(error), config))

    while True:
        attempts += 1
        try:
            image_bytes = provider(job, config)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(image_bytes)
            return _result_base(job, config, attempts) | {"status": "done"}
        except NonRetryableProviderError as error:
            return _failed_result(job, config, attempts, _sanitize_error(str(error), config))
        except RetryableProviderError as error:
            last_error = _sanitize_error(str(error), config)
            if attempts > config.max_retries:
                return _failed_result(job, config, attempts, last_error)
            delay = retry_delay(config, attempts - 1)
            if delay > 0:
                time.sleep(delay)
        except Exception as error:
            return _failed_result(job, config, attempts, _sanitize_error(str(error), config))


def run_storyboard_generation(
    jobs: list[StoryboardJob],
    config: ImageGenerationConfig,
    workspace: Path,
    provider: ProviderCallable = openai_compatible_provider,
    existing_manifest: dict[str, Any] | None = None,
    resume: bool = False,
    on_manifest_update: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    validate_storyboard_jobs(jobs)
    existing = manifest_by_name(existing_manifest) if resume else {}
    results_by_name: dict[str, dict[str, Any]] = {}

    runnable: list[StoryboardJob] = []
    for job in jobs:
        if should_skip_storyboard_job(job, config, existing, workspace, resume):
            results_by_name[job.job_id] = _skipped_result(job, config, existing[job.job_id])
            if on_manifest_update is not None:
                on_manifest_update(_build_manifest(jobs, results_by_name))
        else:
            runnable.append(job)

    if runnable:
        with ThreadPoolExecutor(max_workers=max(1, config.concurrency)) as executor:
            future_map = {
                executor.submit(run_storyboard_job_with_retry, job, config, workspace, provider): job
                for job in runnable
            }
            for future in as_completed(future_map):
                job = future_map[future]
                try:
                    result = future.result()
                except Exception as error:
                    result = _failed_result(job, config, 0, _sanitize_error(str(error), config))
                results_by_name[job.job_id] = result
                if on_manifest_update is not None:
                    on_manifest_update(_build_manifest(jobs, results_by_name))

    return _build_manifest(jobs, results_by_name)


def should_skip_storyboard_job(
    job: StoryboardJob,
    config: ImageGenerationConfig,
    existing: dict[str, dict[str, Any]],
    workspace: Path,
    resume: bool,
) -> bool:
    if not resume:
        return False
    asset = existing.get(job.job_id)
    if not asset or asset.get("status") != "done":
        return False
    path_text = str(asset.get("path", "")).strip()
    if path_text != job.output_path.as_posix():
        return False
    if asset.get("prompt_hash") != prompt_hash(job.prompt):
        return False
    if asset.get("model") != job.model:
        return False
    if asset.get("size") != job.size:
        return False
    if asset.get("references") != [reference.to_dict() for reference in job.reference_images]:
        return False
    return (Path(workspace) / path_text).is_file()


def manifest_by_name(manifest: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(manifest, dict):
        return {}
    assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        return {}
    return {
        str(asset.get("asset_name", "")).strip(): asset
        for asset in assets
        if isinstance(asset, dict) and str(asset.get("asset_name", "")).strip()
    }


def write_storyboard_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _write_text_atomic(path, text)


def write_storyboard_report(path: Path, manifest: dict[str, Any]) -> None:
    assets = [asset for asset in manifest.get("assets", []) if isinstance(asset, dict)]
    failed = [asset for asset in assets if asset.get("status") == "failed"]
    generated = [asset for asset in assets if asset.get("status") == "done"]
    lines = ["# Storyboard Contact Sheet Report", "", "## Failed"]
    lines.extend([f"- {asset.get('asset_name')}: {asset.get('last_error')}" for asset in failed] or ["- None"])
    lines.extend(["", "## Generated"])
    lines.extend([f"- {asset.get('asset_name')}: {asset.get('path')}" for asset in generated] or ["- None"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_manifest(jobs: list[StoryboardJob], results_by_name: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": 1,
        "provider": "openai-compatible",
        "base_url_label": "configured",
        "assets": [
            results_by_name[job.job_id]
            for job in jobs
            if job.job_id in results_by_name
        ],
    }


def _result_base(job: StoryboardJob, config: ImageGenerationConfig, attempts: int) -> dict[str, Any]:
    return {
        "asset_name": job.job_id,
        "asset_type": "storyboard_contact_sheet",
        "path": job.output_path.as_posix(),
        "prompt_hash": prompt_hash(job.prompt),
        "model": job.model or config.model,
        "size": job.size or config.size,
        "attempts": attempts,
        "line_start": job.line_start,
        "line_end": job.line_end,
        "line_count": job.line_count,
        "source_feed": job.source_feed,
        "references": [reference.to_dict() for reference in job.reference_images],
    }


def _failed_result(job: StoryboardJob, config: ImageGenerationConfig, attempts: int, last_error: str) -> dict[str, Any]:
    return _result_base(job, config, attempts) | {"status": "failed", "last_error": last_error}


def _skipped_result(job: StoryboardJob, config: ImageGenerationConfig, existing_asset: dict[str, Any]) -> dict[str, Any]:
    attempts = existing_asset.get("attempts", 0)
    if type(attempts) is not int or attempts < 0:
        attempts = 0
    return _result_base(job, config, attempts) | {"status": "done"}


def _sanitize_error(message: str, config: ImageGenerationConfig) -> str:
    sanitized = message
    for secret in {config.api_key, config.base_url}:
        if secret:
            sanitized = sanitized.replace(secret, "[redacted]")
    return sanitized


def _write_text_atomic(path: Path, text: str) -> None:
    temp_path: Path | None = None
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as temp_file:
        temp_file.write(text)
        temp_path = Path(temp_file.name)
    os.replace(temp_path, path)


def _has_drive_prefix(path: str) -> bool:
    return len(path) >= 2 and path[0].isalpha() and path[1] == ":"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate storyboard contact-sheet QA images.")
    parser.add_argument("--jobs", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--report")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    jobs_path = Path(args.jobs).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()
    report_path = Path(args.report).expanduser().resolve() if args.report else manifest_path.with_name("storyboard-report.md")

    try:
        jobs = load_storyboard_jobs_jsonl(jobs_path)
        existing_manifest = None
        if args.resume and manifest_path.exists():
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        config = load_config_from_env()
        config.reference_workspace = str(workspace)

        def persist(current_manifest: dict[str, Any]) -> None:
            write_storyboard_manifest(manifest_path, current_manifest)
            write_storyboard_report(report_path, current_manifest)

        manifest = run_storyboard_generation(
            jobs,
            config,
            workspace,
            provider=openai_compatible_provider,
            existing_manifest=existing_manifest,
            resume=args.resume,
            on_manifest_update=persist,
        )
        write_storyboard_manifest(manifest_path, manifest)
        write_storyboard_report(report_path, manifest)
    except FileNotFoundError as error:
        missing = Path(error.filename).name if error.filename else "input file"
        print(f"Storyboard generation failed: input file not found: {missing}")
        return 1
    except (json.JSONDecodeError, OSError, StoryboardGenerationError, NonRetryableProviderError, RetryableProviderError) as error:
        print(f"Storyboard generation failed: {error}")
        return 1

    print(f"Storyboard generation wrote {len(manifest.get('assets', []))} sheets to {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run runner tests**

Run:

```powershell
python -m unittest tests.test_storyboard_generation.StoryboardRunnerTests
```

Expected: PASS.

- [ ] **Step 3: Commit**

```powershell
git add scripts/generate_storyboards.py
git commit -m "feat: generate storyboard contact sheets"
```

---

### Task 9: Add Failing Storyboard Manifest Validator Tests

**Files:**
- Modify: `tests/test_storyboard_generation.py`
- Test command: `python -m unittest tests.test_storyboard_generation.StoryboardManifestValidatorTests`

- [ ] **Step 1: Add validator imports**

Extend imports in `tests/test_storyboard_generation.py`.

```python
from scripts.validate_storyboard_manifest import validate_storyboard_manifest
```

- [ ] **Step 2: Add validator test class**

Append this class to `tests/test_storyboard_generation.py`.

```python
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
```

- [ ] **Step 3: Run tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_storyboard_generation.StoryboardManifestValidatorTests
```

Expected: FAIL because `scripts/validate_storyboard_manifest.py` does not exist.

- [ ] **Step 4: Commit failing tests**

```powershell
git add tests/test_storyboard_generation.py
git commit -m "test: cover storyboard manifest validation"
```

---

### Task 10: Implement Storyboard Manifest Validator

**Files:**
- Create: `scripts/validate_storyboard_manifest.py`
- Test command: `python -m unittest tests.test_storyboard_generation.StoryboardManifestValidatorTests`

- [ ] **Step 1: Create validator script**

Create `scripts/validate_storyboard_manifest.py`.

```python
#!/usr/bin/env python3
"""Validate source-true-guoman storyboard contact-sheet manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.storyboard_generation_core import (
        STORYBOARD_OUTPUT_DIR,
        StoryboardGenerationError,
        StoryboardJob,
        load_storyboard_jobs_jsonl,
        prompt_hash,
        validate_storyboard_jobs,
    )
except ModuleNotFoundError:
    from storyboard_generation_core import (
        STORYBOARD_OUTPUT_DIR,
        StoryboardGenerationError,
        StoryboardJob,
        load_storyboard_jobs_jsonl,
        prompt_hash,
        validate_storyboard_jobs,
    )


def validate_storyboard_manifest(
    manifest: dict[str, Any],
    jobs: list[StoryboardJob],
    workspace: Path,
) -> list[str]:
    errors: list[str] = []
    assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        return ["manifest assets must be a list"]

    jobs_by_name = {job.job_id: job for job in jobs}
    seen_names: set[str] = set()
    for asset in assets:
        if not isinstance(asset, dict):
            errors.append("manifest asset entry must be an object")
            continue
        asset_name = str(asset.get("asset_name", "")).strip()
        asset_label = asset_name or "<missing asset_name>"
        path_text = str(asset.get("path", "")).strip()
        status = str(asset.get("status", "")).strip()

        if not asset_name:
            errors.append("asset_name is required")
        elif asset_name in seen_names:
            errors.append(f"duplicate asset_name: {asset_name}")
        seen_names.add(asset_name)

        job = jobs_by_name.get(asset_name)
        if job is None:
            errors.append(f"{asset_label}: manifest asset not present in jobs")
        else:
            if path_text != job.output_path.as_posix():
                errors.append(f"{asset_label}: path must match job output {job.output_path.as_posix()}")
            if asset.get("prompt_hash") not in {None, prompt_hash(job.prompt)}:
                errors.append(f"{asset_label}: prompt_hash must match current job prompt")
            if asset.get("model") not in {None, job.model}:
                errors.append(f"{asset_label}: model must match current job model")
            if asset.get("size") not in {None, job.size}:
                errors.append(f"{asset_label}: size must match current job size")
            if asset.get("line_count") not in {None, job.line_count}:
                errors.append(f"{asset_label}: line_count must match current job")

        if status not in {"done", "failed", "blocked"}:
            errors.append(f"{asset_label}: status must be done, failed, or blocked")
        if status in {"failed", "blocked"} and not str(asset.get("last_error", "")).strip():
            errors.append(f"{asset_label}: {status} storyboard must record last_error")

        image_path = _validate_storyboard_path(asset_label, path_text, workspace, errors)
        if status == "done" and image_path is not None and not image_path.is_file():
            errors.append(f"{asset_label}: done storyboard missing local file {path_text}")

    return errors


def _validate_storyboard_path(
    asset_label: str,
    path_text: str,
    workspace: Path,
    errors: list[str],
) -> Path | None:
    if not path_text:
        errors.append(f"{asset_label}: generated storyboard path is required")
        return None
    path = Path(path_text)
    if _has_drive_prefix(path_text) or path.is_absolute():
        errors.append(f"{asset_label}: generated storyboard path must be relative")
        return None
    workspace_path = Path(workspace).resolve(strict=False)
    resolved_path = (workspace_path / path).resolve(strict=False)
    try:
        relative_path = resolved_path.relative_to(workspace_path)
    except ValueError:
        errors.append(f"{asset_label}: generated storyboard path must stay under workspace")
        return None
    if not relative_path.parts or relative_path.parts[0] != STORYBOARD_OUTPUT_DIR:
        errors.append(f"{asset_label}: path must start with {STORYBOARD_OUTPUT_DIR}")
    return resolved_path


def _has_drive_prefix(path: str) -> bool:
    return len(path) >= 2 and path[0].isalpha() and path[1] == ":"


def print_validation_errors(errors: list[str]) -> None:
    print("Storyboard manifest validation failed:")
    for error in errors:
        print(f"- {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate storyboard contact-sheet manifest files.")
    parser.add_argument("manifest")
    parser.add_argument("--jobs", required=True)
    parser.add_argument("--workspace", default=".")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    jobs_path = Path(args.jobs).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise StoryboardGenerationError("manifest must be a JSON object")
        jobs = load_storyboard_jobs_jsonl(jobs_path)
        validate_storyboard_jobs(jobs)
        errors = validate_storyboard_manifest(manifest, jobs, workspace)
    except FileNotFoundError as error:
        missing = Path(error.filename).name if error.filename else "input file"
        print_validation_errors([f"input file not found: {missing}"])
        return 1
    except json.JSONDecodeError as error:
        print_validation_errors(
            [f"manifest JSON is malformed at line {error.lineno} column {error.colno}"]
        )
        return 1
    except StoryboardGenerationError as error:
        print_validation_errors(str(error).split("; "))
        return 1

    if errors:
        print_validation_errors(errors)
        return 1

    print("Storyboard manifest validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run validator tests**

Run:

```powershell
python -m unittest tests.test_storyboard_generation.StoryboardManifestValidatorTests
```

Expected: PASS.

- [ ] **Step 3: Commit**

```powershell
git add scripts/validate_storyboard_manifest.py
git commit -m "feat: validate storyboard manifests"
```

---

### Task 11: Add CLI Smoke Tests And Full Regression

**Files:**
- Modify: `tests/test_storyboard_generation.py`
- Test command: `python -m unittest discover -s tests`

- [ ] **Step 1: Add CLI smoke tests**

Append this class to `tests/test_storyboard_generation.py`.

```python
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
                                "line_count": job.line_count,
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
```

Also add these imports at the top of the test file:

```python
import subprocess
import sys
```

- [ ] **Step 2: Run all storyboard tests**

Run:

```powershell
python -m unittest tests.test_storyboard_generation
```

Expected: PASS.

- [ ] **Step 3: Run full regression**

Run:

```powershell
python -m unittest discover -s tests
```

Expected: PASS. The previous image-generation tests must still reject normal `image-generator` output under `生产资产`; they must not require adding `分镜资产` to `ALLOWED_OUTPUT_DIRS`.

- [ ] **Step 4: Commit**

```powershell
git add tests/test_storyboard_generation.py
git commit -m "test: add storyboard CLI smoke coverage"
```

---

### Task 12: Sync Installed Skill Copy And Verify Final State

**Files:**
- Modify installed files under: `C:\Users\Administrator\.codex\skills\source-true-guoman`
- Test command: `python -m unittest discover -s tests`

- [ ] **Step 1: Sync changed skill files to installed skill directory**

Run these PowerShell commands from `E:\source-true-guoman`.

```powershell
Copy-Item -Force 'SKILL.md' 'C:\Users\Administrator\.codex\skills\source-true-guoman\SKILL.md'
Copy-Item -Force 'agents\storyboard-contact-sheet.md' 'C:\Users\Administrator\.codex\skills\source-true-guoman\agents\storyboard-contact-sheet.md'
Copy-Item -Force 'scripts\init_workspace.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\scripts\init_workspace.py'
Copy-Item -Force 'scripts\storyboard_generation_core.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\scripts\storyboard_generation_core.py'
Copy-Item -Force 'scripts\build_storyboard_jobs.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\scripts\build_storyboard_jobs.py'
Copy-Item -Force 'scripts\generate_storyboards.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\scripts\generate_storyboards.py'
Copy-Item -Force 'scripts\validate_storyboard_manifest.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\scripts\validate_storyboard_manifest.py'
Copy-Item -Force 'tests\test_storyboard_generation.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\tests\test_storyboard_generation.py'
```

- [ ] **Step 2: Run full test suite in repo**

Run:

```powershell
python -m unittest discover -s tests
```

Expected: PASS.

- [ ] **Step 3: Run full test suite in installed skill copy**

Run:

```powershell
python -m unittest discover -s 'C:\Users\Administrator\.codex\skills\source-true-guoman\tests'
```

Expected: PASS.

- [ ] **Step 4: Confirm sample workspace state**

Run:

```powershell
Test-Path 'E:\xianjie\分镜资产'
Test-Path 'E:\xianjie\生产资产\seedance-all-reference-feed-production-ch01-03.md'
```

Expected:

```text
True
False
```

If the second value is `False`, final reporting must say the implementation is ready but the current `E:\xianjie` sample cannot run storyboard generation until the feed, manifest, and generated asset files exist.

- [ ] **Step 5: Commit sync state if tracked repo files changed after final fixes**

```powershell
git status --short
git add SKILL.md agents/storyboard-contact-sheet.md scripts/init_workspace.py scripts/storyboard_generation_core.py scripts/build_storyboard_jobs.py scripts/generate_storyboards.py scripts/validate_storyboard_manifest.py tests/test_init_workspace.py tests/test_storyboard_generation.py
git commit -m "feat: add storyboard contact sheet workflow"
```

If the working tree is already clean because earlier task commits captured all repo changes, do not create an empty commit.

---

## Final Verification Checklist

- [ ] `python -m unittest discover -s tests` passes in `E:\source-true-guoman`.
- [ ] Installed skill copy has the new agent and scripts.
- [ ] `scripts/init_workspace.py` creates `分镜资产`.
- [ ] `SKILL.md` routes `分镜资产`, `分镜图`, `站位检查`, `站位QA`, and `生成5*5的分镜图`.
- [ ] `image_generation_core.ALLOWED_OUTPUT_DIRS` remains `{"人设资产", "场景资产", "道具资产"}`.
- [ ] Storyboard generated outputs are restricted to `分镜资产`.
- [ ] Storyboard references are restricted to `人设资产`, `场景资产`, and `道具资产`.
- [ ] Full 25-line jobs contain `生成5*5的分镜图，分镜图上不允许有台词。`.
- [ ] Partial jobs contain `生成N格分镜图，分镜图上不允许有台词。` with the actual line count.
- [ ] No API key or base URL secret is written to storyboard manifests or reports.
- [ ] Final user report states whether `E:\xianjie` currently has the required feed and manifest to run the new agent.
