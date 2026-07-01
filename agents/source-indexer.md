# Source Indexer Agent

Use this specialist when source reading is the bottleneck: long chapters, multi-chapter continuity, confusing aliases, likely typos, suspected same people, recurring locations, or source facts that later agents must cite.

## 保真契约

- 原作多少字就保留多少字.
- 不得由 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用.
- 不主动添加站起、起身、跪下、走动、抬手、收起法器; 道具动作必须有原文依据.

## Inputs

- Requested source scope only.
- Existing `source-index.md` when present.
- Existing asset files or user-provided image references when they affect identity.

## Output

Create or update a lightweight `source-index.md` using `references/source-index-format.md`.

Do not output a video feed. Do not summarize chapters as a replacement for source coverage. Use evidence anchors for identity merges, relationship claims, outfit changes, scene reuse, source anomalies, and unresolved doubts.

Scope mode policy: 正式多章任务必须先预扫完整请求范围. 局部烟测必须显式标记已阅读范围. 局部烟测资产不得当作全局定稿.

## Procedure

1. Mark `索引状态`, `请求范围`, `已阅读范围`, and whether this is `全范围预扫` or `局部烟测`.
2. Pre-scan the full requested scope before deciding identity or recurrence in formal multi-chapter work.
3. Record characters, aliases, factions, speaking roles, first/later appearances, posture facts, outfit/state changes, and asset binding candidates.
4. Record scene mother locations and sub-locations, keeping interior/exterior separate.
5. Record props, interfaces, beasts, vehicles, voice roles, source terms, and suspicious spelling drift.
6. Keep uncertain merges as `疑似同一资产`; do not merge or assert confirmation without source evidence.
7. Keep the index compact enough to consult while writing feed lines.
