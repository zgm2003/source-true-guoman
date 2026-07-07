# Source True Guoman Scope Gate, Index Reconciliation, And Next-Step Recommendations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `source-true-guoman` 在长篇正式生产里先问生产章数、用累积索引回填修正旧资产/旧母稿，并在每个阶段给出状态感知的下一步推荐。

**Architecture:** 规则层先收紧 `SKILL.md` 与 specialist docs，确保 agent 行为会停下来问范围、先做回填、再继续生产。脚本层只做确定性辅助：章节范围计算、工作区状态推荐、回填一致性校验、明确改名迁移；剧情身份判断仍由 `source-index` 的证据锚点驱动，不交给脚本猜。

**Tech Stack:** Python standard library, `unittest`, Markdown skill/agent/reference files, JSON/JSONL manifests, existing source-true-guoman workspace layout.

---

## File Structure

- Modify: `tests/test_init_workspace.py`
  - Add documentation contract tests for production scope gate, cumulative reconciliation, and stage-aware recommendations.
- Modify: `SKILL.md`
  - Add production chapter-count gate, default 3-chapter recommendation, cumulative index reconciliation route, and stage-aware next-step handoff.
- Modify: `agents/source-indexer.md`
  - Add cumulative index range calculation and reconciliation ledger requirements.
- Modify: `references/source-index-format.md`
  - Add cumulative range fields, reconciliation ledger, anonymous-to-named upgrade fields, and private future-reveal guard.
- Modify: `agents/asset-bible.md`
  - Require reading reconciliation ledger before asset decisions and blocking unresolved confirmed upgrades.
- Modify: `references/asset-bible-format.md`
  - Add migration action fields on asset entries.
- Modify: `agents/copy-packager.md`, `agents/production-runner.md`, `agents/image-generator.md`, `agents/storyboard-contact-sheet.md`
  - Replace the fixed three-option handoff with stage-aware recommendation rules where each stage applies.
- Create: `scripts/production_scope_core.py`
  - Deterministic helper for chapter-count gate and forward/cumulative index range calculation.
- Create: `tests/test_production_scope.py`
  - Unit tests for ambiguous long-novel gate, default 3 chapters, explicit 1 chapter + next 3, and cumulative range expansion.
- Create: `scripts/recommend_next_steps.py`
  - Deterministic recommendation engine and CLI that inspects workspace artifacts and outputs the status/recommendation block.
- Create: `tests/test_recommend_next_steps.py`
  - Unit and CLI tests for recommendation matrix.
- Create: `scripts/validate_reconciliation.py`
  - Deterministic validator for confirmed upgrades against source-index, asset-bible, mother feed, copy packs, and image manifest.
- Create: `scripts/migrate_asset_names.py`
  - Explicit migration helper for confirmed old asset name -> canonical asset name changes.
- Create: `tests/test_reconciliation.py`
  - Unit and CLI tests for reconciliation validation and manifest/file migration.
- Modify: `scripts/image_generation_core.py`
  - Extend image manifest status handling with `renamed` and `deprecated`.
- Modify: `tests/test_image_generation.py`
  - Add manifest migration status coverage.
- Sync after passing tests: `C:\Users\Administrator\.codex\skills\source-true-guoman`
  - Copy changed skill docs, scripts, and tests to the installed skill copy.

---

### Task 1: Add Failing Documentation Contract Tests

**Files:**
- Modify: `tests/test_init_workspace.py`
- Test command: `python -m unittest tests.test_init_workspace.SkillTextRulesTests`

- [ ] **Step 1: Add production-scope gate doc tests**

Append these methods inside `SkillTextRulesTests` in `tests/test_init_workspace.py`.

```python
    def test_long_formal_production_requires_chapter_count_gate(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        source_indexer_text = root.joinpath("agents", "source-indexer.md").read_text(
            encoding="utf-8"
        )

        required_skill_phrases = [
            "Production scope gate",
            "if the submitted or detected source contains more than 3 chapters",
            "ask the user how many chapters to produce before writing the canonical feed or copy packs",
            "recommend starting with 3 chapters",
            "Default production start: recommend 3 chapters",
            "If the user says `默认` after this scope gate, produce chapters 1-3",
            "If the user explicitly asks for 1 chapter, deliver only chapter 1 and read chapters 1-4 for forward index",
            "If the user chooses full-book batching without a batch size, use 3 chapters per batch",
        ]
        required_prompt = (
            "生产范围缺失：检测到文本超过3章。建议先跑3章；你也可以指定"
            " 1-5 章、具体章节范围，或明确说全本分批。收到选择前，我不会生成连续投喂稿或复制包。"
        )

        for phrase in required_skill_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill_text)
        self.assertIn(required_prompt, skill_text)

        self.assertIn("requested_output_range", source_indexer_text)
        self.assertIn("forward_index_range", source_indexer_text)
        self.assertIn("required_cumulative_index_range", source_indexer_text)
        self.assertIn("existing_index_range ∪ forward_index_range", source_indexer_text)

    def test_cumulative_index_reconciliation_rules_are_declared(self) -> None:
        root = Path(__file__).resolve().parents[1]
        checked_paths = [
            root.joinpath("SKILL.md"),
            root.joinpath("agents", "source-indexer.md"),
            root.joinpath("references", "source-index-format.md"),
            root.joinpath("agents", "asset-bible.md"),
            root.joinpath("references", "asset-bible-format.md"),
        ]
        required_phrases = [
            "Cumulative index reconciliation",
            "source-index is a cumulative fact ledger, not a one-run artifact",
            "confirmed anonymous-to-named upgrade",
            "Former temporary names:",
            "Upgrade status: none / suspected / confirmed / rejected",
            "Migration action: none / rename / deprecated / regenerate",
            "reconciliation-log.md",
            "update the canonical mother feed first, then re-run feed audit, then regenerate copy packs",
            "do not leak future plot into the delivered feed or copy packs",
        ]

        for path in checked_paths:
            text = path.read_text(encoding="utf-8")
            for phrase in required_phrases:
                with self.subTest(path=path.name, phrase=phrase):
                    self.assertIn(phrase, text)

    def test_stage_aware_recommendation_rules_replace_fixed_handoff_only(self) -> None:
        root = Path(__file__).resolve().parents[1]
        checked_paths = [
            root.joinpath("SKILL.md"),
            root.joinpath("agents", "copy-packager.md"),
            root.joinpath("agents", "production-runner.md"),
            root.joinpath("agents", "image-generator.md"),
            root.joinpath("agents", "storyboard-contact-sheet.md"),
        ]
        required_phrases = [
            "Stage-aware next-step recommendations",
            "当前状态：",
            "下一步建议（推荐优先）：",
            "if reconciliation has pending confirmed upgrades, recommend 处理索引回填 first",
            "if style preview images are done but not confirmed, recommend 确认风格基准 first",
            "if images are failed or blocked, recommend 续跑/修复失败图片 first",
            "if all images are done and the canonical feed is valid, recommend 分镜/站位 QA",
            "recommendations only suggest the next action; do not execute unless the user chooses it",
        ]

        for path in checked_paths:
            text = path.read_text(encoding="utf-8")
            for phrase in required_phrases:
                with self.subTest(path=path.name, phrase=phrase):
                    self.assertIn(phrase, text)
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests
```

Expected: FAIL because the new phrases are not yet present in `SKILL.md` and specialist docs.

- [ ] **Step 3: Commit only the failing tests**

```powershell
git add tests/test_init_workspace.py
git commit -m "test: cover long production scope and reconciliation rules"
```

---

### Task 2: Update Skill And Agent Rule Docs

**Files:**
- Modify: `SKILL.md`
- Modify: `agents/source-indexer.md`
- Modify: `references/source-index-format.md`
- Modify: `agents/asset-bible.md`
- Modify: `references/asset-bible-format.md`
- Modify: `agents/copy-packager.md`
- Modify: `agents/production-runner.md`
- Modify: `agents/image-generator.md`
- Modify: `agents/storyboard-contact-sheet.md`
- Test command: `python -m unittest tests.test_init_workspace.SkillTextRulesTests`

- [ ] **Step 1: Add the scope gate block to `SKILL.md`**

Insert this block after the formal production parameter gate rules in `SKILL.md`.

```markdown
Production scope gate: if the submitted or detected source contains more than 3 chapters and the user has not explicitly selected an output range, ask the user how many chapters to produce before writing the canonical feed or copy packs. Recommend starting with 3 chapters. This chapter-count gate has the same priority as camera library and aspect ratio gates.

Use this exact chat prompt when only production scope is missing:

```text
生产范围缺失：检测到文本超过3章。建议先跑3章；你也可以指定 1-5 章、具体章节范围，或明确说全本分批。收到选择前，我不会生成连续投喂稿或复制包。
```

If camera library, aspect ratio, and chapter count are all missing, ask for all three in one prompt. If the user says `默认` after this scope gate, produce chapters 1-3. If the user says `前三章`, produce chapters 1-3. If the user explicitly asks for 1 chapter, deliver only chapter 1 and read chapters 1-4 for forward index. If the user chooses full-book batching without a batch size, use 3 chapters per batch. Default production start: recommend 3 chapters.
```

