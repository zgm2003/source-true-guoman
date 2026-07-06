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

Copy packs preserve the canonical feed's selected aspect ratio. Supported choices are only `9:16（竖屏）`, `16:9（横屏）`, and `21:9（电影）`; 默认 16:9 when the user says default. Do not offer `1:1` or `4:5`.

New formal copy-pack gate: if the source feed or user request does not already record camera library and aspect ratio, stop before writing copy packs and ask in chat; legacy material may be marked 需人工确认 only when it predates this gate.

Use this exact chat prompt when formal production parameters are missing: `正式生产参数缺失：请先选择运镜库（小云雀 / libtv）和画幅比例（9:16竖屏 / 16:9横屏 / 21:9电影）。收到选择前，我不会生成连续投喂稿或复制包。`

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

When `生产资产/_内部/image-manifest.json` exists, use it for image bindings. Copy packs must not invent image paths. If a visible asset has missing, failed, or blocked manifest status, write `需人工确认（image-generator failed or blocked）`.

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
9. Include `- Camera library: 小云雀` or `- Camera library: libtv` in `## Pack Settings` when the selected library is known. Use `- Camera library: 需人工确认` only for legacy material that predates this gate; for new formal batches, stop and ask instead of writing copy packs.
10. Include `- Aspect ratio: 9:16`, `- Aspect ratio: 16:9`, or `- Aspect ratio: 21:9` in `## Pack Settings` when the selected ratio is known. Use `- Aspect ratio: 需人工确认` only for legacy material that predates this gate. For a new formal batch without a selected ratio, ask `画幅比例用哪个？默认 16:9。可选：9:16（竖屏）、16:9（横屏）、21:9（电影）。如果你说默认，我就按 16:9。`
11. Keep each copied video line text unchanged, including `<...>` camera tags. If copied lines use bare camera words, stop and update the canonical feed first; do not patch copy packs directly.
12. After saving the artifact, run `python scripts/validate_copy_packs.py <copy-pack-file> --source-feed <feed-file> --pack-size <N>` when a source feed file is available.

## Output Discipline

Use `投喂包` wording, not `第N组`, `15秒组`, `分镜组`, `节奏组`, or `呼吸组`.

Every pack should be paste-ready, but compact. Do not list every global asset in every pack. List only references the user needs to paste that pack.

Formal production completion handoff: after copy packs are written and validated, the final chat response must include a concise next-step plan with exactly these three options. Do not execute any option unless the user chooses it or already asked for it.

```text
下一步建议（3选1）：
1. 自动化生图 - run `image-generator`: 根据 asset-bible 生成/续跑图片任务、写入 image-manifest，并让复制包绑定本地图片路径。
2. 安全剪辑 - run `cut-safety`: 按连续行号和原文跨度给删减风险、低/中/高风险、可替代边界，不改写剧情。
3. 视频增强 - run `visual-polish`: 在保留原文覆盖和对白的前提下增强镜头表现；如改动视频行，先改母稿，再审计并重生复制包。
```

Recommended plan: if required images are not all generated and validated, recommend 自动化生图 first; if images are complete and the user mentions length, platform duration, deletion, or pacing pressure, recommend 安全剪辑; otherwise recommend 视频增强 when the next goal is stronger visual performance.

Do not end a completed formal production response with only artifact paths, test results, or a generic done message.
