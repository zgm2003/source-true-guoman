# Source True Guoman Image Reference Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make formal multi-chapter production and image generation source-faithful, forward-aware, and reference-image backed instead of prompt-only.

**Architecture:** The skill docs define non-negotiable workflow gates. `build_image_jobs.py` turns asset-bible sections into typed, dependency-aware jobs and resolves reference paths. `generate_images.py` refuses prompt-only references unless an explicit reference payload mode is enabled, and `validate_image_manifest.py` audits local reference paths.

**Tech Stack:** Python stdlib, unittest, JSONL image job files, OpenAI-compatible image relay.

---

### Task 1: Forward Index And Asset Bible Rules

**Files:**
- Modify: `SKILL.md`
- Modify: `agents/source-indexer.md`
- Modify: `references/source-index-format.md`
- Modify: `agents/asset-bible.md`
- Modify: `references/asset-bible-format.md`
- Modify: `references/asset-continuity-rules.md`
- Test: `tests/test_init_workspace.py`

- [ ] **Step 1: Write failing text-rule tests**

Add tests that require formal production to index the requested output range plus the next three chapters for identity/continuity only, while preventing future plot leakage into the delivered feed and copy packs.

- [ ] **Step 2: Run text-rule tests and confirm failure**

Run: `python -m unittest tests.test_init_workspace.SkillTextRulesTests`

- [ ] **Step 3: Add workflow language**

Add a formal forward-index rule: for requested chapters `N-M`, read `N-(M+3)` when available for source-index and asset identity only. The requested output remains `N-M`.

- [ ] **Step 4: Add asset-bible schema fields**

Require `Asset class`, `Output directory`, `Asset family`, and `Reference uploads`. State that characters holding identity props remain character assets under `人设资产`.

- [ ] **Step 5: Re-run text-rule tests**

Run: `python -m unittest tests.test_init_workspace.SkillTextRulesTests`

### Task 2: Section-Based Image Job Typing

**Files:**
- Modify: `scripts/build_image_jobs.py`
- Test: `tests/test_image_generation.py`

- [ ] **Step 1: Write failing job-builder tests**

Add a test where a prompt under `## Character Assets` contains `铁算盘` and `身份道具`; expected result is `asset_type == "character"` and `output_dir == "人设资产"`. Add a prop/interface section test that still outputs `道具资产`.

- [ ] **Step 2: Run targeted tests and confirm failure**

Run: `python -m unittest tests.test_image_generation.BuildImageJobsTests`

- [ ] **Step 3: Track asset-bible sections while parsing**

When a `### 图片N = ...` heading appears under `## Character Assets`, `## Scene Assets`, `## Prop, Interface, Beast, Vehicle Assets`, or `## Global Style Baseline`, pass that section class into job creation and prefer it over keyword guessing.

- [ ] **Step 4: Re-run targeted tests**

Run: `python -m unittest tests.test_image_generation.BuildImageJobsTests`

### Task 3: Real Reference Path Resolution

**Files:**
- Modify: `scripts/build_image_jobs.py`
- Modify: `scripts/image_generation_core.py`
- Test: `tests/test_image_generation.py`

- [ ] **Step 1: Write failing reference path tests**

Add tests requiring `上传参考图：天机一型手机_三视图 = 图片1（手机母资产参考）` to produce `reference_images[0].path == "道具资产/天机一型手机_三视图.png"` when the referenced asset exists in the same job file.

- [ ] **Step 2: Run targeted tests and confirm failure**

Run: `python -m unittest tests.test_image_generation.BuildImageJobsTests`

- [ ] **Step 3: Resolve same-batch references**

After all jobs are parsed, build an `asset_name -> output_path` map and fill each `ReferenceImage.path`. Keep `depends_on` deduped.

- [ ] **Step 4: Validate reference metadata**

Update `validate_jobs` to reject reference entries with missing `asset_name`, `path`, or `purpose`.

- [ ] **Step 5: Re-run targeted tests**

Run: `python -m unittest tests.test_image_generation.BuildImageJobsTests`

### Task 4: User-Confirmed Style Baseline Wave

**Files:**
- Modify: `scripts/build_image_jobs.py`
- Modify: `agents/image-generator.md`
- Modify: `references/image-generation-format.md`
- Test: `tests/test_image_generation.py`
- Test: `tests/test_init_workspace.py`

