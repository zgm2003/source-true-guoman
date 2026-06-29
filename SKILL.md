---
name: source-true-guoman
description: Use when turning Chinese web-novel chapters, excerpts, scripts, or rough story material into source-faithful 3D国漫 short-video production text, initializing such project workspaces, especially when the output needs reusable character/scene/prop/voice assets, lightweight feed blocks, original dialogue preservation, Xiaoyunque camera tags, and no Canvas, keyframe, segment, or MP4 workflow.
---

# Source True Guoman

## Core rule

Produce a **lightweight 3D国漫 production feed**, not a director textbook. Keep source reading, director judgment, asset decisions, and risk checks mostly internal. The final text should be easy for a video model to follow.

Default style: `3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9`.

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
5. For long scripts or multi-chapter projects, create or update a lightweight working-directory source index when it helps continuity. Treat it as internal evidence, not final output.
6. For multi-chapter projects, make a private chapter beat ledger and group budget before drafting. Preserve the requested story coverage; exact dialogue should expand or split groups, not shrink the scope.
7. Build an asset ledger: existing reusable assets first, new assets only when they drive identity, setting, conflict, action, interface, or repeated continuity. Track parent-child reference relationships, such as same character new outfit or main scene to sub-location. Also track similar-character collision risk when multiple important roles share sect, uniform, age, gender, protagonist-like styling.
8. Name assets with stable reusable names before writing prompts. Prefer `角色名_造型/状态`, `场景名_母图/局部_用途`, `道具名_用途`, and `界面名_状态`; keep names short, source-grounded, and reusable across chapters.
9. Reconcile early anonymous roles with later named roles before emitting assets. If a “路人/NPC/弟子/店小二/黑衣人/侍女/守卫” later gets a name, repeated appearances, dialogue, or plot function, upgrade it to one stable reusable asset and bind all appearances to that identity.
10. If identity is plausible but not confirmed, mark it privately as a suspected same asset. Do not invent confirmation, do not merge faces in output, and do not create strong contradictions; wait for source evidence or user confirmation.
11. Draft shots internally: one video line = one visible action target, one main emotion or beat, one camera movement.
12. Emit only the final package:
   - `## 资产提示词`
   - `## 视频投喂块`
13. Before delivery, check source fidelity, dialogue load, asset reuse, Xiaoyunque raw tags, line weight, and multi-chapter coverage.

Read `references/format.md` before writing final feed blocks. Read `references/xiaoyunque-tags.md` whenever choosing the `运镜` field.

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

After creating folders, move root-level source script files into `剧本资产`. This keeps project roots clean when the user starts with a directory that only contains one script. Do not move `source-index.md`, generated feed files, hidden files, code files, or files already inside asset folders. Do not overwrite an existing file in `剧本资产`; leave the root file in place and ask the user if a conflict needs manual resolution.

## Lightweight source index

Use a local source index for long scripts, multi-chapter work, or any task where continuity depends on information that may be far apart. Do not force an index for short excerpts.

- Keep the index in the working directory when useful, such as `source-index.md` or a project-specific equivalent. It is a private working aid unless the user asks to see it.
- Suggested sections: `角色索引`, `场景索引`, `资产索引`, `术语索引`, `疑点索引`, and `证据锚点`.
- Character entries should track names, aliases, first appearance, later appearances, identity/faction, relationships, speaking role, outfit/state changes, and asset bindings.
- Scene entries should track mother scene, sub-locations, interior/exterior split, style/material/light logic, and chapter or scene positions.
- Asset entries should bind reusable character, scene, prop, interface, beast, vehicle, and voice assets to stable names plus existing image references.
- Term entries should track sects, realms, techniques, systems, special props, titles, and any source spelling drift.
- Doubt entries should track likely typos, suspected same assets, contradictions, unresolved reveals, and possible OCR/ASR/machine-translation errors.
- Evidence anchors should point to chapter/scene/line numbers or short source snippets. Any cross-chapter merge, asset reuse, typo correction, relationship claim, reveal handling, or face/scene reference decision should be supported by source/index evidence.
- Before writing each feed group, consult the relevant index entries. If evidence is missing, keep the point unresolved privately; do not invent confirmation in the final feed.
- Update the index when later text upgrades an early NPC, introduces a named recurrence, changes a character state/outfit, revisits a scene, or resolves a previous doubt.
- Do not mention vector databases, embeddings, retrieval services, or implementation architecture in normal feed output; that belongs to a future engineering mode, not this lightweight skill.

## Long-scope coverage

For multi-chapter or long-script output, preserve source coverage before optimizing line weight.