- [ ] **Step 2: Replace old default production slice wording**

In `SKILL.md`, replace the existing default production slice lines with:

```markdown
Default production start: recommend 3 chapters. Do not auto-produce more than 3 chapters from an ambiguous long novel request. If the user explicitly requests a larger range, honor it after camera library, aspect ratio, and scope are clear. If the user explicitly chooses full-book batching without a batch size, use sequential 3-chapter batches.
```

- [ ] **Step 3: Add cumulative reconciliation rules to `SKILL.md`**

Add this block near the current forward index and canonical artifact policies.

```markdown
Cumulative index reconciliation: `source-index` is a cumulative fact ledger, not a one-run artifact. For every formal multi-chapter production request, calculate `requested_output_range`, `forward_index_range`, `existing_index_range`, and `required_cumulative_index_range = existing_index_range ∪ forward_index_range`. If new evidence changes old anonymous roles, aliases, asset tiers, asset names, or source identity, run reconciliation before `asset-bible`, `faithful-feed`, image generation, or copy-pack work continues.

Confirmed anonymous-to-named upgrade: when a former `弟子/NPC/黑衣人/侍女/守卫/路人` later receives a source-backed name, dialogue, recurrence, relationship, faction, or plot function, bind all appearances to one canonical source identity. If prior artifacts used the temporary name, update the canonical mother feed first, then re-run feed audit, then regenerate copy packs. Image assets must be renamed, marked deprecated, or regenerated with evidence recorded in `生产资产/_内部/reconciliation-log.md`.

Suspected upgrades remain private. Do not merge, rename, or claim identity until the source evidence is confirmed or the user explicitly chooses a reconciliation action.
```

- [ ] **Step 4: Add source-index cumulative procedure**

In `agents/source-indexer.md`, add this section after the existing `forward index scope` paragraph.

```markdown
## Cumulative index reconciliation

For formal production, compute these ranges before updating the index:

```text
requested_output_range = chapters the user asked to deliver
forward_index_range = requested_output_range + next 3 chapters when available
existing_index_range = source-index read range from previous runs
required_cumulative_index_range = existing_index_range ∪ forward_index_range
```

Read any missing chapters inside `required_cumulative_index_range` before asset decisions. The forward part is identity/continuity only; do not leak future plot into the delivered feed or copy packs.

After updating the index, run the reconciliation check before `asset-bible`:

- early anonymous roles that later become named, speaking, recurring, faction-linked, or plot-bearing;
- aliases, titles, spelling drift, role tier changes, or period/state changes;
- old asset names, old feed mentions, old copy-pack bindings, and image-manifest records affected by the new evidence;
- whether each case is `none`, `suspected`, `confirmed`, or `rejected`.

Confirmed upgrades must record `Former temporary names:`, `Upgrade status: confirmed`, `Evidence anchors:`, `Affected prior artifacts:`, and `Asset migration status:`. Write a compact entry to `生产资产/_内部/reconciliation-log.md`.
```

- [ ] **Step 5: Extend `references/source-index-format.md`**

Update the `## Scope Status` and `## Character Index` templates with these fields.

```text
## Scope Status
- Index status: 全范围预扫 / 局部烟测
- Requested range:
- Requested output ranges completed:
- Requested output range:
- Forward index ranges read:
- Forward index range:
- Cumulative index range:
- Missing source ranges:
- Reconciliation status: none / pending / completed / needs user confirmation
- Evidence basis:
- Future reveal private: yes / no
- forward index scope: requested output range + next 3 chapters, identity/continuity only; do not leak future plot into the delivered feed or copy packs.

## Character Index
- Name:
  - Canonical source name:
  - Former temporary names:
  - Standard name basis:
  - Alias evidence:
  - Aliases/titles:
  - Role tier:
  - First anonymous appearance:
  - Naming evidence:
  - Upgrade status: none / suspected / confirmed / rejected
  - Affected prior artifacts:
  - Asset migration status: none / rename / deprecated / regenerate / needs user confirmation
  - Evidence anchors:
```

Add this ledger before `## Evidence Anchors`.

```text
## Reconciliation Ledger
- Canonical name:
  - Former temporary names:
  - Upgrade status: none / suspected / confirmed / rejected
  - Migration action: none / rename / deprecated / regenerate / needs user confirmation
  - Evidence anchors:
  - Affected prior artifacts:
  - Updated files:
  - User confirmation needed:
```

- [ ] **Step 6: Extend asset-bible rules and format**

In `agents/asset-bible.md`, add:

```markdown
Before creating or updating assets, read the source-index reconciliation ledger. If there is a confirmed anonymous-to-named upgrade with unresolved migration, do not create new downstream assets under the old temporary name. First choose one migration action: rename, deprecated, regenerate, or needs user confirmation. Asset decisions must cite the source-index evidence anchor.
```

In `references/asset-bible-format.md`, add these fields to each asset entry template:

```text
  - Canonical asset name:
  - Previous asset names:
  - Migration action: none / rename / deprecated / regenerate / needs user confirmation
  - Replaced by:
  - Source-index evidence:
  - Prior feed lines affected:
```

- [ ] **Step 7: Add stage-aware recommendation rules to route docs**

In `SKILL.md`, `agents/copy-packager.md`, `agents/production-runner.md`, `agents/image-generator.md`, and `agents/storyboard-contact-sheet.md`, add this shared block near the existing completion handoff section.

```markdown
Stage-aware next-step recommendations: every completed stage should end with a short status block and exactly three next-step options unless the user already chose the next action. Recommendations only suggest the next action; do not execute unless the user chooses it.

Use this output shape:

```text
当前状态：
- 母稿：已通过 / 未生成 / 需修正
- 复制包：已通过 / 未生成 / 需重生
- 图片资产：未生成 / 风格待确认 / 部分失败 / 已完成
- 分镜QA：未开始 / 已完成 / 需修正
- 索引回填：无待处理 / 有待处理

下一步建议（推荐优先）：
1. 推荐项 - 简短原因
2. 可选项
3. 可选项
```

Recommendation priority:

- if reconciliation has pending confirmed upgrades, recommend 处理索引回填 first;
- if the canonical mother feed and copy packs are done but images are missing, recommend 自动化生图 first;
- if style preview images are done but not confirmed, recommend 确认风格基准 first;
- if images are failed or blocked, recommend 续跑/修复失败图片 first;
- if all images are done and the canonical feed is valid, recommend 分镜/站位 QA;
- if the user mentions duration, deletion, platform pressure, or pacing, recommend 安全剪辑 before visual polish;
- otherwise recommend 视频增强 when the next goal is stronger visual performance;
- if the current batch is closed with feed, copy packs, images, and storyboard QA all valid, recommend 继续下一批章节.
```

- [ ] **Step 8: Run documentation tests**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests
```

Expected: PASS.

- [ ] **Step 9: Commit docs**

```powershell
git add SKILL.md agents/source-indexer.md references/source-index-format.md agents/asset-bible.md references/asset-bible-format.md agents/copy-packager.md agents/production-runner.md agents/image-generator.md agents/storyboard-contact-sheet.md
git commit -m "feat: document scope gate and reconciliation workflow"
```

---

### Task 3: Add Failing Production Scope Tests

**Files:**
- Create: `tests/test_production_scope.py`
- Test command: `python -m unittest tests.test_production_scope`

- [ ] **Step 1: Create scope behavior tests**

Create `tests/test_production_scope.py`.

```python
import unittest

from scripts.production_scope_core import (
    ChapterRange,
    ProductionScopeDecision,
    compute_forward_index_range,
    compute_required_cumulative_index_range,
    parse_scope_choice,
    should_ask_scope_gate,
)


