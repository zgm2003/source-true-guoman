# Source True Guoman Agent Pack Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deepen `source-true-guoman` from a useful prototype into a baseline agent-pack workflow with enforceable routing, scope, asset, feed, and audit contracts.

**Architecture:** Keep one installed skill folder with progressive disclosure: `SKILL.md` stays the orchestrator, `agents/*.md` hold specialist behavior, `references/*.md` hold detailed formats/checklists, and `scripts/*.py` holds deterministic checks. The baseline production route is `source-indexer -> asset-bible -> faithful-feed -> feed-auditor`; `cut-safety`, `visual-polish`, and `production-runner` remain guarded optional specialists.

**Tech Stack:** Markdown skill files, Python 3 standard library scripts, `unittest`, Codex `quick_validate.py` skill validation.

---

## File Structure

- Modify `tests/test_init_workspace.py`: add focused contract tests before changing skill text or scripts. Keep these tests textual and deterministic because this repo is primarily a skill package.
- Modify `SKILL.md`: tighten the orchestrator route table, formal-vs-smoke scope rules, production asset storage policy, and specialist sequencing without bloating the main skill with reference-level detail.
- Modify `agents/source-indexer.md`: deepen source indexing procedure around evidence anchors, pre-scan status, recurring role upgrades, scene hierarchy, and unresolved doubts.
- Modify `references/source-index-format.md`: make the source index template explicit enough for formal and smoke modes, with stable sections and evidence fields.
- Modify `agents/asset-bible.md`: deepen asset planning procedure around full-scope dependency, tiers, tri-view requirements, derived outfit references, scene mother dependencies, and voice assets.
- Modify `references/asset-bible-format.md`: make the asset bible template explicit enough to represent stable reusable assets, slice-limited assets, upload reference purposes, and production dependencies.
- Modify `agents/faithful-feed.md`: tighten required prerequisites for formal multi-chapter feed output and private coverage-audit expectations.
- Modify `agents/feed-auditor.md`: add blocking-first review rules and make script-vs-human responsibilities explicit.
- Modify `references/audit-checklist.md`: expand deterministic and non-deterministic audit categories with file/line reporting expectations.
- Modify `scripts/validate_feed.py`: extend only deterministic feed checks that do not require story understanding.
- Modify `agents/cut-safety.md` and `references/cut-safety-rules.md`: keep cut-safety as deletion-risk analysis, not compression generation.
- Modify `agents/visual-polish.md`: keep polish source-locked and require an existing faithful feed.
- Modify `agents/production-runner.md`: deepen dependency checklist output without introducing Canvas, storyboard, or rendered-video workflow claims.
- Optionally modify `agents/openai.yaml` only if `SKILL.md` frontmatter meaning changes enough that the human-facing chip is stale. Do not add new optional metadata fields.

## Task 1: Orchestrator Routing Contracts

**Files:**
- Modify: `tests/test_init_workspace.py`
- Modify: `SKILL.md`

- [ ] **Step 1: Add failing tests for intent routing and guarded specialist order**

Add these methods inside `SkillTextRulesTests` in `tests/test_init_workspace.py`:

```python
    def test_main_skill_routes_common_intents_to_specialists(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")

        route_phrases = [
            "New project directory or root script file",
            "Process these chapters",
            "turn this into feed",
            "source-indexer -> asset-bible -> faithful-feed -> feed-auditor",
            "Make an index",
            "Make assets",
            "Write feed",
            "Review",
            "Can I delete",
            "Make it look better",
            "Production order",
        ]

        for phrase in route_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill_text)

    def test_optional_agents_are_guarded_by_prerequisites(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")

        guarded_phrases = [
            "cut-safety is a deletion-risk assistant, not a compression writer",
            "Only use `cut-safety` after the user has chosen deletion targets or asks for cut-risk help",
            "Only use `visual-polish` after preserving source coverage",
            "Only use `production-runner` after assets and faithful feed lines exist",
        ]

        for phrase in guarded_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill_text)
```

- [ ] **Step 2: Run the two new tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_main_skill_routes_common_intents_to_specialists tests.test_init_workspace.SkillTextRulesTests.test_optional_agents_are_guarded_by_prerequisites
```

Expected: `FAILED` with missing phrases from `SKILL.md`.

- [ ] **Step 3: Replace the `## Agent pack routing` section in `SKILL.md`**

Replace the current section from `## Agent pack routing` through the paragraph ending `Only use visual-polish after preserving source coverage.` with:

```markdown
## Agent pack routing

Treat this skill as the orchestrator for a lightweight specialist agent pack. The source-faithful feed remains the non-overridable center; specialist files only narrow the task, they do not override the core preservation stance.

Route by user intent:

- New project directory or root script file: initialize workspace first with `scripts/init_workspace.py <workspace>`, then archive root source scripts into `剧本资产`.
- "Process these chapters", "turn this into feed", long requested scope, or formal multi-chapter production: run `source-indexer -> asset-bible -> faithful-feed -> feed-auditor`.
- "Make an index", "read the source", "track roles", continuity questions, confusing aliases, or suspected typos: read `agents/source-indexer.md` and `references/source-index-format.md`.
- "Make assets", "who needs images", "avoid face collision", "what references upload", reusable characters, scenes, props, interfaces, beasts, vehicles, or voices: read `agents/asset-bible.md` and `references/asset-bible-format.md`.
- "Write feed", "video投喂", "faithful draft", or final continuous prompt blocks: read `agents/faithful-feed.md`, `references/format.md`, and `references/xiaoyunque-tags.md`.
- "Review", "check", "audit", "有没有问题", numbering QA, tag QA, or delivery gate: read `agents/feed-auditor.md` and `references/audit-checklist.md`; run `python scripts/validate_feed.py <feed-file>` when the feed is saved in a file.
- "Can I delete", "cut", "trim", "compress", manual deletion ranges, or platform-length pressure: read `agents/cut-safety.md` and `references/cut-safety-rules.md`. `cut-safety` is a deletion-risk assistant, not a compression writer.
- "Make it look better", "shot variety", "画面增强", camera rhythm, or comedy performance: read `agents/visual-polish.md` only after faithful coverage exists.
- "Production order", "upload references", dependency list, or batch checklist: read `agents/production-runner.md` only after assets and faithful feed lines exist.

Default first-phase route for long projects: `source-indexer -> asset-bible -> faithful-feed -> feed-auditor`.

Only use `cut-safety` after the user has chosen deletion targets or asks for cut-risk help. It may return exact line/source spans, risk levels, and safer boundaries; it must not write a rewritten compressed story. Only use `visual-polish` after preserving source coverage. Only use `production-runner` after assets and faithful feed lines exist.
```

- [ ] **Step 4: Run the two routing tests and verify they pass**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_main_skill_routes_common_intents_to_specialists tests.test_init_workspace.SkillTextRulesTests.test_optional_agents_are_guarded_by_prerequisites
```

Expected: `OK`.

- [ ] **Step 5: Run the full test suite**

Run:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Expected: all existing tests plus the two new tests pass.

- [ ] **Step 6: Commit**

```powershell
git add SKILL.md tests/test_init_workspace.py
git commit -m "feat: tighten agent pack routing contracts"
```

## Task 2: Source Index Baseline Depth

**Files:**
- Modify: `tests/test_init_workspace.py`
- Modify: `agents/source-indexer.md`
- Modify: `references/source-index-format.md`

- [ ] **Step 1: Add failing tests for full source-index schema and procedure**

Add these methods inside `SkillTextRulesTests`:

```python
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
```

- [ ] **Step 2: Run the new source-index tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_source_index_agent_requires_evidence_backed_entries tests.test_init_workspace.SkillTextRulesTests.test_source_index_format_contains_all_baseline_sections
```

Expected: `FAILED` with missing English section/field phrases.

- [ ] **Step 3: Replace `agents/source-indexer.md`**

Use this complete file content:

