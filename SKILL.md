---
name: source-true-guoman
description: Use when turning Chinese web-novel chapters, excerpts, scripts, or rough story material into source-faithful 3D国漫 short-video production text, initializing such project workspaces, especially when the output needs reusable character/scene/prop/voice assets, lightweight feed blocks, original dialogue preservation, Xiaoyunque camera tags, and no Canvas, keyframe, segment, or MP4 workflow.
---

# Source True Guoman

## Core rule

Produce a **lightweight 3D国漫 production feed**, not a director textbook. Keep source reading, director judgment, asset decisions, and risk checks mostly internal. The final text should be easy for a video model to follow.

Default style: `3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9`.

Default preservation stance: 原作多少字就保留多少字. Convert source text into continuous numbered feed lines and 把呼吸感、停顿、删减权留给用户. 不得由 AI 帮用户压缩、概括、改短、润色原作对白或剧情；压缩请求只能输出原文切点、连续编号建议, or tell the user which exact source spans they may manually remove.

## Hard bans

- Do not invent lore, factions, motives, outcomes, names, cultivation realms, props, or relationship changes not supported by the source.
- Do not treat old `cine-make` feeds as positive examples unless the user explicitly marks one as good. Existing awkward feeds are failure samples.
- Do not produce Canvas packages, `segment`, `S01/S02`, `keyframe`, `首帧`, `尾帧`, `续接`, `承接`, storyboard image folders, or MP4 claims.
- Do not front-load long rules, negative-prompt walls, internal analysis, or test-contract language into the final feed.
- Do not force every line into rigid `主体/景别/机位/构图/光影` chains when a shorter natural line is clearer.

## Workflow

1. If the user is starting from a project/workspace directory, initialize it before processing: create `场景资产`, `道具资产`, `剧本资产`, `人设资产`, `生产资产`, `视频资产`, and `音色资产`. Use `scripts/init_workspace.py <workspace>` when available. Move root-level source script files into `剧本资产`; do not overwrite an existing archived script with the same name.
2. Read only the requested source scope.
3. For long scripts or multi-scene excerpts, pre-scan the whole requested scope before writing assets. Track recurring characters, locations, props, interfaces, mounts/beasts, and speaking roles across early and later scenes.
4. Build a private source fact sheet: characters, locations, event order, cause-effect, source terms, key dialogue, reveal order, hook.
5. For long scripts or multi-chapter projects, create or update `生产资产/source-index.md` when it helps continuity. Treat it as internal evidence unless the user asks to see it.
6. For multi-chapter projects, make a private chapter beat ledger and continuous numbering plan before drafting. Preserve the requested story coverage; exact dialogue stays in source order and must not shrink the scope.
7. Build an asset ledger: existing reusable assets first, new assets only when they drive identity, setting, conflict, action, interface, or repeated continuity. Track parent-child reference relationships, such as same character new outfit or main scene to sub-location. Also track similar-character collision risk when multiple important roles share sect, uniform, age, gender, protagonist-like styling.
8. Name assets with stable reusable names before writing prompts. Prefer `角色名_造型/状态`, `场景名_母图/局部_用途`, `道具名_用途`, and `界面名_状态`; keep names short, source-grounded, and reusable across chapters.
9. Reconcile early anonymous roles with later named roles before emitting assets. If a “路人/NPC/弟子/店小二/黑衣人/侍女/守卫” later gets a name, repeated appearances, dialogue, or plot function, upgrade it to one stable reusable asset and bind all appearances to that identity.
10. If identity is plausible but not confirmed, mark it privately as a suspected same asset. Do not invent confirmation, do not merge faces in output, and do not create strong contradictions; wait for source evidence or user confirmation.
11. Draft shots internally: one video line = one visible action target, one main emotion or beat, one camera movement.
12. Emit only the final package:
   - `## 资产提示词`
   - `## 视频投喂块`
