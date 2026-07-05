# Source True Guoman Agent Pack Baseline Design

## Problem

`source-true-guoman` already works as a source-faithful 3D国漫 feed skill, but the current prototype still depends too much on the agent's moment-by-moment judgment. Real projects have heavy source text, delayed reveals, anonymous roles that later become important, recurring locations, outfit changes, and platform-driven trimming pressure. If the skill reads only a small early slice and makes final-sounding asset decisions, later chapters can invalidate those decisions.

The baseline v1 must turn the skill into a small production system: a conservative orchestrator, a source indexer, an asset bible, a faithful feed writer, and a feed auditor. The skill must continue to treat the source as the authority and leave compression decisions to the user.

## Goals

- Preserve the current core contract: 原作多少字就保留多少字, no AI rewriting, no AI compression, and exact source dialogue.
- Add a clear orchestration route for common requests so the main skill chooses the right specialist path.
- Make multi-chapter work start with full requested-scope pre-scan before final asset or feed decisions.
- Make `source-index.md` the working evidence map for characters, scenes, assets, terms, doubts, and evidence anchors.
- Make `asset-bible.md` the reusable production asset plan for images, voices, parent-child references, and collision risks.
- Keep faithful feed output continuous, source-first, and compatible with Xiaoyunque camera tags.
- Add delivery audit rules that catch structure errors, unsupported camera tags, old workflow language, source drift, and asset drift.
- Keep project artifacts in the right workspace folders.

## Non-Goals

- Do not implement automatic story compression.
- Do not make `cut-safety` produce rewritten short versions.
- Do not make `visual-polish` change plot, dialogue, event order, or source actions.
- Do not generate Canvas packages, `segment`, `S01/S02`, keyframes, first/last-frame workflows, storyboard folders, or MP4 claims.
- Do not build a UI, database, vector retrieval system, or external service integration in v1.
- Do not generate the full `E:\xianjie` five-chapter feed as part of the baseline spec implementation; use it as a regression sample after the core workflow is in place.

## Core Contracts

The following rules override all specialist behavior:

- Source fidelity: preserve event order, cause-effect, names, factions, realms, props, locations, reveals, hooks, and load-bearing dialogue.
- Dialogue: use exact source excerpts; do not rewrite, polish, invent, shorten, or move later lines earlier.
- Compression: if the user asks for compression, provide exact cut candidates, removable source spans, or line split points; do not write a compressed replacement.
- Visible staging: do not add standing, walking, kneeling, bowing, weapon drawing, prop raising, prop putting away, seat changes, or reporting unless source evidence supports it.
- Scope: 正式多章任务必须先预扫完整请求范围. 局部烟测必须显式标记已阅读范围. 局部烟测资产不得当作全局定稿.
- Storage: 投喂稿、source-index、asset-bible、审计报告、剪辑风险报告属于生产资产. 视频资产只放最终视频文件或渲染结果.

## Architecture

The skill remains one installed skill folder with progressive disclosure:

- `SKILL.md` is the orchestrator and core contract.
- `agents/*.md` files define specialist behavior.
- `references/*.md` files define output formats, audit lists, and allowed camera tags.
- `scripts/*.py` files perform deterministic checks or workspace setup.
- `tests/test_init_workspace.py` protects textual contracts and scripts.

The v1 route is:

```text
source material
-> source-indexer
-> asset-bible
-> faithful-feed
-> feed-auditor
```

`cut-safety`, `visual-polish`, and `production-runner` stay present as lightweight agents, but v1 does not deepen them beyond ensuring they do not violate the core contracts.

## Orchestrator Requirements

`SKILL.md` must route requests by intent:

- New project directory or root script file: initialize workspace first.
- "Process these chapters", "turn this into feed", or multi-chapter production: run source-indexer, asset-bible, faithful-feed, then feed-auditor.
- "Make an index", "read the source", "track roles", or continuity questions: run source-indexer.
- "Make assets", "who needs images", "avoid face collision", or "what references upload": run asset-bible.
- "Write feed", "video投喂", or "faithful draft": run faithful-feed, requiring source index or full requested pre-scan for multi-chapter work.
- "Review", "check", "audit", or "有没有问题": run feed-auditor.
- "Can I delete", "cut", "trim", or "compress": run cut-safety and refuse to write a rewritten compressed story.
- "Make it look better", "shot variety", or "画面增强": run visual-polish only after faithful coverage exists.
- "Production order", "upload references", or "batch checklist": run production-runner.

The orchestrator must distinguish formal production from local smoke tests. Smoke tests may read a slice, but their artifacts must say the exact read span and cannot present asset decisions as global.

## Source Index Requirements

`source-indexer` must create or update `source-index.md` in production assets unless the user explicitly asks for a visible root-level working index.

The index must include:

- Scope status: `全范围预扫` or `局部烟测`.
- Requested range, read range, unread range, and evidence basis.
- Character entries: names, aliases, first appearance, later appearances, identity/faction, relationships, speaking roles, outfit/state changes, posture facts, and asset bindings.
- Scene entries: mother scene, sub-locations, interior/exterior, material and lighting logic, chapter positions, and parent-child scene relationships.
- Asset entries: character, scene, prop, interface, beast, vehicle, and voice bindings.
- Term entries: sects, realms, techniques, systems, special props, titles, and source spelling drift.
- Doubt entries: likely typos, suspected same assets, contradictions, unresolved reveals, and OCR/ASR/machine-translation issues.
- Evidence anchors for every merge, correction, relationship claim, reveal handling, face reference, scene reference, or reusable asset decision.

For formal multi-chapter work, the index must be based on the whole requested scope before final asset or feed output.

## Asset Bible Requirements