class ProductionScopeCoreTests(unittest.TestCase):
    def test_ambiguous_long_formal_request_requires_scope_gate(self) -> None:
        decision = should_ask_scope_gate(
            total_chapters=12,
            explicit_output_range=None,
            is_formal_production=True,
        )

        self.assertTrue(decision.required)
        self.assertEqual(decision.recommended_chapters, 3)
        self.assertIn("建议先跑3章", decision.prompt)
        self.assertIn("收到选择前，我不会生成连续投喂稿或复制包", decision.prompt)

    def test_three_or_fewer_chapters_do_not_require_scope_gate(self) -> None:
        decision = should_ask_scope_gate(
            total_chapters=3,
            explicit_output_range=None,
            is_formal_production=True,
        )

        self.assertFalse(decision.required)
        self.assertEqual(decision.recommended_chapters, 3)

    def test_explicit_one_chapter_delivers_one_and_reads_next_three(self) -> None:
        output_range = parse_scope_choice("跑第1章", total_chapters=8, gate_was_shown=False)
        forward_range = compute_forward_index_range(output_range, total_chapters=8)

        self.assertEqual(output_range, ChapterRange(1, 1))
        self.assertEqual(forward_range, ChapterRange(1, 4))

    def test_default_after_gate_means_first_three_chapters(self) -> None:
        output_range = parse_scope_choice("默认", total_chapters=10, gate_was_shown=True)
        forward_range = compute_forward_index_range(output_range, total_chapters=10)

        self.assertEqual(output_range, ChapterRange(1, 3))
        self.assertEqual(forward_range, ChapterRange(1, 6))

    def test_specific_range_expands_cumulative_index_without_dropping_old_range(self) -> None:
        output_range = parse_scope_choice("跑第2-3章", total_chapters=9, gate_was_shown=False)
        forward_range = compute_forward_index_range(output_range, total_chapters=9)
        cumulative_range = compute_required_cumulative_index_range(
            existing_index_range=ChapterRange(1, 4),
            forward_index_range=forward_range,
        )

        self.assertEqual(output_range, ChapterRange(2, 3))
        self.assertEqual(forward_range, ChapterRange(2, 6))
        self.assertEqual(cumulative_range, ChapterRange(1, 6))

    def test_full_book_batch_default_is_three_chapters(self) -> None:
        output_range = parse_scope_choice("全本分批", total_chapters=20, gate_was_shown=True)

        self.assertEqual(output_range, ChapterRange(1, 3))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_production_scope
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.production_scope_core'`.

- [ ] **Step 3: Commit failing tests**

```powershell
git add tests/test_production_scope.py
git commit -m "test: cover production scope gate calculations"
```

---

### Task 4: Implement Production Scope Core

**Files:**
- Create: `scripts/production_scope_core.py`
- Test command: `python -m unittest tests.test_production_scope`

- [ ] **Step 1: Create deterministic scope helper**

Create `scripts/production_scope_core.py`.

```python
#!/usr/bin/env python3
"""Production scope helpers for source-true-guoman."""

from __future__ import annotations

import re
from dataclasses import dataclass


SCOPE_GATE_PROMPT = (
    "生产范围缺失：检测到文本超过3章。建议先跑3章；你也可以指定 1-5 章、"
    "具体章节范围，或明确说全本分批。收到选择前，我不会生成连续投喂稿或复制包。"
)


@dataclass(frozen=True, order=True)
class ChapterRange:
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 1:
            raise ValueError("chapter range start must be at least 1")
        if self.end < self.start:
            raise ValueError("chapter range end must be greater than or equal to start")


@dataclass(frozen=True)
class ProductionScopeDecision:
    required: bool
    recommended_chapters: int
    prompt: str


def should_ask_scope_gate(
    total_chapters: int,
    explicit_output_range: ChapterRange | None,
    is_formal_production: bool,
) -> ProductionScopeDecision:
    if total_chapters < 0:
        raise ValueError("total_chapters must be zero or greater")
    required = (
        is_formal_production
        and total_chapters > 3
        and explicit_output_range is None
    )
    return ProductionScopeDecision(
        required=required,
        recommended_chapters=3,
        prompt=SCOPE_GATE_PROMPT if required else "",
    )


def parse_scope_choice(
    user_text: str,
    total_chapters: int,
    gate_was_shown: bool,
) -> ChapterRange:
    normalized = user_text.strip()
    if total_chapters < 1:
        raise ValueError("total_chapters must be at least 1")

    if gate_was_shown and normalized in {"默认", "默認", "default"}:
        return ChapterRange(1, min(3, total_chapters))
    if "前三章" in normalized or "前3章" in normalized:
        return ChapterRange(1, min(3, total_chapters))
    if "全本分批" in normalized or "全书分批" in normalized:
        return ChapterRange(1, min(3, total_chapters))

    range_match = re.search(r"第?\s*(\d+)\s*[-~到至]\s*(\d+)\s*章", normalized)
    if range_match:
        start = int(range_match.group(1))
        end = min(int(range_match.group(2)), total_chapters)
        return ChapterRange(start, end)

    single_match = re.search(r"第?\s*(\d+)\s*章", normalized)
    if single_match:
        chapter = min(int(single_match.group(1)), total_chapters)
        return ChapterRange(chapter, chapter)

    count_match = re.search(r"(?:先)?跑\s*(\d+)\s*章", normalized)
    if count_match:
        count = max(1, int(count_match.group(1)))
        return ChapterRange(1, min(count, total_chapters))

    raise ValueError("could not parse production scope choice")


def compute_forward_index_range(
    requested_output_range: ChapterRange,
    total_chapters: int,
    lookahead_chapters: int = 3,
) -> ChapterRange:
    if total_chapters < requested_output_range.start:
        raise ValueError("total_chapters must include requested range start")
    return ChapterRange(
        requested_output_range.start,
        min(total_chapters, requested_output_range.end + lookahead_chapters),
    )


def compute_required_cumulative_index_range(
    existing_index_range: ChapterRange | None,
    forward_index_range: ChapterRange,
) -> ChapterRange:
    if existing_index_range is None:
        return forward_index_range
    return ChapterRange(
        min(existing_index_range.start, forward_index_range.start),
        max(existing_index_range.end, forward_index_range.end),
    )
```

- [ ] **Step 2: Run scope tests**

Run:

```powershell
python -m unittest tests.test_production_scope
```

Expected: PASS.

- [ ] **Step 3: Commit implementation**

```powershell
git add scripts/production_scope_core.py
git commit -m "feat: add production scope helpers"
```

---

### Task 5: Add Failing Recommendation Engine Tests

**Files:**
- Create: `tests/test_recommend_next_steps.py`
- Test command: `python -m unittest tests.test_recommend_next_steps`

- [ ] **Step 1: Create recommendation tests**

Create `tests/test_recommend_next_steps.py`.

```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.recommend_next_steps import (
    RecommendationState,
    inspect_workspace,
    recommendation_block,
    recommend_next_steps,
)


class RecommendationEngineTests(unittest.TestCase):
    def test_pending_reconciliation_is_first_priority(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="done",
            storyboard="not_started",
            reconciliation="pending",
            recent_user_intent="continue",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "处理索引回填")
        self.assertIn("新章节证据改变了旧角色/资产判断", recommendation.options[0].reason)

    def test_missing_images_after_copy_packs_recommends_image_generation(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="missing",
            storyboard="not_started",
            reconciliation="none",
            recent_user_intent="",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "自动化生图")
        self.assertEqual(recommendation.options[0].command, "image-generator")

    def test_style_preview_done_requires_user_confirmation(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="style_preview_done",
            storyboard="not_started",
            reconciliation="none",
            recent_user_intent="",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "确认风格基准")
        self.assertIn("未确认前不跑全量依赖资产", recommendation.options[0].reason)

    def test_failed_images_block_storyboard_recommend_retry_first(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="failed",
            storyboard="not_started",
            reconciliation="none",
            recent_user_intent="分镜",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "续跑/修复失败图片")
        self.assertTrue(
            any("暂不建议分镜 QA" in blocked.reason for blocked in recommendation.blocked)
        )

    def test_done_images_recommend_storyboard_qa(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="done",
            storyboard="not_started",
            reconciliation="none",
            recent_user_intent="",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "分镜/站位 QA")
        self.assertEqual(recommendation.options[0].command, "storyboard-contact-sheet")

    def test_duration_intent_recommends_cut_safety(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="done",
            storyboard="done",
            reconciliation="none",
            recent_user_intent="平台时长太长，需要删减",
        )

        recommendation = recommend_next_steps(state)

        self.assertEqual(recommendation.options[0].action, "安全剪辑")
        self.assertEqual(recommendation.options[0].command, "cut-safety")

    def test_recommendation_block_contains_status_and_three_options(self) -> None:
        state = RecommendationState(
            mother_feed="passed",
            copy_packs="passed",
            images="missing",
            storyboard="not_started",
            reconciliation="none",
            recent_user_intent="",
        )

        block = recommendation_block(state, recommend_next_steps(state))

        self.assertIn("当前状态：", block)
        self.assertIn("下一步建议（推荐优先）：", block)
        self.assertEqual(block.count("\n1. "), 1)
        self.assertEqual(block.count("\n2. "), 1)
        self.assertEqual(block.count("\n3. "), 1)


class RecommendationWorkspaceInspectionTests(unittest.TestCase):
    def test_inspect_workspace_reads_image_manifest_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            internal = workspace / "生产资产" / "_内部"
            internal.mkdir(parents=True)
            (workspace / "生产资产" / "feed.md").write_text("母稿", encoding="utf-8")
            (workspace / "生产资产" / "copy-packs.md").write_text("复制包", encoding="utf-8")
            (internal / "image-manifest.json").write_text(
                json.dumps(
                    {
                        "assets": [
                            {"asset_name": "a", "status": "done", "path": "人设资产/a.png"},
                            {"asset_name": "b", "status": "blocked", "path": "人设资产/b.png"},
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            state = inspect_workspace(workspace)

        self.assertEqual(state.mother_feed, "passed")
        self.assertEqual(state.copy_packs, "passed")
        self.assertEqual(state.images, "blocked")

    def test_cli_prints_recommendation_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "recommend_next_steps.py"),
                    "--workspace",
                    str(workspace),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("当前状态：", result.stdout)
        self.assertIn("下一步建议（推荐优先）：", result.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_recommend_next_steps
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.recommend_next_steps'`.

