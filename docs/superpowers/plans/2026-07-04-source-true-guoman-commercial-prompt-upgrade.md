# Source True Guoman Commercial Prompt Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the `source-true-guoman` agent pack with commercial-prompt mechanics for identity, period/state, asset continuity, feed alignment, safe physicalization, and audit hygiene while preserving the skill's source-faithful contract.

**Architecture:** Keep `SKILL.md` as a lean orchestrator and deepen behavior through specialist agent files plus one-level reference files. Use textual contract tests in `tests/test_init_workspace.py` to lock routing, required phrases, prompt hygiene, and validation boundaries.

**Tech Stack:** Markdown skill files, Python `unittest`, `scripts/validate_feed.py`, and `skill-creator/scripts/quick_validate.py`.

---

## File Structure

- Create: `references/identity-period-rules.md`  
  Canonical-name, alias, generic-role upgrade, period/state trigger, evidence, and smoke-test limitation rules for `source-indexer`.
- Create: `references/asset-continuity-rules.md`  
  Asset variant matrix, reference purpose labels, prop/interface double gate, scene mother/sub-scene dependencies, and voice triggers for `asset-bible`.
- Create: `references/feed-alignment-rules.md`  
  Source-span planning, coverage ledger, local continuity, dialogue alignment, and fixed-timeline exclusion rules for `faithful-feed`.
- Create: `references/source-safe-physicalization.md`  
  Safe facial, breath, cloth, hair, environmental, and ambient performance examples for `visual-polish`.
- Create: `references/commercial-upgrade-audit.md`  
  Commercial-upgrade audit checklist for identity drift, period/state drift, source-span coverage, continuity, physicalization safety, and copied-prompt hygiene.
- Modify: `agents/source-indexer.md`  
  Route to `identity-period-rules.md` and require canonical source names, alias evidence, standard-name basis, period/state variants, and evidence anchors.
- Modify: `agents/asset-bible.md`  
  Route to `asset-continuity-rules.md` and require the prop/interface double gate, derived variants, parent references, similar-character separation, and voice triggers.
- Modify: `agents/faithful-feed.md`  
  Route to `feed-alignment-rules.md` and require source-span planning plus line-to-line continuity before drafting.
- Modify: `agents/visual-polish.md`  
  Route to `source-safe-physicalization.md` and require source-safe physicalization without motion escalation.
- Modify: `agents/feed-auditor.md`  
  Route to `commercial-upgrade-audit.md` and add the commercial-upgrade review pass.
- Modify: `references/source-index-format.md`  
  Add standard-name and period/state fields to the source-index template.
- Modify: `references/asset-bible-format.md`  
  Add value/dependency gates, variant types, and parent-reference purposes to the asset-bible template.
- Modify: `references/audit-checklist.md`  
  Add commercial-upgrade checklist items without turning deterministic scripts into story-understanding checks.
- Modify: `references/format.md`  
  Add a compact note pointing feed writers to source-span alignment and source-safe physicalization where relevant.
- Modify: `tests/test_init_workspace.py`  
  Add focused text-contract tests, following the existing `SkillTextRulesTests` style.
- Review only: `SKILL.md`  
  Confirm it remains a lean orchestrator and does not absorb the new commercial-prompt rule detail.
- Review only: `agents/openai.yaml`  
  Confirm metadata still matches the skill. No change is expected unless descriptions become stale.

---

### Task 1: Identity And Period Rules

**Files:**
- Create: `references/identity-period-rules.md`
- Modify: `agents/source-indexer.md`
- Modify: `references/source-index-format.md`
- Test: `tests/test_init_workspace.py`

- [ ] **Step 1: Write the failing test**

Append this method inside `SkillTextRulesTests` in `tests/test_init_workspace.py`, before `if __name__ == "__main__":`.

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_commercial_upgrade_identity_period_reference_is_routed
```

Expected: `FAILED (failures=1)` with `AssertionError: False is not true` because `references/identity-period-rules.md` does not exist yet.

- [ ] **Step 3: Create the identity/period reference**

Create `references/identity-period-rules.md` with this content:

```markdown
# Identity And Period Rules

Use this file when `source-indexer` needs stronger identity, alias, role-tier, or period/state discipline.

## Canonical Names