`asset-bible` must produce `asset-bible.md` or a compact asset plan in production assets.

It must include:

- Character asset tiers: `主角/高频配角`, `命名低频角色`, `群像模板`, `一次性背景人`.
- Tri-view requirements for main and high-frequency characters.
- Derived outfit/state requirements with previous face references.
- Similar-character separation anchors for same sect, same uniform, same gender/age band, or similar protagonist styling.
- Scene mother images and sub-location dependencies.
- Prop/interface/beast/vehicle assets only when they carry identity, action, interface, or repeated continuity.
- Voice assets for speaking roles in the requested scope.
- Upload reference purposes: `人脸身份参考`, `旧造型参考`, `避撞脸参考`, `同门服制参考`, `场景母图参考`, `局部场景参考`, `材质风格参考`, `界面风格参考`.

If the index is only a smoke-test slice, `asset-bible` must label all assets as slice-limited.

## Faithful Feed Requirements

`faithful-feed` must output only:

```text
## 资产提示词

## 视频投喂块
```

The video block must start with the exact global requirement line and then continuous numbering from `1` to the end.

Each video line must follow:

```text
序号 日/夜 内/外 具体场景 人物 可见行为画面 镜头概念 运镜 音频/对白
```

Rules:

- Use one visible action target, one main beat, and one Xiaoyunque camera tag per line.
- Use exact source dialogue in source order.
- Split long dialogue only at natural source punctuation into adjacent continuous lines.
- Do not reduce coverage by reducing line count.
- Speaker lines should usually show the speaker in front half-body, medium close, or medium shot with spatial context.
- Micro-performance may only stay within source-supported posture and placement.
- No groups, 15-second pacing blocks, `segment`, `S01/S02`, keyframes, first/last-frame workflow, Canvas package, storyboard folders, or MP4 claims.

For multi-chapter work, faithful-feed must run a private chapter beat ledger before drafting and a coverage audit before delivery.

## Feed Auditor Requirements

`feed-auditor` must lead with blocking issues and cite file/line references when reviewing saved files.

It must check:

- Exact global requirement line.
- Continuous numbering from `1`.
- No group markers or forbidden old workflow terms.
- Xiaoyunque camera tags are from `references/xiaoyunque-tags.md`.
- Dialogue exactness when source is available.
- Dialogue order and setup/reaction continuity.
- Unsourced movement, prop handling, posture changes, reports, attacks, or seat changes.
- Asset name stability.
- No disposable early NPC when later evidence makes them recurring or named.
- Outfit variants preserve face identity references.
- Scene sub-locations bind to mother scenes when continuity depends on it.
- Multi-chapter setup, turning point, result, and hook coverage.
- Scope status is explicit when the artifact is a smoke test.

The script `scripts/validate_feed.py` should cover deterministic structure checks. Human/agent audit text should cover source and asset fidelity that scripts cannot reliably infer.

## Workspace Artifact Policy

The workspace has these folders:

- `剧本资产`: source scripts.
- `生产资产`: text production artifacts, including `source-index.md`, `asset-bible.md`, feed drafts, audit reports, cut-risk reports, and production checklists.
- `人设资产`: generated character images.
- `场景资产`: generated scene images.
- `道具资产`: generated prop/interface images.
- `音色资产`: voice assets.
- `视频资产`: final video files or rendered video results only.

`scripts/init_workspace.py` must keep root project folders clean and must not overwrite archived source scripts.

## Validation Strategy

Tests must protect:

- Workspace initialization creates required folders and archives root source scripts safely.
- Main skill declares agent routing.
- Each agent repeats the non-overridable source-faithfulness contract.
- Scope policy appears in orchestrator, source-indexer, asset-bible, faithful-feed, and source-index format.
- Storage policy appears in orchestrator and faithful-feed.
- `validate_feed.py` rejects group markers, invalid camera tags, missing global requirement, forbidden old workflow terms, and broken numbering.
- `validate_feed.py` accepts a valid continuous feed.

Skill validation must run with UTF-8 on Windows:

```powershell
$env:PYTHONUTF8='1'; python C:\Users\Administrator\.codex\skills\.system\skill-creator\scripts\quick_validate.py E:\source-true-guoman
```

## Rollout Plan

Phase 1: Baseline contracts and routing

- Keep the current agent-pack prototype.
- Tighten orchestrator route rules.
- Keep `cut-safety`, `visual-polish`, and `production-runner` lightweight.

Phase 2: Source index and asset bible depth

- Deepen `source-indexer.md` and `references/source-index-format.md`.
- Deepen `asset-bible.md` and `references/asset-bible-format.md`.
- Use `E:\xianjie` five chapters as a regression sample after rules are implemented.

Phase 3: Auditor depth

- Expand `feed-auditor.md` and `references/audit-checklist.md`.
- Extend `scripts/validate_feed.py` only for deterministic checks.
- Add tests for every new deterministic validator behavior.

Phase 4: Controlled expansion

- Deepen `cut-safety` only as a delete-risk assistant, not a compressor.
- Deepen `visual-polish` only after faithful coverage exists.
- Deepen `production-runner` for production-order checklists and upload-reference dependencies.

## Acceptance Criteria

Baseline v1 is ready when:

- A formal multi-chapter request routes to source-indexer, asset-bible, faithful-feed, and feed-auditor.
- A smoke test artifact clearly states it is a smoke test and lists read/unread scope.
- `source-index.md` can represent evidence-backed continuity decisions.
- `asset-bible.md` can represent stable reusable asset decisions and reference dependencies.
- A feed draft stays continuous, source-faithful, and Xiaoyunque-tag valid.
- The auditor can identify both deterministic format problems and non-deterministic source-fidelity risks.
- All tests pass and skill validation passes.