- [ ] **Step 3: Commit failing tests**

```powershell
git add tests/test_recommend_next_steps.py
git commit -m "test: cover stage-aware recommendations"
```

---

### Task 6: Implement Recommendation Engine

**Files:**
- Create: `scripts/recommend_next_steps.py`
- Test command: `python -m unittest tests.test_recommend_next_steps`

- [ ] **Step 1: Create recommendation script**

Create `scripts/recommend_next_steps.py`.

```python
#!/usr/bin/env python3
"""Stage-aware next-step recommendations for source-true-guoman workspaces."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATUS_LABELS = {
    "mother_feed": {
        "passed": "已通过",
        "missing": "未生成",
        "needs_fix": "需修正",
    },
    "copy_packs": {
        "passed": "已通过",
        "missing": "未生成",
        "needs_regeneration": "需重生",
    },
    "images": {
        "missing": "未生成",
        "style_preview_done": "风格待确认",
        "failed": "部分失败",
        "blocked": "部分失败",
        "done": "已完成",
        "deprecated": "需迁移",
        "renamed": "需复核",
    },
    "storyboard": {
        "not_started": "未开始",
        "done": "已完成",
        "needs_fix": "需修正",
    },
    "reconciliation": {
        "none": "无待处理",
        "pending": "有待处理",
        "needs_user_confirmation": "需用户确认",
    },
}


@dataclass(frozen=True)
class RecommendationState:
    mother_feed: str
    copy_packs: str
    images: str
    storyboard: str
    reconciliation: str
    recent_user_intent: str = ""


@dataclass(frozen=True)
class RecommendationOption:
    action: str
    reason: str
    command: str = ""


@dataclass(frozen=True)
class BlockedAction:
    action: str
    reason: str


@dataclass(frozen=True)
class Recommendation:
    options: list[RecommendationOption]
    blocked: list[BlockedAction]


def recommend_next_steps(state: RecommendationState) -> Recommendation:
    blocked: list[BlockedAction] = []

    if state.reconciliation in {"pending", "needs_user_confirmation"}:
        return Recommendation(
            options=[
                RecommendationOption("处理索引回填", "新章节证据改变了旧角色/资产判断，先修正索引、母稿、复制包和 manifest。", "validate-reconciliation"),
                RecommendationOption("暂停并人工确认疑似身份", "存在不能自动合并的疑似同一角色或旧图沿用判断。"),
                RecommendationOption("查看 reconciliation-log", "先看证据锚点和受影响文件，再决定 rename/deprecated/regenerate。"),
            ],
            blocked=[
                BlockedAction("继续下一批章节", "索引回填未处理前继续生产会沿用错误身份。")
            ],
        )

    if state.images == "style_preview_done":
        return Recommendation(
            options=[
                RecommendationOption("确认风格基准", "请先看第一个人设和第一个场景；未确认前不跑全量依赖资产。", "image-generator"),
                RecommendationOption("调整人设风格", "如果人设基准不对，先改提示词再重跑预览。"),
                RecommendationOption("调整场景风格", "如果场景基准不对，先改提示词再重跑预览。"),
            ],
            blocked=[
                BlockedAction("全量生图", "风格基准未确认。"),
                BlockedAction("分镜 QA", "真实图片资产还没有全量生成。"),
            ],
        )

    if state.images in {"failed", "blocked"}:
        return Recommendation(
            options=[
                RecommendationOption("续跑/修复失败图片", "分镜 QA 需要真实图片引用；当前仍有 failed 或 blocked 图片资产。", "image-generator --resume"),
                RecommendationOption("查看失败报告", "先定位失败资产、依赖资产或供应商错误。"),
                RecommendationOption("人工标记跳过并继续文本流程", "只适合确认该资产暂时不影响当前交付时使用。"),
            ],
            blocked=[BlockedAction("分镜 QA", "暂不建议分镜 QA：图片资产还没有全部生成并验证。")],
        )

    if state.mother_feed == "passed" and state.copy_packs == "passed" and state.images == "missing":
        return Recommendation(
            options=[
                RecommendationOption("自动化生图", "当前已有母稿、asset-bible 和复制包，但还没有本地图片资产。", "image-generator"),
                RecommendationOption("安全剪辑", "如有时长或删减压力，可先做删减风险报告。", "cut-safety"),
                RecommendationOption("视频增强", "如需加强镜头表现，先改母稿、再审计、再重生复制包。", "visual-polish"),
            ],
            blocked=[BlockedAction("分镜 QA", "图片资产未生成。")],
        )

    if _mentions_cut_pressure(state.recent_user_intent):
        return Recommendation(
            options=[
                RecommendationOption("安全剪辑", "你提到时长/删减/平台压力，先按连续行号和原文跨度给删减风险。", "cut-safety"),
                RecommendationOption("视频增强", "如果不是删减问题，可增强镜头表现但不能改写剧情。", "visual-polish"),
                RecommendationOption("继续下一批章节", "当前批次闭环后再进入下一批。"),
            ],
            blocked=[],
        )

    if state.mother_feed == "passed" and state.images == "done" and state.storyboard == "not_started":
        return Recommendation(
            options=[
                RecommendationOption("分镜/站位 QA", "图片资产已经齐了，下一步检查角色、场景、道具在真实镜头里的站位和连续性。", "storyboard-contact-sheet"),
                RecommendationOption("复制包绑定图片路径", "如果复制包还没有绑定 manifest，可先补绑定。", "copy-packager"),
                RecommendationOption("继续下一批章节", "当前批次文本和图片都通过后可进入下一批。"),
            ],
            blocked=[],
        )

    if state.mother_feed == "passed" and state.copy_packs == "passed" and state.images == "done" and state.storyboard == "done":
        return Recommendation(
            options=[
                RecommendationOption("继续下一批章节", "当前批次文本、图片、分镜 QA 都已闭环，可以进入下一批并执行累积索引回填。"),
                RecommendationOption("安全剪辑", "如果要控时长，先做删减风险报告。", "cut-safety"),
                RecommendationOption("视频增强", "如果要加强画面表现，先改母稿、再审计、再重生复制包。", "visual-polish"),
            ],
            blocked=[],
        )

    return Recommendation(
        options=[
            RecommendationOption("补齐正式生产链路", "先完成 source-index、asset-bible、faithful-feed、feed-auditor、copy-packager。"),
            RecommendationOption("自动化生图", "母稿和 asset-bible 通过后再运行。", "image-generator"),
            RecommendationOption("处理索引回填", "如果后续证据改变旧角色判断，先回填再继续。", "validate-reconciliation"),
        ],
        blocked=[],
    )


def recommendation_block(state: RecommendationState, recommendation: Recommendation) -> str:
    lines = [
        "当前状态：",
        f"- 母稿：{_label('mother_feed', state.mother_feed)}",
        f"- 复制包：{_label('copy_packs', state.copy_packs)}",
        f"- 图片资产：{_label('images', state.images)}",
        f"- 分镜QA：{_label('storyboard', state.storyboard)}",
        f"- 索引回填：{_label('reconciliation', state.reconciliation)}",
        "",
        "下一步建议（推荐优先）：",
    ]
    for index, option in enumerate(_three_options(recommendation.options), start=1):
        command = f" - run `{option.command}`" if option.command else ""
        lines.append(f"{index}. {option.action}{command}：{option.reason}")
    for blocked in recommendation.blocked:
        lines.append(f"暂不建议{blocked.action}：{blocked.reason}")
    return "\n".join(lines)


def inspect_workspace(workspace: Path, recent_user_intent: str = "") -> RecommendationState:
    workspace = Path(workspace)
    production_dir = workspace / "生产资产"
    internal_dir = production_dir / "_内部"
    manifest_path = internal_dir / "image-manifest.json"
    reconciliation_log = internal_dir / "reconciliation-log.md"

    return RecommendationState(
        mother_feed="passed" if _has_file(production_dir, ("feed", "母稿", "投喂")) else "missing",
        copy_packs="passed" if _has_file(production_dir, ("copy", "复制包", "投喂包")) else "missing",
        images=_image_state(manifest_path, internal_dir),
        storyboard="done" if (internal_dir / "storyboard-manifest.json").is_file() else "not_started",
        reconciliation=_reconciliation_state(reconciliation_log),
        recent_user_intent=recent_user_intent,
    )


def _has_file(directory: Path, markers: tuple[str, ...]) -> bool:
    if not directory.is_dir():
        return False
    for path in directory.glob("*.md"):
        lowered = path.name.casefold()
        if any(marker.casefold() in lowered for marker in markers):
            return True
    return False


def _image_state(manifest_path: Path, internal_dir: Path) -> str:
    preview_jobs = internal_dir / "image-jobs-style-preview.jsonl"
    if not manifest_path.is_file():
        return "style_preview_done" if preview_jobs.is_file() else "missing"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "failed"
    assets = manifest.get("assets", [])
    if not isinstance(assets, list) or not assets:
        return "missing"
    statuses = {
        str(asset.get("status", "")).strip()
        for asset in assets
        if isinstance(asset, dict)
    }
    for status in ("failed", "blocked", "deprecated", "renamed"):
        if status in statuses:
            return status
    if statuses == {"done"}:
        return "done"
    return "missing"


def _reconciliation_state(log_path: Path) -> str:
    if not log_path.is_file():
        return "none"
    try:
        text = log_path.read_text(encoding="utf-8")
    except OSError:
        return "pending"
    if "Reconciliation status: pending" in text or "Upgrade status: confirmed" in text:
        return "pending"
    if "needs user confirmation" in text:
        return "needs_user_confirmation"
    return "none"


def _mentions_cut_pressure(text: str) -> bool:
    return any(
        marker in text
        for marker in ("时长", "删减", "剪短", "节奏", "平台", "投放", "太长", "压缩")
    )


def _three_options(options: list[RecommendationOption]) -> list[RecommendationOption]:
    padded = list(options)
    while len(padded) < 3:
        padded.append(RecommendationOption("继续当前生产链路", "先补齐缺失产物再进入下一阶段。"))
    return padded[:3]


def _label(group: str, value: str) -> str:
    return STATUS_LABELS.get(group, {}).get(value, value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Recommend next source-true-guoman production steps.")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--recent-user-intent", default="")
    args = parser.parse_args()

    state = inspect_workspace(Path(args.workspace), recent_user_intent=args.recent_user_intent)
    print(recommendation_block(state, recommend_next_steps(state)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run recommendation tests**

Run:

```powershell
python -m unittest tests.test_recommend_next_steps
```

Expected: PASS.

- [ ] **Step 3: Commit implementation**

```powershell
git add scripts/recommend_next_steps.py
git commit -m "feat: add stage-aware recommendation engine"
```

---

### Task 7: Add Failing Reconciliation Tests

**Files:**
- Create: `tests/test_reconciliation.py`
- Test command: `python -m unittest tests.test_reconciliation.ReconciliationValidationTests`

- [ ] **Step 1: Create reconciliation validation tests**

Create `tests/test_reconciliation.py`.

```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.validate_reconciliation import (
    ReconciliationInputs,
    extract_reconciliation_upgrades,
    validate_reconciliation,
)


