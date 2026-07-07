# Asset Continuity Rules

Use these rules when asset decisions must stay stable across chapters, scenes, prompts, or uploaded references.

Image QA gate: image generation must start with environment preflight, then a 风格确认波次 that generates only 第一个场景和第一个人设. Stop and ask for 用户确认风格基准 before generating dependent assets. After confirmation, later characters must upload 人设风格基准参考; later scenes, props, and interfaces must upload 场景风格基准参考 plus any asset-family mother image. Do not write fixed style bans: 不要写死非Q版、非玩具感、非卡通低龄化. 如果用户选择 Q版, the first confirmed scene/character baselines define the Q版 style and later images follow those references. Reference-dependent jobs must use 真实上传/编码参考图; prompt-only reference is forbidden. character with identity props remains a character asset: `鬼财神_财神殿执掌者铁算盘造型` belongs in `人设资产`, not `道具资产`. Asset family: `天机一型手机_三视图` is the phone mother asset; system mall, Douyin UI, and phone screen variants must reference it and keep body, camera, border, screen ratio, and material consistent.

## Cross-batch asset reuse gate

Before writing prompts for a later batch, build an Existing Asset Map from prior canonical feed asset headings, asset-bible, source-index, and image-manifest. Each needed asset gets one action: `reuse`, `rename`, `derived`, or `new`. `reuse` and confirmed `rename` must bind the prior image label/path and must not emit another full `GPT-image` prompt. `derived` must cite the parent asset and reference upload purpose. Only `new` assets get standalone full prompts without a prior binding.

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
