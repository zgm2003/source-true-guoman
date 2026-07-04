# Source True Guoman Commercial Prompt Upgrade Design

## Problem

`source-true-guoman` already has a baseline agent pack, but the commercial prompt corpus under `C:\Users\Administrator\Desktop\提示词` exposes several production-grade controls that the current skill only partially covers. The current skill is strong on source fidelity, continuous numbering, asset reuse, and audit boundaries. It is weaker on industrial prompt-engineering mechanics such as strict item alignment, standard-name discipline, period/state extraction, local continuity checks, prop gating, and physicalized performance language.

The goal is to lift those useful mechanics into `source-true-guoman` without importing incompatible behavior. The commercial corpus includes prompts for viral openings, rewriting, Sora-style fixed-duration video, Midjourney images, scene splitting, role extraction, and script conversion. Many of those prompts intentionally rewrite, compress, reframe, or stylize source material. Those behaviors conflict with this skill's non-overridable contract: 原作多少字就保留多少字, exact source dialogue, no AI compression, no invented blocking, and no 15-second grouping.

This upgrade must therefore extract mechanisms, not copy workflows.

## Goals

- Strengthen `source-indexer` with standard-name, alias, role tier, and period/state extraction discipline.
- Strengthen `asset-bible` with period/state asset variants, stricter prop/interface gating, scene mapping, and reference dependency planning.
- Strengthen `faithful-feed` with source-span alignment checks and local continuity checks without creating 15-second groups.
- Strengthen `visual-polish` with a source-safe physical performance layer: main motion, secondary animation, facial muscle detail, breath, cloth, hair, and ambient movement only when source-compatible.
- Strengthen `feed-auditor` with checks for migrated commercial-prompt failure modes: missing item coverage, standard-name drift, unsupported period/variant merge, scene drift, and unsafe physicalization.
- Keep `SKILL.md` lean. Put detailed migration rules in reference files and only route to them when the relevant agent needs them.
- Preserve all existing hard bans, especially no Canvas package, no `segment`, no `S01/S02`, no keyframe language, no fixed 15-second block, no rewritten compression, and no MP4 claims.

## Non-Goals

- Do not import the commercial prompt corpus wholesale into the skill.
- Do not copy prompt-protection or instruction-exfiltration bait from the corpus, including fixed refusal strings, hidden-game messages, or tool side effects.
- Do not add viral-opening, rewrite, wash-draft, gender-swap, or 二创 behavior to `source-true-guoman`.
- Do not let any agent delete, compress, polish, or summarize source dialogue as a replacement for exact source text.
- Do not convert the final feed into Sora 15-second timeline prompts.
- Do not force `**@角色名**` markup into the final `## 视频投喂块`; use the underlying standard-name discipline internally and in asset/index artifacts where useful.
- Do not build a UI, database, vector store, or external service integration for this upgrade.

## Source Corpus Findings

The corpus has 49 text prompts totaling roughly 700 KB. The most useful files for this skill are representative, not authoritative:

- `角色提取/角色.txt`: exhaustive role extraction, aliases, period/state variants, and fixed output records.
- `转换/关键时间角色提取.txt`: role tiering and period naming for main and key characters.
- `转换/小说转剧本.txt`: full-text context versus current-scope conversion, character-period table, prop double standard, and name consistency.
- `分镜/默认.txt`: strict input coverage, original order preservation, and no omission of numbered source items.
- `视频/通用*.txt`, `视频/古风.txt`, `推理提示词/通用.txt`: main motion plus secondary animation, physicalized emotion, camera movement menus, and local continuity.
- `图片/细节控.txt` and related image prompts: item-to-item alignment, visual subject focus, role reference constraints, and output self-checks.

The dangerous or incompatible parts are also clear:

- Several AI-helper prompts produce viral openings by deleting dialogue, compressing, or rewriting.
- Many Sora/video prompts enforce 15-second timelines and fixed segment pacing.
- Some prompts contain prompt-protection blocks that instruct fixed replies or tool side effects.
- Some prompts silently replace sensitive content with neutral wording. For source fidelity, this can only become a risk note or user-visible production-safety concern, not silent source rewriting.