13. In `## 视频投喂块`, start with the global `统一要求` line, then number lines continuously from `1` to the end. Do not create 15-second groups, `第N组`, group titles, group footers, or per-group pacing blocks.
14. Before delivery, check source fidelity, dialogue preservation, asset reuse, Xiaoyunque raw tags, continuous numbering, and multi-chapter coverage.
15. If the user explicitly asks for paste-ready copy packs, run `copy-packager` after source index, asset bible, faithful feed, and feed audit exist; keep copy packs in a separate `生产资产` artifact.

Read `references/format.md` before writing final feed blocks. Read `references/xiaoyunque-tags.md` whenever choosing the `运镜` field.

Workspace storage policy: 投喂稿、source-index、asset-bible、审计报告、剪辑风险报告属于生产资产. 视频资产只放最终视频文件或渲染结果.

Scope mode policy: 正式多章任务必须先预扫完整请求范围. 局部烟测必须显式标记已阅读范围. 局部烟测资产不得当作全局定稿. If only a slice was read, say so in the working artifact and avoid final-sounding asset decisions beyond that slice.

Canonical artifact policy: 连续投喂稿 is the canonical mother feed. 复制投喂包 is a derived paste wrapper. Any operation that changes video line text, line numbers, or asset bindings must update the canonical continuous feed first, then re-run feed audit and regenerate copy packs. Do not edit copy packs as the source of truth.

## Agent pack routing

Treat this skill as the orchestrator for a lightweight specialist agent pack. The source-faithful feed remains the non-overridable center; specialist files only narrow the task, they do not override the core preservation stance.

Route by user intent:

- New project directory or root script file: initialize workspace first with `scripts/init_workspace.py <workspace>`, then archive root source scripts into `剧本资产`.
- "Process these chapters", "turn this into feed", long requested scope, or formal multi-chapter production: run `source-indexer -> asset-bible -> faithful-feed -> feed-auditor`.
- "Make an index", "read the source", "track roles", continuity questions, confusing aliases, or suspected typos: read `agents/source-indexer.md` and `references/source-index-format.md`.
- "Make assets", "who needs images", "avoid face collision", "what references upload", reusable characters, scenes, props, interfaces, beasts, vehicles, or voices: read `agents/asset-bible.md` and `references/asset-bible-format.md`.
- "Write feed", "video投喂", "faithful draft", or final continuous prompt blocks: read `agents/faithful-feed.md`, `references/format.md`, and `references/xiaoyunque-tags.md`.
- "Review", "check", "audit", "有没有问题", numbering QA, tag QA, or delivery gate: read `agents/feed-auditor.md` and `references/audit-checklist.md`; run `python scripts/validate_feed.py <feed-file>` when the feed is saved in a file.
- "Can I delete", "cut", "trim", "compress", manual deletion ranges, or platform-length pressure: read `agents/cut-safety.md` and `references/cut-safety-rules.md` only for deletion-risk review and manual cut candidates. Generic compression requests are refused as rewrites and answered with exact cut/source-span advice. cut-safety is a deletion-risk assistant, not a compression writer; it writes a risk report and must not directly modify the canonical feed or copy packs.
- "Make it look better", "shot variety", "画面增强", camera rhythm, or comedy performance: read `agents/visual-polish.md` only after faithful coverage exists. If polish is applied to saved files, update the canonical continuous feed first, re-run feed audit, then regenerate copy packs.
- "复制包", "投喂包", "paste-ready", "每5条一包", "分包方便复制", "不用每次复制统一要求", or "场景1= / 角色1= / 音色1=": read `agents/copy-packager.md` and `references/copy-pack-format.md` only after source index, asset bible, faithful feed, and feed audit exist. Run `python scripts/validate_copy_packs.py <copy-pack-file> --source-feed <feed-file> --pack-size <N>` after saving the artifact.
- "Production order", "upload references", dependency list, or batch checklist: read `agents/production-runner.md` only after assets and faithful feed lines exist. It creates a dependency checklist and must not modify the canonical feed or copy packs.

Default first-phase route for long projects: `source-indexer -> asset-bible -> faithful-feed -> feed-auditor`; optional `-> copy-packager` only when paste-ready copy packs are requested.

