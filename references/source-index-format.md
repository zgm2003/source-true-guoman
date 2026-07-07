# Source Index Format

Use this file when creating or updating `source-index.md`.

Production scope gate: if an ambiguous formal production request may cover more than 3 chapters, stop before source-indexing, drafting, writing the canonical feed, or writing copy packs; ask the user how many chapters to produce and recommend 3 chapters. Do not write the canonical feed or copy packs before scope is chosen.

Use this exact chat prompt when formal production scope is missing: `生产范围缺失：检测到文本超过3章。建议先跑3章；你也可以指定 1-5 章、具体章节范围，或明确说全本分批。收到选择前，我不会生成连续投喂稿或复制包。`

Scope defaults after the gate: `默认` means chapters 1-3. Explicit 1 chapter delivers only chapter 1 in the canonical feed and copy packs. Explicit 1 chapter still reads chapters 1-4 when available for forward index. Full-book production batching defaults to 3 chapters per batch.

Cumulative range procedure: calculate `requested_output_range`, `forward_index_range`, `existing_index_range`, and `required_cumulative_index_range = existing_index_range ∪ forward_index_range` before changing source-index. If required cumulative ranges include unread chapters, mark them under `Missing source ranges:` and stop downstream production until the missing source is provided or the user narrows the scope.

Reconciliation contract: source-index is cumulative, not one-run. For every confirmed anonymous-to-named upgrade, record Former temporary names:, Evidence anchors:, Affected artifacts:, Migration action:, and reconciliation-log before downstream artifacts. If the migration changes video line text, line numbers, or asset bindings, update in canonical mother feed -> audit -> copy packs order.

```text
# Source Index

## Scope Status
- Index status: 全范围预扫 / 局部烟测
- Requested range:
- Read range:
- Unread range:
- Evidence basis:
- Requested output range:
- Forward index range:
- Existing index range:
- Required cumulative index range:
- Requested output ranges completed:
- Forward index ranges read:
- Cumulative index range:
- Missing source ranges:
- Reconciliation status: none / pending / completed / needs user confirmation
- Future reveal private: yes / no
- Scope statement: 正式多章任务必须先预扫完整请求范围；局部烟测必须显式标记已阅读范围；局部烟测资产不得当作全局定稿。
- Scope defaults after the gate: `默认` means chapters 1-3.
- Explicit 1 chapter delivers only chapter 1 in the canonical feed and copy packs.
- Explicit 1 chapter still reads chapters 1-4 when available for forward index.
- Full-book production batching defaults to 3 chapters per batch.
- forward index scope: requested output range + next 3 chapters, identity/continuity only; do not leak future plot into the delivered feed or copy packs.
- Smoke-test warning: Do not promote smoke-test assets to global final decisions.

## Character Index
- Name:
  - Canonical source name:
  - Standard name basis:
  - Alias evidence:
  - Aliases/titles:
  - Role tier:
  - First appearance:
  - Later appearances:
  - Identity/faction:
  - Relationships:
  - Speaking range:
  - Posture facts:
  - Outfit/state changes:
  - Period/state variants:
    - Variant name:
    - Period/state trigger:
    - Start evidence:
    - End/change evidence:
  - Slice limitation:
  - Anonymous-to-named upgrade:
  - confirmed anonymous-to-named upgrade:
    - Former temporary names:
    - Upgrade status: none / suspected / confirmed / rejected
    - Evidence anchors:
    - Affected artifacts:
    - Affected prior artifacts:
    - Migration action:
    - Asset migration status: none / rename / deprecated / regenerate / needs user confirmation
    - reconciliation-log:
  - Suspected same asset:
  - Asset binding:
  - Evidence anchors:

## Reconciliation Ledger
- Canonical name:
  - Former temporary names:
  - Upgrade status: none / suspected / confirmed / rejected
  - Migration action:
  - Asset migration status: none / rename / deprecated / regenerate / needs user confirmation
  - Evidence anchors:
  - Affected artifacts:
  - Affected prior artifacts:
  - Prior feed lines affected:
  - reconciliation-log:

## Scene Index
- Scene name:
  - Interior/exterior:
  - Parent scene:
  - Sub-locations:
  - Material/light/space logic:
  - Chapter/line positions:
  - Asset binding:
  - Evidence anchors:

## Asset Index
- Asset name:
  - Type: character / scene / prop / interface / beast / vehicle / voice
  - Source basis:
  - Reuse range:
  - Parent reference:
  - Collision/separation reference:
  - Evidence anchors:

## Term Index
- Term:
  - Type: sect / realm / technique / system / prop / title / other
  - Source spelling:
  - Possible spelling drift:
  - Current handling:
  - Evidence anchors:

## Doubt Index
- Doubt:
  - Possible explanations:
  - Current handling:
  - Not safe to confirm:
  - Evidence anchors:

## Evidence Anchors
- Anchor id:
  - Source position:
  - Short source excerpt:
  - Supports:
```

Keep entries short. Do not use the index as a synopsis replacement. Every merge, correction, relationship claim, reveal handling, face reference, scene reference, or reusable asset decision needs evidence.