- Canonical name is an evidence-backed source identity, not the prettiest alias.
- Prefer the most stable source name once the source has confirmed it.
- Keep aliases, titles, kinship names, first-person labels, and generic labels as evidence.
- Aliases are evidence, not production names, unless the source dialogue itself uses the alias.
- Record a `standard-name basis` for every reusable identity.

## Alias Mapping

- Map titles, kinship references, faction labels, and temporary labels to the canonical source name when evidence supports the merge.
- Keep uncertain mappings as suspected until source evidence confirms them.
- Do not collapse two similar roles only because they share sect, age, uniform, gender, or scene position.

## Generic-Role Upgrade

- Generic-role upgrade applies when `弟子`, `NPC`, `黑衣人`, `侍女`, `守卫`, `路人`, or another generic label later gains a name, dialogue, recurrence, relationship, faction function, or plot effect.
- Bind early generic mentions to the later confirmed source identity once the evidence is strong.
- Do not create a disposable face for the generic mention and a separate face for the later named role.

## Period/State Trigger

- Period/state trigger means the source gives a stable change in age stage, identity/status, outfit, injury, battle state, disguise, transformation, location, or public role.
- Name variants with short source-grounded terms such as `黑袍时期`, `宗门礼服时期`, `重伤状态`, or `伪装状态`.
- Do not split tiny one-line gestures, temporary camera posture, seat position, or mood into permanent periods.
- A period/state variant must cite the source span that starts it and the span that resolves or changes it when known.

## Evidence Anchors

- Every canonical-name merge, alias mapping, period/state variant, role-tier decision, and suspected merge needs an evidence anchor.
- Evidence anchors use chapter, scene, line number, or a short source excerpt.
- Evidence must support the exact claim; do not use a distant theme or genre expectation as proof.

## Smoke-Test Limitation

- Smoke-test limitation is mandatory for partial reads.
- Period/state decisions are slice-limited when the requested source scope has not been fully pre-scanned.
- Mark `局部烟测` artifacts with exact read range and unread range.
- Do not promote smoke-test identity, alias, or period/state decisions to global-final decisions.
```

- [ ] **Step 4: Route the reference from `source-indexer`**

Modify `agents/source-indexer.md`:

```markdown
## Required References

- Read `references/source-index-format.md` before writing or updating `生产资产/source-index.md`.
- Read `references/identity-period-rules.md` when the task has aliases, titles, generic roles, repeated roles, confusing names, or outfit/state changes.
```

Add this sentence to the `Output` section:

```markdown
Record the canonical source name, standard-name basis, alias mapping, period/state trigger, and evidence anchor for every reusable identity or period/state variant; period/state decisions are slice-limited when the index is only `局部烟测`.
```

Add these procedure steps after the existing scope steps:

```markdown
4. Apply `references/identity-period-rules.md` before deciding canonical source name, alias mapping, role tier, or period/state variants.
5. Record `standard-name basis` separately from aliases; aliases prove identity history but do not become production names by default.
6. Record the `period/state trigger` only when the source establishes a stable age, status, outfit, injury, disguise, transformation, or location change.
```

Renumber the remaining procedure steps continuously.

- [ ] **Step 5: Extend the source-index format**

Modify the `## Character Index` block in `references/source-index-format.md` so it includes these fields:

```text
  - Canonical source name:
  - Standard name basis:
  - Alias evidence:
  - Role tier:
  - Period/state variants:
    - Variant name:
    - Period/state trigger:
    - Start evidence:
    - End/change evidence:
  - Slice limitation:
```

Keep the existing fields for first appearance, later appearances, identity/faction, relationships, posture facts, asset binding, and evidence anchors.

- [ ] **Step 6: Run task test to verify it passes**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_commercial_upgrade_identity_period_reference_is_routed
```

Expected: `Ran 1 test` and `OK`.

- [ ] **Step 7: Commit**

```bash
git add tests/test_init_workspace.py references/identity-period-rules.md agents/source-indexer.md references/source-index-format.md
git commit -m "feat: add identity period rules"
```

---

### Task 2: Asset Continuity Rules

**Files:**
- Create: `references/asset-continuity-rules.md`
- Modify: `agents/asset-bible.md`
- Modify: `references/asset-bible-format.md`
- Test: `tests/test_init_workspace.py`

- [ ] **Step 1: Write the failing test**

Append this method inside `SkillTextRulesTests`.

```python
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
            "Value gate:",
            "Dependency gate:",
            "Variant type:",
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_commercial_upgrade_asset_continuity_reference_is_routed
```

Expected: `FAILED (failures=1)` with `AssertionError: False is not true` because `references/asset-continuity-rules.md` does not exist yet.

- [ ] **Step 3: Create the asset-continuity reference**

Create `references/asset-continuity-rules.md` with this content:

```markdown
# Asset Continuity Rules