Use `E:\xianjie` only as a regression sample unless the user explicitly asks to produce its chapters. For baseline implementation, do not generate the full five-chapter feed as part of baseline implementation; use it after implementation to check that formal multi-chapter work pre-scans the requested scope before final assets or feed output.

Only use `cut-safety` after the user has chosen deletion targets or asks for cut-risk help. It may return exact line/source spans, exact cut/source-span advice, risk levels, and safer boundaries; generic compression requests are refused as rewrites, and it must not write a rewritten compressed story. Only use `visual-polish` after preserving source coverage. Only use `production-runner` after assets and faithful feed lines exist. Only use `copy-packager` after source index, asset bible, faithful feed, and feed audit exist; copy-packager creates paste-ready wrappers, not pacing groups.

## Workspace initialization

Use this when the user points to a new project directory, such as a workspace that only contains one script file.

Run:

```bash
python scripts/init_workspace.py <workspace>
```

Create exactly these top-level folders when missing:

- `场景资产`
- `道具资产`
- `剧本资产`
- `人设资产`
- `生产资产`
- `视频资产`
- `音色资产`

After creating folders, move root-level source script files into `剧本资产`. This keeps project roots clean when the user starts with a directory that only contains one script. Do not archive existing generated working files, including legacy root `source-index.md`, generated feed files, hidden files, code files, or files already inside asset folders; continuing formal work should create or update the production copy under `生产资产`. Do not overwrite an existing file in `剧本资产`; leave the root file in place and ask the user if a conflict needs manual resolution.

## Lightweight source index

Use a lightweight source index for long scripts, multi-chapter work, or any task where continuity depends on information that may be far apart. Do not force an index for short excerpts.

- Keep the index under production assets, normally `生产资产/source-index.md` or a project-specific equivalent inside `生产资产`. It is a private working aid unless the user asks to see it.
- Suggested sections: `角色索引`, `场景索引`, `资产索引`, `术语索引`, `疑点索引`, and `证据锚点`.
- Character entries should track names, aliases, first appearance, later appearances, identity/faction, relationships, speaking role, outfit/state changes, and asset bindings.
- Scene entries should track mother scene, sub-locations, interior/exterior split, style/material/light logic, and chapter or scene positions.
- Asset entries should bind reusable character, scene, prop, interface, beast, vehicle, and voice assets to stable names plus existing image references.
- Term entries should track sects, realms, techniques, systems, special props, titles, and any source spelling drift.
- Doubt entries should track likely typos, suspected same assets, contradictions, unresolved reveals, and possible OCR/ASR/machine-translation errors.
- Evidence anchors should point to chapter/scene/line numbers or short source snippets. Any cross-chapter merge, asset reuse, typo correction, relationship claim, reveal handling, or face/scene reference decision should be supported by source/index evidence.
- Before writing each feed line/span, consult the relevant index entries. If evidence is missing, keep the point unresolved privately; do not invent confirmation in the final feed.
- Update the index when later text upgrades an early NPC, introduces a named recurrence, changes a character state/outfit, revisits a scene, or resolves a previous doubt.
- Do not mention vector databases, embeddings, retrieval services, or implementation architecture in normal feed output; that belongs to a future engineering mode, not this lightweight skill.

## Long-scope coverage

For multi-chapter or long-script output, preserve source coverage before any pacing judgment.

- Make a private beat ledger per chapter before writing video lines: opening state, key conflict, source dialogue anchor, action turn, result, and chapter hook when present.
- Do not estimate 15-second group count, do not create group titles, and do not package lines into `第N组`. Ten requested chapters should normally become many continuous numbered lines; 十章不得压成十几行 unless the user explicitly asks for a short synopsis.
- Exact dialogue preservation is not permission to skip beats. 不得用减少编号行数解决对白变长; add continuous lines in source order when needed.
- Default output may be long. 原作多少字就保留多少字; 把删减权留给用户 so they can cut by taste, pacing, platform, or production budget after seeing the full source-faithful draft. 不得由 AI 帮用户压缩上下文。
- Avoid broad cross-chapter labels such as `第1-2章` in video feed lines; the numbering should run from `1` to the end without grouping.
- Run a 多章覆盖审计 before delivery: compare the continuous numbered lines against the chapter beat ledger and source index. Every requested chapter needs its setup, turning point, result, and hook represented by visible lines; if an anchor is missing, add source-faithful lines before final output.

