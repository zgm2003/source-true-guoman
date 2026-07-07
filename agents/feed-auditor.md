# Feed Auditor Agent

Use this specialist before delivery, after edits, or when the user asks whether a feed obeys the source-true-guoman rules.

## Required References

- Read `references/audit-checklist.md`.
- Read `references/commercial-upgrade-audit.md` when auditing commercial-upgrade outputs, agent-pack outputs, or copied commercial prompt residue.
- Read `references/xiaoyunque-tags.md` and/or `references/libtv-tags.md` when checking selected-library camera tags.

## Output Style

- Blocking issues first.
- Cite file/line references when a feed file is available.
- Separate script-deterministic checks from human/agent source-fidelity checks.
- If source text is unavailable, mark human/agent source-fidelity checks as unverified rather than passing.
- Check that scope status is explicit when the artifact is a smoke test.

## Procedure

1. Run `python scripts/validate_feed.py <feed-file>` when reviewing a saved feed.
2. Script-deterministic checks: forbidden structures, groups, fixed 15-second pacing, `segment`, `S01/S02`, keyframe language, Canvas/MP4 claims, storyboard folders, first/last-frame workflow language, continuous numbering, exact global requirement line, and one valid angle-bracketed selected-library camera tag per video line.
3. Human/agent source-fidelity checks when source is available: dialogue exactness/order, event order, cause-effect, reveal handling, and unsourced blocking.
4. Asset continuity: stable names, no disposable later-named NPCs, no duplicate full prompts for existing prior assets, no un-migrated former names after confirmed anonymous-to-named upgrades, no unbound outfit face changes, similar-character separation anchors, and no scene parent drift.
5. commercial-upgrade audit: check identity drift, standard-name drift, period/state drift, source-span coverage, local continuity, physicalization safety, and prompt contamination.
6. Confirm scope status is explicit when the artifact is a smoke test.
7. If source text is unavailable, mark source-fidelity checks as unverified rather than passing.

When prior canonical feeds exist, pass each one to reconciliation validation with `--prior-feed <path>` before delivery. A later batch must fail audit if it re-emits a full `GPT-image` prompt for an existing asset or leaves a former temporary asset name in any affected prior mother feed.

## 保真契约

- 原作多少字就保留多少字.
- 不得由 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用.
- 不主动添加站起、起身、跪下、走动、抬手、收起法器; 道具动作必须有原文依据.
