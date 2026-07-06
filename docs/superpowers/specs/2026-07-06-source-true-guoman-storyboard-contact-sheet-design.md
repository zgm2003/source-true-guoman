# Source True Guoman Storyboard Contact Sheet Design

## Problem

`source-true-guoman` now has a stricter production chain: source indexing, asset bible, style-confirmed image generation, faithful feed, feed audit, and copy packs. That chain solves source fidelity and reusable asset consistency, but it still leaves a late production risk: when the model combines finished characters, scenes, and props inside real feed lines, it can create stance, blocking, scale, orientation, and relationship errors that are hard to detect from text alone.

The user needs a fast visual QA pass after all image assets are generated. This pass should take the existing production feed, group the video lines mechanically by 25, upload the relevant generated scene, character, and prop references for each group, and generate contact-sheet style storyboard images under `分镜资产`. The output is not the old Canvas/keyframe/storyboard-video workflow. It is a visual inspection artifact for finding production problems before video generation.

## Goals

- Add a new specialist agent for post-asset storyboard contact sheets.
- Allow this agent only after the required asset image generation is complete and validated.
- Read a canonical production feed such as `生产资产/seedance-all-reference-feed-production-ch01-03.md`.
- Split numbered video feed lines into mechanical groups of 25.
- For every full 25-line group, create one storyboard image prompt ending with `生成5*5的分镜图，分镜图上不允许有台词。`
- For the final partial group, generate exactly the number of panels needed by the remaining feed lines; do not pad to 25.
- Upload real generated reference images for the corresponding scenes, characters, props, and interfaces used by the group.
- Save generated storyboard QA images under `分镜资产/`.
- Store internal jobs, manifests, and reports under `生产资产/_内部/`.
- Preserve the source-faithfulness contract: the storyboard pass must not rewrite feed lines, change line numbers, compress source dialogue, invent assets, or modify copy packs.

## Non-Goals

- Do not generate video or MP4 files.
- Do not create Canvas packages, keyframes, first-frame/last-frame chains, segment workflows, or old storyboard folders.
- Do not use storyboard contact sheets as the canonical feed.
- Do not edit the canonical continuous feed from storyboard output.
- Do not infer missing assets from the prompt alone.
- Do not run before image assets are complete.
- Do not produce a new asset bible or replace `image-generator`.
- Do not use prompt-only references when reference images are required.
- Do not force a fixed visual style such as non-Q版 or mature 3D国漫; the already confirmed asset images define the style baseline.

## Core Contract

The new feature is a post-asset visual QA artifact.

Use these terms:

- `分镜资产`: generated contact-sheet QA images for visual inspection.
- `storyboard-contact-sheet`: the specialist agent and script family.
- `分镜预览` or `站位QA`: user-facing shorthand.

Avoid treating this feature as:

- a canonical feed
- a pacing system
- a shot rewrite pass
- a video generation pass
- a Canvas/keyframe/segment pipeline

The existing hard ban on storyboard image folders remains valid for the old workflow. This design adds a narrow exception: `分镜资产` may exist only for post-asset visual QA contact sheets after all required image assets are done.

## Recommended Approach

Use an independent CLI-based storyboard QA layer with explicit job and manifest files.

Pipeline placement:

```text
source-indexer
-> asset-bible
-> image-generator
-> faithful-feed
-> feed-auditor
-> copy-packager
-> storyboard-contact-sheet
```

The agent can also run after `image-generator` and a validated canonical feed exist, even if the user does not need copy packs. The hard gate is not copy-pack completion; the hard gate is complete generated image assets plus a valid canonical feed.

### Considered Alternatives

1. Extend `image-generator` to emit storyboard images.
   - Pro: reuses provider and manifest code.
   - Con: mixes reusable asset images with QA contact sheets and weakens the existing `人设资产/场景资产/道具资产` validation boundary.
   - Decision: reject as the primary design.

2. Add an independent storyboard QA agent and scripts.
   - Pro: clean lifecycle, separate output folder, separate manifest, clear post-asset gate, easier to validate.
   - Con: some provider helper code may need reuse or thin wrapping.
   - Decision: use this.