## Source fidelity

Priority order:

1. event order and cause-effect
2. character motive and stance
3. source names, factions, realms, props, locations
4. key reveals and chapter hook
5. load-bearing dialogue

Source text anomalies:

- Read the source first, then detect likely typos, OCR/ASR mistakes, machine-translation artifacts, repeated fragments, or near-homophone name drift internally.
- Do not treat obvious mistakes as new lore, new names, new factions, new realms, or relationship changes.
- If a correction is obvious from nearby context, preserve the intended meaning in the feed while keeping source terms stable.
- If a term affects plot, identity, realm, faction, prop, or reveal and is not clearly a typo, keep the original wording and mark the ambiguity privately; do not silently rewrite it.
- If the user asks for exact source dialogue/OS, keep the text exact unless they explicitly allow cleanup.

Visible staging fidelity:

- Do not invent concrete blocking to make a line feel cinematic. 不主动添加站起、起身、跪下、走动、抬手、收起法器, turning around, kneeling, bowing, drawing weapons, or changing seats unless the source says it or it is already established by a previous visible line.
- Preserve explicit source posture and placement. 原文只写坐着就写坐着; if the source says `坐在左侧第二位`, do not turn it into `站在左侧席位前`.
- 道具动作必须有原文依据. If the source says a prop exists or was refined but does not say the character is holding, shaking, raising, or putting it away, do not add those hand actions. Use neutral visible framing instead, such as `左侧第二席的枯瘦老者正面半身开口`, `群魔听着对白压低视线`, or `林夜远处眼皮轻跳`.
- You may add neutral camera framing, lighting, ambient sound, and facial reactions when needed for video readability, but those additions must not change who is sitting, standing, moving, holding, attacking, kneeling, or reporting.

Dialogue handling:

- 对白必须从原文摘取：不改写，不补写，不把旁白改成角色台词，不把角色口吻润色成“更顺”的新句。
- Keep source dialogue in source order and local context. 不提前挪用 later lines into an earlier beat, and do not leave a reaction line without the source setup that makes it make sense.
- If source dialogue is long, keep the full source wording in continuous numbered lines. Do not paraphrase, do not replace it with a shorter invented summary, and do not silently choose a shorter source sentence that changes what the user sees. 不删上下文.
- If the user asks for compression, do not rewrite a compressed version inside this skill. Offer exact-source cut candidates, removable source spans, or continuous-line split points; the user decides what to delete.
- Reducing line count must not reduce total coverage. 不得用减少编号行数解决对白变长.
- Keep short source dialogue exact when it carries plot, identity, threat, comedy, or hook.
- For long dialogue, preserve the complete source wording in order. Natural source punctuation can become adjacent continuous lines; shortening is not allowed.
- Do not compress dialogue into a dangling 孤句. A line like `神魂也收入到了万魂幡中。` is too isolated if the source point depends on who was captured, what happened before, and where the body or artifact goes next. Preserve enough 前因, 动作对象, and 结果 for the viewer to understand the beat without reading the source.
- Do not use a line like `宗主哥哥，你怎么也不夸夸奴家？` unless the preceding setup about what she did is also present in nearby continuous lines.

## Asset rules

Use assets to stabilize identity, not to decorate every object.