SOURCE_INDEX_WITH_CONFIRMED_UPGRADE = """
# Source Index

## Reconciliation Ledger
- Canonical name: 沈砚_青云宗内门弟子造型
  - Former temporary names: 黑衣弟子_一次性造型
  - Upgrade status: confirmed
  - Migration action: rename
  - Evidence anchors: ch06-line12
  - Affected prior artifacts: 生产资产/feed.md, 生产资产/copy-packs.md, 人设资产/黑衣弟子_一次性造型.png
"""


class ReconciliationValidationTests(unittest.TestCase):
    def test_extract_confirmed_upgrade_from_source_index(self) -> None:
        upgrades = extract_reconciliation_upgrades(SOURCE_INDEX_WITH_CONFIRMED_UPGRADE)

        self.assertEqual(len(upgrades), 1)
        self.assertEqual(upgrades[0].canonical_name, "沈砚_青云宗内门弟子造型")
        self.assertEqual(upgrades[0].former_names, ["黑衣弟子_一次性造型"])
        self.assertEqual(upgrades[0].status, "confirmed")
        self.assertEqual(upgrades[0].migration_action, "rename")

    def test_confirmed_upgrade_fails_when_old_name_remains_in_feed(self) -> None:
        inputs = ReconciliationInputs(
            source_index_text=SOURCE_INDEX_WITH_CONFIRMED_UPGRADE,
            asset_bible_text="### 图片1 = 沈砚_青云宗内门弟子造型\n- Migration action: rename\n- Source-index evidence: ch06-line12\n",
            mother_feed_text="1 白天 大殿 黑衣弟子_一次性造型 低头站着 <固定镜头> 无对白",
            copy_pack_text="1 白天 大殿 沈砚_青云宗内门弟子造型 低头站着 <固定镜头> 无对白",
            image_manifest={
                "assets": [
                    {
                        "asset_name": "黑衣弟子_一次性造型",
                        "status": "renamed",
                        "replaced_by": "沈砚_青云宗内门弟子造型",
                    }
                ]
            },
        )

        errors = validate_reconciliation(inputs)

        self.assertTrue(any("mother feed still contains former name" in error for error in errors))

    def test_confirmed_upgrade_requires_manifest_migration(self) -> None:
        inputs = ReconciliationInputs(
            source_index_text=SOURCE_INDEX_WITH_CONFIRMED_UPGRADE,
            asset_bible_text="### 图片1 = 沈砚_青云宗内门弟子造型\n- Migration action: rename\n- Source-index evidence: ch06-line12\n",
            mother_feed_text="1 白天 大殿 沈砚_青云宗内门弟子造型 低头站着 <固定镜头> 无对白",
            copy_pack_text="1 白天 大殿 沈砚_青云宗内门弟子造型 低头站着 <固定镜头> 无对白",
            image_manifest={
                "assets": [
                    {
                        "asset_name": "黑衣弟子_一次性造型",
                        "status": "done",
                        "path": "人设资产/黑衣弟子_一次性造型.png",
                    }
                ]
            },
        )

        errors = validate_reconciliation(inputs)

        self.assertTrue(any("manifest former asset must be renamed or deprecated" in error for error in errors))

    def test_suspected_upgrade_does_not_force_migration(self) -> None:
        source_index = SOURCE_INDEX_WITH_CONFIRMED_UPGRADE.replace(
            "Upgrade status: confirmed",
            "Upgrade status: suspected",
        )
        inputs = ReconciliationInputs(
            source_index_text=source_index,
            asset_bible_text="### 图片1 = 黑衣弟子_一次性造型\n",
            mother_feed_text="1 白天 大殿 黑衣弟子_一次性造型 低头站着 <固定镜头> 无对白",
            copy_pack_text="1 白天 大殿 黑衣弟子_一次性造型 低头站着 <固定镜头> 无对白",
            image_manifest={"assets": []},
        )

        errors = validate_reconciliation(inputs)

        self.assertEqual(errors, [])

    def test_cli_reports_validation_errors_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            internal = workspace / "生产资产" / "_内部"
            internal.mkdir(parents=True)
            feed = workspace / "生产资产" / "feed.md"
            copy_pack = workspace / "生产资产" / "copy-packs.md"
            source_index = internal / "source-index.md"
            asset_bible = internal / "asset-bible.md"
            manifest = internal / "image-manifest.json"
            source_index.write_text(SOURCE_INDEX_WITH_CONFIRMED_UPGRADE, encoding="utf-8")
            asset_bible.write_text("### 图片1 = 沈砚_青云宗内门弟子造型\n- Migration action: rename\n", encoding="utf-8")
            feed.write_text("1 黑衣弟子_一次性造型 <固定镜头>", encoding="utf-8")
            copy_pack.write_text("1 沈砚_青云宗内门弟子造型 <固定镜头>", encoding="utf-8")
            manifest.write_text(json.dumps({"assets": []}, ensure_ascii=False), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "validate_reconciliation.py"),
                    "--source-index",
                    str(source_index),
                    "--asset-bible",
                    str(asset_bible),
                    "--mother-feed",
                    str(feed),
                    "--copy-packs",
                    str(copy_pack),
                    "--image-manifest",
                    str(manifest),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Reconciliation validation failed:", result.stdout)
        self.assertIn("mother feed still contains former name", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_reconciliation.ReconciliationValidationTests
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.validate_reconciliation'`.

- [ ] **Step 3: Commit failing tests**

```powershell
git add tests/test_reconciliation.py
git commit -m "test: cover reconciliation validation"
```

---

### Task 8: Implement Reconciliation Validator

**Files:**
- Create: `scripts/validate_reconciliation.py`
- Test command: `python -m unittest tests.test_reconciliation.ReconciliationValidationTests`

- [ ] **Step 1: Create validator script**

Create `scripts/validate_reconciliation.py`.

```python
#!/usr/bin/env python3
"""Validate source-index reconciliation against downstream artifacts."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReconciliationUpgrade:
    canonical_name: str
    former_names: list[str]
    status: str
    migration_action: str
    evidence_anchors: str


@dataclass(frozen=True)
class ReconciliationInputs:
    source_index_text: str
    asset_bible_text: str
    mother_feed_text: str
    copy_pack_text: str
    image_manifest: dict[str, Any]


def extract_reconciliation_upgrades(source_index_text: str) -> list[ReconciliationUpgrade]:
    upgrades: list[ReconciliationUpgrade] = []
    current: dict[str, str] | None = None

    for raw_line in source_index_text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("- Canonical name:"):
            if current is not None:
                upgrades.append(_upgrade_from_fields(current))
            current = {"canonical_name": stripped.partition(":")[2].strip()}
            continue
        if current is None or not stripped.startswith("- "):
            continue
        key, separator, value = stripped[2:].partition(":")
        if not separator:
            continue
        normalized_key = key.strip().casefold().replace(" ", "_")
        current[normalized_key] = value.strip()

    if current is not None:
        upgrades.append(_upgrade_from_fields(current))
    return [upgrade for upgrade in upgrades if upgrade.canonical_name]


def validate_reconciliation(inputs: ReconciliationInputs) -> list[str]:
    errors: list[str] = []
    upgrades = extract_reconciliation_upgrades(inputs.source_index_text)
    manifest_assets = _manifest_assets_by_name(inputs.image_manifest)

    for upgrade in upgrades:
        if upgrade.status != "confirmed":
            continue
        label = upgrade.canonical_name
        if not upgrade.evidence_anchors:
            errors.append(f"{label}: confirmed upgrade requires evidence anchors")
        if upgrade.migration_action not in {"rename", "deprecated", "regenerate"}:
            errors.append(f"{label}: confirmed upgrade requires rename, deprecated, or regenerate migration action")
        if label not in inputs.asset_bible_text:
            errors.append(f"{label}: asset-bible missing canonical asset name")
        if "Migration action:" not in inputs.asset_bible_text:
            errors.append(f"{label}: asset-bible missing Migration action")
        if "Source-index evidence:" not in inputs.asset_bible_text:
            errors.append(f"{label}: asset-bible missing Source-index evidence")

        for former_name in upgrade.former_names:
            if former_name and former_name in inputs.mother_feed_text:
                errors.append(f"{label}: mother feed still contains former name {former_name}")
            if former_name and former_name in inputs.copy_pack_text:
                errors.append(f"{label}: copy packs still contain former name {former_name}")
            former_asset = manifest_assets.get(former_name)
            if former_asset is not None:
                status = str(former_asset.get("status", "")).strip()
                replaced_by = str(former_asset.get("replaced_by", "")).strip()
                if status not in {"renamed", "deprecated"} or replaced_by != label:
                    errors.append(
                        f"{label}: manifest former asset must be renamed or deprecated with replaced_by {label}"
                    )

    return errors


def _upgrade_from_fields(fields: dict[str, str]) -> ReconciliationUpgrade:
    return ReconciliationUpgrade(
        canonical_name=fields.get("canonical_name", "").strip(),
        former_names=_split_names(fields.get("former_temporary_names", "")),
        status=fields.get("upgrade_status", "none").strip(),
        migration_action=fields.get("migration_action", "none").strip(),
        evidence_anchors=fields.get("evidence_anchors", "").strip(),
    )


def _split_names(value: str) -> list[str]:
    names: list[str] = []
    for item in value.replace("，", ",").split(","):
        stripped = item.strip()
        if stripped:
            names.append(stripped)
    return names


def _manifest_assets_by_name(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    assets = manifest.get("assets", [])
    if not isinstance(assets, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        asset_name = str(asset.get("asset_name", "")).strip()
        if asset_name:
            result[asset_name] = asset
    return result


def _read_text(path_text: str) -> str:
    return Path(path_text).expanduser().resolve().read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate source-true-guoman reconciliation state.")
    parser.add_argument("--source-index", required=True)
    parser.add_argument("--asset-bible", required=True)
    parser.add_argument("--mother-feed", required=True)
    parser.add_argument("--copy-packs", required=True)
    parser.add_argument("--image-manifest", required=True)
    args = parser.parse_args()

    try:
        manifest = json.loads(_read_text(args.image_manifest))
        if not isinstance(manifest, dict):
            raise ValueError("image manifest must be a JSON object")
        inputs = ReconciliationInputs(
            source_index_text=_read_text(args.source_index),
            asset_bible_text=_read_text(args.asset_bible),
            mother_feed_text=_read_text(args.mother_feed),
            copy_pack_text=_read_text(args.copy_packs),
            image_manifest=manifest,
        )
        errors = validate_reconciliation(inputs)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        errors = [str(error)]

    if errors:
        print("Reconciliation validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Reconciliation validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run reconciliation validation tests**

Run:

```powershell
python -m unittest tests.test_reconciliation.ReconciliationValidationTests
```

Expected: PASS.

- [ ] **Step 3: Commit implementation**

```powershell
git add scripts/validate_reconciliation.py
git commit -m "feat: validate cumulative index reconciliation"
```

---

### Task 9: Add Manifest Migration Status Tests

**Files:**
- Modify: `tests/test_image_generation.py`
- Test command: `python -m unittest tests.test_image_generation.ImageManifestValidationTests`

- [ ] **Step 1: Add manifest migration tests**

Find the image manifest validation test class in `tests/test_image_generation.py` and add these tests.

```python
    def test_validate_manifest_accepts_renamed_asset_with_alias_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            job = self.make_job("沈砚_青云宗内门弟子造型")
            output_path = root / job.output_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"image")
            manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [
                    self.manifest_asset(
                        job,
                        status="renamed",
                        previous_asset_name="黑衣弟子_一次性造型",
                        aliases=["黑衣弟子_一次性造型"],
                        migration_reason="ch06 reveals the early black-clothed disciple is 沈砚",
                        evidence_anchor="ch06-line12",
                    )
                ],
            }

            errors = validate_manifest(manifest, [job], root)

        self.assertEqual(errors, [])

    def test_validate_manifest_accepts_deprecated_former_asset_with_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [
                    {
                        "asset_name": "黑衣弟子_一次性造型",
                        "asset_type": "character",
                        "status": "deprecated",
                        "replaced_by": "沈砚_青云宗内门弟子造型",
                        "migration_reason": "identity upgraded by later source evidence",
                        "evidence_anchor": "ch06-line12",
                    }
                ],
            }

            errors = validate_manifest(manifest, [], root)

        self.assertEqual(errors, [])

    def test_validate_manifest_rejects_incomplete_migration_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            job = self.make_job("沈砚_青云宗内门弟子造型")
            manifest = {
                "version": 1,
                "provider": "openai-compatible",
                "assets": [
                    self.manifest_asset(job, status="renamed"),
                    {
                        "asset_name": "黑衣弟子_一次性造型",
                        "asset_type": "character",
                        "status": "deprecated",
                    },
                ],
            }

            errors = validate_manifest(manifest, [job], root)

        joined = "; ".join(errors)
        self.assertIn("renamed asset requires previous_asset_name", joined)
        self.assertIn("renamed asset requires aliases", joined)
        self.assertIn("deprecated asset requires replaced_by", joined)
        self.assertIn("migration_reason is required", joined)
        self.assertIn("evidence_anchor is required", joined)
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_image_generation.ImageManifestValidationTests
```

Expected: FAIL because `renamed` and `deprecated` are not accepted manifest statuses yet.

- [ ] **Step 3: Commit failing tests**

```powershell
git add tests/test_image_generation.py
git commit -m "test: cover image manifest migration statuses"
```

---

### Task 10: Extend Image Manifest Migration Validation

**Files:**
- Modify: `scripts/image_generation_core.py`
- Test command: `python -m unittest tests.test_image_generation.ImageManifestValidationTests`

- [ ] **Step 1: Extend allowed statuses**

Change `ALLOWED_MANIFEST_STATUSES` in `scripts/image_generation_core.py`.

```python
ALLOWED_MANIFEST_STATUSES = {"done", "failed", "blocked", "renamed", "deprecated"}
```

- [ ] **Step 2: Add migration metadata validation**

Inside `validate_manifest`, after status validation and before the done-file check, add this helper call:

```python
        errors.extend(_validate_migration_metadata(asset_label, asset, status))