3. Build a UI/dashboard for reviewing contact sheets.
   - Pro: better review experience.
   - Con: not needed before the job format and asset binding rules are stable.
   - Decision: defer.

## New Agent

Add:

```text
agents/storyboard-contact-sheet.md
```

Route it from `SKILL.md` when the user asks for:

- `分镜资产`
- `分镜图`
- `站位检查`
- `站位QA`
- `生成5*5的分镜图`
- `storyboard contact sheet`
- `blocking QA`
- `看站位问题`

The agent must state and enforce:

- It runs only after generated image assets are complete.
- It uses the existing canonical feed without changing it.
- It uploads real local images from manifest paths.
- It writes contact-sheet outputs to `分镜资产/`.
- It writes internal jobs/reports to `生产资产/_内部/`.

## Inputs

Required inputs:

- Canonical production feed, for example:

```text
生产资产/seedance-all-reference-feed-production-ch01-03.md
```

- Generated image manifest:

```text
生产资产/_内部/image-manifest.json
```

- Image jobs used to validate the manifest when available:

```text
生产资产/_内部/image-jobs.jsonl
```

- Asset bible or copy-pack bindings when needed for stable feed-line-to-asset resolution:

```text
生产资产/_内部/asset-bible.md
生产资产/seedance-copy-packs-production-ch01-03.md
```

The implementation should prefer explicit copy-pack image bindings if they exist, because they already map feed-line packs to scene, character, and prop references. If copy packs do not exist, the implementation should resolve from the asset bible and manifest. It must not invent unresolved bindings.

## Outputs

User-facing generated storyboard images:

```text
分镜资产/storyboard-contact-sheet-001-lines-001-025.png
分镜资产/storyboard-contact-sheet-002-lines-026-050.png
分镜资产/storyboard-contact-sheet-003-lines-051-063.png
```

Internal artifacts:

```text
生产资产/_内部/storyboard-jobs.jsonl
生产资产/_内部/storyboard-manifest.json
生产资产/_内部/storyboard-report.md
```

Optional internal debug log:

```text
生产资产/_内部/storyboard-generation-log.jsonl
```

## Job Format

Use JSONL so jobs can be validated, resumed, and inspected.

Example:

```json
{
  "job_id": "storyboard-001-lines-001-025",
  "group_index": 1,
  "line_start": 1,
  "line_end": 25,
  "line_count": 25,
  "source_feed": "生产资产/seedance-all-reference-feed-production-ch01-03.md",
  "prompt": "...",
  "output_dir": "分镜资产",
  "output_file": "storyboard-contact-sheet-001-lines-001-025.png",
  "reference_images": [
    {
      "asset_name": "鬼王宗宗门大殿_母图",
      "path": "场景资产/鬼王宗宗门大殿_母图.png",
      "purpose": "场景空间参考"
    },
    {
      "asset_name": "林夜_黑袍造型",
      "path": "人设资产/林夜_黑袍造型.png",
      "purpose": "人物身份参考"
    }
  ],
  "provider": "openai-compatible",
  "model": "gpt-image-2",
  "size": "16:9",
  "status": "pending"
}
```

## Prompt Construction

For every job, the prompt must include:

- A compact purpose line: this is a contact-sheet QA image for checking stance, blocking, scale, character identity, prop continuity, and scene continuity.
- The original feed lines for the group, preserving original line numbers and text.
- A reference list naming each uploaded image and its purpose.
- A no-dialogue/no-text instruction for the image itself.

For a full 25-line group, append exactly:

```text
生成5*5的分镜图，分镜图上不允许有台词。
```

For a final partial group, append:

```text
生成N格分镜图，分镜图上不允许有台词。
```

`N` is the actual number of remaining feed lines. The last group must not be padded with empty panels.

The prompt may contain the original video lines as guidance, including dialogue text from the feed. The generated contact sheet itself must not draw dialogue, subtitles, speech bubbles, captions, panel labels, or visible text.

## Reference Binding Rules

The storyboard job builder must collect only references needed by the group:

- Scenes and sub-scenes visible in the grouped lines.
- Characters visible in the grouped lines.
- Props, interfaces, beasts, vehicles, or signature objects visible in the grouped lines.
- Style baseline images only when the generated asset manifest records them as dependencies or references.

