# Lightweight feed format

Use this file when producing final user-facing output.

## Package shape

```text
## 资产提示词

### 图片1 = 林夜_黑袍造型
GPT-image-2，16:9，3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续。...

### 图片2 = 青云宗主殿_母图
GPT-image-2，16:9，3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续。...

## 视频投喂块

### 第1组｜15秒｜第1-5条
1 日 内 场景 人物 可见行为画面 镜头概念 运镜 音频/对白
2 ...
3 ...
4 ...
5 ...

上传参考图：资产名 = 图片N；资产名 = 图片N
音色：按本组必要对白匹配角色年龄、身份和情绪；没有对白的组不要新增旁白。对白必须从原文摘取，不改写、不补写、不提前挪用；默认不主动删减原文内容，太长就拆镜头或拆成下一组。
音色资产：角色音色=角色.mp3。
统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。
```

Each 15-second group may use 3-7 lines: use 3-4 for dense dialogue or pauses, 5 for normal beats, and 6-7 only for light low-dialogue micro-actions.

15秒组必须承载剧情推进. 不要整组只做空定场、氛围、人物坐着、群像压迫. 开场定场最多占1个短镜头; 第一组应尽快进入原文事件或对白, such as a source event, source dialogue, conflict, system prompt, or visible decision.

Spoken dialogue density is a pacing judgment, not a hard low character budget. A normal 15-second group can carry one full source report plus a reaction when the line is important and readable. 不要用过低对白字数预算把一句完整汇报拆成多组; split only when the actual spoken load is too long for the target model, not because the line looks long in text.

Default stance: 默认不主动删减原文内容. 把删减权留给用户; output the source-faithful draft in enough groups so the user can trim later. 只有用户明确要求压缩版, 精简版, or a shorter target duration may you intentionally remove non-load-bearing source material.

Dialogue must be exact source excerpts. Do not rewrite, polish, invent, or move later dialogue into an earlier beat. If an exact line is too long, use fewer shots inside the current group or split the beat into another group. 不得用减少总组数解决对白变长.

For multi-chapter work, make a private beat ledger first and run a 多章覆盖审计 before delivery. A 15-second group normally covers one small beat; exact dialogue and dense events should add groups, not erase chapter beats. 十章不得压成十几组 unless the user explicitly asks for a short synopsis. Avoid broad `第1-2章` group titles except for clean transitions.

Visible staging must stay source-grounded. 不主动添加站起、起身、跪下、走动、抬手、收起法器 or other concrete body/prop actions just to make the shot more active. 原文只写坐着就写坐着. 道具动作必须有原文依据; otherwise use neutral framing, facial reactions, ambient sound, or camera movement.

Dialogue camera: 谁说话，镜头优先给谁. 对白默认优先给说话人正面半身, not side-by-default. 默认不要纯大脸特写. 对白行优先使用中近景、半身中景或中景, 保留说话人的身体姿态、所在席位/环境, surrounding reactions, and scene depth so the clip is easy to edit. 空间感放在背景纵深、席位关系和反应层次里; 不要把默认对白镜头写成半身侧面. Use 正面半身, 正面中景, slight front three-quarter, or brief reaction cutaways for variation. 说话微表演 can add life, such as 正面开口, 眼神微压, 短暂停顿, 喉结轻动, 袖口轻动, or fingers lightly tapping an existing armrest/table, but it must stay inside the current source posture and placement. 不得把微动作升级成原文没有的站起、走动、跪下、抬手收法器, weapon drawing, attacking, seat changes, or new prop handling.

Name assets by reusable source identity and version: `角色名_造型/状态`, `场景名_母图/局部_用途`, `道具名_用途`, `界面名_状态`. Use crowd templates for repeated nameless groups, e.g. `青云宗外门弟子_群像模板`, instead of generating separate assets for one-off background people.

Character assets are concept sheets, not shots. 人设资产只写身份、脸、体型、服装和气质. 不要把坐在左侧第二位、站在席位前、当前镜头姿态写进三视图人设; 席位、站位、坐姿、当前动作属于视频行. Use reusable outfit names such as `骨灵教老者_骨纹法袍造型`, not position-based names tied to a temporary seat or camera angle. If an object is only a character identity marker, describe it as a waist/side accessory; do not force a hand-held pose unless creating a dedicated held-prop asset.

When a new asset depends on an older image, include both in `上传参考图` with purpose labels:

```text
上传参考图：林夜第一章黑袍造型 = 图片1（人脸身份参考）；林夜第二章宗门礼服 = 图片2（新造型参考）；青云宗主殿母图 = 图片3（场景母图参考）；主殿左侧丹炉区 = 图片4（局部场景参考）
```

For similar important characters, use reference labels that preserve shared sect style while separating faces:

```text
上传参考图：沈照青云宗弟子服 = 图片1（同门服制参考、避撞脸参考）；陆衡青云宗弟子服 = 图片2（人物参考，要求不同脸型、眉眼、发型轮廓和体态）
```

## Video line shape

```text
序号 日/夜 内/外 具体场景 人物 可见行为画面 镜头概念 运镜 音频/对白
```

Good opening group:

```text
### 第1组｜15秒｜鬼王宗大殿与骨灵教汇报
1 日 内 鬼王宗宗门大殿 林夜 黑袍白发的林夜面无表情坐在漆黑石椅上，十名魔门首领分坐两侧，冷雾贴地压低 中景 + 轻微低机位 + 王座居中 + 两侧席位 固定镜头 环境音：大殿低鸣、衣袖摩擦，无对白
2 日 内 鬼王宗宗门大殿 骨灵教老者 枯瘦老者坐在左侧第二席，正面半身阴沉开口，背景保留大殿纵深和王座方向冷光 中近景 + 正面半身 + 背景纵深 + 王座方向冷光 镜头前推 骨灵教老者：宗主大人，昨日我骨灵教内又发现了一名正道奸细，今日一早我就已经把他剥皮抽筋，将他的一身骨头炼制成了法器，神魂也收入到了万魂幡中。
3 日 内 鬼王宗宗门大殿 骨灵教老者 老者不改变坐姿，语气平静补上后续安排，林夜在王座方向眼皮轻跳 中近景 + 正面半身 + 王座方向冷光 + 反应层次 固定镜头 骨灵教老者：明日一早我就安排弟子将他的皮囊丢到烈阳宗。
4 日 内 鬼王宗宗门大殿 林夜 林夜眼皮子不由自主跳了跳，冷脸差点没绷住，手指在扶手边缘轻轻收紧 近景 + 正面半身 + 面瘫反差 + 扶手细节 急速变焦 音效：心跳一顿，无对白
```

Good line:

```text
1 日 内 鬼王宗宗门大殿 林夜 白发黑袍的林夜坐在黑石王座上，两侧魔门首领低头列席，血色符纹映在他冷脸上 中景 + 轻微低机位 + 王座居中 + 两侧压迫 固定镜头 环境音：大殿低鸣、衣袖摩擦，无对白
```

Avoid:

- Long slash chains that read like a checklist instead of a shot.
- Multiple actions and multiple dialogue lines in one video line.
- Rewritten dialogue, invented dialogue, or later source dialogue used before its setup.
- Invented blocking such as making a seated speaker stand up, raise a prop, or put a prop away when the source did not say that.
- Rule dumps like `不要...不要...不要...` inside every line.
- Film-school explanation when the model only needs visible content.

## Asset prompt shape

Character:

Use the shared tri-view structure for all character assets. For male characters, the compact template below is usually enough.

```text
### 图片N = 骨灵教老者_骨纹法袍造型
GPT-image-2，16:9，3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续。【三视图生成模板】设计人物三视图：骨灵教老者，正面全身照、侧面全身照、背面全身照，最左侧单独的上半身+头部细节展示，白色或极浅灰背景，整体构图工整专业。三视图为一张图。角色设定：枯瘦老年男性，骨灵教魔修，脸颊凹陷，眉眼阴鸷，灰白乱发，身形干瘦佝偻但不要剧情动作，骨色纹路法袍，袖口和衣摆有骨纹符号，气质阴森克制。不要写席位、坐姿、站位、当前镜头动作，不要复杂场景，不要多人，不要换脸，不要文字水印。4K画质！
```

Female character:

```text
GPT-image-2，16:9，3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续。【三视图生成模板】设计成年成熟女修三视图：角色名，正面全身照、侧面全身照、背面全身照，最左侧单独的上半身+头部细节展示，白色或极浅灰背景，整体构图工整专业。三视图为一张图。角色设定：成年女性，高级好看，性感但克制，吸引力来自脸、发型、肩颈锁骨、腰线、腿部线条、衣料层次、剪裁和气质。成年女修可以适度露腿，腿部线条可以是服装美感的一部分，但不要把腿写成唯一卖点。服装设定：... 裙装、旗袍、JK、舞服必须写清完整衣料结构，包括内衬、里裙、安全短裤或不透明下摆；可露小腿、膝盖、膝上自然腿部线条；旗袍或长裙可以有合理开衩，走动时可见一侧腿线；短裙、JK、舞服可以正常露出双腿，正常双腿可见不算违规。禁止低机位扫腿、腿部特写、胸臀腿特写、透明无遮挡、走光、内裤或私密部位可见、超短无遮挡、开衩露到胯根；薄纱只能作为外层装饰，不能替代遮挡。禁止幼态、低俗裸露、夜店风、泳装化、内衣化。不要剧情动作，不要复杂场景，不要多人，不要换脸，不要文字水印。4K画质！
```

Child character:

```text
GPT-image-2，16:9，3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续。【三视图生成模板】设计儿童/少年角色三视图：角色名，正面全身照、侧面全身照、背面全身照，最左侧单独的上半身+头部细节展示，白色或极浅灰背景，整体构图工整专业。三视图为一张图。角色设定：符合原文年龄的儿童/少年，服装完整保守，突出身份、发型、表情和性格气质，不使用成年性感化表达。不要剧情动作，不要复杂场景，不要多人，不要换脸，不要文字水印。4K画质！
```

Do not overcorrect female prompts into ankle-length full coverage by default, and do not overcorrect into leg-only styling. Keep legs visible when the outfit supports it, while avoiding low-angle scans, wardrobe malfunction, private-part exposure, and body-part close-ups.

Scene:

```text
GPT-image-2，16:9，3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续。场景名场景参考图，空场景，写清内/外、空间结构、入口、主要活动区、关键光源和氛围。不要人物，不要现代无关物品，不要文字水印。4K画质！
```

Prop/interface:

```text
GPT-image-2，16:9，3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续。道具名单体参考图，只生成一个完整主体，干净白色或浅灰背景，主体居中，外轮廓和材质清楚。不要人物、不要手持、不要场景摆拍、不要拆件、不要第二件道具、不要文字水印。4K画质！
```