Use this file when `asset-bible` plans reusable assets, derived variants, parent references, prop/interface assets, or voice assets.

## Character Variant Matrix

- Character variant matrix records one canonical source identity across source-supported visual versions.
- Variant types: base outfit, new outfit, injury state, battle state, disguise, transformed state, age-stage change, public-status change.
- A derived variant must keep face, age band, facial structure, hairstyle logic, body type, and identity marks unless the source explicitly changes them.
- Every derived variant needs a face/identity reference or an explicit note that no previous image exists.
- Do not create a new face because the character moves scenes, sits elsewhere, changes camera angle, or receives a temporary expression.

## Similar-Character Separation

- Similar-character separation is required when important roles share sect, uniform, profession, age band, gender, black/white/blue robe styling, or protagonist-like design language.
- Separate face shape, brows/eyes, nose bridge, mouth, jawline, hairstyle silhouette, height/build, posture, temperament, and identity marks.
- Shared costume systems can remain shared; faces and silhouettes must not collapse.

## Prop/Interface Double Gate

- Prop/interface double gate means an asset is created only when both value and dependency are true.
- Value gate: the object has repeated, symbolic, identity, interface, conflict, action, or plot-continuity value in the requested scope.
- Dependency gate: the current feed lines or upcoming production dependency need a stable reference image.
- Incidental furniture, candles, bowls, generic tables, generic weapons, and one-off background objects stay in video lines unless the source makes them load-bearing.

## Scene Mother And Sub-Scene Dependencies

- Scene mother and sub-scene dependencies keep local spaces visually connected.
- A room, gate, corridor, altar, stall, interface close-up, or detail corner inside a known location uses the parent scene as scene mother reference when architecture, material, light, palette, or faction identity matters.
- Do not reuse an exterior scene for an interior shot.
- Do not invent a disconnected local set when a parent scene already defines the world identity.

## Reference Purpose Labels

- Reference purpose labels make upload intent explicit.
- Use `人脸身份参考`, `旧造型参考`, `避撞脸参考`, `同门服制参考`, `场景母图参考`, `局部场景参考`, `材质风格参考`, and `界面风格参考`.
- Parent reference purpose must name what is inherited and what must change.

## Voice Asset Trigger

- Voice asset trigger applies only to speaking roles in the requested scope.
- Do not create voice assets for silent background people.
- Reuse prior voice direction when the same speaking role appears across distant spans.
```

- [ ] **Step 4: Route the reference from `asset-bible`**

Modify `agents/asset-bible.md`:

```markdown
## Required References

- Read `references/asset-bible-format.md` before writing `生产资产/asset-bible.md` or a compact `## 资产提示词` plan.
- Read `references/asset-continuity-rules.md` before deciding character variants, parent references, prop/interface assets, scene sub-locations, or voice assets.
```

Add these procedure steps after the existing source-index status step:

```markdown
2. Apply the character variant matrix before writing any derived variant; every outfit, injury, battle, disguise, transformation, age-stage, or public-status version keeps the same source identity unless evidence says otherwise.
3. Apply the prop/interface double gate: create a prop or interface asset only when both value and dependency are true.
4. Bind every derived variant, sub-scene, prop/interface detail, and similar-character separation to the correct parent reference purpose, including face/identity reference and scene mother reference when needed.
5. Record a voice asset trigger only for speaking roles in the requested scope.
```

Renumber the remaining procedure steps continuously.

- [ ] **Step 5: Extend the asset-bible format**

Modify `references/asset-bible-format.md`.

In `## Character Assets`, add these fields:

```text
  - Canonical source identity:
  - Character variant matrix:
  - Variant type:
  - Parent reference purpose:
  - Face/identity reference:
```

In `## Scene Assets`, add:

```text
  - Scene mother reference:
  - Parent reference purpose:
```

In `## Prop, Interface, Beast, Vehicle Assets`, add:

```text
  - Value gate:
  - Dependency gate:
  - Parent reference purpose:
```

