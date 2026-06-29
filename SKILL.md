---
name: source-true-guoman
description: Use when turning Chinese web-novel chapters, excerpts, scripts, or rough story material into source-faithful 3D国漫 short-video production text, especially when the output needs reusable character/scene/prop/voice assets, lightweight feed blocks, original dialogue preservation, Xiaoyunque camera tags, and no Canvas, keyframe, segment, or MP4 workflow.
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

1. Read only the requested source scope.
2. Build a private source fact sheet: characters, locations, event order, cause-effect, source terms, key dialogue, reveal order, hook.
3. Build an asset ledger: existing reusable assets first, new assets only when they drive identity, setting, conflict, action, interface, or repeated continuity.
4. Draft shots internally: one video line = one visible action target, one main emotion or beat, one camera movement.
5. Emit only the final package:
   - `## 资产提示词`
   - `## 视频投喂块`
6. Before delivery, check source fidelity, dialogue load, asset reuse, Xiaoyunque raw tags, and line weight.

Read `references/format.md` before writing final feed blocks. Read `references/xiaoyunque-tags.md` whenever choosing the `运镜` field.

## Source fidelity

Priority order:

1. event order and cause-effect
2. character motive and stance
3. source names, factions, realms, props, locations
4. key reveals and chapter hook
5. load-bearing dialogue

Dialogue compression:

- Keep short source dialogue exact when it carries plot, identity, threat, comedy, or hook.
- For long dialogue, keep the source subject, object, result, special terms, and strongest conflict clause.
- Delete filler, repeated explanation, and process detail first.
- Do not delete the target of an action, the result, the named term, or the爽点 just to shorten a line.
- If the user requests exact OS/dialogue, add more video lines instead of cramming the line.

## Asset rules

Use assets to stabilize identity, not to decorate every object.

- Character: one white/light-gray background tri-view image; far-left upper-body + head detail, plus front/side/back full body. Lock one face, hairstyle, body, costume, and identity marks.
- Scene: empty location reference. Separate interior/exterior and materially different rooms; do not reuse an exterior for an interior shot.
- Prop/interface: create a clean single-subject product shot only for high-value props or interfaces. If phone orientation matters, make the prompt explicitly `正面屏幕朝镜头` or create a separate front-screen reference; do not force one asset to solve both front and back.
- Voice: bind voice assets only for characters who speak in that group.
- Reuse: when the user provides existing images or earlier generated assets, write `沿用图片N` or bind the existing filename; do not regenerate identity assets unless asked.

## Shot writing rules

Final video lines must describe what is visible in the frame. Keep them light.

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
音色：按本组必要对白匹配角色年龄、身份和情绪；没有对白的组不要新增旁白。必要对白只保留本组逐条文本里的短句。
音色资产：角色音色=文件名.mp3。
统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。
```

If there is no dialogue in the group, omit `音色资产`.

## Common mistakes

| Mistake | Fix |
| --- | --- |
| Final feed reads like production guidelines | Move reasoning internal; output lighter video lines |
| Dialogue gets “cleaned” until source flavor disappears | Preserve source names, target, result, threat/comedy clause |
| Every shot overuses positioning rules | Use position only when it prevents a real generation error |
| Phone flips to back camera | Specify `屏幕正面朝镜头` and avoid mixed front/back asset prompts |
| Non-library camera word appears | Replace with exact Xiaoyunque tag from `references/xiaoyunque-tags.md` |