- [ ] **Step 1: Write failing style baseline tests**

Add tests requiring `--style-stage preview` to output only the first scene and first character from the requested range. Add tests proving Q版 prompts stay Q版 and no fixed `非Q版/非玩具感/非卡通低龄化` guard is appended.

- [ ] **Step 2: Run targeted tests and confirm failure**

Run: `python -m unittest tests.test_image_generation.BuildImageJobsTests tests.test_init_workspace.SkillTextRulesTests`

- [ ] **Step 3: Implement style preview and confirmed stages**

In preview stage, emit only the first scene and first character. In confirmed stage, attach `人设风格基准参考` to later characters and `场景风格基准参考` to later scenes, props, and interfaces.

- [ ] **Step 4: Add user confirmation gate**

Require `SOURCE_TRUE_STYLE_CONFIRMED=1` before generating jobs that depend on `人设风格基准参考` or `场景风格基准参考`.

- [ ] **Step 5: Re-run targeted tests**

Run: `python -m unittest tests.test_image_generation.BuildImageJobsTests tests.test_init_workspace.SkillTextRulesTests`

### Task 5: Provider Reference Payload

**Files:**
- Modify: `scripts/generate_images.py`
- Test: `tests/test_image_generation.py`

- [ ] **Step 1: Write failing provider tests**

Add one test that a job with `reference_images` fails non-retryably when `SOURCE_TRUE_IMAGE_REFERENCE_MODE` is unset or `unsupported`, and another test that `reference_mode="data-url"` embeds base64 reference image data in the provider request payload.

- [ ] **Step 2: Run provider tests and confirm failure**

Run: `python -m unittest tests.test_image_generation.ProviderRetryTests`

- [ ] **Step 3: Add reference mode config**

Extend `ImageGenerationConfig` with `reference_mode` and `reference_workspace`, defaulting to `unsupported`. Load `SOURCE_TRUE_IMAGE_REFERENCE_MODE`.

- [ ] **Step 4: Add payload builder**

In `openai_compatible_provider`, if a job has references and mode is `unsupported`, raise `NonRetryableProviderError`. If mode is `data-url`, read each local reference image and add a `reference_images` payload array containing `asset_name`, `purpose`, `path`, and `data_url`.

- [ ] **Step 5: Re-run provider tests**

Run: `python -m unittest tests.test_image_generation.ProviderRetryTests`

### Task 6: Manifest Reference QA

**Files:**
- Modify: `scripts/image_generation_core.py`
- Modify: `scripts/validate_image_manifest.py`
- Modify: `agents/feed-auditor.md`
- Modify: `references/audit-checklist.md`
- Test: `tests/test_image_generation.py`
- Test: `tests/test_init_workspace.py`

- [ ] **Step 1: Write failing validation tests**

Add tests that reject manifest references with empty paths, missing files, workspace escapes, or mismatch against the current job references.

- [ ] **Step 2: Run validation tests and confirm failure**

Run: `python -m unittest tests.test_image_generation.ImageGenerationRunnerTests`

- [ ] **Step 3: Validate manifest `references`**

Require manifest references to be lists of objects with `asset_name`, `path`, and `purpose`. Resolve paths under the workspace and require local files for referenced images.

- [ ] **Step 4: Add audit checklist text**

Add QA bullets for real references used, style baseline followed, asset family consistency, no Q版 drift, no character-as-prop drift, and UI/phone continuity.

- [ ] **Step 5: Re-run targeted tests**

Run: `python -m unittest tests.test_image_generation.ImageGenerationRunnerTests tests.test_init_workspace.SkillTextRulesTests`

### Task 7: Full Verification And Installed Skill Sync

**Files:**
- Sync: `C:\Users\Administrator\.codex\skills\source-true-guoman`

- [ ] **Step 1: Run full test suite**

Run: `python -m unittest discover -s tests`

- [ ] **Step 2: Copy changed skill files to installed skill directory**

Sync changed `SKILL.md`, `agents`, `references`, and `scripts` files into the installed skill package.

- [ ] **Step 3: Re-run full test suite after sync**

Run: `python -m unittest discover -s tests`

- [ ] **Step 4: Report concrete verification**

Report changed files, test command output summary, and any remaining provider-schema limitation.