```markdown
# Source Indexer Agent

Use this specialist when source reading is the bottleneck: long chapters, multi-chapter continuity, confusing aliases, likely typos, suspected same people, recurring locations, or source facts that later agents must cite.

## 保真契约

- 原作多少字就保留多少字
- 不得用 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用
- 不主动添加站起、起身、跪下、走动、抬手、收起法器。道具动作必须有原文依据。

## Inputs

- Requested source scope only.
- Existing `source-index.md` when present.
- Existing asset files or user-provided image references when they affect identity.

## Output

Create or update `生产资产/source-index.md` unless the user explicitly asks for a visible root-level working index. Use `references/source-index-format.md`.

Do not output a video feed. Do not output a synopsis replacement. Do not summarize chapters as a replacement for source coverage. Use evidence anchors for every merge, correction, relationship claim, reveal handling, face reference, scene reference, reusable asset decision, outfit/state change, and unresolved doubt.

Scope mode policy: 正式多章任务必须先预扫完整请求范围. 局部烟测必须显式标记已阅读范围. 局部烟测资产不得当作全局定稿.

## Procedure

1. Mark `索引状态`, `请求范围`, `已阅读范围`, `未阅读范围`, and evidence basis before any character or asset decision.
2. For formal multi-chapter work must pre-scan the whole requested scope before deciding identity, recurrence, scene reuse, or final asset value.
3. For smoke tests, label `局部烟测`, list exact read span and unread span, and write `Do not promote smoke-test assets to global final decisions.`
4. Record characters, aliases, factions, speaking roles, first/later appearances, relationships, posture facts, outfit/state changes, and asset binding candidates.
5. Track anonymous-to-named upgrade cases: early `弟子/NPC/黑衣人/侍女/守卫/路人` becomes one stable role if later named, recurring, speaking, or plot-bearing.
6. Record scene mother locations and sub-locations, keeping interior/exterior, material logic, lighting logic, and parent-child scene relationships separate.
7. Record props, interfaces, beasts, vehicles, voice roles, sects, realms, techniques, systems, titles, and suspicious spelling drift.
8. Keep uncertain merges as `suspected same asset`; do not merge or assert confirmation without source evidence.
9. Every merge, correction, relationship claim, reveal handling, face reference, scene reference, or reusable asset decision must cite an evidence anchor.
10. Keep the index compact enough to consult while writing feed lines.
```

- [ ] **Step 4: Replace `references/source-index-format.md`**

Use this complete file content:

````markdown
# Source Index Format

Use this file when creating or updating `source-index.md`.

```text
# Source Index

## Scope Status
- Index status: 全范围预扫 / 局部烟测
- Requested range:
- Read range:
- Unread range:
- Evidence basis:
- Scope statement: 正式多章任务必须先预扫完整请求范围；局部烟测必须显式标记已阅读范围；局部烟测资产不得当作全局定稿。
- Smoke-test warning: Do not promote smoke-test assets to global final decisions.

## Character Index
- Name:
  - Aliases/titles:
  - First appearance:
  - Later appearances:
  - Identity/faction:
  - Relationships:
  - Speaking range:
  - Posture facts:
  - Outfit/state changes:
  - Anonymous-to-named upgrade:
  - Suspected same asset:
  - Asset binding:
  - Evidence anchors:

## Scene Index
- Scene name:
  - Interior/exterior:
  - Parent scene:
  - Sub-locations:
  - Material/light/space logic:
  - Chapter/line positions:
  - Asset binding:
  - Evidence anchors:

## Asset Index
- Asset name:
  - Type: character / scene / prop / interface / beast / vehicle / voice
  - Source basis:
  - Reuse range:
  - Parent reference:
  - Collision/separation reference:
  - Evidence anchors:

## Term Index
- Term:
  - Type: sect / realm / technique / system / prop / title / other
  - Source spelling:
  - Possible spelling drift:
  - Current handling:
  - Evidence anchors:

## Doubt Index
- Doubt:
  - Possible explanations:
  - Current handling:
  - Not safe to confirm:
  - Evidence anchors:

## Evidence Anchors
- Anchor id:
  - Source position:
  - Short source excerpt:
  - Supports:
```

Keep entries short. Do not use the index as a synopsis replacement. Every merge, correction, relationship claim, reveal handling, face reference, scene reference, or reusable asset decision needs evidence.
````

- [ ] **Step 5: Run the source-index tests**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_source_index_agent_requires_evidence_backed_entries tests.test_init_workspace.SkillTextRulesTests.test_source_index_format_contains_all_baseline_sections
```

Expected: `OK`.

- [ ] **Step 6: Run the full suite**

Run:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```powershell
git add agents/source-indexer.md references/source-index-format.md tests/test_init_workspace.py
git commit -m "feat: deepen source index baseline"
```

## Task 3: Asset Bible Baseline Depth

**Files:**
- Modify: `tests/test_init_workspace.py`
- Modify: `agents/asset-bible.md`
- Modify: `references/asset-bible-format.md`

- [ ] **Step 1: Add failing tests for asset-bible requirements**

Add these methods inside `SkillTextRulesTests`:

```python
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
```

- [ ] **Step 2: Run the new asset-bible tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_asset_bible_agent_requires_full_scope_or_slice_labels tests.test_init_workspace.SkillTextRulesTests.test_asset_bible_format_tracks_references_and_dependencies
```

Expected: `FAILED` with missing phrases.

- [ ] **Step 3: Replace `agents/asset-bible.md`**

Use this complete file content:

```markdown
# Asset Bible Agent

Use this specialist when reusable assets need to be planned before image or video production: character tri-views, outfit variants, scene mother images, sub-scenes, props, interfaces, beasts, vehicles, voice assets, and reference-upload dependencies.

## 保真契约

- 原作多少字就保留多少字
- 不得用 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用
- 不主动添加站起、起身、跪下、走动、抬手、收起法器。道具动作必须有原文依据。

## Inputs

- Source text or `source-index.md`.
- Existing generated images, filenames, or user-provided references.
- Requested production scope.

## Output

Create `生产资产/asset-bible.md` or a compact `## 资产提示词` plan using `references/asset-bible-format.md`.

Scope mode policy: 正式多章任务必须先预扫完整请求范围. 局部烟测必须显式标记已阅读范围. 局部烟测资产不得当作全局定稿.

## Procedure

1. Confirm the source index is `全范围预扫`; final asset decisions require `全范围预扫` for formal multi-chapter work.
2. If the index is `局部烟测`, label every asset as slice-limited and do not present it as a global final asset decision.
3. Reuse existing assets first; only add assets that stabilize identity, setting, conflict, action, interface, or repeated continuity.
4. Classify people as `主角/高频配角`, `命名低频角色`, `群像模板`, or `一次性背景人`.
5. Main and high-frequency characters need tri-view assets; one-off background people stay in video-line description unless later evidence upgrades them.
6. Upgrade early anonymous roles when later text gives them names, dialogue, recurrence, relationship, faction, or plot function.
7. Name assets by reusable source identity and version, not by temporary camera position, seat, or shot action.
8. For derived outfit/state assets, require previous face/identity references and state what changes versus what must remain stable.
9. Separate similar important characters when they share same sect, same uniform, same gender/age band, or similar protagonist styling. Write contrast anchors for face shape, eyes/brows, nose, mouth, jaw, hair silhouette, build, temperament, and identity marks.
10. Bind parent-child references: character outfit variants to prior face references, sub-scenes to scene mother images, props/interfaces to owner or parent scene when useful.
11. Create prop/interface/beast/vehicle assets only when they carry identity, action, interface, or repeated continuity.
12. Create voice assets for speaking roles in the requested scope.
13. List upload reference purposes with exact labels such as `人脸身份参考`, `旧造型参考`, `避撞脸参考`, `同门服制参考`, `场景母图参考`, `局部场景参考`, `材质风格参考`, and `界面风格参考`.
```

- [ ] **Step 4: Replace `references/asset-bible-format.md`**

Use this complete file content:

````markdown
# Asset Bible Format

Use this file when creating `asset-bible.md` or a compact asset plan.

```text
# Asset Bible

## Scope Status
- Asset status: 全范围预扫定稿 / 局部烟测资产
- Requested range:
- Source-index basis:
- Slice warning: 局部烟测资产不得当作全局定稿。

## Character Assets
- Asset name:
  - Tier: 主角/高频配角 / 命名低频角色 / 群像模板 / 一次性背景人
  - Source evidence:
  - Outfit/state version:
  - Tri-view requirement:
  - Derived from previous asset:
  - Face/identity constants:
  - Similar-character separation anchors:
  - Reference uploads:
    - 人脸身份参考:
    - 旧造型参考:
    - 避撞脸参考:
    - 同门服制参考:
  - Evidence anchors:

## Scene Assets
- Asset name:
  - Type: mother image / sub-location / interior / exterior
  - Source evidence:
  - Parent scene:
  - Sub-locations:
  - Material/light/space constants:
  - Reference uploads:
    - 场景母图参考:
    - 局部场景参考:
    - 材质风格参考:
  - Evidence anchors:

## Prop, Interface, Beast, Vehicle Assets
- Asset name:
  - Type: prop / interface / magic item / beast / vehicle
  - Source evidence:
  - Single-subject image requirement:
  - Parent character/scene reference:
  - Interface orientation:
  - Reference uploads:
    - 人脸身份参考:
    - 场景母图参考:
    - 界面风格参考:
    - 材质风格参考:
  - Evidence anchors:

## Voice Assets
- Character name:
  - Speaking range:
  - Voice direction:
  - Source evidence:

## Production Dependencies
- Generate first:
- Generate after references exist:
- Reusable across line ranges:
- Waiting for user confirmation:
```

Only create assets that improve identity, setting, conflict, action, interface, or continuity. Use video lines for temporary posture or blocking.
````

- [ ] **Step 5: Run the asset-bible tests**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_asset_bible_agent_requires_full_scope_or_slice_labels tests.test_init_workspace.SkillTextRulesTests.test_asset_bible_format_tracks_references_and_dependencies
```

