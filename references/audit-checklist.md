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
- Each video line uses exactly one selected-library camera tag wrapped in angle brackets, optionally followed by parentheses, e.g. `<镜头前推>（压迫靠近）`.
- No bare camera-library terms such as `固定镜头` or `镜头前推` appear as the video-line `运镜` value.
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
- Image QA gate: confirm `全局风格基准图` exists as an 环境风格基准 and dependent images follow `非Q版、非玩具感、非卡通低龄化，成熟3D国漫`.
- Confirm reference-dependent jobs used 真实上传/编码参考图; prompt-only reference is forbidden.
- Confirm character with identity props remains a character asset, for example `鬼财神_财神殿执掌者铁算盘造型` stays under `人设资产`.
- Confirm Asset family: `天机一型手机_三视图` is reused by phone UI variants and keeps body, camera, border, screen ratio, and material consistent.

## Commercial-Upgrade Audit

- Run a commercial-upgrade audit when output may inherit commercial workflow residue or multi-agent asset drift.
- identity drift: recurring people, aliases, and later names stay merged by source evidence.
- standard-name drift: production names follow the evidence-backed standard name.
- period/state drift: age, state, outfit, injury, face, and faction changes have local source evidence.
- source-span coverage: requested spans keep setup, reactions, reveals, transitions, and hooks.
- local continuity: each line preserves the previous visible state, speaker, prop possession, and scene.
- physicalization safety: motion and prop handling stay source-supported or direct consequence.
- prompt contamination: remove copied commercial boilerplate, instruction games, fixed refusal text, tool side effects, silent source replacement, fixed-duration packaging, and rewrite formulas.
