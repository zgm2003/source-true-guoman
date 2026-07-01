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

Create or update `生产资产/source-index.md` unless the user explicitly asks for a visible root-level working index. Use `references/source-index-format.md`.

Do not output a video feed; do not output a synopsis replacement. Do not summarize chapters as a replacement for source coverage. Use evidence anchors for every merge, correction, relationship claim, reveal handling, face reference, scene reference, or reusable asset decision; also cite outfit/state changes and unresolved doubts.

Scope mode policy: use `全范围预扫` when formal multi-chapter work has completed the full requested pre-scan; use `局部烟测` only when a smoke-test span was read. 正式多章任务必须先预扫完整请求范围. 局部烟测必须显式标记已阅读范围. 局部烟测资产不得当作全局定稿.

## Procedure

1. Mark `索引状态`, `请求范围`, `已阅读范围`, `未阅读范围`, and `证据依据` before any character or asset decision.
2. Confirm that formal multi-chapter work must pre-scan the whole requested scope before deciding identity, recurrence, scene reuse, or final asset value.
3. Smoke tests must label `局部烟测`, list exact read span and unread span, and write `Do not promote smoke-test assets to global final decisions.`
4. Record characters, aliases, factions, speaking roles, first/later appearances, relationships, posture facts, outfit/state changes, and asset binding candidates.
5. Track anonymous-to-named upgrade cases: early `弟子/NPC/黑衣人/侍女/守卫/路人` becomes one stable role if later named, recurring, speaking, or plot-bearing.
6. Record scene mother locations and sub-locations, keeping interior/exterior, material logic, lighting logic, and parent-child scene relationships separate.
7. Record props, interfaces, beasts, vehicles, voice roles, sects, realms, techniques, systems, titles, and suspicious spelling drift.
8. Keep uncertain merges as `suspected same asset`; do not merge or assert confirmation without source evidence.
9. Every merge, correction, relationship claim, reveal handling, face reference, scene reference, or reusable asset decision must cite an evidence anchor.
10. Keep the index compact enough to consult while writing feed lines.