In `## Voice Assets`, add:

```text
  - Voice asset trigger:
```

- [ ] **Step 6: Run task test to verify it passes**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_commercial_upgrade_asset_continuity_reference_is_routed
```

Expected: `Ran 1 test` and `OK`.

- [ ] **Step 7: Commit**

```bash
git add tests/test_init_workspace.py references/asset-continuity-rules.md agents/asset-bible.md references/asset-bible-format.md
git commit -m "feat: add asset continuity rules"
```

---

### Task 3: Feed Alignment And Local Continuity

**Files:**
- Create: `references/feed-alignment-rules.md`
- Modify: `agents/faithful-feed.md`
- Modify: `references/format.md`
- Test: `tests/test_init_workspace.py`

- [ ] **Step 1: Write the failing test**

Append this method inside `SkillTextRulesTests`.

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_commercial_upgrade_feed_alignment_reference_is_routed
```

Expected: `FAILED (failures=1)` with `AssertionError: False is not true` because `references/feed-alignment-rules.md` does not exist yet.

- [ ] **Step 3: Create the feed-alignment reference**

Create `references/feed-alignment-rules.md` with this content:

```markdown
# Feed Alignment Rules

Use this file when `faithful-feed` drafts final continuous video feed lines from a long source scope, multi-chapter span, dense dialogue, or previously indexed production package.

## Source-Span Alignment

- Source-span alignment maps requested source spans to continuous feed line ranges before final drafting.
- It is a planning check, not a rigid one-source-sentence-to-one-video-line requirement.
- Every requested source span needs visible representation unless the user explicitly chose a manual cut range.
- Preserve source order, cause-effect, reveal order, and load-bearing dialogue.

## Private Line/Span Plan

- Private line/span plan records the source span, expected feed line range, key event, exact dialogue/OS/system anchor, visible state, and required asset references.
- Keep the plan private unless the user asks to see the audit trail.
- For long dialogue, split adjacent continuous feed lines only at natural source punctuation.
- Do not shorten dialogue to reduce line count.

## Coverage Ledger

- Coverage ledger checks every requested chapter or scene for setup, conflict, action turn, result, and hook when present.
- A line-count target cannot remove source coverage.
- Add continuous numbered lines when coverage is missing.

## Local Continuity Check

- Local continuity check compares each new line with the previous visible state.
- Track scene, posture, seat, held prop state, outfit/state, injury, speaking role, emotion beat, and active report/combat state.
- A scene, posture, prop, outfit, injury, or action change needs source support or prior-line support.
- Keep unresolved continuity doubts private and choose the less committal visible wording.

## Dialogue Alignment

- Speaker dialogue normally keeps the speaker as the primary subject.
- Use offscreen, overheard, or reaction-only dialogue only when the source supports that staging.
- Keep source dialogue exact and local; do not pull a later reaction into an earlier beat.

## Fixed-Timeline Exclusion

- Do not import fixed-second timelines.
- Do not create fixed-duration groups, fixed line counts per group, per-group pacing footers, or breathing blocks.
- Use continuous numbering and let the user decide pauses, cuts, merges, and splits after receiving the source-faithful draft.
```

- [ ] **Step 4: Route the reference from `faithful-feed`**

Modify `agents/faithful-feed.md`.

Extend `## Required References`:

```markdown
- Read `references/feed-alignment-rules.md` for long scope, multi-chapter work, dense dialogue, source-span alignment, or local continuity checks.
```

Add these procedure steps after checking `source-index` and `asset-bible`:

```markdown
5. Create a private line/span plan for source-span alignment before drafting final numbered lines.
6. Run a local continuity check before each line: compare the new line with the previous visible state, including scene, posture, seat, prop state, outfit/state, injury, speaking role, and emotional beat.
7. Keep the speaker as the primary subject for dialogue unless the source supports offscreen, overheard, or reaction-only staging.
8. Do not import fixed-second timelines, fixed-duration groups, or per-group pacing blocks.
```

Renumber the remaining procedure steps continuously.

- [ ] **Step 5: Add a compact format note**

Modify `references/format.md` after the paragraph beginning `For multi-chapter work`:

```markdown
For long or dense source spans, use source-span alignment and a local continuity check before finalizing numbered lines. Each line must remain compatible with the previous visible state unless the source or prior line supports the change.
```