- Make a private beat ledger per chapter before writing video groups: opening state, key conflict, source dialogue anchor, action turn, result, and chapter hook when present.
- Estimate group count from source beats. A 15-second group usually covers one small beat; a dense chapter often needs several groups. Ten requested chapters should normally become dozens of groups; 十章不得压成十几组 unless the user explicitly asks for a short synopsis.
- Exact dialogue preservation is not permission to skip beats. 不得用减少总组数解决对白变长; split the beat, reduce lines inside the current group, or add another group.
- Avoid broad cross-chapter group titles such as `第1-2章` unless the group is only a clean transition or recap. If one group contains plot turns from two chapters, it is usually under-covered and should be split.
- Run a 多章覆盖审计 before delivery: compare the draft groups against the chapter beat ledger and source index. Every requested chapter needs its setup, turning point, result, and hook represented by at least one visible group; if an anchor is missing, add groups before final output.

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

Dialogue handling:

- 对白必须从原文摘取：不改写，不补写，不把旁白改成角色台词，不把角色口吻润色成“更顺”的新句。
- Keep source dialogue in source order and local context. Do not提前挪用 later lines into an earlier beat, and do not leave a reaction line without the source setup that makes it make sense.
- If source dialogue is long, delete whole non-load-bearing clauses or choose a shorter exact sentence. Do not paraphrase. 太长就拆镜头, reduce group line count, or split into another 15-second group.
- Reducing line count means reducing lines inside the current group, not reducing total coverage. 不得用减少总组数解决对白变长.
- Keep short source dialogue exact when it carries plot, identity, threat, comedy, or hook.
- For long dialogue, preserve the source subject, action object, result, special terms, and strongest conflict clause.
- Do not compress dialogue into a dangling 孤句. A line like `神魂也收入到了万魂幡中。` is too isolated if the source point depends on who was captured, what happened before, and where the body or artifact goes next. Preserve enough 前因, 动作对象, and 结果 for the viewer to understand the beat without reading the source.
- Do not use a line like `宗主哥哥，你怎么也不夸夸奴家？` unless the preceding setup about what she did is also present in the same group or immediately clear from the previous line.

## Asset rules

Use assets to stabilize identity, not to decorate every object.

- Asset naming: use stable names that remain useful after chapter boundaries. Prefer `林夜_黑袍造型`, `林夜_宗门礼服`, `青云宗主殿_母图`, `青云宗主殿_左侧丹炉区`, `传功玉简_单体`, `系统界面_惩罚弹窗`. Avoid vague names like `男主图1`, `场景2`, `新图`, or names based only on temporary image numbers.
- Crowd tiers: classify visible people before creating assets: `主角/高频配角` get individual tri-view assets; `命名低频角色` get assets only when identity, dialogue, or later recurrence matters; `群像模板` covers repeated nameless disciples, guards, villagers, vendors, or soldiers; `一次性背景人` should stay as shot description, not a new asset.
- Long-script reuse: decide asset value from the whole requested script, not from first appearance. Early background roles may need named reusable assets if later scenes reveal identity or importance.
- Character: one white/light-gray background tri-view image; far-left upper-body + head detail, plus front/side/back full body. Lock one face, hairstyle, body, costume, and identity marks.
- Similar-character separation: when two or more important characters share sect uniforms, clan style, profession, age band, gender, protagonist aura, or black/white/blue robe styling, create contrast anchors before writing prompts. Separate face shape, brows/eyes, nose bridge, mouth, jawline, hairstyle silhouette, height/build, posture, temperament, and identity marks. Keep the shared costume system consistent, but explicitly write `不要撞脸、不要像兄弟或双胞胎、不要复用五官和发型轮廓`.
- Anti-face-collision references: if one similar character already has an image, upload it when generating the next similar character as `避撞脸参考` or `同门服制参考`. The prompt should say which parts to share, such as sect palette, robe structure, badge, or material language, and which parts must differ, such as face, hair silhouette, body type, and temperament.
- Character outfit variants: if the same character needs a new chapter/episode outfit, battle state, disguise, injury state, or transformed look, create it as a derived asset. Require uploading the previous stable character image or closest prior outfit as a face/identity reference, e.g. `上传参考图：林夜第一章黑袍造型 = 图片1（人脸身份参考）；林夜第二章宗门礼服 = 图片2（新造型参考）`. The new prompt must say keep the same face, age, facial structure, hairstyle logic, body type, and identity marks while changing only the justified outfit/state.
- Anonymous-to-named character: when a role first appears only as `某弟子`, `黑衣人`, `守卫`, `侍女`, `路人`, or another generic label but later has a name, dialogue, repeated action, relationship, faction, or plot effect, merge those mentions into one character asset. Do not generate a disposable NPC face first and a separate named face later.
- Uncertain identity: if two mentions may be the same person or object but the source has not confirmed it, keep a private `疑似同一资产` note with evidence. Do not merge, rename, or assert the relationship in final output until the source makes it clear.
- Female character assets: 女角色统一按成年成熟女修处理，除非原文明确她真的是小孩。国漫仙侠、高级好看、性感但克制，吸引力来自脸、发型、肩颈锁骨、腰线、衣料层次、剪裁和气质，不靠露腿卖点。裙装、旗袍、JK、舞服必须有完整衣料结构：内衬、里裙、安全短裤或不透明下摆要明确写出；可以有小开衩、走动时露出少量腿部轮廓，但禁止高开衩、整条腿暴露、同时露出双腿、低机位扫腿、腿部特写、胸臀腿特写、透明无遮挡。薄纱只能作为外层装饰，不能替代遮挡。禁止幼态、低俗裸露、夜店风、泳装化、内衣化。
- Child character assets: 只有当前角色真的是小孩时，才使用单独的儿童/少年角色提示词。儿童角色必须完整保守、非性感化，不套用成年成熟女修模板。
- Scene: empty location reference. Separate interior/exterior and materially different rooms; do not reuse an exterior for an interior shot.
- Scene/prop reuse: if the same place, weapon, token, phone/interface, beast, vehicle, or signature object appears across distant scenes, create or bind one reusable asset instead of renaming or redesigning it per group.
- Scene parent reference: when generating a room, gate, corridor, altar, stall, close-up corner, or other sub-area inside an existing large scene, upload the large scene mother image as style/structure reference. The derived prompt should keep the parent scene's architecture, materials, light logic, color mood, and world identity while focusing on the new sub-area. Do not invent a visually unrelated local set just because the shot is closer.
- Prop/interface derived reference: when a prop or interface is a detail from a known scene or owner character, bind the parent scene/character image if it helps keep scale, material, faction style, or screen language consistent.
- Prop/interface: create a clean single-subject product shot only for high-value props or interfaces. If phone orientation matters, make the prompt explicitly `正面屏幕朝镜头` or create a separate front-screen reference; do not force one asset to solve both front and back.
- Voice: bind voice assets only for characters who speak in that group.
- Reuse: when the user provides existing images or earlier generated assets, write `沿用图片N` or bind the existing filename; do not regenerate identity assets unless asked.
- Reference binding: the `上传参考图` line must include parent or comparison references whenever continuity or separation depends on them, not only the newly generated asset. State the purpose in parentheses: `人脸身份参考`, `旧造型参考`, `避撞脸参考`, `同门服制参考`, `场景母图参考`, `局部场景参考`, `材质风格参考`, or `界面风格参考`.