It must use real local image paths from `image-manifest.json`. A reference is valid only when:

- manifest status is `done`
- the path is relative to the workspace
- the path starts with `人设资产`, `场景资产`, or `道具资产`
- the local file exists
- the reference path is uploaded or encoded for the provider request

If a needed reference is missing, failed, blocked, ambiguous, or not found on disk, job creation must fail with a report. The agent should not proceed with weaker prompt-only references.

## Asset Completion Gate

Before building or running storyboard jobs, validate:

- The canonical feed exists.
- The feed has continuous numbered video lines.
- `image-manifest.json` exists.
- The manifest contains no failed or blocked assets needed by the feed.
- All needed assets have `done` status.
- Every needed local image file exists.
- No reference path escapes the workspace.
- No reference path points under `生产资产`.
- `分镜资产` exists or can be created.

This gate is stricter than copy-pack fallback behavior. Copy packs may mark unresolved references as `需人工确认`; storyboard contact sheets must not generate if required references are unresolved, because the whole purpose is visual QA with actual images.

## Grouping Policy

Grouping is mechanical and line-count based:

- Group size: 25 video lines.
- Preserve original line numbers.
- Do not renumber inside groups.
- Do not split by scene, rhythm, duration, dialogue length, or perceived pacing.
- The final group may contain 1 to 24 lines.
- The final group prompt must ask for exactly that number of panels.

Example:

```text
1-25    -> 5*5 contact sheet
26-50   -> 5*5 contact sheet
51-63   -> 13-panel contact sheet
```

## Script Design

Add:

```text
scripts/build_storyboard_jobs.py
scripts/generate_storyboards.py
scripts/validate_storyboard_manifest.py
```

### `build_storyboard_jobs.py`

Responsibilities:

- Parse a canonical feed file.
- Extract continuous numbered video lines.
- Split lines into 25-line groups.
- Resolve references from copy-pack bindings when available, otherwise from asset bible plus image manifest.
- Validate the asset completion gate.
- Write `生产资产/_内部/storyboard-jobs.jsonl`.

Suggested command:

```powershell
python scripts/build_storyboard_jobs.py --feed 生产资产/seedance-all-reference-feed-production-ch01-03.md --manifest 生产资产/_内部/image-manifest.json --out 生产资产/_内部/storyboard-jobs.jsonl
```

Optional arguments:

```text
--asset-bible 生产资产/_内部/asset-bible.md
--copy-packs 生产资产/seedance-copy-packs-production-ch01-03.md
--workspace .
--model gpt-image-2
--size 16:9
```

### `generate_storyboards.py`

Responsibilities:

- Load storyboard jobs.
- Validate job shape and output path policy.
- Use OpenAI-compatible image provider configuration from environment variables.
- Require `SOURCE_TRUE_IMAGE_REFERENCE_MODE=data-url` or the equivalent supported real-upload mode.
- Encode/upload every reference image.
- Save successful images under `分镜资产`.
- Update `storyboard-manifest.json` and `storyboard-report.md`.
- Support `--resume`.
- Never write API keys into output artifacts.

Suggested command:

```powershell
python scripts/generate_storyboards.py --jobs 生产资产/_内部/storyboard-jobs.jsonl --manifest 生产资产/_内部/storyboard-manifest.json --resume
```

### `validate_storyboard_manifest.py`

Responsibilities:

- Validate output paths under `分镜资产`.
- Validate no generated output is under `生产资产`.
- Validate every `done` storyboard image exists locally.
- Validate every job used real reference paths.
- Validate full groups have 25 lines and final partial groups have the recorded count.
- Validate the required final instruction exists in each job prompt.

## Provider Reuse

`generate_storyboards.py` should reuse provider helpers from `scripts/generate_images.py` where practical:

- environment loading
- retry behavior
- response parsing
- data-url reference encoding
- secret sanitization
- manifest/report writing patterns

It should not reuse `ImageJob` validation directly if that would require adding `分镜资产` to the reusable asset output directories. `分镜资产` is a different artifact type and should have its own output policy.

## Workspace Initialization

Update workspace initialization to include:

```text
分镜资产
```

The directory is a standard top-level workspace folder after this feature. It stores generated QA contact sheets only.