- [ ] **Step 6: Run task test to verify it passes**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_commercial_upgrade_feed_alignment_reference_is_routed
```

Expected: `Ran 1 test` and `OK`.

- [ ] **Step 7: Commit**

```bash
git add tests/test_init_workspace.py references/feed-alignment-rules.md agents/faithful-feed.md references/format.md
git commit -m "feat: add feed alignment rules"
```

---

### Task 4: Source-Safe Physicalization

**Files:**
- Create: `references/source-safe-physicalization.md`
- Modify: `agents/visual-polish.md`
- Modify: `agents/faithful-feed.md`
- Test: `tests/test_init_workspace.py`

- [ ] **Step 1: Write the failing test**

Append this method inside `SkillTextRulesTests`.

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_commercial_upgrade_physicalization_reference_is_routed
```

Expected: `FAILED (failures=1)` with `AssertionError: False is not true` because `references/source-safe-physicalization.md` does not exist yet.

- [ ] **Step 3: Create the source-safe physicalization reference**

Create `references/source-safe-physicalization.md` with this content:

```markdown
# Source-Safe Physicalization

Use this file when `visual-polish` improves visible performance after faithful coverage already exists.

## Core Rule

- Source-safe physicalization makes abstract emotion visible without changing story facts.
- Main motion requires source support.
- Secondary animation must be consequence of current posture, action, clothing, environment, or camera movement.
- The original event order, exact dialogue, posture, prop state, and scene placement remain unchanged.

## Safe Detail Menu

- Facial micro-performance: eyelids tightening, brows pressing, lip tension, jaw set, throat movement, brief eye pressure, or a short pause before exact source dialogue.
- Breath/cloth/hair/environment: breath fog, robe edge moving with breath, sleeve fabric settling, hair tips shifting in wind, dust drifting, candle flame shaking, cold mist sliding behind a seated speaker.
- Sound detail: robe friction, table edge creak, low hall hum, distant crowd hush, system prompt sound, object resonance already supported by the scene.
- Comedy contrast: a frozen expression, tiny eye twitch, breath catching, or a restrained hand/finger reaction when the source supports the emotional beat and the current posture allows it.

## Unsafe Motion Escalation

- Unsafe motion escalation turns micro-performance into new blocking or action.
- Do not use visual polish to add a new body move, route through space, combat beat, prop operation, or scene exit.
- A polished line must not add standing, walking, kneeling, bowing, weapon drawing, attacks, prop raising, prop putting away, seat changes, or exits.
- If the source only supports sitting and speaking, keep sitting and speaking; use face, breath, cloth, light, sound, or camera instead.

## Examples

Safe:

```text
坐在左侧第二席的老者正面半身开口，眼皮微压，骨纹袖口在冷光里轻轻贴住扶手
```

Unsafe:

```text
老者站起抬手晃动法器
```

The unsafe example invents standing, hand action, and prop handling.
```

- [ ] **Step 4: Route the reference from `visual-polish`**

Modify `agents/visual-polish.md`.

Add:

```markdown
## Required References

- Read `references/source-safe-physicalization.md` before adding physical performance details, secondary animation, comedy contrast, or environmental motion.
```

Replace procedure steps 3-5 with:

```markdown
3. Improve only visible framing, scene depth, lighting, ambient/action audio, source-safe physicalization, legal micro-performance, and Xiaoyunque tag choice.
4. Apply source-safe physicalization: main motion requires source support; secondary animation must be consequence of current posture, current action, clothing, environment, or camera movement.
5. Use facial micro-performance and breath/cloth/hair/environment details to clarify emotion without changing source facts.
6. Reject unsafe motion escalation: must not add standing, walking, kneeling, bowing, weapon drawing, attacks, prop raising, prop putting away, seat changes, or exits.
```

Renumber the remaining procedure steps continuously.

- [ ] **Step 5: Add a feed-agent pointer**

Modify `agents/faithful-feed.md` under `## Required References`:

```markdown
- Read `references/source-safe-physicalization.md` only when first-pass feed lines need source-safe physicalization; keep this lighter than `visual-polish`.
```

