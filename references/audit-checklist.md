# Feed Audit Checklist

Use this checklist when reviewing a source-true-guoman feed.

## Output Style

- Blocking issues first.
- Cite file/line references for every concrete saved-file issue.
- Separate script-deterministic checks from human/agent source-fidelity checks.
- If source text is unavailable, mark human/agent source-fidelity checks as unverified rather than passing.

## Script-Deterministic Checks

- Exact global line appears immediately under `## 视频投喂块`.
- Numbering starts at `1` and stays continuous.
- No groups, old workflow terms, storyboard folder language, Canvas package, or MP4 claim.
- No `segment`, `S01/S02`, keyframe language, `首帧`, `尾帧`, `续接`, or `承接`.
- Each video line uses exactly one Xiaoyunque raw tag, optionally followed by parentheses.
- Check that scope status is explicit when the artifact is a smoke test.

## Human/Agent Source-Fidelity Checks

- Dialogue is exact source text, in source order and local context.
- Long dialogue is split only at natural source punctuation, not shortened.
- Events preserve cause-effect, reveal order, and chapter hooks.
- No unsourced movement, prop handling, reporting, attacks, standing, walking, kneeling, bowing, weapon drawing, seat changes, or scene exits.

## Asset Checks

- Asset names are stable source identities and versions.
- Later-named recurring NPCs are not split from earlier anonymous appearances.
- Outfit variants preserve face references and identity marks.
- Similar important characters have separation anchors.
- Sub-scenes bind to scene mother images when continuity depends on it.
- Speaking roles have voice assets when voice continuity matters.
