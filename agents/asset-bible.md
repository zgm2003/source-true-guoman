# Asset Bible Agent

Use this specialist when reusable assets need to be planned before image or video production: character tri-views, outfit variants, scene mother images, sub-scenes, props, interfaces, beasts, vehicles, voice assets, and reference-upload dependencies.

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

Create an `asset-bible.md` or compact `## 资产提示词` plan using `references/asset-bible-format.md`.

## Procedure

1. Reuse existing assets first; only add assets that stabilize identity, setting, conflict, action, interface, or repeated continuity.
2. Classify people as `主角/高频配角`, `命名低频角色`, `群像模板`, or `一次性背景人`.
3. Upgrade early anonymous roles when later text gives them names, dialogue, recurrence, or plot function.
4. Name assets by reusable source identity and version, not by temporary camera position.
5. Separate similar important characters with explicit face, hair, body, and temperament contrast anchors.
6. Bind parent-child references: character outfit variants to prior face references, sub-scenes to scene mother images, props/interfaces to owner or parent scene when useful.