The source script archiving rules remain unchanged. Root scripts still move into `剧本资产`; generated working files still stay out of root.

## Skill Routing Changes

Update `SKILL.md`:

- Add `storyboard-contact-sheet` to the agent pack routing.
- Add a workflow note that it runs after image assets are complete and validated.
- Add the narrow exception to the existing storyboard-folder ban.
- Add `分镜资产` to the workspace folder list.

Suggested route line:

```text
"分镜资产", "分镜图", "站位检查", "站位QA", "生成5*5的分镜图", "storyboard contact sheet", or "blocking QA": read `agents/storyboard-contact-sheet.md` only after generated image assets and a valid canonical feed exist. It creates post-asset QA contact sheets under `分镜资产` and must not modify the canonical feed or copy packs.
```

## Error Handling

Hard failures:

- feed file missing
- manifest missing
- feed has no numbered video lines
- required image asset is failed or blocked
- required image asset path missing on disk
- reference path is absolute, outside workspace, or under `生产资产`
- no real reference upload mode is configured
- generated output would be outside `分镜资产`

Recoverable provider failures:

- timeout
- 429
- 5xx
- malformed temporary response
- image download failure

Provider failures should use retry/backoff and then record a failed storyboard job. A failed storyboard job does not change the canonical feed or reusable asset manifest.

## Testing Strategy

Add focused tests before implementation.

Routing and documentation tests:

- `SKILL.md` routes storyboard QA intents to `agents/storyboard-contact-sheet.md`.
- `SKILL.md` explains `分镜资产` is a post-asset QA exception, not the old storyboard workflow.
- Workspace initialization creates `分镜资产`.
- The new agent states it only runs after all required assets are generated.
- The new agent includes the exact instruction `生成5*5的分镜图，分镜图上不允许有台词。`

Job builder tests:

- Parses numbered feed lines and groups 1-25, 26-50, and final partial lines.
- Preserves original line numbers and text in job prompts.
- Full 25-line jobs use the exact 5*5 instruction.
- Final partial jobs use the actual panel count.
- Rejects missing feed files.
- Rejects missing or malformed manifests.
- Rejects failed or blocked required assets.
- Rejects `done` assets whose local files are missing.
- Rejects unresolved references instead of inventing paths.
- Writes output jobs under `生产资产/_内部/`.

Manifest/generation tests:

- Storyboard outputs are allowed only under `分镜资产`.
- Reference images are allowed only from `人设资产`, `场景资产`, or `道具资产`.
- Reference images must be encoded/uploaded when jobs have references.
- Secrets are not written to storyboard manifest or report.
- `--resume` skips existing successful storyboard images with matching prompt hash.

Regression tests:

- Existing `image-generator` tests still reject normal image outputs under `生产资产`.
- Existing reusable asset output dirs remain limited to `人设资产`, `场景资产`, and `道具资产`.
- Existing feed validator continues to reject old storyboard/keyframe/segment wording in canonical feeds.

## Acceptance Criteria

- A user can ask for `分镜资产` after asset generation completes.
- The system refuses to run if generated assets are missing, failed, blocked, or only prompt-bound.
- The system creates `分镜资产` as a standard workspace folder.
- The system splits feed lines into 25-line jobs with a final partial job when needed.
- Full jobs append exactly `生成5*5的分镜图，分镜图上不允许有台词。`
- Partial jobs request exactly the remaining panel count.
- Every storyboard job uploads real scene, character, and prop references from local manifest paths.
- Generated contact sheets are saved under `分镜资产`.
- Internal jobs, manifests, and reports are saved under `生产资产/_内部`.
- The canonical feed and copy packs are never modified by this agent.
- Tests cover routing, gating, grouping, reference validation, output policy, and resume behavior.

## Implementation Notes

The first implementation should be conservative. It is better to stop with a precise missing-reference report than to generate a weaker contact sheet without real references.

`E:\xianjie` can be used as a regression workspace when the required feed and image manifest exist. At the time of this design, `E:\xianjie\分镜资产` exists, but `E:\xianjie\生产资产\seedance-all-reference-feed-production-ch01-03.md` was not present, so the implementation should not assume that sample is runnable until the production artifacts exist.
