# Copy Packager Agent

Use this specialist only after source index, asset bible, faithful feed, and feed audit exist, and the user needs paste-ready `复制投喂包` output such as `每5条一包`, `投喂包`, `paste-ready`, `分包方便复制`, `不用每次复制统一要求`, or `场景1= / 角色1= / 音色1=`.

## 保真契约

- 原作多少字就保留多少字.
- 不得由 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用.
- 不主动添加站起、起身、跪下、走动、抬手、收起法器; 道具动作必须有原文依据.

## Boundary

`复制投喂包` is a delivery wrapper around existing continuous feed lines. It is not the canonical story order, not pacing groups, not a 15-second workflow, and not permission to compress source content.

The canonical source truth remains the `连续投喂稿`: `## 视频投喂块`, one global `统一要求`, and continuous numbering from `1` to the end.

## Required References

- Read `references/copy-pack-format.md` before writing any copy-pack artifact.
- Read `references/format.md` only to confirm the canonical faithful feed shape and exact `统一要求` line.
- Read `references/xiaoyunque-tags.md` or `references/libtv-tags.md` only when checking that copied video lines still contain one valid selected-library tag marked with `<...>`.

## Inputs

- Faithful feed file or final faithful feed text.
- `生产资产/_内部/source-index.md` or equivalent source index.
- `生产资产/_内部/asset-bible.md` or equivalent asset bible.
- Feed audit result or saved audit report.
- Existing image and voice filenames or image numbers when available.

If source index, asset bible, faithful feed, or feed audit is missing, stop and ask to run `source-indexer -> asset-bible -> faithful-feed -> feed-auditor` first; do not invent references to fill the gap.

## Output

Write a separate user-facing copy-pack artifact under the top level of `生产资产`, for example:

```text
生产资产/seedance-copy-packs-production-ch01-05.md
```

Do not insert copy packs into `## 视频投喂块` and do not change the faithful feed file just because copy packs were requested.

## Procedure

1. Confirm the faithful feed already passed source-fidelity and deterministic feed checks.
2. Detect pack size from explicit user text such as `每6条一包`; otherwise default pack size is 5.
3. Split by mechanical numbered feed lines only. Do not pick boundaries from story rhythm, shot breathing, dialogue length, or perceived 15-second pacing.
4. For every pack, preserve original continuous line numbers; do not renumber each pack from 1.
5. Repeat the exact `统一要求` line inside every pack.
6. Collect only visible dependencies needed by the copied lines: scene, visible characters, props/interfaces, and speaking voices.
7. Use stable asset names and existing image or voice bindings from source index and asset bible.
8. If a needed binding is ambiguous, write `需人工确认` with the stable source-grounded name. Do not invent a new image, voice, scene, or character reference.
9. Include `- Camera library: 小云雀`, `- Camera library: libtv`, or `- Camera library: 需人工确认` in `## Pack Settings`.
10. Keep each copied video line text unchanged, including `<...>` camera tags. If copied lines use bare camera words, stop and update the canonical feed first; do not patch copy packs directly.
11. After saving the artifact, run `python scripts/validate_copy_packs.py <copy-pack-file> --source-feed <feed-file> --pack-size <N>` when a source feed file is available.

## Output Discipline

Use `投喂包` wording, not `第N组`, `15秒组`, `分镜组`, `节奏组`, or `呼吸组`.

Every pack should be paste-ready, but compact. Do not list every global asset in every pack. List only references the user needs to paste that pack.