Expected: `OK`.

- [ ] **Step 6: Run the full suite**

Run:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```powershell
git add agents/asset-bible.md references/asset-bible-format.md tests/test_init_workspace.py
git commit -m "feat: deepen asset bible baseline"
```

## Task 4: Faithful Feed Preconditions and Coverage

**Files:**
- Modify: `tests/test_init_workspace.py`
- Modify: `agents/faithful-feed.md`
- Modify: `references/format.md`

- [ ] **Step 1: Add failing tests for feed prerequisites and coverage**

Add these methods inside `SkillTextRulesTests`:

```python
    def test_faithful_feed_requires_index_assets_and_coverage_audit(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_text = root.joinpath("agents", "faithful-feed.md").read_text(
            encoding="utf-8"
        )

        required_phrases = [
            "formal multi-chapter output requires either a `全范围预扫` source index or an explicit full requested-scope pre-scan",
            "private chapter beat ledger",
            "coverage audit before delivery",
            "asset-bible",
            "source-index",
            "do not reduce coverage by reducing line count",
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
            "one Xiaoyunque camera tag",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, format_text)
```

- [ ] **Step 2: Run the new feed tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_faithful_feed_requires_index_assets_and_coverage_audit tests.test_init_workspace.SkillTextRulesTests.test_format_reference_declares_only_two_output_blocks
```

Expected: `FAILED` with missing phrases.

- [ ] **Step 3: Patch `agents/faithful-feed.md`**

Keep the existing file structure. In the `## Output` section, replace the paragraph after the two-block example with:

```markdown
Start the video block with the exact global `统一要求` line from `references/format.md`, then number from `1` to the end. Do not create `第N组`, 15-second blocks, `segment`, `S01/S02`, keyframes, first/last-frame instructions, Canvas packages, storyboard folders, or MP4 claims.

The feed depends on `source-index` and `asset-bible` decisions when the requested scope is long or multi-chapter. Formal multi-chapter output requires either a `全范围预扫` source index or an explicit full requested-scope pre-scan before drafting.
```

In the `## Procedure` list, replace the current list with:

```markdown
1. For formal multi-chapter output, require a `全范围预扫` source index or perform the full requested pre-scan before drafting.
2. For slice experiments, label the output as `局部烟测` and state the exact read span before any reusable assets.
3. Check `source-index` for names, aliases, event order, scene hierarchy, posture facts, and unresolved doubts.
4. Check `asset-bible` for stable asset names, existing references, outfit variants, scene mother images, and voice roles.
5. Make a private chapter beat ledger before drafting: opening state, key conflict, source dialogue anchor, action turn, result, and hook.
6. Use one visible action target, one main beat, and one Xiaoyunque camera tag per numbered line.
7. Keep speaker-focused dialogue shots, usually front half-body or medium shots with spatial context.
8. Preserve long dialogue in adjacent continuous lines when needed; never shorten it to reduce line count.
9. Do not reduce coverage by reducing line count. Missing setup, reaction, result, or hook must be restored as source-faithful continuous lines.
10. Run a coverage audit before delivery for multi-chapter work.
```

- [ ] **Step 4: Patch `references/format.md` near `## Package shape`**

Immediately under `## Package shape`, add:

```markdown
Emit only these two user-facing blocks:

- `## 资产提示词`
- `## 视频投喂块`

Each numbered video line should carry one visible action target, one main beat, and one Xiaoyunque camera tag.
```

- [ ] **Step 5: Run the feed tests**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_faithful_feed_requires_index_assets_and_coverage_audit tests.test_init_workspace.SkillTextRulesTests.test_format_reference_declares_only_two_output_blocks
```

Expected: `OK`.

- [ ] **Step 6: Run the full suite**

Run:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```powershell
git add agents/faithful-feed.md references/format.md tests/test_init_workspace.py
git commit -m "feat: require faithful feed coverage gates"
```

## Task 5: Auditor and Deterministic Validator Depth

**Files:**
- Modify: `tests/test_init_workspace.py`
- Modify: `agents/feed-auditor.md`
- Modify: `references/audit-checklist.md`
- Modify: `scripts/validate_feed.py`

- [ ] **Step 1: Add failing auditor text tests**

Add this method inside `SkillTextRulesTests`:

```python
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
            self.assertIn("scope status is explicit when the artifact is a smoke test", text)
```

- [ ] **Step 2: Add failing validator behavior tests**

Add this method inside `SkillTextRulesTests`:

```python
    def test_validate_feed_rejects_duplicate_camera_tags_and_storyboard_terms(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_feed = Path(temp_dir) / "bad-feed.md"
            bad_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白。3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。】",
                        "1 日 内 大殿 林夜 坐在王座上 中景 + 平视 固定镜头 镜头前推 环境音：低鸣",
                        "2 日 内 大殿 林夜 坐在王座上 中景 + 平视 固定镜头 storyboard folder 环境音：低鸣",
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
            self.assertIn("invalid camera tag count 2", result.stdout)
            self.assertIn("forbidden term `storyboard`", result.stdout)
```

- [ ] **Step 3: Run the new auditor and validator tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_feed_auditor_splits_script_checks_from_source_fidelity_review tests.test_init_workspace.SkillTextRulesTests.test_validate_feed_rejects_duplicate_camera_tags_and_storyboard_terms
```

Expected: `FAILED`. The text test should miss phrases, and the validator test should miss `storyboard`.

- [ ] **Step 4: Replace `agents/feed-auditor.md`**

Use this complete file content:

```markdown
# Feed Auditor Agent

Use this specialist before delivery, after edits, or when the user asks whether a feed obeys the source-true-guoman rules.

## 保真契约

- 原作多少字就保留多少字
- 不得用 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用
- 不主动添加站起、起身、跪下、走动、抬手、收起法器。道具动作必须有原文依据。

## Required References

- Read `references/audit-checklist.md`.
- Read `references/xiaoyunque-tags.md` when checking camera tags.

## Output

Blocking issues first. Include file/line references when a feed file is available. If no issues are found, state remaining risk, such as source text not provided or dialogue exactness not verifiable.

## Procedure

1. Run script-deterministic checks with `python scripts/validate_feed.py <feed-file>` when reviewing a saved feed.
2. Check forbidden structures: groups, fixed 15-second pacing, `segment`, `S01/S02`, keyframe language, Canvas/MP4 claims, storyboard folders, and first/last-frame workflow language.
3. Check continuous numbering and the exact global requirement line.
4. Check Xiaoyunque raw tags.
5. Run human/agent source-fidelity checks when source is available: dialogue exactness, dialogue order, event order, cause-effect, reveal handling, and unsourced blocking.
6. Check asset continuity: stable names, no disposable later-named NPCs, no unbound outfit face changes, similar-character separation anchors, and no scene parent drift.
7. Check that scope status is explicit when the artifact is a smoke test.
8. If source text is unavailable, mark source-fidelity checks as unverified rather than passing.
```

- [ ] **Step 5: Replace `references/audit-checklist.md`**

Use this complete file content:

```markdown
# Feed Audit Checklist

Use this checklist when reviewing a source-true-guoman feed.

## Output Style

- Blocking issues first.
- Cite file/line references when reviewing saved files.
- Separate script-deterministic checks from human/agent source-fidelity checks.
- If source text is unavailable, mark dialogue and plot exactness as unverified rather than claiming they pass.

## Script-Deterministic Checks

- The feed starts `## 视频投喂块` with the exact global `统一要求` line.
- Numbering starts at `1` and stays continuous.
- No `第N组`, `第N-N条`, 15-second groups, group footers, or pacing blocks.
- No `segment`, `S01/S02`, `keyframe`, `首帧`, `尾帧`, `续接`, `承接`, Canvas package, storyboard folder, or MP4 claim.
- Each video line uses exactly one Xiaoyunque raw tag, optionally followed by parentheses.
- Scope status is explicit when the artifact is a smoke test.

## Human/Agent Source-Fidelity Checks

- Dialogue is exact source text when source is available.
- Dialogue stays in source order and local context.
- Long dialogue is split only at natural source punctuation, not shortened.
- Events preserve cause-effect, reveal order, and chapter hooks.
- No unsourced standing, walking, kneeling, bowing, weapon drawing, prop raising, prop putting away, seat changes, reporting, or attacks.

## Asset Checks

- Asset names are stable source identities and versions.
- Later-named recurring NPCs are not split from earlier anonymous appearances.
- Outfit variants preserve face identity references.
- Similar important characters have separation anchors.
- Sub-scenes bind to scene mother images when continuity depends on it.
- Voice assets exist for speaking roles that need production.
```

- [ ] **Step 6: Extend deterministic forbidden terms in `scripts/validate_feed.py`**

Change `FORBIDDEN_TERMS` to include storyboard-folder language:

```python
FORBIDDEN_TERMS = (
    "segment",
    "S01",
    "S02",
    "keyframe",
    "棣栧抚",
    "灏惧抚",
    "首帧",
    "尾帧",
    "缁帴",
    "鎵挎帴",
    "续接",
    "承接",
    "Canvas",
    "MP4",
    "storyboard",
    "Storyboard",
)
```

Do not add checks that require understanding the source story.

- [ ] **Step 7: Run the auditor and validator tests**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_feed_auditor_splits_script_checks_from_source_fidelity_review tests.test_init_workspace.SkillTextRulesTests.test_validate_feed_rejects_duplicate_camera_tags_and_storyboard_terms
```