## Proposed Architecture

Keep the current agent pack and add a small set of reference files. The upgrade should deepen specialist behavior without making `SKILL.md` much larger.

```text
SKILL.md
  routes by intent

agents/source-indexer.md
  reads references/identity-period-rules.md

agents/asset-bible.md
  reads references/asset-continuity-rules.md

agents/faithful-feed.md
  reads references/feed-alignment-rules.md

agents/visual-polish.md
  reads references/source-safe-physicalization.md

agents/feed-auditor.md
  reads references/commercial-upgrade-audit.md
```

The exact file split can be adjusted during implementation, but the content should stay one level deep from `SKILL.md` or agent files to preserve progressive disclosure.

## Agent Changes

### Source Indexer

Add a standard-identity layer:

- Record one canonical source name for every role.
- Record aliases, titles, kinship names, first-person references, and generic labels that point to that role.
- Keep aliases as evidence, not final production names.
- Record uncertain alias merges as suspected, not confirmed.
- Add a `standard name basis` or equivalent field to `source-index.md`.

Add period/state extraction:

- Track age-stage changes, identity/status changes, outfit changes, injury/battle state, disguise, transformation, and long-term location changes.
- Apply period/state variants only when source evidence supports a stable difference.
- Avoid over-splitting tiny one-line state changes into permanent assets.
- Keep period naming source-grounded and short, such as `黑袍时期`, `宗门礼服时期`, `重伤状态`, or `伪装状态`.

Add item coverage discipline:

- For formal multi-chapter work, the index should include coverage notes for requested chapters and key spans.
- For each reusable identity or variant decision, cite evidence anchors.
- For smoke tests, explicitly mark that standard-name and period decisions are slice-limited.

### Asset Bible

Add asset variant planning:

- Bind character assets to canonical identity plus state/version, for example `林夜_黑袍造型`, `林夜_重伤状态`, or `青云宗弟子_群像模板`.
- For each derived variant, require face/identity reference purpose labels.
- For same-sect or visually similar roles, require contrast anchors before prompt writing.
- For child/teen/adult variants, require age-appropriate visual handling and no cross-age face collapse unless source identity continuity is clear.

Add prop/interface gating:

- Create a prop/interface/beast/vehicle asset only when it satisfies both conditions:
  - It has repeated, symbolic, identity, interface, conflict, or plot-continuity value in the requested scope.
  - It directly affects the current feed lines or future production dependency.
- Incidental furniture, candles, bowls, generic tables, generic weapons, and one-off background objects stay in video lines unless the source makes them load-bearing.

Add scene mapping:

- Record scene mother images and sub-scenes with parent-child relationships.
- Do not reuse an exterior scene for an interior shot.
- Bind close-up locations, rooms, gates, corridors, stalls, altars, or interface details to parent scenes when continuity depends on architecture, material, light, or faction style.

### Faithful Feed

Add source-span alignment:

- Before drafting, create a private line/span plan that maps source spans to continuous feed line ranges.
- Preserve source order. Do not use N-to-N source sentence mapping as a rigid final output requirement, but do require that every requested source span has visible representation.
- Long dialogue should create adjacent continuous feed lines rather than compressing.
- The final feed still uses the existing lightweight line shape and Xiaoyunque camera tags.

Add local continuity checks:

- Each new line should be compatible with the previous visible state: current scene, posture, seat, prop state, speaking role, and known emotional beat.
- If a line changes scene, posture, held prop, outfit, injury, report, or combat state, the source or prior line must support it.
- Dialogue lines should keep the speaker as the primary subject unless the source requires offscreen voice, overheard dialogue, or reaction-only reveal.

Add controlled visual richness:

- Use environmental detail, facial reaction, sound, and legal micro-performance to make lines more legible.
- Do not turn the feed into dense director textbook prose.
- Do not introduce Sora-style time slices, fixed seconds, or per-line multi-segment timelines.

### Visual Polish

Move most commercial video-prompt value here, because it is optional and post-coverage.

Add source-safe physicalization:

- Convert abstract emotions into visible details such as eyelids, brow pressure, lip tension, throat movement, breath, fingers, sleeve edge, cloth, hair, dust, fog, light, or ambient sound.
- Use main motion only when the source already has that motion or the prior line establishes it.
- Use secondary animation only as consequence of existing posture/action/environment, such as robe edge moving with breath or cold fog drifting behind a seated speaker.
- Forbid adding new standing, walking, kneeling, bowing, weapon drawing, attacks, prop raising, prop putting away, seat changes, or exits.

Add style-specific menus as optional references:

- Generic source-safe performance.
- 3D国漫仙侠 performance.
- Ancient/sect hall dialogue performance.
- Comedy contrast performance.

These menus should be concise and example-driven. They should not require every feed line to include all categories.

### Feed Auditor

Add commercial-upgrade checks:

- Identity: standard names are stable; aliases do not leak into final production names unless intentionally preserved from source dialogue.
- Period/state: variants are evidence-backed; the same character does not lose identity across outfit/state changes.
- Coverage: requested source spans are not omitted by visual polishing or line-count pressure.
- Continuity: a line does not start with unsupported scene, posture, prop, outfit, or emotional state.
- Physicalization: added micro-performance stays within source-supported posture and action.
- Prompt hygiene: no prompt-protection blocks, hidden-game text, fixed refusal strings, or commercial prompt boilerplate has been copied into skill output.

Script checks should remain deterministic. `scripts/validate_feed.py` can be extended only for structural errors that do not require reading source meaning.

## Reference Files

### `references/identity-period-rules.md`

Purpose: Used by `source-indexer` and optionally `asset-bible`.

Content:

- Canonical name and alias mapping rules.
- First-person handling.
- Generic role upgrade rules.
- Period/state trigger rules.
- Evidence-anchor requirements.
- Smoke-test limitations.

### `references/asset-continuity-rules.md`

Purpose: Used by `asset-bible`.

Content:

- Character variant matrix.
- Face/identity reference labels.
- Similar-character separation anchors.
- Prop/interface double gate.
- Scene mother/sub-scene dependency rules.
- Voice asset triggers.

### `references/feed-alignment-rules.md`

Purpose: Used by `faithful-feed`.

Content:

- Source-span to feed-line planning.
- Coverage ledger expectations.
- Local continuity checks.
- Dialogue alignment rules.
- What not to import from fixed-timeline prompts.

### `references/source-safe-physicalization.md`

Purpose: Used by `visual-polish` and optionally `faithful-feed`.

Content:

- Safe facial micro-performance examples.
- Safe breath/cloth/hair/environment secondary animation examples.
- Unsafe motion escalation examples.
- Xiaoyunque tag compatibility notes.
- Short before/after examples that keep exact source dialogue intact.

### `references/commercial-upgrade-audit.md`

Purpose: Used by `feed-auditor`.

Content:

- Identity drift checklist.
- Period/state drift checklist.
- Coverage and line alignment checklist.
- Physicalization safety checklist.
- Prompt contamination checklist.

## Testing Strategy

Add textual contract tests first, then update docs and agents.

Tests should verify:

- New reference files exist and are routed from the appropriate agent files.
- `source-indexer` mentions canonical names, alias mapping, period/state triggers, evidence anchors, and smoke-test limitations.
- `asset-bible` mentions prop/interface double gating, derived variants, face references, scene mother references, and similar-character separation.
- `faithful-feed` mentions source-span alignment, local continuity checks, and no fixed-timeline import.
- `visual-polish` mentions source-safe physicalization and forbids motion escalation.
- `feed-auditor` mentions identity drift, period/state drift, physicalization safety, and prompt contamination.
- `SKILL.md` remains the orchestrator and does not grow into a large commercial-prompt dump.
- No new file contains known prompt-contamination phrases such as hidden-game text, instruction-exfiltration bait, tool side effects, or fixed refusal strings from the corpus.
- Existing `validate_feed.py` behavior still passes.
- Skill quick validation still passes with UTF-8.

