# Asset Bible Format

Use this file when creating `asset-bible.md` or a compact asset plan.

Image QA gate: create or bind `全局风格基准图` as an 环境风格基准 before dependent image batches; every later image prompt must carry `非Q版、非玩具感、非卡通低龄化，成熟3D国漫`. Reference-dependent jobs must use 真实上传/编码参考图; prompt-only reference is forbidden. character with identity props remains a character asset: `鬼财神_财神殿执掌者铁算盘造型` belongs in `人设资产`, not `道具资产`. Asset family: `天机一型手机_三视图` is the phone mother asset; system mall, Douyin UI, and phone screen variants must reference it and keep body, camera, border, screen ratio, and material consistent.

```text
# Asset Bible

## Scope Status
- Asset status: 全范围预扫定稿 / 局部烟测资产
- Requested range:
- Requested output range:
- Forward index range:
- Source-index basis:
- Slice warning: 局部烟测资产不得当作全局定稿。
- forward index scope: requested output range + next 3 chapters, identity/continuity only; do not leak future plot into the delivered feed or copy packs.

## Character Assets
- Asset name:
  - Asset class: character
  - Output directory: 人设资产
  - Asset family:
  - Tier: 主角/高频配角 / 命名低频角色 / 群像模板 / 一次性背景人
  - Canonical source identity:
  - Source evidence:
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
  - Type: mother image / sub-location / interior / exterior
  - Source evidence:
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
  - Type: prop / interface / magic item / beast / vehicle
  - Source evidence:
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