## Shot writing rules

Final video lines must describe what is visible in the frame. Keep them light.

15-second grouping:

- Treat one video group as roughly 15 seconds. Default to 5 lines, but adjust between 3-7 lines based on density.
- Use 3-4 lines when dialogue, OS, system prompts, exposition, emotional pauses, or complex actions need breathing room.
- Use 5 lines for normal plot beats: one clear action or emotion per line, about 3 seconds each.
- Use 6-7 lines only when shots are light, mostly visual, low-dialogue, and made of quick micro-actions.
- Do not exceed 7 lines per 15-second group; split the group instead.
- Spoken Chinese text per 15-second group should usually stay around 20-32 chars; 33-40 chars is crowded; 40+ chars should trigger fewer lines, fewer shots, or another group. Do not solve length by rewriting dialogue.
- For multi-chapter output, the group count is elastic. Exact source dialogue and dense events should create more groups, not broader summaries. Run the 多章覆盖审计 when the requested scope spans more than one chapter.
- If one line contains multiple main actions, split the action or reduce the group line count.

Use this line shape:

```text
序号 日/夜 内/外 具体场景 人物 可见行为画面 镜头概念 运镜 音频/对白
```

`镜头概念` should be compact, e.g. `近景 + 平视 + 单人主镜头 + 冷光压脸`, not a long paragraph.

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

Default block footer:

```text
上传参考图：资产名 = 图片N；资产名 = 图片N
音色：按本组必要对白匹配角色年龄、身份和情绪；没有对白的组不要新增旁白。对白必须从原文摘取，不改写、不补写、不提前挪用；太长就拆镜头或减少本组镜头数。
音色资产：角色音色=文件名.mp3。
统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。
```

If there is no dialogue in the group, omit `音色资产`.

## Common mistakes

| Mistake | Fix |
| --- | --- |
| Final feed reads like production guidelines | Move reasoning internal; output lighter video lines |
| Dialogue gets “cleaned” until source flavor disappears | Extract exact source dialogue; do not rewrite, polish, or invent |
| Dialogue compression creates a 孤句 like `神魂也收入到了万魂幡中。` | Restore the 前因, 动作对象, and 结果, or keep the fuller original line |
| A later reaction line appears without setup, e.g. `宗主哥哥，你怎么也不夸夸奴家？` | Keep source order and include the setup, or omit that dialogue |
| Exact dialogue causes a ten-chapter feed to shrink to 14 groups | Do a 多章覆盖审计, restore missing chapter beats, and add groups. 十章不得压成十几组; 不得用减少总组数解决对白变长 |
| Obvious typo becomes new lore | Treat source anomalies as private notes; do not invent new terms from likely errors |
| Every shot overuses positioning rules | Use position only when it prevents a real generation error |
| 15-second group is forced to exactly 5 lines | Use 3-7 lines based on dialogue density, pauses, and action complexity |
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