```

Add this helper near the other manifest helpers.

```python
def _validate_migration_metadata(
    asset_label: str,
    asset: dict[str, Any],
    status: str,
) -> list[str]:
    errors: list[str] = []
    if status not in {"renamed", "deprecated"}:
        return errors

    migration_reason = str(asset.get("migration_reason", "")).strip()
    evidence_anchor = str(asset.get("evidence_anchor", "")).strip()
    if not migration_reason:
        errors.append(f"{asset_label}: migration_reason is required")
    if not evidence_anchor:
        errors.append(f"{asset_label}: evidence_anchor is required")

    if status == "renamed":
        previous_asset_name = str(asset.get("previous_asset_name", "")).strip()
        aliases = asset.get("aliases")
        if not previous_asset_name:
            errors.append(f"{asset_label}: renamed asset requires previous_asset_name")
        if not isinstance(aliases, list) or not aliases:
            errors.append(f"{asset_label}: renamed asset requires aliases")
    if status == "deprecated":
        replaced_by = str(asset.get("replaced_by", "")).strip()
        if not replaced_by:
            errors.append(f"{asset_label}: deprecated asset requires replaced_by")

    return errors
```

- [ ] **Step 3: Allow deprecated entries without generated file paths**

In `validate_manifest`, skip generated-path validation for deprecated entries:

```python
        image_path: Path | None = None
        if status != "deprecated":
            path_errors, image_path = _validate_manifest_image_path(
                asset_label, path_text, workspace
            )
            errors.extend(path_errors)
