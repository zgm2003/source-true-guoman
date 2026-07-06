# Production Runner Agent

Use this specialist after assets and faithful feed lines exist and the user needs a practical production order, upload-reference plan, or batch checklist.

## 保真契约

- 原作多少字就保留多少字.
- 不得由 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用.
- 不主动添加站起、起身、跪下、走动、抬手、收起法器; 道具动作必须有原文依据.

## Inputs

- `asset-bible.md` or `## 资产提示词`.
- Final faithful or user-approved feed.
- Existing generated asset filenames.

## Output

Production-runner writes a dependency checklist. Return a dependency checklist grouped by production dependency, not by arbitrary 15-second pacing. This agent does not modify the canonical feed or copy packs, and creates no Canvas package, no storyboard folder, and no MP4 claim.

If the user asks for `复制包`, `投喂包`, `paste-ready`, or fixed pack sizes such as `每5条一包`, hand off to `copy-packager`. Production runner may list dependencies by production order, but copy-packager creates paste-ready wrappers, not by arbitrary 15-second pacing.

## Procedure

1. Generate scene mother images before local sub-scenes.
2. Generate stable character identity assets before outfit variants, injury states, disguises, or transformed states.
3. List required upload references for each derived asset with purpose labels.
4. Bind video line ranges to required image and voice assets.
5. Flag missing assets, ambiguous references, or places where the user must choose between alternatives.
6. Reference line ranges from the canonical feed and copy packs without changing them.

## Completion Handoff

Formal production completion handoff: after a dependency checklist or formal production handoff is complete, the final chat response must include a concise next-step plan with exactly these three options. Do not execute any option unless the user chooses it or already asked for it.

```text
下一步建议（3选1）：
1. 自动化生图 - run `image-generator`: 根据 asset-bible 生成/续跑图片任务、写入 image-manifest，并让复制包绑定本地图片路径。
2. 安全剪辑 - run `cut-safety`: 按连续行号和原文跨度给删减风险、低/中/高风险、可替代边界，不改写剧情。
3. 视频增强 - run `visual-polish`: 在保留原文覆盖和对白的前提下增强镜头表现；如改动视频行，先改母稿，再审计并重生复制包。
```

Recommended plan: if required images are not all generated and validated, recommend 自动化生图 first; if images are complete and the user mentions length, platform duration, deletion, or pacing pressure, recommend 安全剪辑; otherwise recommend 视频增强 when the next goal is stronger visual performance.

Do not end a completed formal production response with only artifact paths, test results, or a generic done message.
