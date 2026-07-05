# Source True Guoman Copy Packager Design

## Problem

`source-true-guoman` currently emits one source-faithful continuous feed: `## 资产提示词` followed by `## 视频投喂块`, one global `统一要求`, then line numbers from `1` to the end. This solved the earlier failure where AI-made `第N组` blocks compressed, skipped, or re-paced source content.

The current contract creates a new production pain: when users paste small batches into a video tool, they must repeatedly scroll back to copy the global requirement and manually collect the relevant scene, character, and voice references. That is clerical work, not creative judgment. The skill should remove that friction without reintroducing AI compression or pacing groups.

## Goals

- Keep the faithful feed as the source of truth: continuous numbering, exact source dialogue, no compression, no rewrite.
- Add an optional copy-facing packaging pass after the faithful feed exists.
- Package existing continuous lines into small copy packs, defaulting to 5 lines per pack.
- Repeat the global `统一要求` inside each copy pack so users can paste one pack directly.
- Include only the references needed for the lines in that pack: scenes, characters, props/interfaces, and voice assets.
- Preserve original line numbers inside packs; never renumber from 1 inside each pack.
- Make pack size configurable by user request, such as 5, 6, 8, or 10 lines.
- Keep validation separate: faithful feed validator remains strict; copy-pack validation checks packaging invariants.

## Non-Goals

- Do not restore old `第N组` feed output.
- Do not create 15-second groups, fixed-duration batches, or breathing/pacing blocks.
- Do not shorten dialogue, merge source beats, or remove source context.
- Do not move copy-pack output back into `## 视频投喂块`.
- Do not make every pack a full asset bible. Include only references needed to paste that pack.
- Do not claim copy packs are the canonical story order; the continuous faithful feed remains canonical.

## Core Contract

The new feature is a delivery view, not a story transform.

Use these terms:

- `连续投喂稿`: the canonical source-faithful feed.
- `复制投喂包`: a paste-ready wrapper around existing continuous feed lines.

Avoid these terms for the new feature:

- `第N组`
- `15秒组`
- `分镜组`
- `节奏组`
- `呼吸组`

The packager may duplicate wrapper metadata, but it must not alter source content.

## Architecture

Add one specialist agent:

```text
agents/copy-packager.md
```

Route it from `SKILL.md` when the user asks for:

- `复制包`
- `投喂包`
- `paste-ready`
- `每5条一包`
- `分包方便复制`
- `不用每次复制统一要求`
- `场景1= / 角色1= / 音色1=`

The default long-production path becomes:

```text
source-indexer -> asset-bible -> faithful-feed -> feed-auditor
optional -> copy-packager
```

The copy-packager depends on existing artifacts:

- faithful feed file or in-memory final feed
- source index
- asset bible
- existing image/voice reference names when available

If these do not exist, it should refuse to invent references and ask to run the normal production chain first.

## Output Shape

Create a separate file under `生产资产`, for example:

```text
生产资产/seedance-copy-packs-production-ch01-05.md
```

The file shape:

```text
# Seedance Copy Packs - ch01-05

## Pack Settings
- Source feed:
- Pack size: 5
- Numbering: preserve original continuous line numbers
- Contract: copy convenience only; not pacing or compression

### 投喂包 001｜原始行 1-5

统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。

上传参考图：
- 场景1 = 鬼王宗宗门大殿_母图 = 图片2
- 角色1 = 林夜_黑袍白发宗主造型 = 图片1
- 角色2 = 骨灵教枯瘦老者_骨纹法袍造型 = 图片3
- 音色1 = 林夜.mp3
- 音色2 = 骨灵教枯瘦老者.mp3

1 ...
2 ...
3 ...
4 ...
5 ...
```

For the next pack:

```text
### 投喂包 002｜原始行 6-10
```

The final pack may contain fewer lines when the feed length is not divisible by pack size.

## Reference Binding Rules

The packager should read each feed line and collect only visible dependencies:

- Scene references from explicit scene names and asset-bible scene bindings.
- Character references from the primary visible character and any named visible supporting role.
- Prop/interface references when the line needs them, such as phone screen, system interface, jade slip, or magic item.
- Voice assets only for characters who speak or have source-supported voice/OS in that pack.

Do not list every global asset in every pack. That recreates the same copy burden in another form.

When evidence is ambiguous, use the stable asset name from `asset-bible.md` or mark the reference as `需人工确认`, but do not invent a new asset.

## Pack Size Policy

Default pack size: `5` numbered feed lines.

Allowed user override:

- `每6条一包`
- `每8条一包`
- `每10条一包`
- similar explicit positive integer requests

Guardrails:

- Minimum: 1
- Recommended range: 5-10
- If the user asks for a very large pack, allow it but state that it is only a copy wrapper, not a pacing decision.

Do not auto-pick pack size from perceived story beats. That would reintroduce AI pacing judgment.

## Validation

Extend deterministic validation with a new script or script mode:

```text
scripts/validate_copy_packs.py <copy-pack-file> [--source-feed <feed-file>] [--pack-size 5]
```

It should check:

- Each pack contains the exact global `统一要求` line.
- Pack headings use `### 投喂包 NNN｜原始行 A-B`.
- Numbered lines preserve original continuous numbers.
- No line number is missing, duplicated, or reordered across packs.
- No `第N组`, `15秒`, `segment`, `S01/S02`, keyframe, Canvas, MP4, `首帧`, `尾帧`, `续接`, or `承接`.
- Each copied video line still contains exactly one Xiaoyunque tag.
- Pack line counts match requested pack size except the final pack.

The script must not attempt source-fidelity judgment. Source fidelity remains covered by the existing feed audit and quote checks.

## Test Strategy

Add focused tests to `tests/test_init_workspace.py` or split a new test file if the current file becomes too large.

Required tests:

- `SKILL.md` routes copy/paste packaging requests to `agents/copy-packager.md`.
- `copy-packager.md` repeats the non-compression contract.
- `copy-packager.md` says copy packs are delivery wrappers, not pacing groups.
- `references/format.md` still defines the canonical feed as continuous.
- `validate_copy_packs.py` accepts a valid 5-line pack file.
- `validate_copy_packs.py` rejects missing global requirement per pack.
- `validate_copy_packs.py` rejects missing, duplicated, or reset line numbers.
- `validate_copy_packs.py` rejects old group and workflow terms.

Update old tests that currently assert no per-group `上传参考图` anywhere. The new distinction should be:

- canonical `## 视频投喂块`: no per-group reference blocks
- separate copy-pack file: may include per-pack reference blocks

## Migration

Existing faithful feeds remain valid and unchanged.

Existing `seedance-all-reference-feed-production-*.md` files should not be rewritten just because copy-pack support exists.

For future production runs:

1. Produce source index.
2. Produce asset bible.
3. Produce canonical faithful feed.
4. Run feed audit.
5. If requested or enabled by workflow, produce copy packs.
6. Run copy-pack validation.

## Risks And Mitigations

- Risk: Copy packs are mistaken for old story groups.
  - Mitigation: Use `投喂包` wording, preserve original line numbers, and document that packs are copy wrappers only.
- Risk: The packager invents references.
  - Mitigation: Require source index and asset bible; mark uncertain bindings instead of inventing assets.
- Risk: Tests weaken the no-group contract.
  - Mitigation: Keep canonical feed tests strict and add separate copy-pack tests.
- Risk: Pack size becomes pacing.
  - Mitigation: Default to a mechanical line count and never infer pack boundaries from story rhythm.

## Acceptance Criteria

- A user can ask for `每5条一包的复制投喂包`.
- The system creates a separate copy-pack artifact under `生产资产`.
- Every pack is paste-ready with `统一要求` and relevant references.
- Original feed line numbers stay continuous across all packs.
- Exact source dialogue and video lines are not changed.
- Existing feed validator still passes for the canonical feed.
- New copy-pack validator passes for the copy-pack artifact.