```

Keep the existing done-file check only for `status == "done"`.

- [ ] **Step 4: Run manifest tests**

Run:

```powershell
python -m unittest tests.test_image_generation.ImageManifestValidationTests
```

Expected: PASS.

- [ ] **Step 5: Commit implementation**

```powershell
git add scripts/image_generation_core.py
git commit -m "feat: support image manifest migration states"
```

---

### Task 11: Add Failing Asset Migration Tests

**Files:**
- Modify: `tests/test_reconciliation.py`
- Test command: `python -m unittest tests.test_reconciliation.AssetMigrationTests`

- [ ] **Step 1: Add migration tests**

Append this class to `tests/test_reconciliation.py`.

```python
from scripts.migrate_asset_names import migrate_asset_name


class AssetMigrationTests(unittest.TestCase):
    def test_migrate_asset_name_renames_file_and_updates_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            asset_dir = workspace / "人设资产"
            asset_dir.mkdir()
            old_file = asset_dir / "黑衣弟子_一次性造型.png"
            old_file.write_bytes(b"image")
            manifest = {
                "version": 1,
                "assets": [
                    {
                        "asset_name": "黑衣弟子_一次性造型",
                        "asset_type": "character",
                        "status": "done",
                        "path": "人设资产/黑衣弟子_一次性造型.png",
                    }
                ],
            }

            updated = migrate_asset_name(
                manifest=manifest,
                workspace=workspace,
                old_name="黑衣弟子_一次性造型",
                new_name="沈砚_青云宗内门弟子造型",
                asset_dir="人设资产",
                mode="rename",
                migration_reason="ch06 reveals the early black-clothed disciple is 沈砚",
                evidence_anchor="ch06-line12",
                apply=True,
            )

        new_file = asset_dir / "沈砚_青云宗内门弟子造型.png"
        self.assertFalse(old_file.exists())
        self.assertTrue(new_file.is_file())
        assets = {asset["asset_name"]: asset for asset in updated["assets"]}
        self.assertEqual(assets["黑衣弟子_一次性造型"]["status"], "renamed")
        self.assertEqual(assets["黑衣弟子_一次性造型"]["replaced_by"], "沈砚_青云宗内门弟子造型")
        self.assertEqual(assets["沈砚_青云宗内门弟子造型"]["status"], "renamed")
        self.assertEqual(assets["沈砚_青云宗内门弟子造型"]["previous_asset_name"], "黑衣弟子_一次性造型")

    def test_migrate_asset_name_deprecates_old_asset_without_renaming_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            asset_dir = workspace / "人设资产"
            asset_dir.mkdir()
            old_file = asset_dir / "黑衣弟子_一次性造型.png"
            old_file.write_bytes(b"image")
            manifest = {"assets": [{"asset_name": "黑衣弟子_一次性造型", "asset_type": "character", "status": "done"}]}

            updated = migrate_asset_name(
                manifest=manifest,
                workspace=workspace,
                old_name="黑衣弟子_一次性造型",
                new_name="沈砚_青云宗内门弟子造型",
                asset_dir="人设资产",
                mode="deprecated",
                migration_reason="old face cannot represent confirmed source identity",
                evidence_anchor="ch06-line12",
                apply=True,
            )

        self.assertTrue(old_file.is_file())
        assets = {asset["asset_name"]: asset for asset in updated["assets"]}
        self.assertEqual(assets["黑衣弟子_一次性造型"]["status"], "deprecated")
        self.assertEqual(assets["黑衣弟子_一次性造型"]["replaced_by"], "沈砚_青云宗内门弟子造型")

    def test_migrate_asset_name_refuses_to_overwrite_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            asset_dir = workspace / "人设资产"
            asset_dir.mkdir()
            (asset_dir / "黑衣弟子_一次性造型.png").write_bytes(b"old")
            (asset_dir / "沈砚_青云宗内门弟子造型.png").write_bytes(b"new")

            with self.assertRaises(ValueError) as context:
                migrate_asset_name(
                    manifest={"assets": []},
                    workspace=workspace,
                    old_name="黑衣弟子_一次性造型",
                    new_name="沈砚_青云宗内门弟子造型",
                    asset_dir="人设资产",
                    mode="rename",
                    migration_reason="confirmed source evidence",
                    evidence_anchor="ch06-line12",
                    apply=True,
                )

        self.assertIn("target asset file already exists", str(context.exception))
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_reconciliation.AssetMigrationTests
```

Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.migrate_asset_names'`.

- [ ] **Step 3: Commit failing tests**

```powershell
git add tests/test_reconciliation.py
git commit -m "test: cover explicit asset name migration"
```

---

### Task 12: Implement Asset Migration Helper

**Files:**
- Create: `scripts/migrate_asset_names.py`
- Test command: `python -m unittest tests.test_reconciliation.AssetMigrationTests`

- [ ] **Step 1: Create migration helper**

Create `scripts/migrate_asset_names.py`.

```python
#!/usr/bin/env python3
"""Explicit asset-name migration helper for confirmed reconciliation cases."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def migrate_asset_name(
    manifest: dict[str, Any],
    workspace: Path,
    old_name: str,
    new_name: str,
    asset_dir: str,
    mode: str,
    migration_reason: str,
    evidence_anchor: str,
    apply: bool = False,
) -> dict[str, Any]:
    if mode not in {"rename", "deprecated"}:
        raise ValueError("mode must be rename or deprecated")
    if not old_name or not new_name:
        raise ValueError("old_name and new_name are required")
    if not migration_reason:
        raise ValueError("migration_reason is required")
    if not evidence_anchor:
        raise ValueError("evidence_anchor is required")

    workspace = Path(workspace)
    old_path = workspace / asset_dir / f"{old_name}.png"
    new_path = workspace / asset_dir / f"{new_name}.png"
    updated = deepcopy(manifest)
    assets = updated.setdefault("assets", [])
    if not isinstance(assets, list):
        raise ValueError("manifest assets must be a list")

    if mode == "rename":
        if apply:
            if new_path.exists():
                raise ValueError("target asset file already exists")
            if old_path.exists():
                new_path.parent.mkdir(parents=True, exist_ok=True)
                old_path.rename(new_path)
        _mark_old_asset(assets, old_name, new_name, migration_reason, evidence_anchor, status="renamed")
        _upsert_new_asset(
            assets,
            old_name=old_name,
            new_name=new_name,
            asset_dir=asset_dir,
            status="renamed",
            migration_reason=migration_reason,
            evidence_anchor=evidence_anchor,
        )
        return updated

    _mark_old_asset(assets, old_name, new_name, migration_reason, evidence_anchor, status="deprecated")
    return updated


def _mark_old_asset(
    assets: list[Any],
    old_name: str,
    new_name: str,
    migration_reason: str,
    evidence_anchor: str,
    status: str,
) -> None:
    asset = _find_asset(assets, old_name)
    if asset is None:
        asset = {"asset_name": old_name, "asset_type": "character"}
        assets.append(asset)
    asset["status"] = status
    asset["replaced_by"] = new_name
    asset["migration_reason"] = migration_reason
    asset["evidence_anchor"] = evidence_anchor


def _upsert_new_asset(
    assets: list[Any],
    old_name: str,
    new_name: str,
    asset_dir: str,
    status: str,
    migration_reason: str,
    evidence_anchor: str,
) -> None:
    asset = _find_asset(assets, new_name)
    if asset is None:
        asset = {"asset_name": new_name, "asset_type": "character"}
        assets.append(asset)
    asset["status"] = status
    asset["path"] = f"{asset_dir}/{new_name}.png"
    asset["previous_asset_name"] = old_name
    asset["aliases"] = sorted(set([*asset.get("aliases", []), old_name]))
    asset["migration_reason"] = migration_reason
    asset["evidence_anchor"] = evidence_anchor


def _find_asset(assets: list[Any], asset_name: str) -> dict[str, Any] | None:
    for asset in assets:
        if isinstance(asset, dict) and asset.get("asset_name") == asset_name:
            return asset
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate a confirmed asset name in image-manifest.json.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--old-name", required=True)
    parser.add_argument("--new-name", required=True)
    parser.add_argument("--asset-dir", required=True, choices=("人设资产", "场景资产", "道具资产"))
    parser.add_argument("--mode", required=True, choices=("rename", "deprecated"))
    parser.add_argument("--migration-reason", required=True)
    parser.add_argument("--evidence-anchor", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be a JSON object")
        updated = migrate_asset_name(
            manifest=manifest,
            workspace=Path(args.workspace).expanduser().resolve(),
            old_name=args.old_name,
            new_name=args.new_name,
            asset_dir=args.asset_dir,
            mode=args.mode,
            migration_reason=args.migration_reason,
            evidence_anchor=args.evidence_anchor,
            apply=args.apply,
        )
        if args.apply:
            manifest_path.write_text(
                json.dumps(updated, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Asset migration failed: {error}")
        return 1

    print(json.dumps(updated, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run migration tests**

Run:

```powershell
python -m unittest tests.test_reconciliation.AssetMigrationTests
```

Expected: PASS.

- [ ] **Step 3: Commit implementation**

```powershell
git add scripts/migrate_asset_names.py
git commit -m "feat: add explicit asset name migration helper"
```

---

### Task 13: Add CLI Smoke Tests And Full Regression

**Files:**
- Modify: `tests/test_reconciliation.py`
- Test command: `python -m unittest discover -s tests`

- [ ] **Step 1: Add asset migration CLI smoke test**

Append this test to `AssetMigrationTests`.

```python
    def test_migrate_asset_names_cli_writes_manifest_when_applied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            asset_dir = workspace / "人设资产"
            internal = workspace / "生产资产" / "_内部"
            asset_dir.mkdir(parents=True)
            internal.mkdir(parents=True)
            (asset_dir / "黑衣弟子_一次性造型.png").write_bytes(b"image")
            manifest_path = internal / "image-manifest.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "assets": [
                            {
                                "asset_name": "黑衣弟子_一次性造型",
                                "asset_type": "character",
                                "status": "done",
                                "path": "人设资产/黑衣弟子_一次性造型.png",
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve().parents[1] / "scripts" / "migrate_asset_names.py"),
                    "--manifest",
                    str(manifest_path),
                    "--workspace",
                    str(workspace),
                    "--old-name",
                    "黑衣弟子_一次性造型",
                    "--new-name",
                    "沈砚_青云宗内门弟子造型",
                    "--asset-dir",
                    "人设资产",
                    "--mode",
                    "rename",
                    "--migration-reason",
                    "confirmed by chapter 6",
                    "--evidence-anchor",
                    "ch06-line12",
                    "--apply",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            updated = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((asset_dir / "沈砚_青云宗内门弟子造型.png").is_file())
        self.assertTrue(any(asset["asset_name"] == "沈砚_青云宗内门弟子造型" for asset in updated["assets"]))
