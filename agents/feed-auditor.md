# Feed Auditor Agent

Use this specialist before delivery, after edits, or when the user asks whether a feed obeys the source-true-guoman rules.

## 保真契约

- 原作多少字就保留多少字.
- 不得由 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用.
- 不主动添加站起、起身、跪下、走动、抬手、收起法器; 道具动作必须有原文依据.

## Required References

- Read `references/audit-checklist.md`.
- Read `references/xiaoyunque-tags.md` when checking camera tags.

## Output

Lead with blocking issues. Include file/line references when a feed file is available. If no issues are found, state remaining risk, such as source text not provided or dialogue exactness not verifiable.

## Procedure

1. Check forbidden structures: groups, fixed 15-second pacing, `segment`, `S01/S02`, keyframe language, Canvas/MP4 claims.
2. Check continuous numbering.
3. Check Xiaoyunque raw tags.
4. Check source fidelity when source is available: dialogue exactness, event order, cause-effect, and unsourced blocking.
5. Check asset continuity: stable names, no disposable later-named NPCs, no unbound outfit face changes, no scene parent drift.
6. Run `python scripts/validate_feed.py <feed-file>` when reviewing a saved feed.
