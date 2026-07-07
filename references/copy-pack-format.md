# Copy Pack Format

Use this file when `copy-packager` creates a separate paste-ready `复制投喂包` artifact.

## Boundary

A `复制投喂包` is a delivery wrapper around existing faithful feed lines. 连续投喂稿 is the canonical mother feed. 复制投喂包 is a derived paste wrapper. It is not the canonical feed, not pacing groups, not a 15-second plan, and not a source transform.

The canonical source truth remains the `连续投喂稿`: `## 视频投喂块`, one global `统一要求`, and continuous numbering from `1` to the end.

Any operation that changes video line text, line numbers, or asset bindings must update the canonical continuous feed first, then re-run feed audit and regenerate copy packs. Do not edit copy packs as the source of truth.

Copied video lines must already contain one selected-library camera tag marked with angle brackets, such as `<固定镜头>` or `<镜头前推>`. If a source feed contains bare camera terms, fix and audit the canonical mother feed first, then regenerate copy packs.

Copied packs must preserve the canonical feed's selected aspect ratio. Supported choices are only `9:16（竖屏）`, `16:9（横屏）`, and `21:9（电影）`; 默认 16:9 when the user says default. Do not offer `1:1` or `4:5`.

New formal copy-pack gate: if the source feed or user request does not already record camera library and aspect ratio, stop before writing copy packs and ask in chat; legacy material may be marked 需人工确认 only when it predates this gate.

Use this exact chat prompt when camera library, aspect ratio, and production chapter count are all missing: `正式生产参数缺失：请先选择运镜库（小云雀 / libtv）、画幅比例（9:16竖屏 / 16:9横屏 / 21:9电影）和生产章数。检测到文本超过3章，建议先跑3章；你也可以指定 1-5 章、具体章节范围，或明确说全本分批。收到选择前，我不会生成连续投喂稿或复制包。`

Use this exact chat prompt only when production scope is already explicit and camera library or aspect ratio is missing: `正式生产参数缺失：请先选择运镜库（小云雀 / libtv）和画幅比例（9:16竖屏 / 16:9横屏 / 21:9电影）。收到选择前，我不会生成连续投喂稿或复制包。`

## File Location

Write copy-pack files at the user-facing top level under `生产资产`, while source-index, asset-bible, audit reports, and other evidence stay under `生产资产/_内部/`, for example:

```text
生产资产/seedance-copy-packs-production-ch01-05.md
```

## File Shape

```text
# Seedance Copy Packs - ch01-05

## Pack Settings
- Source feed: 生产资产/seedance-all-reference-feed-production-ch01-05.md
- Pack size: 5
- Numbering: preserve original continuous line numbers
- Camera library: 小云雀
- Aspect ratio: 16:9
- Contract: copy convenience only; not pacing or compression

### 投喂包 001｜原始行 1-5

统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。

上传参考图：
- 场景1 = 鬼王宗宗门大殿_母图 = 图片2
- 角色1 = 林夜_黑袍白发宗主造型 = 图片1
- 角色2 = 骨灵教枯瘦老者_骨纹法袍造型 = 图片3
- 道具1 = 万魂幡_单体 = 图片4

音色绑定：
- 音色1 = 林夜.mp3
- 音色2 = 骨灵教枯瘦老者.mp3

1 日 内 鬼王宗宗门大殿 林夜 黑袍白发的林夜面无表情坐在漆黑石椅上，十名魔门首领分坐两侧，冷雾贴地压低 中景 + 轻微低机位 + 王座居中 + 两侧席位 <固定镜头> 环境音：大殿低鸣、衣袖摩擦，无对白
2 日 内 鬼王宗宗门大殿 骨灵教老者 枯瘦老者坐在左侧第二席，正面半身阴沉开口，画面只显示说话人，后景虚化暗柱和席位边缘 中近景 + 正面半身 + 单人主镜头 + 后景虚化 <镜头前推> 骨灵教老者：宗主大人。
3 日 内 鬼王宗宗门大殿 骨灵教老者 老者不改变坐姿，语气平静补上后续安排，骨纹袖口被冷光压住 中近景 + 正面半身 + 单人主镜头 + 袖口细节 <固定镜头> 骨灵教老者：明日一早我就安排弟子将他的皮囊丢到烈阳宗。
4 日 内 鬼王宗宗门大殿 林夜 林夜眼皮子不由自主跳了跳，冷脸差点没绷住，手指在扶手边缘轻轻收紧 近景 + 正面半身 + 面瘫反差 + 扶手细节 <急速变焦> 音效：心跳一顿，无对白
5 日 内 鬼王宗宗门大殿 林夜 林夜维持宗主威严，喉结轻动压住反差表情，殿内冷雾从扶手下方滑过 中近景 + 正面半身 + 克制喜剧反差 <固定镜头> 环境音：冷雾低鸣，无对白
```