Expected: `OK`.

- [ ] **Step 8: Run the full suite**

Run:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Expected: all tests pass.

- [ ] **Step 9: Commit**

```powershell
git add agents/feed-auditor.md references/audit-checklist.md scripts/validate_feed.py tests/test_init_workspace.py
git commit -m "feat: deepen feed audit checks"
```

## Task 6: Guard Optional Agents Without Expanding Scope

**Files:**
- Modify: `tests/test_init_workspace.py`
- Modify: `agents/cut-safety.md`
- Modify: `references/cut-safety-rules.md`
- Modify: `agents/visual-polish.md`
- Modify: `agents/production-runner.md`

- [ ] **Step 1: Add failing tests for optional agent boundaries**

Add these methods inside `SkillTextRulesTests`:

```python
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
        self.assertIn("must not remove, shorten, reorder, or rewrite source dialogue", visual_text)
        self.assertIn("dependency checklist", runner_text)
        self.assertIn("no Canvas package", runner_text)
        self.assertIn("no storyboard folder", runner_text)
        self.assertIn("no MP4 claim", runner_text)
```

- [ ] **Step 2: Run the optional-agent tests and verify they fail**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_cut_safety_outputs_risk_notes_not_rewritten_compression tests.test_init_workspace.SkillTextRulesTests.test_visual_polish_and_production_runner_keep_existing_boundaries
```

Expected: `FAILED` with missing phrases.

- [ ] **Step 3: Patch `agents/cut-safety.md`**

Replace the `## Output` and `## Procedure` sections with:

```markdown
## Output

Return cut-risk notes, not a rewritten compressed story. Use `references/cut-safety-rules.md`.

## Procedure

1. Identify each proposed deletion by exact feed line numbers and, when available, exact source spans.
2. Mark each span as low, medium, or high risk.
3. Explain concrete breakage: lost setup, lost cause, dangling reaction, broken reveal, lost identity evidence, broken asset continuity, missing payoff, or missing hook.
4. Suggest safer line boundaries when possible.
5. Leave final deletion choices to the user.
6. Do not write a replacement compressed feed or rewritten story.
```

- [ ] **Step 4: Replace `references/cut-safety-rules.md`**

Use this complete file content:

````markdown
# Cut Safety Rules

Use this reference only when the user asks about manual deletion, trimming, or compression risk.

## Output Boundary

- Return risk notes, not a rewritten compressed story.
- Identify deletions by exact feed line numbers.
- Add exact source spans when source text or source-index anchors are available.
- Leave final deletion choices to the user.

## Risk Levels

- Low risk: repeated visual pause, redundant ambient-only beat, or removable reaction that does not carry setup, result, reveal, dialogue, identity, or asset continuity.
- Medium risk: useful but non-load-bearing reaction, mood extension, or secondary beat whose removal may reduce clarity.
- High risk: lost setup, lost cause, dangling reaction, broken reveal, lost identity evidence, broken relationship evidence, broken asset continuity, missing payoff, or missing hook.

## Required Note Shape

```text
- Lines/source span:
  - Risk:
  - Why:
  - Safer boundary:
```

Do not produce a rewritten short version.
````

- [ ] **Step 5: Patch `agents/visual-polish.md`**

In the first paragraph, replace it with:

```markdown
Use this specialist after a faithful feed exists and the user wants stronger shot variety, clearer spatial depth, or better 3D国漫/light-comedy performance without changing source content. This requires an existing faithful feed.
```

In `## Procedure`, add this as step 1 and renumber the existing list:

```markdown
1. Confirm a faithful feed already exists; visual polish must not create first-pass story coverage.
2. Keep every original event and exact dialogue intact.
3. Improve only visible framing, scene depth, lighting, ambient/action audio, legal micro-performance, and Xiaoyunque tag choice.
4. Do not remove, shorten, reorder, or rewrite source dialogue.
5. Avoid making dialogue a row of isolated faces; retain speaker posture, seat/scene context, and nearby reactions.
6. Do not upgrade micro-performance into new body movement or prop handling.
7. Prefer compact shot concepts over long film-school explanations.
```

