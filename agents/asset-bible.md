# Asset Bible Agent

Use this specialist when reusable assets need to be planned before image or video production: character tri-views, outfit variants, scene mother images, sub-scenes, props, interfaces, beasts, vehicles, voice assets, and reference-upload dependencies.

## Required References

- Read `references/asset-bible-format.md` before creating the asset bible structure.
- Read `references/asset-continuity-rules.md` before deciding the character variant matrix, prop/interface double gate, scene mother reference, similar-character separation, or voice asset trigger.

## 保真契约

- 原作多少字就保留多少字.
- 不得由 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用.
- 不主动添加站起、起身、跪下、走动、抬手、收起法器; 道具动作必须有原文依据.

## Inputs

- Source text or `source-index.md`.
- Existing generated images, filenames, or user-provided references.
- Prior top-level `生产资产/连续投喂稿-*` asset headings, prior copy-pack bindings, and `生产资产/_内部/image-manifest.json` when a workspace already has earlier batches.
- Requested production scope.

## Output

Create `生产资产/_内部/asset-bible.md`, or a compact `## 资产提示词` plan when the user only needs asset prompts inside a feed package. Use `references/asset-bible-format.md` for the structure. Keep internal asset-bible files out of the production-asset top level; the top level is for the mother feed and copy packs.

Scope mode policy: 正式多章任务必须先预扫完整请求范围. 局部烟测必须显式标记已阅读范围. 局部烟测资产不得当作全局定稿.

forward index scope: for formal multi-chapter production, use the requested output range + next 3 chapters when available before final asset identity decisions. Requested output range: only the chapters the user asked to produce are delivered in the feed and copy packs. Forward index range: the extra three chapters are identity/continuity only; do not leak future plot into the delivered feed or copy packs.

Scope defaults after the gate: `默认` means chapters 1-3. Explicit 1 chapter delivers only chapter 1 in the canonical feed and copy packs. Explicit 1 chapter still reads chapters 1-4 when available for forward index. Full-book production batching defaults to 3 chapters per batch.

Reconciliation contract: source-index is cumulative, not one-run. For every confirmed anonymous-to-named upgrade, record Former temporary names:, Evidence anchors:, Affected artifacts:, Migration action:, and reconciliation-log before downstream artifacts. If the migration changes video line text, line numbers, or asset bindings, update in canonical mother feed -> audit -> copy packs order.

Image QA gate: image generation must start with environment preflight, then a 风格确认波次 that generates only 第一个场景和第一个人设. Stop and ask for 用户确认风格基准 before generating dependent assets. After confirmation, later characters must upload 人设风格基准参考; later scenes, props, and interfaces must upload 场景风格基准参考 plus any asset-family mother image. Do not write fixed style bans: 不要写死非Q版、非玩具感、非卡通低龄化. 如果用户选择 Q版, the first confirmed scene/character baselines define the Q版 style and later images follow those references. Reference-dependent jobs must use 真实上传/编码参考图; prompt-only reference is forbidden. character with identity props remains a character asset: `鬼财神_财神殿执掌者铁算盘造型` belongs in `人设资产`, not `道具资产`. Asset family: `天机一型手机_三视图` is the phone mother asset; system mall, Douyin UI, and phone screen variants must reference it and keep body, camera, border, screen ratio, and material consistent.

Asset status must be visible near the top of the output:

- Use `全范围预扫` only after the full requested source scope has been read.
- Use `局部烟测` only for a deliberately limited smoke-test span.
- If the index is `局部烟测`, label every asset as slice-limited and avoid global-final wording.

## Procedure