```

- [ ] **Step 2: Run focused tests**

Run:

```powershell
python -m unittest tests.test_production_scope tests.test_recommend_next_steps tests.test_reconciliation
python -m unittest tests.test_image_generation.ImageManifestValidationTests
python -m unittest tests.test_init_workspace.SkillTextRulesTests
```

Expected: PASS.

- [ ] **Step 3: Run full regression**

Run:

```powershell
python -m unittest discover -s tests
```

Expected: PASS. Existing image-generation tests must still keep generated files out of `生产资产`; only manifest statuses are extended.

- [ ] **Step 4: Run placeholder scan on changed docs**

Run:

```powershell
rg -n "[T]BD|[T]ODO|[待]定|[占]位|\?\?" SKILL.md agents references docs/superpowers/plans/2026-07-07-source-true-guoman-scope-gate-index-recommendations.md
```

Expected: no matches.

- [ ] **Step 5: Commit final tests**

```powershell
git add tests/test_reconciliation.py
git commit -m "test: add reconciliation CLI smoke coverage"
```

---

### Task 14: Sync Installed Skill Copy And Verify Final State

**Files:**
- Modify installed files under: `C:\Users\Administrator\.codex\skills\source-true-guoman`
- Test command: `python -m unittest discover -s tests`

- [ ] **Step 1: Sync changed files to installed skill directory**

Run from `E:\source-true-guoman`.

```powershell
Copy-Item -Force 'SKILL.md' 'C:\Users\Administrator\.codex\skills\source-true-guoman\SKILL.md'
Copy-Item -Force 'agents\source-indexer.md' 'C:\Users\Administrator\.codex\skills\source-true-guoman\agents\source-indexer.md'
Copy-Item -Force 'agents\asset-bible.md' 'C:\Users\Administrator\.codex\skills\source-true-guoman\agents\asset-bible.md'
Copy-Item -Force 'agents\copy-packager.md' 'C:\Users\Administrator\.codex\skills\source-true-guoman\agents\copy-packager.md'
Copy-Item -Force 'agents\production-runner.md' 'C:\Users\Administrator\.codex\skills\source-true-guoman\agents\production-runner.md'
Copy-Item -Force 'agents\image-generator.md' 'C:\Users\Administrator\.codex\skills\source-true-guoman\agents\image-generator.md'
Copy-Item -Force 'agents\storyboard-contact-sheet.md' 'C:\Users\Administrator\.codex\skills\source-true-guoman\agents\storyboard-contact-sheet.md'
Copy-Item -Force 'references\source-index-format.md' 'C:\Users\Administrator\.codex\skills\source-true-guoman\references\source-index-format.md'
Copy-Item -Force 'references\asset-bible-format.md' 'C:\Users\Administrator\.codex\skills\source-true-guoman\references\asset-bible-format.md'
Copy-Item -Force 'scripts\production_scope_core.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\scripts\production_scope_core.py'
Copy-Item -Force 'scripts\recommend_next_steps.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\scripts\recommend_next_steps.py'
Copy-Item -Force 'scripts\validate_reconciliation.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\scripts\validate_reconciliation.py'
Copy-Item -Force 'scripts\migrate_asset_names.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\scripts\migrate_asset_names.py'
Copy-Item -Force 'scripts\image_generation_core.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\scripts\image_generation_core.py'
Copy-Item -Force 'tests\test_init_workspace.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\tests\test_init_workspace.py'
Copy-Item -Force 'tests\test_production_scope.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\tests\test_production_scope.py'
Copy-Item -Force 'tests\test_recommend_next_steps.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\tests\test_recommend_next_steps.py'
Copy-Item -Force 'tests\test_reconciliation.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\tests\test_reconciliation.py'
Copy-Item -Force 'tests\test_image_generation.py' 'C:\Users\Administrator\.codex\skills\source-true-guoman\tests\test_image_generation.py'
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

- [ ] **Step 4: Smoke-check recommendation script on `E:\xianjie`**

Run:

```powershell
python scripts/recommend_next_steps.py --workspace 'E:\xianjie'
```

Expected: prints `当前状态：` and `下一步建议（推荐优先）：` without traceback. The recommendation may say missing artifacts if `E:\xianjie` does not currently contain saved mother feed, copy packs, or manifest.

- [ ] **Step 5: Commit sync-relevant repo changes**

Run:

```powershell
git status --short
git add SKILL.md agents/source-indexer.md agents/asset-bible.md agents/copy-packager.md agents/production-runner.md agents/image-generator.md agents/storyboard-contact-sheet.md references/source-index-format.md references/asset-bible-format.md scripts/production_scope_core.py scripts/recommend_next_steps.py scripts/validate_reconciliation.py scripts/migrate_asset_names.py scripts/image_generation_core.py tests/test_init_workspace.py tests/test_production_scope.py tests/test_recommend_next_steps.py tests/test_reconciliation.py tests/test_image_generation.py
git commit -m "feat: add scope gate reconciliation and recommendations"
```

If earlier task commits already captured all tracked changes and `git status --short` is clean except unrelated user files, do not create an empty commit.

---

## Final Verification Checklist

- [ ] `python -m unittest discover -s tests` passes in `E:\source-true-guoman`.
- [ ] Installed skill copy passes `python -m unittest discover -s 'C:\Users\Administrator\.codex\skills\source-true-guoman\tests'`.
- [ ] Ambiguous formal production over 3 chapters asks for production chapter count and recommends 3.
- [ ] Explicit 1-chapter production delivers only chapter 1 and reads chapters 1-4 for forward index.
- [ ] Continuing with chapters 2-3 after a prior chapter-1 run expands cumulative index to chapters 1-6.
- [ ] Confirmed anonymous-to-named upgrades cannot proceed while old names remain in mother feed or copy packs.
- [ ] Image manifest supports `done`, `failed`, `blocked`, `renamed`, and `deprecated`.
- [ ] `migrate_asset_names.py` refuses to overwrite an existing target image file.
- [ ] `recommend_next_steps.py` outputs exactly one status block and three next-step options.
- [ ] Stage-aware recommendations prioritize reconciliation, style confirmation, failed images, image generation, storyboard QA, safety cut, visual polish, and next batch in that order.
- [ ] Copy packs remain derived artifacts; all text changes start from the canonical mother feed.
- [ ] Forward-index future plot stays internal and does not leak into delivered feed or copy packs.
