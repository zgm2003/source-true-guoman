# Storyboard Contact Sheet Agent

Use this specialist for `分镜资产` only after generated image assets and a valid canonical feed exist. It is post-asset visual QA for contact sheets and blocking QA, not a new production workflow.

## 保真契约

- 原作多少字就保留多少字.
- 不得由 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用.
- 不主动添加站起、起身、跪下、走动、抬手、收起法器; 道具动作必须有原文依据.

## Boundary

- This is post-asset visual QA.
- It must not modify the canonical feed or copy packs.
- It is not Canvas, not keyframe, not segment, and not MP4.
- It must not create `首帧`, `尾帧`, `续接`, `承接`, old storyboard folders, or video-render claims.
- It checks visible standing/seating/blocking continuity against the canonical feed and generated images; it does not rewrite lines, add shots, remove dialogue, or change asset bindings.

## Required Inputs

- A valid canonical feed, preferably already checked with `scripts/validate_feed.py` when saved as a file.
- Generated image assets recorded in `生产资产/_内部/image-manifest.json` or an equivalent image-manifest.
- Real local references from image-manifest for every character, scene, prop, interface, or derived asset that appears in a panel.
- The relevant source index and asset bible when needed to resolve identity, scene hierarchy, or blocking questions.

prompt-only references are forbidden. If a required panel reference is missing, failed, blocked, or not a real local file in image-manifest, stop and report the missing reference instead of inventing one.

## Output

Write outputs under `分镜资产`. The output is a visual QA contact sheet and, when useful, a short QA note file that points back to canonical feed line numbers.

Use this request wording for full sheets:

```text
生成5*5的分镜图，分镜图上不允许有台词。
```

Use partial group wording when the current batch has fewer than 25 panels:

```text
生成N格分镜图，分镜图上不允许有台词。
```

Do not draw dialogue, subtitles, speech bubbles, captions, or production instructions on the contact sheet image. If line numbers or QA notes are needed, put them in the separate QA note text, not on the image.

## Procedure

1. Confirm the canonical feed exists and is valid enough to trust as the source of truth.
2. Confirm generated image assets exist and bind to real local files in image-manifest.
3. Select panels in canonical feed order, normally 25 lines per sheet.
4. For each panel, bind only real local references from image-manifest; no prompt-only references.
5. Check blocking QA: standing/sitting state, left/right position, scene continuity, recurring character identity, outfit/state continuity, and whether any proposed panel would invent unsourced movement.
6. Write the contact-sheet generation request and any QA notes under `分镜资产`.
7. If QA finds a feed problem, report it as a finding. Do not edit the canonical feed or copy packs.

## Failure Cases

- Missing or invalid canonical feed: stop and ask for a valid canonical feed.
- Missing image-manifest or missing local image files: stop and list the missing real local references.
- User asks for Canvas/keyframe/segment/MP4 output: refuse that part and keep the task limited to `分镜资产` post-asset visual QA.
