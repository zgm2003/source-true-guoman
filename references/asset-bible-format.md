# Asset Bible Format

Use this file when creating `asset-bible.md` or a compact asset plan.

Scope defaults after the gate: `默认` means chapters 1-3. Explicit 1 chapter delivers only chapter 1 in the canonical feed and copy packs. Explicit 1 chapter still reads chapters 1-4 when available for forward index. Full-book production batching defaults to 3 chapters per batch.

Reconciliation contract: source-index is cumulative, not one-run. For every confirmed anonymous-to-named upgrade, record Former temporary names:, Evidence anchors:, Affected artifacts:, Migration action:, and reconciliation-log before downstream artifacts. If the migration changes video line text, line numbers, or asset bindings, update in canonical mother feed -> audit -> copy packs order.

Image QA gate: image generation must start with environment preflight, then a 风格确认波次 that generates only 第一个场景和第一个人设. Stop and ask for 用户确认风格基准 before generating dependent assets. After confirmation, later characters must upload 人设风格基准参考; later scenes, props, and interfaces must upload 场景风格基准参考 plus any asset-family mother image. Do not write fixed style bans: 不要写死非Q版、非玩具感、非卡通低龄化. 如果用户选择 Q版, the first confirmed scene/character baselines define the Q版 style and later images follow those references. Reference-dependent jobs must use 真实上传/编码参考图; prompt-only reference is forbidden. character with identity props remains a character asset: `鬼财神_财神殿执掌者铁算盘造型` belongs in `人设资产`, not `道具资产`. Asset family: `天机一型手机_三视图` is the phone mother asset; system mall, Douyin UI, and phone screen variants must reference it and keep body, camera, border, screen ratio, and material consistent.

```text
# Asset Bible

## Scope Status
- Asset status: 全范围预扫定稿 / 局部烟测资产
- Requested range:
- Requested output range:
- Forward index range:
- Source-index basis:
- Slice warning: 局部烟测资产不得当作全局定稿。
- Scope defaults after the gate: `默认` means chapters 1-3.
- Explicit 1 chapter delivers only chapter 1 in the canonical feed and copy packs.
- Explicit 1 chapter still reads chapters 1-4 when available for forward index.
- Full-book production batching defaults to 3 chapters per batch.
- forward index scope: requested output range + next 3 chapters, identity/continuity only; do not leak future plot into the delivered feed or copy packs.

## Character Assets
- Asset name:
  - Canonical asset name:
  - Previous asset names:
  - Asset class: character
  - Output directory: 人设资产
  - Asset family:
  - Tier: 主角/高频配角 / 命名低频角色 / 群像模板 / 一次性背景人
  - Canonical source identity:
  - Source evidence:
  - Migration action: none / rename / deprecated / regenerate / needs user confirmation
  - Replaced by:
  - Source-index evidence:
  - Prior feed lines affected:
  - confirmed anonymous-to-named upgrade:
    - Former temporary names:
    - Evidence anchors:
    - Affected artifacts:
    - Migration action:
    - reconciliation-log:
  - Character variant matrix:
  - Outfit/state version:
  - Variant type:
  - Tri-view requirement:
  - Derived from previous asset:
  - Face/identity reference:
  - Face/identity constants:
  - Similar-character separation anchors:
  - Parent reference purpose:
  - Reference uploads:
    - 人脸身份参考:
    - 旧造型参考:
    - 避撞脸参考:
    - 同门服制参考:
  - Evidence anchors:

## Scene Assets
- Asset name:
  - Canonical asset name:
  - Previous asset names:
  - Type: mother image / sub-location / interior / exterior
  - Source evidence:
  - Migration action: none / rename / deprecated / regenerate / needs user confirmation
  - Replaced by:
  - Source-index evidence:
  - Prior feed lines affected:
  - Parent scene:
  - Scene mother reference:
  - Sub-locations:
  - Material/light/space constants:
  - Parent reference purpose:
  - Reference uploads:
    - 场景母图参考:
    - 局部场景参考:
    - 材质风格参考:
  - Evidence anchors:

## Prop, Interface, Beast, Vehicle Assets
- Asset name:
  - Canonical asset name:
  - Previous asset names:
  - Type: prop / interface / magic item / beast / vehicle
  - Source evidence:
  - Migration action: none / rename / deprecated / regenerate / needs user confirmation
  - Replaced by:
  - Source-index evidence:
  - Prior feed lines affected:
  - Value gate:
  - Dependency gate:
  - Variant type:
  - View requirement: single-subject / prop tri-view
  - Single-subject image requirement:
  - Required labeled views: 正面 / 背面 / 侧面
  - Front/back/side notes:
  - Parent character/scene reference:
  - Parent reference purpose:
  - Interface orientation:
  - Reference uploads:
    - 人脸身份参考:
    - 场景母图参考:
    - 界面风格参考:
    - 材质风格参考:
  - Evidence anchors:

## Voice Assets
- Character name:
  - Speaking range:
  - Voice asset trigger:
  - Voice direction:
  - Source evidence:

## Production Dependencies
- Generate first:
- Generate after references exist:
- Reusable across line ranges:
- Waiting for user confirmation:
```

Only create assets that improve identity, setting, conflict, action, interface, or continuity. Use video lines for temporary posture or blocking.