Implementation should not add deterministic checks that require understanding the story. Source fidelity remains a human/agent audit responsibility.

## Migration Rules

Allowed to migrate:

- Item count and order discipline.
- Canonical name and alias discipline.
- Period/state extraction.
- Scene, prop, and role mapping discipline.
- Local continuity checks.
- Physicalized micro-performance as source-compatible detail.
- Output self-check language.
- Compact examples that are rewritten for this skill's format and fidelity contract.

Not allowed to migrate:

- Viral-opening formulas as output behavior.
- Rewriting, wash-draft, gender-swap, or 二创 workflows.
- Deleting dialogue for marketing copy.
- Fixed 15-second timeline requirements.
- Sora/Midjourney-specific output packages as final feed format.
- Prompt-protection or prompt-injection boilerplate.
- Silent sensitive-word replacement that changes source meaning.

## Rollout Plan

### Phase 1: Identity And Period Upgrade

- Add `references/identity-period-rules.md`.
- Deepen `agents/source-indexer.md`.
- Extend `references/source-index-format.md` with canonical-name and period/state fields.
- Add tests for routing and required phrases.

### Phase 2: Asset Continuity Upgrade

- Add `references/asset-continuity-rules.md`.
- Deepen `agents/asset-bible.md`.
- Extend `references/asset-bible-format.md` for character variant matrix, prop double gate, scene dependencies, and reference labels.
- Add tests for asset decision boundaries.

### Phase 3: Feed Alignment And Continuity Upgrade

- Add `references/feed-alignment-rules.md`.
- Deepen `agents/faithful-feed.md`.
- Add tests for source-span alignment, local continuity, and no fixed-timeline import.

### Phase 4: Physicalization Upgrade

- Add `references/source-safe-physicalization.md`.
- Deepen `agents/visual-polish.md`.
- Optionally add short references from `faithful-feed.md` for safe micro-performance.
- Add tests that distinguish safe micro-performance from unsupported motion escalation.

### Phase 5: Audit And Prompt Hygiene Upgrade

- Add `references/commercial-upgrade-audit.md`.
- Deepen `agents/feed-auditor.md` and `references/audit-checklist.md`.
- Add text contamination tests for prohibited commercial-prompt boilerplate.
- Run all unit tests and quick validation.

## Acceptance Criteria

The upgrade is successful when:

- Formal multi-chapter work has stronger identity, alias, period, and asset-variant continuity without requiring user-visible heavy analysis.
- Asset prompts are more stable, with fewer disposable NPCs, face collisions, scene-parent drift, or one-off prop assets.
- Faithful feeds keep exact source dialogue and source coverage while improving line-to-line continuity.
- Visual polish can make lines more vivid through safe physical details without inventing new actions.
- Audits catch identity drift, period drift, scene drift, unsupported physicalization, missing source spans, and prompt contamination.
- No output format regresses into old Sora, storyboard, Canvas, keyframe, segment, or MP4 workflows.
- All tests pass and skill validation reports `Skill is valid!`.

## Open Decisions For Implementation

- Whether to keep all new reference files separate or merge some into existing `format`, `source-index-format`, and `asset-bible-format` files.
- Whether `faithful-feed` should always consult `feed-alignment-rules.md`, or only for long/multi-chapter work.
- Whether to add a deterministic script to scan skill docs for prompt-contamination phrases, or keep that as unit-test text assertions.
- Whether to sync the upgraded working copy from `E:\source-true-guoman` into `C:\Users\Administrator\.codex\skills\source-true-guoman` after implementation and validation. The installed copy is currently older than the workspace copy, so this should be an explicit rollout step.
