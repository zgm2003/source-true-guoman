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
音色：按本组必要对白匹配角色年龄、身份和情绪；没有对白的组不要新增旁白。必要对白只保留本组逐条文本里的短句。
音色资产：角色音色=角色.mp3。
统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。
```

Each 15-second group may use 3-7 lines: use 3-4 for dense dialogue or pauses, 5 for normal beats, and 6-7 only for light low-dialogue micro-actions.

Name assets by reusable source identity and version: `角色名_造型/状态`, `场景名_母图/局部_用途`, `道具名_用途`, `界面名_状态`. Use crowd templates for repeated nameless groups, e.g. `青云宗外门弟子_群像模板`, instead of generating separate assets for one-off background people.

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

Good line:

```text
1 日 内 鬼王宗宗门大殿 林夜 白发黑袍的林夜坐在黑石王座上，两侧魔门首领低头列席，血色符纹映在他冷脸上 中景 + 轻微低机位 + 王座居中 + 两侧压迫 固定镜头 环境音：大殿低鸣、衣袖摩擦，无对白
```

Good dialogue line:

```text
2 日 内 鬼王宗宗门大殿 骨灵教老者 枯瘦老者侧背影站在左侧席位前，白骨法器在指节间轻晃，王座上的林夜在远处冷光中压住表情 中近景 + 侧背影 + 法器居中 + 王座远处可见 镜头前推 骨灵教老者：正道奸细已炼成法器，皮囊明日丢去烈阳宗。；音效：骨片轻响
```

Avoid:

- Long slash chains that read like a checklist instead of a shot.
- Multiple actions and multiple dialogue lines in one video line.
- Rule dumps like `不要...不要...不要...` inside every line.
- Film-school explanation when the model only needs visible content.

## Asset prompt shape

Character:

Use the shared tri-view structure for all character assets. For male characters, the compact template below is usually enough.

```text
GPT-image-2，16:9，3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续。【三视图生成模板】设计人物三视图：角色名，正面全身照、侧面全身照、背面全身照，最左侧单独的上半身+头部细节展示，白色或极浅灰背景，整体构图工整专业。三视图为一张图。角色设定：... 不要剧情动作，不要复杂场景，不要多人，不要换脸，不要文字水印。4K画质！
```

Female character:

```text
GPT-image-2，16:9，3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续。【三视图生成模板】设计成年成熟女修三视图：角色名，正面全身照、侧面全身照、背面全身照，最左侧单独的上半身+头部细节展示，白色或极浅灰背景，整体构图工整专业。三视图为一张图。角色设定：成年女性，高级好看，性感但克制，吸引力来自脸、发型、肩颈锁骨、腰线、衣料层次、剪裁和气质，不靠露腿卖点。服装设定：... 裙装、旗袍、JK、舞服必须写清完整衣料结构，包括内衬、里裙、安全短裤或不透明下摆；可以有小开衩，走动时只露出少量腿部轮廓。禁止高开衩、整条腿暴露、同时露出双腿、低机位扫腿、腿部特写、胸臀腿特写、透明无遮挡；薄纱只能作为外层装饰，不能替代遮挡。禁止幼态、低俗裸露、夜店风、泳装化、内衣化。不要剧情动作，不要复杂场景，不要多人，不要换脸，不要文字水印。4K画质！
```

Child character:

```text
GPT-image-2，16:9，3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续。【三视图生成模板】设计儿童/少年角色三视图：角色名，正面全身照、侧面全身照、背面全身照，最左侧单独的上半身+头部细节展示，白色或极浅灰背景，整体构图工整专业。三视图为一张图。角色设定：符合原文年龄的儿童/少年，服装完整保守，突出身份、发型、表情和性格气质，不使用成年性感化表达。不要剧情动作，不要复杂场景，不要多人，不要换脸，不要文字水印。4K画质！
```

Do not write female prompt rules such as `单侧腿部线条必须清楚` or `不要厚重长裙挡死腿部线条`; they push the generator toward excessive leg exposure.

Scene:

```text
GPT-image-2，16:9，3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续。场景名场景参考图，空场景，写清内/外、空间结构、入口、主要活动区、关键光源和氛围。不要人物，不要现代无关物品，不要文字水印。4K画质！
```

Prop/interface:

```text
GPT-image-2，16:9，3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续。道具名单体参考图，只生成一个完整主体，干净白色或浅灰背景，主体居中，外轮廓和材质清楚。不要人物、不要手持、不要场景摆拍、不要拆件、不要第二件道具、不要文字水印。4K画质！
```