Next pack heading:

```text
### 投喂包 002｜原始行 6-10
```

The final pack may contain fewer lines when the source feed line count is not divisible by pack size.

## Heading Grammar

- Heading exact grammar: `### 投喂包 {NNN}｜原始行 {start}-{end}`.
- `NNN` must be zero-padded to three digits and increase by 1 per pack.
- The heading separator is full-width `｜`.
- The heading range must match copied original line numbers.

## Pack Size

- Default pack size: 5.
- User may request a positive integer pack size, such as `每6条一包`, `每8条一包`, or `每10条一包`.
- Recommended range is 5-10, but larger sizes are allowed as copy convenience.
- Never choose pack size from perceived story rhythm or 15-second pacing.

## Numbering

- Preserve original continuous line numbers; do not renumber from 1 inside each pack.
- A heading range must match copied numbered lines, for example `### 投喂包 001｜原始行 1-5` contains lines `1` through `5`.
- The next pack continues with the next original line number.
- Preserve the bracketed camera tag exactly as it appears in the canonical feed. Do not convert `<固定镜头>` back to `固定镜头`.

## Reference Binding

List only references needed by the copied lines:

- `上传参考图：` contains only image or visual references needed by the copied lines: scene references, character references, prop references, interface references, and other visible reference images.
- `音色绑定：` contains voice assets only for speaking characters or source-supported system/OS voices in the pack.
- Voice assets belong under `音色绑定：`, not the image-upload block.

Do not list every global asset in every pack. That recreates the copy burden.

Do not invent references. Use stable asset names and image/voice bindings from source index and asset bible. If evidence is ambiguous, write `需人工确认` with the source-grounded asset name.

When `生产资产/_内部/image-manifest.json` exists, use it for image bindings. Copy packs must not invent image paths. If a visible asset has missing, failed, or blocked manifest status, write `需人工确认（image-generator failed or blocked）`.

Example manifest-aware image binding:

```text
上传参考图：
- 角色1 = 林夜_黑袍造型 = 人设资产/林夜_黑袍造型.png
- 场景1 = 鬼王宗宗门大殿_母图 = 需人工确认（image-generator failed or blocked）
```

In `## Pack Settings`, include `- Camera library: 小云雀` or `- Camera library: libtv` when the selected library is known. If legacy source material does not record the selected library, write `- Camera library: 需人工确认` and keep copied line tags bracketed. For new formal production, stop and ask before writing copy packs.

In `## Pack Settings`, include `- Aspect ratio: 9:16`, `- Aspect ratio: 16:9`, or `- Aspect ratio: 21:9` when the selected ratio is known. If legacy source material does not record the selected ratio, write `- Aspect ratio: 需人工确认`; for new formal production, stop and ask `画幅比例用哪个？默认 16:9。可选：9:16（竖屏）、16:9（横屏）、21:9（电影）。如果你说默认，我就按 16:9。`

## Forbidden Shape

Do not write copy packs as `第N组`, `15秒组`, `分镜组`, `节奏组`, or `呼吸组`. Do not use `segment`, `S01/S02`, `keyframe`, `Canvas`, `MP4`, `首帧`, `尾帧`, `续接`, or `承接`.