- [ ] **Step 6: Run task test to verify it passes**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_commercial_upgrade_physicalization_reference_is_routed
```

Expected: `Ran 1 test` and `OK`.

- [ ] **Step 7: Commit**

```bash
git add tests/test_init_workspace.py references/source-safe-physicalization.md agents/visual-polish.md agents/faithful-feed.md
git commit -m "feat: add source safe physicalization"
```

---

### Task 5: Audit And Prompt Hygiene

**Files:**
- Create: `references/commercial-upgrade-audit.md`
- Modify: `agents/feed-auditor.md`
- Modify: `references/audit-checklist.md`
- Test: `tests/test_init_workspace.py`

- [ ] **Step 1: Write the failing tests**

Append these methods inside `SkillTextRulesTests`.

```python
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
```

- [ ] **Step 2: Run audit routing test to verify it fails**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_commercial_upgrade_audit_reference_is_routed
```

Expected: `FAILED (failures=1)` with `AssertionError: False is not true` because `references/commercial-upgrade-audit.md` does not exist yet.

- [ ] **Step 3: Run contamination test to establish baseline**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_skill_docs_do_not_copy_commercial_prompt_contamination_terms
```

Expected: `Ran 1 test` and `OK`. If it fails, remove copied commercial-prompt boilerplate from the reported skill doc before continuing.

- [ ] **Step 4: Create the commercial-upgrade audit reference**

Create `references/commercial-upgrade-audit.md` with this content:

```markdown
# Commercial Upgrade Audit

Use this file when `feed-auditor` checks artifacts after the commercial-prompt mechanics upgrade.

## Commercial-Upgrade Audit

- commercial-upgrade audit is a second pass after the existing source-faithfulness and deterministic structure checks.
- It checks migrated mechanics without importing rewrite, fixed-timeline, or copied-prompt behaviors.

## Identity Checks

- identity drift: one source identity is split into multiple production identities without evidence.
- standard-name drift: aliases, titles, temporary labels, or generic labels become production names without a standard-name basis.
- Generic roles that later become named, speaking, recurring, or plot-bearing must not remain disposable background faces.

## Period/State Checks

- period/state drift: a stable outfit, injury, disguise, transformation, age-stage, or status variant loses face continuity or lacks evidence.
- Do not merge two incompatible periods into one asset when the source gives a stable visual/state difference.
- Do not create permanent variants for momentary expression, camera posture, or one-line mood.

## Coverage And Continuity Checks

- source-span coverage: every requested source span has visible representation unless the user selected a manual cut range.
- local continuity: each line remains compatible with previous scene, posture, seat, prop state, outfit/state, injury, speaking role, and emotional beat.
- Dialogue remains exact, in source order, and locally supported.

## Physicalization Safety

- physicalization safety: facial, breath, cloth, hair, environment, and sound details stay inside source-supported posture and action.
- Block any added standing, walking, kneeling, bowing, weapon drawing, attacks, prop raising, prop putting away, seat changes, or exits unless source evidence supports it.

## Prompt Contamination

- prompt contamination means copied commercial prompt boilerplate, instruction-protection games, fixed refusal strings, tool side effects, silent sensitive-word replacement, fixed-duration packaging, or rewrite formulas appear in skill docs or output.
- Remove the copied boilerplate. Keep only rewritten mechanics that fit source-faithful 3D国漫 production.
```

- [ ] **Step 5: Route the audit reference**

Modify `agents/feed-auditor.md`.

Extend `## Required References`:

```markdown
- Read `references/commercial-upgrade-audit.md` for commercial-upgrade audit checks after identity, asset, feed-alignment, or physicalization changes.
```

Add these procedure steps after the existing asset continuity step:

```markdown
5. Run the commercial-upgrade audit: check identity drift, standard-name drift, period/state drift, source-span coverage, local continuity, physicalization safety, and prompt contamination.
6. Keep prompt contamination as a documentation/output hygiene issue; do not add hidden games, fixed refusal strings, tool side effects, silent source replacement, or fixed-duration packaging to the skill.
```

Renumber the remaining procedure steps continuously.

- [ ] **Step 6: Extend the audit checklist**

Append this section to `references/audit-checklist.md`:

```markdown
## Commercial-Upgrade Audit

- commercial-upgrade audit: run after the existing deterministic and source-fidelity checks when the artifact uses upgraded identity, asset, alignment, or physicalization rules.
- identity drift: one source identity is split across production names, faces, or assets without evidence.
- standard-name drift: aliases, titles, temporary labels, or generic labels replace the canonical source identity without a standard-name basis.
- period/state drift: outfit, injury, disguise, transformation, age-stage, or status variants lack evidence or lose face continuity.
- source-span coverage: requested source spans are not omitted by line-count pressure, polishing, or asset simplification.
- local continuity: new lines remain compatible with previous visible state unless source or prior line supports the change.
- physicalization safety: added facial, breath, cloth, hair, environment, or sound detail does not become unsupported body movement or prop handling.
- prompt contamination: copied commercial prompt boilerplate, hidden instruction games, fixed refusal strings, tool side effects, silent source replacement, fixed-duration packaging, and rewrite formulas are absent.
```

- [ ] **Step 7: Run task tests to verify they pass**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_commercial_upgrade_audit_reference_is_routed
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_skill_docs_do_not_copy_commercial_prompt_contamination_terms
```

Expected for each command: `Ran 1 test` and `OK`.

- [ ] **Step 8: Commit**

```bash
git add tests/test_init_workspace.py references/commercial-upgrade-audit.md agents/feed-auditor.md references/audit-checklist.md
git commit -m "feat: add commercial upgrade audit"
```

---

### Task 6: Full Validation And Rollout Note

**Files:**
- Review: `SKILL.md`
- Review: `agents/openai.yaml`
- Review: `docs/superpowers/specs/2026-07-04-source-true-guoman-commercial-prompt-upgrade-design.md`
- Test: `tests/test_init_workspace.py`

- [ ] **Step 1: Confirm `SKILL.md` stayed lean**

Run:

```bash
python - <<'PY'
from pathlib import Path
root = Path.cwd()
skill = root.joinpath("SKILL.md").read_text(encoding="utf-8")
for phrase in [
    "references/identity-period-rules.md",
    "references/asset-continuity-rules.md",
    "references/feed-alignment-rules.md",
    "references/source-safe-physicalization.md",
    "references/commercial-upgrade-audit.md",
]:
    if phrase in skill:
        raise SystemExit(f"SKILL.md absorbed specialist reference detail: {phrase}")
print("SKILL.md remains a lean orchestrator")
PY
```

Expected: `SKILL.md remains a lean orchestrator`.

- [ ] **Step 2: Confirm `agents/openai.yaml` still describes the skill**

Run:

```bash
Get-Content -Raw -Encoding UTF8 -LiteralPath 'agents\openai.yaml'
```

Expected output includes:

```yaml
display_name: "Source True Guoman"
short_description: "原著保真3D国漫短剧资产提示词与视频轻量投喂"
```

No change is needed if those lines remain accurate.

- [ ] **Step 3: Run the full unit suite**

Run:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Expected: all tests pass. Baseline before this plan was `Ran 49 tests`; after tasks 1-5, the count increases by 6 to `Ran 55 tests`.

- [ ] **Step 4: Run skill validation with UTF-8**

Run:

```bash
$env:PYTHONUTF8='1'; python C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py E:\source-true-guoman
```

Expected:

```text
Skill is valid!
```

- [ ] **Step 5: Check git diff for unwanted implementation scope**

Run:

```bash
git status --short
git diff --stat
```

Expected: only the planned agent, reference, and test files have changes before the final commit. No installed-skill sync under `C:\Users\Administrator\.codex\skills\source-true-guoman` happens in this plan.

- [ ] **Step 6: Commit final validation note if files changed during review**

If Step 1 or Step 2 required a real file change, commit it:

```bash
git add SKILL.md agents/openai.yaml
git commit -m "chore: finalize commercial prompt upgrade metadata"
```

If no files changed, skip this commit and record in the final response that installed-skill sync remains a separate rollout step.

---

## Self-Review Checklist

- Spec coverage: Tasks 1-5 cover standard names, aliases, period/state extraction, asset variants, prop/interface gating, scene dependencies, source-span alignment, local continuity, source-safe physicalization, audit checks, and prompt hygiene.
- Non-goals: No task imports rewrite workflows, viral opening formulas, fixed-duration groups, silent source replacement, or copied protection boilerplate.
- Test strategy: Every behavior starts with a failing text-contract test and ends with a targeted pass plus full-suite validation.
- Progressive disclosure: Detailed rules live in `references/*.md`; `SKILL.md` stays lean.
- Rollout boundary: Workspace upgrade is separate from syncing the installed copy at `C:\Users\Administrator\.codex\skills\source-true-guoman`.
