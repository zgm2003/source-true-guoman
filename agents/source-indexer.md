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

## Required References

- Read `references/source-index-format.md` before writing or updating production source index.
- Read `references/identity-period-rules.md` when aliases, titles, generic roles, repeated roles, confusing names, or outfit/state changes matter.

## Output

Create or update `生产资产/_内部/source-index.md` unless the user explicitly asks for a visible root-level working index. Legacy notes may call the visible path `生产资产/source-index.md`; keep the default internal path for formal production evidence. Use `references/source-index-format.md`.

Do not output a video feed; do not output a synopsis replacement. Do not summarize chapters as a replacement for source coverage. Use evidence anchors for every merge, correction, relationship claim, reveal handling, face reference, scene reference, or reusable asset decision; also cite outfit/state changes and unresolved doubts.

Scope mode policy: use `全范围预扫` when formal multi-chapter work has completed the full requested pre-scan; use `局部烟测` only when a smoke-test span was read. 正式多章任务必须先预扫完整请求范围. 局部烟测必须显式标记已阅读范围. 局部烟测资产不得当作全局定稿.

forward index scope: for formal multi-chapter production, read the requested output range + next 3 chapters when available before final asset identity decisions. Requested output range: only the chapters the user asked to produce are delivered in the feed and copy packs. Forward index range: the extra three chapters are identity/continuity only; do not leak future plot into the delivered feed or copy packs.

Cumulative range procedure: calculate `requested_output_range`, `forward_index_range`, `existing_index_range`, and `required_cumulative_index_range = existing_index_range ∪ forward_index_range` before changing source-index. If required cumulative ranges include unread chapters, mark them under `Missing source ranges:` and stop downstream production until the missing source is provided or the user narrows the scope. Do not treat a prior 1-chapter smoke index as complete when a later 2-3 chapter or 1-3 chapter batch needs the private forward index through chapter 6.

Production scope gate: if an ambiguous formal production request may cover more than 3 chapters, stop before source-indexing, drafting, writing the canonical feed, or writing copy packs; ask the user how many chapters to produce and recommend 3 chapters. Do not write the canonical feed or copy packs before scope is chosen.

Use this exact chat prompt when formal production scope is missing: `生产范围缺失：检测到文本超过3章。建议先跑3章；你也可以指定 1-5 章、具体章节范围，或明确说全本分批。收到选择前，我不会生成连续投喂稿或复制包。`

Scope defaults after the gate: `默认` means chapters 1-3. Explicit 1 chapter delivers only chapter 1 in the canonical feed and copy packs. Explicit 1 chapter still reads chapters 1-4 when available for forward index. Full-book production batching defaults to 3 chapters per batch.

Only split full-book production after the scope gate records an explicit user choice for full-book batching.

Reconciliation contract: source-index is cumulative, not one-run. For every confirmed anonymous-to-named upgrade, record Former temporary names:, Evidence anchors:, Affected artifacts:, Migration action:, and reconciliation-log before downstream artifacts. If the migration changes video line text, line numbers, or asset bindings, update in canonical mother feed -> audit -> copy packs order.

## Procedure

1. Mark `索引状态`, `请求范围`, `已阅读范围`, `未阅读范围`, and `证据依据` before any character or asset decision.
2. Confirm that formal multi-chapter work must pre-scan the whole requested scope before deciding identity, recurrence, scene reuse, or final asset value. If the requested scope is more than 3 chapters, build 3-chapter batch ledgers so locally important named roles are not swallowed by a coarse global index.
3. Smoke tests must label `局部烟测`, list exact read span and unread span, and write `Do not promote smoke-test assets to global final decisions.`
4. Record characters, aliases, factions, speaking roles, first/later appearances, relationships, posture facts, outfit/state changes, and asset binding candidates. For each reusable role, choose a canonical source name, record the standard-name basis, alias mapping, role tier, and evidence anchor.
5. Track anonymous-to-named upgrade cases: early `弟子/NPC/黑衣人/侍女/守卫/路人` becomes one stable role if later named, recurring, speaking, or plot-bearing. For a confirmed anonymous-to-named upgrade, add the former temporary names, evidence anchors, affected artifacts, migration action, and reconciliation-log entry.
6. Record period/state trigger, start evidence, and end/change evidence for outfit, disguise, injury, transformation, faction-role, or battle-state variants; period/state decisions are slice-limited when the index is a smoke test.
7. Record scene mother locations and sub-locations, keeping interior/exterior, material logic, lighting logic, and parent-child scene relationships separate.
8. Record props, interfaces, beasts, vehicles, voice roles, sects, realms, techniques, systems, titles, and suspicious spelling drift.
9. Keep uncertain merges as `suspected same asset`; do not merge or assert confirmation without source evidence.
10. Every merge, correction, relationship claim, reveal handling, face reference, scene reference, or reusable asset decision must cite an evidence anchor.
11. Keep the index compact enough to consult while writing feed lines.