- Asset naming: use stable names that remain useful after chapter boundaries. Prefer `林夜_黑袍造型`, `林夜_宗门礼服`, `青云宗主殿_母图`, `青云宗主殿_左侧丹炉区`, `传功玉简_单体`, `系统界面_惩罚弹窗`. Avoid vague names like `男主图1`, `场景2`, `新图`, or names based only on temporary image numbers.
- Crowd tiers: classify visible people before creating assets: `主角/高频配角` get individual tri-view assets; `命名低频角色` get assets only when identity, dialogue, or later recurrence matters; `群像模板` covers repeated nameless disciples, guards, villagers, vendors, or soldiers; `一次性背景人` should stay as shot description, not a new asset.
- Long-script reuse: decide asset value from the whole requested script, not from first appearance. Early background roles may need named reusable assets if later scenes reveal identity or importance.
- Character: one white/light-gray background tri-view image; far-left upper-body + head detail, plus front/side/back full body. Lock one face, hairstyle, body, costume, and identity marks.
- Character concept boundary: 人设资产只写身份、脸、体型、服装和气质. Do not mix shot blocking into tri-view prompts. 不要把坐在左侧第二位、站在席位前、当前镜头姿态写进三视图人设; 席位、站位、坐姿、当前动作属于视频行. Name the asset by reusable identity/outfit, e.g. `骨灵教老者_骨纹法袍造型`, not by a temporary seat or camera position. If a prop is only an identity marker, write it as `腰间或身侧配饰`; do not force `手拿` unless the source needs a held-prop asset.
- Similar-character separation: when two or more important characters share sect uniforms, clan style, profession, age band, gender, protagonist aura, or black/white/blue robe styling, create contrast anchors before writing prompts. Separate face shape, brows/eyes, nose bridge, mouth, jawline, hairstyle silhouette, height/build, posture, temperament, and identity marks. Keep the shared costume system consistent, but explicitly write `不要撞脸、不要像兄弟或双胞胎、不要复用五官和发型轮廓`.
- Anti-face-collision references: if one similar character already has an image, upload it when generating the next similar character as `避撞脸参考` or `同门服制参考`. The prompt should say which parts to share, such as sect palette, robe structure, badge, or material language, and which parts must differ, such as face, hair silhouette, body type, and temperament.
- Character outfit variants: if the same character needs a new chapter/episode outfit, battle state, disguise, injury state, or transformed look, create it as a derived asset. Require uploading the previous stable character image or closest prior outfit as a face/identity reference, e.g. `上传参考图：林夜第一章黑袍造型 = 图片1（人脸身份参考）；林夜第二章宗门礼服 = 图片2（新造型参考）`. The new prompt must say keep the same face, age, facial structure, hairstyle logic, body type, and identity marks while changing only the justified outfit/state.
- Anonymous-to-named character: when a role first appears only as `某弟子`, `黑衣人`, `守卫`, `侍女`, `路人`, or another generic label but later has a name, dialogue, repeated action, relationship, faction, or plot effect, merge those mentions into one character asset. Do not generate a disposable NPC face first and a separate named face later.
- Uncertain identity: if two mentions may be the same person or object but the source has not confirmed it, keep a private `疑似同一资产` note with evidence. Do not merge, rename, or assert the relationship in final output until the source makes it clear.
- Female character assets: 女角色统一按成年成熟女修处理，除非原文明确她真的是小孩。国漫仙侠、高级好看、性感但克制，吸引力来自脸、发型、肩颈锁骨、腰线、腿部线条、衣料层次、剪裁和气质。成年女修可以适度露腿，腿部线条可以是服装美感的一部分，但不要把腿写成唯一卖点。裙装、旗袍、JK、舞服必须有完整衣料结构：内衬、里裙、安全短裤或不透明下摆要明确写出；可露小腿、膝盖、膝上自然腿部线条；旗袍或长裙可以有合理开衩，走动时可见一侧腿线；短裙、JK、舞服可以正常露出双腿，正常双腿可见不算违规。禁止低机位扫腿、腿部特写、胸臀腿特写、透明无遮挡、走光、内裤或私密部位可见、超短无遮挡、开衩露到胯根。薄纱只能作为外层装饰，不能替代遮挡。禁止幼态、低俗裸露、夜店风、泳装化、内衣化。
- Child character assets: 只有当前角色真的是小孩时，才使用单独的儿童/少年角色提示词。儿童角色必须完整保守、非性感化，不套用成年成熟女修模板。
- Scene: empty location reference. Separate interior/exterior and materially different rooms; do not reuse an exterior for an interior shot.
- Scene/prop reuse: if the same place, weapon, token, phone/interface, beast, vehicle, or signature object appears across distant scenes, create or bind one reusable asset instead of renaming or redesigning it per line.
- Scene parent reference: when generating a room, gate, corridor, altar, stall, close-up corner, or other sub-area inside an existing large scene, upload the large scene mother image as style/structure reference. The derived prompt should keep the parent scene's architecture, materials, light logic, color mood, and world identity while focusing on the new sub-area. Do not invent a visually unrelated local set just because the shot is closer.
- Prop/interface derived reference: when a prop or interface is a detail from a known scene or owner character, bind the parent scene/character image if it helps keep scale, material, faction style, or screen language consistent.
- Prop/interface: 道具默认生成单体参考图, create a clean single-subject product shot only for high-value props or interfaces, and 只生成一个完整主体. 手机等需要前后侧信息的道具可以使用道具三视图, but 生产需要三视图的道具必须显式标注正面、背面、侧面. 不要把普通一次性道具升级成三视图. If phone orientation matters, make the prompt explicitly `正面屏幕朝镜头` or create a separate front-screen reference; do not force one asset to solve both front and back unless a labeled prop tri-view is explicitly required for production.
- Voice: bind voice assets only for characters who speak in the requested scope.
- Reuse: when the user provides existing images or earlier generated assets, write `沿用图片N` or bind the existing filename; do not regenerate identity assets unless asked.
- Reference binding: the `上传参考图` line must include parent or comparison references whenever continuity or separation depends on them, not only the newly generated asset. State the purpose in parentheses: `人脸身份参考`, `旧造型参考`, `避撞脸参考`, `同门服制参考`, `场景母图参考`, `局部场景参考`, `材质风格参考`, or `界面风格参考`.

