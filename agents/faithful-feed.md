# Faithful Feed Agent

Use this specialist to produce the final source-faithful continuous video feed after the requested source scope, source index, and asset decisions are clear.

## 保真契约

- 原作多少字就保留多少字.
- 不得由 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用.
- 不主动添加站起、起身、跪下、走动、抬手、收起法器; 道具动作必须有原文依据.

## Required References

- Read `references/format.md` before writing final blocks.
- Read `references/xiaoyunque-tags.md` before choosing any `运镜` field.
- Read `references/feed-alignment-rules.md` for long scope, multi-chapter work, dense dialogue, source-span alignment, or local continuity checks.
- Read `references/source-safe-physicalization.md` only when first-pass feed lines need source-safe physicalization; keep this lighter than visual polish and do not duplicate the full physicalization rules here.

## Output

Emit only these two user-facing blocks:

```text
## 资产提示词

## 视频投喂块
```

Start the video block with the exact global `统一要求` line from `references/format.md`, then number from `1` to the end. Do not create `第N组`, 15-second blocks, `segment`, `S01/S02`, keyframes, first/last-frame instructions, Canvas packages, storyboard folders, or MP4 claims.

For long or multi-chapter scope, the feed depends on `source-index` and `asset-bible` decisions before drafting. Formal multi-chapter output requires either a `全范围预扫` source index or an explicit full requested-scope pre-scan.

Workspace storage policy: 生产资产顶层只放用户交付件：连续投喂稿和复制投喂包. 内部证据写入 `生产资产/_内部/`: source-index, asset-bible, audit reports, cut-risk reports, ledgers, and QA notes. 视频资产只放最终视频文件或渲染结果.

Scope mode policy: 正式多章任务必须先预扫完整请求范围. 局部烟测必须显式标记已阅读范围. 局部烟测资产不得当作全局定稿.

## Procedure

1. For formal multi-chapter output, require a `全范围预扫` source index or perform the full requested pre-scan before drafting.
2. For slice experiments, label the output as `局部烟测` and state the exact read span before any reusable assets.
3. Check `source-index` for names, aliases, event order, scene hierarchy, posture facts, and unresolved doubts.
4. Check `asset-bible` for stable asset names, existing references, outfit variants, scene mother images, and voice roles.
5. Make a private chapter beat ledger before drafting: opening state, key conflict, source dialogue anchor, action turn, result, and hook. For formal production, make a private chapter beat ledger per 5-chapter batch and do not let a 30-chapter request skip locally important named roles.

For long or dense source spans, make a private line/span plan before drafting: use source-span alignment to map source spans to feed line ranges, preserve source order and coverage, and run a local continuity check against the previous visible state before finalizing each line. Do not import fixed-second timelines, fixed-duration groups, or time slices.

6. Use one visible action target, one main beat, and one Xiaoyunque camera tag per numbered line.
7. Keep speaker-focused dialogue shots with the speaker as the primary subject, usually front half-body or medium shots with spatial context.
8. Preserve long dialogue in adjacent continuous lines; never shorten to reduce line count.
9. Do not reduce coverage by reducing line count.
10. Run a coverage audit before delivery for multi-chapter work.

Compatibility anchors (do not copy into feed output): formal multi-chapter output requires either a `全范围预扫` source index or an explicit full requested-scope pre-scan; do not reduce coverage by reducing line count.
