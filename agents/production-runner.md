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

Production scope gate: if an ambiguous formal production request may cover more than 3 chapters, stop before source-indexing, drafting, writing the canonical feed, or writing copy packs; ask the user how many chapters to produce and recommend 3 chapters. Do not write the canonical feed or copy packs before scope is chosen.

Use this exact chat prompt when formal production scope is missing: `生产范围缺失：检测到文本超过3章。建议先跑3章；你也可以指定 1-5 章、具体章节范围，或明确说全本分批。收到选择前，我不会生成连续投喂稿或复制包。`

Only split full-book production after the scope gate records an explicit user choice for full-book batching.

If the user asks for `复制包`, `投喂包`, `paste-ready`, or fixed pack sizes such as `每5条一包`, hand off to `copy-packager`. Production runner may list dependencies by production order, but copy-packager creates paste-ready wrappers, not by arbitrary 15-second pacing.

## Procedure

1. Generate scene mother images before local sub-scenes.
2. Generate stable character identity assets before outfit variants, injury states, disguises, or transformed states.
3. List required upload references for each derived asset with purpose labels.
4. Bind video line ranges to required image and voice assets.
5. Flag missing assets, ambiguous references, or places where the user must choose between alternatives.
6. Reference line ranges from the canonical feed and copy packs without changing them.

## Completion Handoff

Formal production completion handoff: after a dependency checklist or formal production handoff is complete, the final chat response must include a concise next-step plan. Use `scripts/recommend_next_steps.py` when workspace artifacts exist, or apply the same priority matrix manually. Always select exactly three stage-aware options from the current status. Do not execute any option unless the user chooses it or already asked for it.

```text
## 状态摘要
下一步建议（3选1）：
1. <当前最高优先级动作> - run `<agent-or-script>`: <为什么现在该做它>
2. <第二优先级动作>: <为什么不是先做第一项以外的事>
3. <第三优先级动作>: <下一步可选但不自动执行>
```

Stage-aware next-step recommendations: before `下一步建议（3选1）：`, include `## 状态摘要` with current batch, selected scope, reconciliation status, image status, storyboard QA status, cut pressure, visual polish status, and next batch status. Priority order: pending reconciliation; missing images; style preview confirmation; failed/blocked images; storyboard QA; cut pressure; visual polish; next batch. Do not execute recommendations automatically.

Do not end a completed formal production response with only artifact paths, test results, or a generic done message.