## Shot writing rules

Final video lines must describe what is visible in the frame. Keep them light.

Continuous numbering:

- Do not create 15-second groups. Do not write `第1组`, `第1-5条`, group titles, group footers, or any fixed 3-7 line pacing rule.
- Start `## 视频投喂块` with this exact line: `统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。`
- After the `统一要求` line, number video lines continuously from `1` to the end. Do not reset numbering by scene, chapter, or asset.
- The video feed should stay source-content-first: original events, exact dialogue/OS/system prompts, source-grounded visible reactions, and necessary environmental/action audio.
- 把呼吸感交给用户. Do not decide pauses by making 15-second blocks, do not enforce a 100-character spoken limit, and do not add pacing commentary.
- 原作多少字就保留多少字. If a source sentence is long, keep it; if readability requires line breaks, split only at natural source punctuation into adjacent continuous numbers.
- If one line contains multiple unrelated visible actions, split into adjacent continuous numbers without deleting or rewriting the source content.

Use this line shape:

```text
序号 日/夜 内/外 具体场景 人物 可见行为画面 镜头概念 运镜 音频/对白
```

`镜头概念` should be compact, e.g. `近景 + 平视 + 单人主镜头 + 冷光压脸`, not a long paragraph.

Dialogue camera and micro-performance:

- 谁说话，镜头优先给谁; the speaking role should usually be the primary visible subject of that dialogue line unless the source clearly needs an offscreen voice, overheard line, or reaction-only reveal.
- 对白默认优先给说话人正面半身. 默认不要纯大脸特写. 对白行优先使用中近景、半身中景或中景, 保留说话人的身体姿态、所在席位/环境, nearby reactions, and scene depth for spatial continuity and editing.
- 单人对白镜头不要点名另一个重要角色做后景, especially the protagonist on a throne. Use blurred pillars, seat edge, cold fog, lamps, or robe details to carry space instead of forcing another named character into the frame.
- 空间感放在背景纵深、席位关系和反应层次里. Do not make dialogue shots a row of isolated faces, and 不要把默认对白镜头写成半身侧面. Use 正面半身, 正面中景, slight front three-quarter, or brief reaction cutaways for variation.
- 说话微表演 is allowed and useful when it stays source-compatible: 正面开口, 眼神微压, 短暂停顿, 喉结轻动, 袖口轻动, or fingers lightly tapping an existing armrest/table already visible in the setting.
- Micro-actions must stay within the current source posture and placement. 不得把微动作升级成原文没有的站起、走动、跪下、抬手收法器, weapon drawing, attacking, changing seats, or new prop handling.

