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
- Requested production scope.

## Output

Create `生产资产/asset-bible.md`, or a compact `## 资产提示词` plan when the user only needs asset prompts inside a feed package. Use `references/asset-bible-format.md` for the structure.

Scope mode policy: 正式多章任务必须先预扫完整请求范围. 局部烟测必须显式标记已阅读范围. 局部烟测资产不得当作全局定稿.

Asset status must be visible near the top of the output:

- Use `全范围预扫` only after the full requested source scope has been read.
- Use `局部烟测` only for a deliberately limited smoke-test span.
- If the index is `局部烟测`, label every asset as slice-limited and avoid global-final wording.

## Procedure

1. Check the source-index status before making asset calls: final asset decisions require `全范围预扫`. For formal multi-chapter work, do not finalize reusable identities, scene families, or production dependencies from an unread tail.
2. Reuse existing assets first. Only add new assets that stabilize identity, setting, conflict, action, interface, or repeated continuity. Temporary posture, blocking, camera position, seat, and one-off action stay in video lines.
3. Classify every visible person into one tier: `主角/高频配角`, `命名低频角色`, `群像模板`, or `一次性背景人`.
4. Give `主角/高频配角` individual tri-view assets. Use group templates for repeated nameless disciples, guards, villagers, vendors, or soldiers. Keep `一次性背景人` in shot description unless identity or later continuity makes them reusable.
5. Handle early anonymous role upgrades before prompt writing. If a later line gives an early NPC, disciple, guard, servant, black-clothed person, passerby, or shop worker a name, dialogue, repeated action, relationship, faction, or plot effect, merge those mentions into one stable source identity.
6. Use source identity/version names, not temporary camera position, seat, or action. Prefer names such as `林夜_黑袍造型`, `青云宗主殿_母图`, `传功玉简_单体`, or `系统界面_惩罚弹窗`.
7. For every derived outfit/state asset, require previous face/identity references. Keep the same face, age band, facial structure, hairstyle logic, body type, and identity marks while changing only the source-justified outfit, injury, disguise, battle state, or transformed state.
8. Separate similar important characters before writing prompts when they share same sect, same uniform, same gender/age band, or similar protagonist styling. Record contrast anchors for face shape, brows/eyes, nose bridge, mouth, jawline, hairstyle silhouette, height/build, posture, temperament, and identity marks.
9. Bind parent-child references explicitly: outfit variants to face references, sub-scenes to scene mother images, props/interfaces to owner or parent scene, and interface variants to the previous screen language when continuity depends on them.
10. Create prop/interface/beast/vehicle assets only when they carry identity, action, interface, or repeated continuity. Use clean single-subject images for high-value props and interfaces; do not generate a separate asset for every incidental object.
11. Create voice assets for speaking roles in the requested scope. Do not create voice assets for silent background people.
12. List reference upload purposes with clear labels: `人脸身份参考`, `旧造型参考`, `避撞脸参考`, `同门服制参考`, `场景母图参考`, `局部场景参考`, `材质风格参考`, `界面风格参考`.
13. Cite source/index evidence for each reusable asset, derived asset, similar-character separation, reference dependency, and user-confirmation wait state.

Continuity gates:

- Keep a character variant matrix for each reusable identity. A derived variant must name the parent outfit/state and bind a face/identity reference.
- Apply similar-character separation before prompt writing when important characters could share face, uniform, silhouette, or protagonist styling.
- Apply the prop/interface double gate: create the asset only when it has both value and dependency; keep incidental props in video lines.
- Use a scene mother reference for sub-scenes, close details, and local sets that must inherit architecture, materials, light logic, or world identity.
- Record the voice asset trigger as source dialogue or recurring voice continuity in the requested scope.

## Output Discipline

- Keep the asset bible readable and production-facing. Do not include private uncertainty as fact.
- Mark unresolved identity merges as suspected or waiting for confirmation; do not collapse faces without evidence.
- Do not promote local smoke-test assets to global-final decisions.
- Keep copyable prompts focused on the asset itself. Shot posture and blocking belong in video lines.