- [ ] **Step 6: Patch `agents/production-runner.md`**

Replace the `## Output` paragraph with:

```markdown
Return a dependency checklist grouped by production dependency, not by arbitrary 15-second pacing. This agent creates no Canvas package, no storyboard folder, and no MP4 claim.
```

- [ ] **Step 7: Run the optional-agent tests**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_cut_safety_outputs_risk_notes_not_rewritten_compression tests.test_init_workspace.SkillTextRulesTests.test_visual_polish_and_production_runner_keep_existing_boundaries
```

Expected: `OK`.

- [ ] **Step 8: Run the full suite**

Run:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Expected: all tests pass.

- [ ] **Step 9: Commit**

```powershell
git add agents/cut-safety.md references/cut-safety-rules.md agents/visual-polish.md agents/production-runner.md tests/test_init_workspace.py
git commit -m "feat: guard optional production agents"
```

## Task 7: Skill Validation and Regression Sample Notes

**Files:**
- Modify: `tests/test_init_workspace.py`
- Modify: `SKILL.md`
- Optionally modify: `agents/openai.yaml`

- [ ] **Step 1: Add final regression contract tests**

Add this method inside `SkillTextRulesTests`:

```python
    def test_skill_baseline_mentions_xianjie_only_as_regression_sample(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Use `E:\\\\xianjie` only as a regression sample unless the user explicitly asks to produce its chapters", skill_text)
        self.assertIn("do not generate the full five-chapter feed as part of baseline implementation", skill_text)
```

- [ ] **Step 2: Run the new regression test and verify it fails**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_skill_baseline_mentions_xianjie_only_as_regression_sample
```

Expected: `FAILED` with missing phrases.

- [ ] **Step 3: Add regression-sample note to `SKILL.md`**

Add this paragraph after the default first-phase route paragraph in `## Agent pack routing`:

```markdown
Use `E:\xianjie` only as a regression sample unless the user explicitly asks to produce its chapters. Do not generate the full five-chapter feed as part of baseline implementation; use it after implementation to check that formal multi-chapter work pre-scans the requested scope before final assets or feed output.
```

- [ ] **Step 4: Check whether `agents/openai.yaml` needs an update**

Run:

```powershell
Get-Content -Raw agents\openai.yaml
```

Expected: current `display_name`, `short_description`, and `default_prompt` still describe the skill. If unchanged meaning is acceptable, do not modify the file.

- [ ] **Step 5: Run the final regression test**

Run:

```powershell
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_skill_baseline_mentions_xianjie_only_as_regression_sample
```

Expected: `OK`.

- [ ] **Step 6: Run all unit tests**

Run:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Expected: all tests pass.

- [ ] **Step 7: Run skill validation with UTF-8**

Run:

```powershell
$env:PYTHONUTF8='1'; python C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py E:\source-true-guoman
```

Expected:

```text
Skill is valid!
```

- [ ] **Step 8: Commit**

```powershell
git add SKILL.md tests/test_init_workspace.py
git commit -m "docs: document baseline regression boundary"
```

## Task 8: Final Verification

**Files:**
- No planned edits.

- [ ] **Step 1: Inspect git status**

Run:

```powershell
git status --short --branch
```

Expected: branch is ahead by the implementation commits and has no unexpected unstaged tracked changes.

- [ ] **Step 2: Run all tests one final time**

Run:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

Expected: all tests pass.

- [ ] **Step 3: Run skill validation one final time**

Run:

```powershell
$env:PYTHONUTF8='1'; python C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py E:\source-true-guoman
```

Expected:

```text
Skill is valid!
```

- [ ] **Step 4: Review changed files**

Run:

```powershell
git diff --stat origin/feat/agent-pack-prototype...HEAD
```

Expected: changes are limited to the skill, agents, references, validator, tests, spec/plan docs, and any intentional commits on this feature branch.

- [ ] **Step 5: Prepare completion summary**

Summarize:

```text
- Implemented baseline route: source-indexer -> asset-bible -> faithful-feed -> feed-auditor.
- Strengthened formal-vs-smoke scope policy and production-asset storage policy.
- Deepened source-index and asset-bible formats with evidence and dependency anchors.
- Expanded deterministic feed validation only for structure/tag/forbidden-term checks.
- Kept cut-safety as deletion-risk analysis, not compression generation.
- Verification: unit tests passed; skill quick validation passed.
```

Do not claim that `E:\xianjie` five chapters were fully produced unless the user explicitly requested that work and it was actually done.