Guidelines:

- One line has one main visible action.
- One line uses one Xiaoyunque camera tag.
- Let performance, sound, and pause carry tension instead of adding exposition.
- Do not rely on abstract intent like “镜头语言尊重空间”. Write visible pixels.
- `看向/视线/朝向` are allowed only when local and obvious; they must not carry the whole spatial relationship.
- If a character must not face the camera, say it directly and briefly: `侧背影`, `背对镜头`, `不拍正脸`, `声音从侧背方向传来`.
- For hand/phone close-ups, lock orientation: `掌心朝上`, `手腕自然`, `屏幕正面朝镜头`, `不要背面摄像头`.

## Output discipline

Final answer should be copyable. Do not include long explanations unless the user asks for analysis.

Video block header:

```text
统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。
```

Do not repeat this line as a footer. Do not add per-group `上传参考图`, `音色`, or `音色资产` blocks under video lines. Put reusable images and voices in `## 资产提示词` or one compact asset list only when the user needs it.

## Common mistakes

| Mistake | Fix |
| --- | --- |
| Final feed reads like production guidelines | Move reasoning internal; output lighter video lines |
| Dialogue gets “cleaned” until source flavor disappears | Extract exact source dialogue; do not rewrite, polish, invent, or shorten |
| The agent pre-edits the story down because it thinks the user wants a tighter cut | 原作多少字就保留多少字; 把删减权留给用户. 不得由 AI 帮用户压缩 |
| Speaker is made to stand up, raise a prop, or put a prop away when the source only gave dialogue | 原文只写坐着就写坐着. 不主动添加站起、起身、跪下、走动、抬手、收起法器; 道具动作必须有原文依据 |
| Dialogue compression creates a 孤句 like `神魂也收入到了万魂幡中。` | Restore the 前因, 动作对象, and 结果, or keep the fuller original line |
| Agent tries to solve breathing/pacing with 15-second groups | Remove all groups. Use continuous numbering and let the user decide pauses |
| A later reaction line appears without setup, e.g. `宗主哥哥，你怎么也不夸夸奴家？` | Keep source order and include the setup, or omit that dialogue |
| Video feed starts with a group title instead of the global requirement | Start `## 视频投喂块` with the exact `统一要求` line, then `1...2...3...` |
| Exact dialogue causes a ten-chapter feed to shrink to 14 lines | Do a 多章覆盖审计, restore missing chapter beats, and add continuous numbered lines. 十章不得压成十几行 |
| Obvious typo becomes new lore | Treat source anomalies as private notes; do not invent new terms from likely errors |
| Every shot overuses positioning rules | Use position only when it prevents a real generation error |
| Continuous numbering resets by chapter or scene | Keep one sequence from `1` to the end |
| Phone flips to back camera | Specify `屏幕正面朝镜头` and avoid mixed front/back asset prompts |
| Non-library camera word appears | Replace with exact Xiaoyunque tag from `references/xiaoyunque-tags.md` |
| Long script treats early NPCs as disposable | Pre-scan later scenes; upgrade any later-named or recurring role into one reusable asset |
| Long context is handled from memory | Use a lightweight source index with evidence anchors before merging identities, reusing assets, correcting source anomalies, or claiming relationships |
| Asset names are image-number based | Name by source identity and version, e.g. `林夜_黑袍造型`, not `男主图1` |
| Similar hints get merged into one asset too early | Keep `疑似同一资产` private until the source confirms the identity |
| Every background person becomes an asset | Use crowd tiers; only repeated or identity-bearing people get individual assets |
| Same character changes outfit and loses face | Make the new outfit a derived asset and upload the earlier stable character image as `人脸身份参考` |
| Scene close-up no longer matches the main location | Bind the scene mother image as `场景母图参考` when generating sub-areas or close details |
| Same-sect important characters share a face | Add contrast anchors and upload the existing similar role as `避撞脸参考` or `同门服制参考` |
