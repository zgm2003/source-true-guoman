# Asset Continuity Rules

Use these rules when asset decisions must stay stable across chapters, scenes, prompts, or uploaded references.

Image QA gate: create or bind `全局风格基准图` as an 环境风格基准 before dependent image batches; every later image prompt must carry `非Q版、非玩具感、非卡通低龄化，成熟3D国漫`. Reference-dependent jobs must use 真实上传/编码参考图; prompt-only reference is forbidden. character with identity props remains a character asset: `鬼财神_财神殿执掌者铁算盘造型` belongs in `人设资产`, not `道具资产`. Asset family: `天机一型手机_三视图` is the phone mother asset; system mall, Douyin UI, and phone screen variants must reference it and keep body, camera, border, screen ratio, and material consistent.

## Character variant matrix

Track each important character by source identity, current outfit/state, parent asset, and required reference. A new outfit, injury, disguise, battle state, age/state change, or transformation is a derived variant. Every derived variant needs a face/identity reference or closest prior outfit reference, and similar-character separation when another important role could be confused with it.

## Prop/interface double gate

Create a prop or interface asset only when it passes both value and dependency. The value gate asks whether it carries identity, action, interface content, plot conflict, or repeated continuity. The dependency gate asks whether later prompts need a reusable image, parent scene/owner style, screen orientation, or material reference. Incidental props that fail either gate stay in video lines.

道具默认生成单体参考图: use clean single-subject prop references and 只生成一个完整主体. 手机等需要前后侧信息的道具可以使用道具三视图, but 生产需要三视图的道具必须显式标注正面、背面、侧面. 不要把普通一次性道具升级成三视图. Use prop tri-views only when production continuity depends on distinct front/back/side information, such as phone screen/front, back camera/body, and side buttons or thickness.

## Scene mother and sub-scene dependencies

Treat large reusable locations as scene mother references. Sub-scenes such as rooms, gates, corridors, stalls, altars, counters, close-up corners, or screen details should bind the scene mother reference when architecture, materials, light logic, palette, or world identity must match.

## Reference purpose labels

Every upload reference needs a purpose label: face/identity reference, old outfit reference, similar-character separation, same-uniform reference, scene mother reference, local scene reference, material/style reference, or interface style reference. Parent reference purposes should state what stays stable and what may change.

## Voice asset trigger

Create voice assets only for characters who speak in the requested scope. Silent background people, incidental crowds, and unvoiced cameos stay out of the voice asset list unless later source evidence gives them dialogue or recurring voice continuity.