1. Check the source-index status before making asset calls: final asset decisions require `全范围预扫`. For formal multi-chapter work, do not finalize reusable identities, scene families, or production dependencies from an unread tail. When scope exceeds 3 chapters, review each 3-chapter batch ledger before pruning assets so named local roles, speaking roles, and repeated props do not disappear from the bible.
2. Build an Existing Asset Map before adding assets: scan prior top-level mother feeds for `### 图片N = ...`, read the existing `_内部/asset-bible.md`, `_内部/source-index.md`, and `_内部/image-manifest.json` when present, and map previous asset names, canonical names, aliases, image labels, manifest paths, and affected artifacts.
3. For every current-batch visual or voice asset, record exactly one reuse decision: `reuse`, `rename`, `derived`, or `new`. `reuse` and confirmed `rename` entries must point to the existing feed/image label or manifest path and must set `Do not re-emit full prompt: yes`. `derived` must name the parent asset and required reference uploads. `new` is the only normal action that permits a full prompt without prior references.
4. If a confirmed anonymous-to-named upgrade changes earlier asset bindings, stop downstream feed/copy-pack work until the source-index reconciliation, asset-bible decision, and affected prior artifacts are updated or explicitly marked `needs user confirmation`. Update canonical mother feed -> audit -> copy packs order.
5. Reuse existing assets first. Only add new assets that stabilize identity, setting, conflict, action, interface, or repeated continuity. Temporary posture, blocking, camera position, seat, and one-off action stay in video lines.
6. Classify every visible person into one tier: `主角/高频配角`, `命名低频角色`, `群像模板`, or `一次性背景人`.
7. Give `主角/高频配角` individual tri-view assets. Use group templates for repeated nameless disciples, guards, villagers, vendors, or soldiers. Keep `一次性背景人` in shot description unless identity or later continuity makes them reusable.
8. Handle early anonymous role upgrades before prompt writing. If a later line gives an early NPC, disciple, guard, servant, black-clothed person, passerby, or shop worker a name, dialogue, repeated action, relationship, faction, or plot effect, merge those mentions into one stable source identity. For a confirmed anonymous-to-named upgrade, cite the reconciliation-log entry and do not emit separate old/new faces.
9. Use source identity/version names, not temporary camera position, seat, or action. Prefer names such as `林夜_黑袍造型`, `青云宗主殿_母图`, `传功玉简_单体`, or `系统界面_惩罚弹窗`.
10. For every derived outfit/state asset, require previous face/identity references. Keep the same face, age band, facial structure, hairstyle logic, body type, and identity marks while changing only the source-justified outfit, injury, disguise, battle state, or transformed state.
11. Separate similar important characters before writing prompts when they share same sect, same uniform, same gender/age band, or similar protagonist styling. Record contrast anchors for face shape, brows/eyes, nose bridge, mouth, jawline, hairstyle silhouette, height/build, posture, temperament, and identity marks.
12. Bind parent-child references explicitly: outfit variants to face references, sub-scenes to scene mother images, props/interfaces to owner or parent scene, and interface variants to the previous screen language when continuity depends on them.
13. Create prop/interface/beast/vehicle assets only when they carry identity, action, interface, or repeated continuity. 道具默认生成单体参考图; use clean single-subject images for high-value props and interfaces, and 只生成一个完整主体. 手机等需要前后侧信息的道具可以使用道具三视图, but 生产需要三视图的道具必须显式标注正面、背面、侧面. 不要把普通一次性道具升级成三视图 or generate a separate asset for every incidental object.
14. Create voice assets for speaking roles in the requested scope. Do not create voice assets for silent background people.
15. List reference upload purposes with clear labels: `人脸身份参考`, `旧造型参考`, `避撞脸参考`, `同门服制参考`, `场景母图参考`, `局部场景参考`, `材质风格参考`, `界面风格参考`.
16. Cite source/index evidence for each reusable asset, derived asset, similar-character separation, reference dependency, and user-confirmation wait state.

Continuity gates:

- Keep a character variant matrix for each reusable identity. A derived variant must name the parent outfit/state and bind a face/identity reference.
- Apply similar-character separation before prompt writing when important characters could share face, uniform, silhouette, or protagonist styling.
- Apply the prop/interface double gate: create the asset only when it has both value and dependency; keep incidental props in video lines.
- For prop view choice, default to a single-subject prop reference. Use a labeled prop tri-view only when production needs distinct front/back/side information, such as phone front screen, back camera/body, and side thickness/buttons.
- Use a scene mother reference for sub-scenes, close details, and local sets that must inherit architecture, materials, light logic, or world identity.
- Record the voice asset trigger as source dialogue or recurring voice continuity in the requested scope.

## Output Discipline

- Keep the asset bible readable and production-facing. Do not include private uncertainty as fact.
- Mark unresolved identity merges as suspected or waiting for confirmation; do not collapse faces without evidence.
- Do not promote local smoke-test assets to global-final decisions.
- Keep copyable prompts focused on the asset itself. Shot posture and blocking belong in video lines.
