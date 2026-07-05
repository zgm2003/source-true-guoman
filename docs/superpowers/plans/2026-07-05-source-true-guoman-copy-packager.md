# Source True Guoman Copy Packager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional paste-ready `复制投喂包` output so users can copy small batches with repeated `统一要求` and local `场景/角色/音色` bindings, while the canonical `连续投喂稿` remains continuous, uncompressed, and source-faithful.

**Architecture:** Keep `SKILL.md` as the orchestrator. Add one specialist agent, one format reference, and one separate validator script; copy packs are separate `生产资产` artifacts and never weaken `scripts/validate_feed.py`.

**Tech Stack:** Markdown skill files, Python 3 standard library, existing `scripts/validate_feed.py` helpers, Python `unittest`, and `skill-creator/scripts/quick_validate.py`.

---

## File Structure

- Create: `agents/copy-packager.md`  
  Specialist instructions for producing `复制投喂包` only after source index, asset bible, faithful feed, and feed audit exist.
- Create: `references/copy-pack-format.md`  
  Copy-pack artifact shape, heading contract, default pack-size policy, reference binding rules, and forbidden legacy group vocabulary.
- Create: `scripts/validate_copy_packs.py`  
  Deterministic validator for copy-pack headings, per-pack `统一要求`, continuous original numbering, pack-size counts, forbidden workflow terms, Xiaoyunque tag counts, and optional exact source-feed comparison.
- Modify: `SKILL.md`  
  Route copy-pack requests and make `copy-packager` optional after `feed-auditor`.
- Modify: `references/format.md`  
  Clarify that canonical feed stays `## 资产提示词` + `## 视频投喂块`; copy packs live outside the canonical video block.
- Modify: `agents/production-runner.md`  
  Hand paste-ready batching requests to `copy-packager` instead of creating old groups.
- Modify if stale: `agents/openai.yaml`  
  Mention optional paste-ready copy packs only if current metadata becomes misleading.
- Modify: `tests/test_init_workspace.py`  
  Add text-contract tests and CLI validator tests in the existing `SkillTextRulesTests` class.
- Install sync target after validation: `C:\Users\20931\.codex\skills\source-true-guoman`  
  Replace the installed skill copy from this repo so no stale old skill remains.

---

### Task 1: Route Copy-Pack Requests

**Files:**
- Create: `agents/copy-packager.md`
- Modify: `SKILL.md`
- Test: `tests/test_init_workspace.py`

- [ ] **Step 1: Write the failing tests**

Modify `tests/test_init_workspace.py`.

In `test_agent_pack_references_are_declared_and_routed_from_main_skill`, add:

```python
            "agents/copy-packager.md",
```

In `test_main_skill_routes_common_intents_to_specialists`, add this case before the `Production order` case:

```python
            (
                ("复制包", "投喂包"),
                ("agents/copy-packager.md", "references/copy-pack-format.md"),
            ),
```

In `test_optional_agents_are_guarded_by_prerequisites`, add:

```python
            "Only use `copy-packager` after source index, asset bible, faithful feed, and feed audit exist",
            "copy-packager creates paste-ready wrappers, not pacing groups",
```

Append this method inside `SkillTextRulesTests`:

```python
    def test_copy_packager_contract_preserves_non_compression_and_wrapper_boundary(self) -> None:
        root = Path(__file__).resolve().parents[1]
        agent_path = root.joinpath("agents", "copy-packager.md")

        self.assertTrue(agent_path.is_file())
        agent_text = agent_path.read_text(encoding="utf-8")

        required_phrases = [
            "保真契约",
            "原作多少字就保留多少字",
            "不得由 AI 帮用户压缩",
            "对白必须从原文摘取",
            "复制投喂包",
            "delivery wrapper",
            "not pacing groups",
            "preserve original continuous line numbers",
            "do not renumber each pack from 1",
            "default pack size is 5",
            "do not invent references",
            "references/copy-pack-format.md",
            "scripts/validate_copy_packs.py",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agent_text)
```

- [ ] **Step 2: Run the new tests and verify failure**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_agent_pack_references_are_declared_and_routed_from_main_skill
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_main_skill_routes_common_intents_to_specialists
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_optional_agents_are_guarded_by_prerequisites
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_copy_packager_contract_preserves_non_compression_and_wrapper_boundary
```

Expected: at least one failure mentions missing `agents/copy-packager.md`, missing route, or missing guard text.

- [ ] **Step 3: Create `agents/copy-packager.md`**

Create `agents/copy-packager.md`:

```markdown
# Copy Packager Agent

Use this specialist only after source index, asset bible, faithful feed, and feed audit exist, and the user needs paste-ready `复制投喂包` output such as `每5条一包`, `投喂包`, `paste-ready`, `分包方便复制`, `不用每次复制统一要求`, or `场景1= / 角色1= / 音色1=`.

## 保真契约

- 原作多少字就保留多少字.
- 不得由 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用.
- 不主动添加站起、起身、跪下、走动、抬手、收起法器; 道具动作必须有原文依据.

## Boundary

`复制投喂包` is a delivery wrapper around existing continuous feed lines. It is not the canonical story order, not pacing groups, not a 15-second workflow, and not permission to compress source content.

The canonical source truth remains the `连续投喂稿`: `## 视频投喂块`, one global `统一要求`, and continuous numbering from `1` to the end.

## Required References

- Read `references/copy-pack-format.md` before writing any copy-pack artifact.
- Read `references/format.md` only to confirm the canonical faithful feed shape and exact `统一要求` line.
- Read `references/xiaoyunque-tags.md` only when checking that copied video lines still contain one valid raw tag.

## Inputs

- Faithful feed file or final faithful feed text.
- `生产资产/source-index.md` or equivalent source index.
- `生产资产/asset-bible.md` or equivalent asset bible.
- Feed audit result or saved audit report.
- Existing image and voice filenames or image numbers when available.

If source index, asset bible, faithful feed, or feed audit is missing, stop and ask to run `source-indexer -> asset-bible -> faithful-feed -> feed-auditor` first. Do not invent references to fill the gap.

## Output

Write a separate copy-pack artifact under `生产资产`, for example:

```text
生产资产/seedance-copy-packs-production-ch01-05.md
```

Do not insert copy packs into `## 视频投喂块` and do not change the faithful feed file just because copy packs were requested.

## Procedure

1. Confirm the faithful feed already passed source-fidelity and deterministic feed checks.
2. Detect pack size from explicit user text such as `每6条一包`; otherwise default pack size is 5.
3. Split by mechanical numbered feed lines only. Do not pick boundaries from story rhythm, shot breathing, dialogue length, or perceived 15-second pacing.
4. For every pack, preserve original continuous line numbers. Do not renumber each pack from 1.
5. Repeat the exact `统一要求` line inside every pack.
6. Collect only visible dependencies needed by the copied lines: scene, visible characters, props/interfaces, and speaking voices.
7. Use stable asset names and existing image or voice bindings from source index and asset bible.
8. If a needed binding is ambiguous, write `需人工确认` with the stable source-grounded name. Do not invent a new image, voice, scene, or character reference.
9. Keep each copied video line text unchanged. The packager may duplicate wrapper metadata, but it must not alter source content.
10. After saving the artifact, run `python scripts/validate_copy_packs.py <copy-pack-file> --source-feed <feed-file> --pack-size <N>` when a source feed file is available.

## Output Discipline

Use `投喂包` wording, not `第N组`, `15秒组`, `分镜组`, `节奏组`, or `呼吸组`.

Every pack should be paste-ready, but compact. Do not list every global asset in every pack. List only references the user needs to paste that pack.
```

- [ ] **Step 4: Update `SKILL.md`**

In `## Workflow`, after the delivery-check step, add:

```markdown
15. If the user explicitly asks for paste-ready copy packs, run `copy-packager` after the faithful feed and audit exist; keep copy packs in a separate `生产资产` artifact.
```

Under `## Agent pack routing`, add:

```markdown
- "复制包", "投喂包", "paste-ready", "每5条一包", "分包方便复制", "不用每次复制统一要求", or "场景1= / 角色1= / 音色1=": read `agents/copy-packager.md` and `references/copy-pack-format.md` only after source index, asset bible, faithful feed, and feed audit exist. Run `python scripts/validate_copy_packs.py <copy-pack-file> --source-feed <feed-file> --pack-size <N>` after saving the artifact.
```

Change:

```markdown
Default first-phase route for long projects: `source-indexer -> asset-bible -> faithful-feed -> feed-auditor`.
```

to:

```markdown
Default first-phase route for long projects: `source-indexer -> asset-bible -> faithful-feed -> feed-auditor`; optional `-> copy-packager` only when paste-ready copy packs are requested.
```

In the optional-agent guard paragraph, append:

```markdown
Only use `copy-packager` after source index, asset bible, faithful feed, and feed audit exist; copy-packager creates paste-ready wrappers, not pacing groups.
```

- [ ] **Step 5: Run routing tests again**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_agent_pack_references_are_declared_and_routed_from_main_skill
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_main_skill_routes_common_intents_to_specialists
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_optional_agents_are_guarded_by_prerequisites
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_copy_packager_contract_preserves_non_compression_and_wrapper_boundary
```

Expected: all commands report `OK`.

- [ ] **Step 6: Commit**

```bash
git add tests/test_init_workspace.py agents/copy-packager.md SKILL.md
git commit -m "feat: route source true guoman copy packager"
```

---

### Task 2: Document Copy-Pack Format And Canonical Boundary

**Files:**
- Create: `references/copy-pack-format.md`
- Modify: `references/format.md`
- Modify: `agents/production-runner.md`
- Test: `tests/test_init_workspace.py`

- [ ] **Step 1: Write the failing tests**

Append these methods inside `SkillTextRulesTests`:

```python
    def test_copy_pack_format_defines_paste_ready_wrapper_shape(self) -> None:
        root = Path(__file__).resolve().parents[1]
        reference_path = root.joinpath("references", "copy-pack-format.md")

        self.assertTrue(reference_path.is_file())
        reference_text = reference_path.read_text(encoding="utf-8")

        required_phrases = [
            "# Copy Pack Format",
            "复制投喂包",
            "delivery wrapper",
            "not pacing groups",
            "Pack size: 5",
            "### 投喂包 001｜原始行 1-5",
            "preserve original continuous line numbers",
            "do not renumber from 1 inside each pack",
            "上传参考图：",
            "场景1 =",
            "角色1 =",
            "音色1 =",
            "需人工确认",
            "Do not invent references",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, reference_text)

    def test_canonical_format_keeps_copy_packs_out_of_video_feed(self) -> None:
        root = Path(__file__).resolve().parents[1]
        format_text = root.joinpath("references", "format.md").read_text(
            encoding="utf-8"
        )
        runner_text = root.joinpath("agents", "production-runner.md").read_text(
            encoding="utf-8"
        )

        for phrase in [
            "canonical continuous feed",
            "Copy packs are separate paste-ready artifacts",
            "references/copy-pack-format.md",
            "Do not put `复制投喂包` inside `## 视频投喂块`",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, format_text)

        for phrase in [
            "copy-packager",
            "paste-ready wrappers",
            "not by arbitrary 15-second pacing",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, runner_text)
```

- [ ] **Step 2: Run the new tests and verify failure**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_copy_pack_format_defines_paste_ready_wrapper_shape
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_canonical_format_keeps_copy_packs_out_of_video_feed
```

Expected: failures mention missing `references/copy-pack-format.md` and missing boundary phrases.

- [ ] **Step 3: Create `references/copy-pack-format.md`**

Create `references/copy-pack-format.md`:

```markdown
# Copy Pack Format

Use this file when `copy-packager` creates a separate paste-ready `复制投喂包` artifact.

## Boundary

A `复制投喂包` is a delivery wrapper around existing faithful feed lines. It is not the canonical feed, not pacing groups, not a 15-second plan, and not a source transform.

The canonical source truth remains the `连续投喂稿`: `## 视频投喂块`, one global `统一要求`, and continuous numbering from `1` to the end.

## File Location

Write copy-pack files under `生产资产`, for example:

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
- Contract: copy convenience only; not pacing or compression

### 投喂包 001｜原始行 1-5

统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。

上传参考图：
- 场景1 = 鬼王宗宗门大殿_母图 = 图片2
- 角色1 = 林夜_黑袍白发宗主造型 = 图片1
- 角色2 = 骨灵教枯瘦老者_骨纹法袍造型 = 图片3
- 道具1 = 万魂幡_单体 = 图片4
- 音色1 = 林夜.mp3
- 音色2 = 骨灵教枯瘦老者.mp3

1 日 内 鬼王宗宗门大殿 林夜 黑袍白发的林夜面无表情坐在漆黑石椅上，十名魔门首领分坐两侧，冷雾贴地压低 中景 + 轻微低机位 + 王座居中 + 两侧席位 固定镜头 环境音：大殿低鸣、衣袖摩擦，无对白
2 日 内 鬼王宗宗门大殿 骨灵教老者 枯瘦老者坐在左侧第二席，正面半身阴沉开口，画面只显示说话人，后景虚化暗柱和席位边缘 中近景 + 正面半身 + 单人主镜头 + 后景虚化 镜头前推 骨灵教老者：宗主大人。
3 日 内 鬼王宗宗门大殿 骨灵教老者 老者不改变坐姿，语气平静补上后续安排，骨纹袖口被冷光压住 中近景 + 正面半身 + 单人主镜头 + 袖口细节 固定镜头 骨灵教老者：明日一早我就安排弟子将他的皮囊丢到烈阳宗。
4 日 内 鬼王宗宗门大殿 林夜 林夜眼皮子不由自主跳了跳，冷脸差点没绷住，手指在扶手边缘轻轻收紧 近景 + 正面半身 + 面瘫反差 + 扶手细节 急速变焦 音效：心跳一顿，无对白
5 日 内 鬼王宗宗门大殿 林夜 林夜维持宗主威严，喉结轻动压住反差表情，殿内冷雾从扶手下方滑过 中近景 + 正面半身 + 克制喜剧反差 固定镜头 环境音：冷雾低鸣，无对白
```

Next pack heading:

```text
### 投喂包 002｜原始行 6-10
```

The final pack may contain fewer lines when the source feed line count is not divisible by pack size.

## Pack Size

- Default Pack size: 5.
- User may request a positive integer pack size, such as `每6条一包`, `每8条一包`, or `每10条一包`.
- Recommended range is 5-10, but larger sizes are allowed as copy convenience.
- Never choose pack size from perceived story rhythm or 15-second pacing.

## Numbering

- Preserve original continuous line numbers.
- Do not renumber from 1 inside each pack.
- A heading range must match copied numbered lines, for example `### 投喂包 001｜原始行 1-5` contains lines `1` through `5`.
- The next pack continues with the next original line number.

## Reference Binding

List only references needed by the copied lines:

- Scene references visible in the pack.
- Character references for primary visible characters and named visible supporting roles.
- Prop or interface references only when the copied lines need them.
- Voice assets only for speaking characters or source-supported system/OS voices in the pack.

Do not list every global asset in every pack. That recreates the copy burden.

Do not invent references. Use stable asset names and image/voice bindings from source index and asset bible. If evidence is ambiguous, write `需人工确认` with the source-grounded asset name.

## Forbidden Shape

Do not write copy packs as `第N组`, `15秒组`, `分镜组`, `节奏组`, or `呼吸组`. Do not use `segment`, `S01/S02`, `keyframe`, `Canvas`, `MP4`, `首帧`, `尾帧`, `续接`, or `承接`.
```

- [ ] **Step 4: Update `references/format.md`**

After the paragraph that starts `Use continuous numbering only`, add:

```markdown
This is the canonical continuous feed. Copy packs are separate paste-ready artifacts described in `references/copy-pack-format.md`; they may repeat `统一要求` and local reference bindings for user convenience, but they must never be placed inside `## 视频投喂块`. Do not put `复制投喂包` inside `## 视频投喂块`.
```

- [ ] **Step 5: Update `agents/production-runner.md`**

Under `## Output`, add:

```markdown
If the user asks for `复制包`, `投喂包`, `paste-ready`, or fixed copy counts such as `每5条一包`, hand off to `copy-packager`. Production runner may list dependencies by production order, but copy-packager creates paste-ready wrappers, not by arbitrary 15-second pacing.
```

- [ ] **Step 6: Run format-boundary tests again**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_copy_pack_format_defines_paste_ready_wrapper_shape
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_canonical_format_keeps_copy_packs_out_of_video_feed
```

Expected: both commands report `OK`.

- [ ] **Step 7: Commit**

```bash
git add tests/test_init_workspace.py references/copy-pack-format.md references/format.md agents/production-runner.md agents/copy-packager.md
git commit -m "feat: document source true guoman copy packs"
```

---

### Task 3: Add Copy-Pack Validator

**Files:**
- Create: `scripts/validate_copy_packs.py`
- Test: `tests/test_init_workspace.py`

- [ ] **Step 1: Write validator tests**

Append these methods inside `SkillTextRulesTests`:

```python
    def test_validate_copy_packs_accepts_valid_five_line_pack_file(self) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_pack = Path(temp_dir) / "copy-packs.md"
            copy_pack.write_text(
                "\n".join(
                    [
                        "# Seedance Copy Packs - ch01",
                        "## Pack Settings",
                        "- Pack size: 5",
                        "### 投喂包 001｜原始行 1-5",
                        requirement,
                        "上传参考图：",
                        "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                        "- 角色1 = 林夜_黑袍造型 = 图片1",
                        "- 音色1 = 林夜.mp3",
                        "1 日 内 鬼王宗宗门大殿 林夜 坐在黑石王座上 中景 + 平视 固定镜头 环境音：低鸣",
                        "2 日 内 鬼王宗宗门大殿 骨灵教老者 正面半身开口 中近景 + 平视 镜头前推 骨灵教老者：宗主大人。",
                        "3 日 内 鬼王宗宗门大殿 骨灵教老者 不改变坐姿继续说话 中近景 + 正面半身 固定镜头 骨灵教老者：明日一早。",
                        "4 日 内 鬼王宗宗门大殿 林夜 眼皮轻跳 近景 + 正面半身 急速变焦 音效：心跳一顿",
                        "5 日 内 鬼王宗宗门大殿 林夜 压住反差表情 中近景 + 正面半身 固定镜头 环境音：冷雾低鸣",
                        "### 投喂包 002｜原始行 6-7",
                        requirement,
                        "上传参考图：",
                        "- 场景1 = 鬼王宗宗门大殿_母图 = 图片2",
                        "6 日 内 鬼王宗宗门大殿 林夜 抬眼看向殿中 中景 + 平视 镜头前推 环境音：衣袖轻响",
                        "7 日 内 鬼王宗宗门大殿 群魔 殿内众人压低视线 远景 + 两侧席位 固定镜头 环境音：大殿低鸣",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(root / "scripts" / "validate_copy_packs.py"), str(copy_pack), "--pack-size", "5"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Copy-pack validation passed", result.stdout)

    def test_validate_copy_packs_rejects_missing_requirement_per_pack(self) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_pack = Path(temp_dir) / "missing-requirement.md"
            copy_pack.write_text(
                "\n".join(
                    [
                        "### 投喂包 001｜原始行 1-2",
                        requirement,
                        "1 日 内 大殿 林夜 坐在王座上 中景 + 平视 固定镜头 环境音：低鸣",
                        "2 日 内 大殿 林夜 抬眼 中景 + 平视 镜头前推 环境音：衣袖轻响",
                        "### 投喂包 002｜原始行 3-3",
                        "上传参考图：",
                        "- 角色1 = 林夜_黑袍造型 = 图片1",
                        "3 日 内 大殿 林夜 表情微顿 近景 + 正面半身 急速变焦 音效：心跳一顿",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(root / "scripts" / "validate_copy_packs.py"), str(copy_pack), "--pack-size", "2"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("pack 002 missing global requirement line", result.stdout)

    def test_validate_copy_packs_rejects_reset_duplicate_or_missing_numbers(self) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_pack = Path(temp_dir) / "bad-numbering.md"
            copy_pack.write_text(
                "\n".join(
                    [
                        "### 投喂包 001｜原始行 1-2",
                        requirement,
                        "1 日 内 大殿 林夜 坐在王座上 中景 + 平视 固定镜头 环境音：低鸣",
                        "2 日 内 大殿 林夜 抬眼 中景 + 平视 镜头前推 环境音：衣袖轻响",
                        "### 投喂包 002｜原始行 3-4",
                        requirement,
                        "1 日 内 大殿 林夜 错误重置编号 近景 + 正面半身 急速变焦 音效：心跳一顿",
                        "4 日 内 大殿 群魔 压低视线 远景 + 两侧席位 固定镜头 环境音：低鸣",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(root / "scripts" / "validate_copy_packs.py"), str(copy_pack), "--pack-size", "2"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("heading range 3-4 does not match numbered lines 1,4", result.stdout)
            self.assertIn("duplicate original line 1", result.stdout)
            self.assertIn("expected original line 3, got 1", result.stdout)
```

- [ ] **Step 2: Run validator tests and verify failure**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_validate_copy_packs_accepts_valid_five_line_pack_file
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_validate_copy_packs_rejects_missing_requirement_per_pack
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_validate_copy_packs_rejects_reset_duplicate_or_missing_numbers
```

Expected: failures mention missing `scripts/validate_copy_packs.py`.

- [ ] **Step 3: Create `scripts/validate_copy_packs.py`**

Create `scripts/validate_copy_packs.py`:

```python
#!/usr/bin/env python3
"""Validate source-true-guoman paste-ready copy-pack files."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

try:
    from validate_feed import (
        FORBIDDEN_TERMS,
        GLOBAL_REQUIREMENT,
        GROUP_PATTERNS,
        NUMBERED_LINE_RE,
        line_camera_tags,
        load_camera_tags,
    )
except ImportError:
    from scripts.validate_feed import (
        FORBIDDEN_TERMS,
        GLOBAL_REQUIREMENT,
        GROUP_PATTERNS,
        NUMBERED_LINE_RE,
        line_camera_tags,
        load_camera_tags,
    )


PACK_HEADING_RE = re.compile(r"^### 投喂包 (\d{3})｜原始行 (\d+)-(\d+)$")


@dataclass(frozen=True)
class CopiedLine:
    file_line: int
    number: int
    text: str


@dataclass(frozen=True)
class Pack:
    file_line: int
    index: int
    start: int
    end: int
    body: list[tuple[int, str]]
    copied_lines: list[CopiedLine]


def describe_numbers(numbers: list[int]) -> str:
    if not numbers:
        return "none"
    if len(numbers) <= 8:
        return ",".join(str(number) for number in numbers)
    return f"{numbers[0]}..{numbers[-1]} ({len(numbers)} lines)"


def collect_numbered_lines(lines: list[tuple[int, str]], tags: set[str]) -> tuple[list[CopiedLine], list[str]]:
    copied: list[CopiedLine] = []
    errors: list[str] = []
    for file_line, line in lines:
        stripped = line.strip()
        match = NUMBERED_LINE_RE.match(stripped)
        if not match:
            continue
        copied.append(CopiedLine(file_line, int(match.group(1)), stripped))
        found_tags = line_camera_tags(stripped, tags)
        if len(found_tags) != 1:
            errors.append(f"line {file_line}: invalid camera tag count {len(found_tags)}")
    return copied, errors


def split_packs(lines: list[str], tags: set[str]) -> tuple[list[Pack], list[str]]:
    errors: list[str] = []
    headings: list[tuple[int, re.Match[str]]] = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("### 投喂包"):
            continue
        match = PACK_HEADING_RE.match(stripped)
        if match is None:
            errors.append(f"line {index + 1}: invalid copy-pack heading")
            continue
        headings.append((index, match))

    packs: list[Pack] = []
    for position, (heading_index, match) in enumerate(headings):
        next_heading_index = headings[position + 1][0] if position + 1 < len(headings) else len(lines)
        body = [
            (file_line, body_line)
            for file_line, body_line in enumerate(lines[heading_index + 1 : next_heading_index], start=heading_index + 2)
        ]
        copied_lines, copied_errors = collect_numbered_lines(body, tags)
        errors.extend(copied_errors)
        packs.append(
            Pack(
                file_line=heading_index + 1,
                index=int(match.group(1)),
                start=int(match.group(2)),
                end=int(match.group(3)),
                body=body,
                copied_lines=copied_lines,
            )
        )

    if not headings:
        errors.append("no copy-pack headings found")
    return packs, errors


def load_source_feed_lines(source_feed: Path) -> dict[int, str]:
    source_lines: dict[int, str] = {}
    for line in source_feed.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        match = NUMBERED_LINE_RE.match(stripped)
        if match:
            source_lines[int(match.group(1))] = stripped
    return source_lines


def validate_copy_packs(path: Path, root: Path, pack_size: int, source_feed: Path | None = None) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tags = load_camera_tags(root)
    packs, errors = split_packs(lines, tags)

    for file_line, line in enumerate(lines, start=1):
        stripped = line.strip()
        if any(pattern.search(stripped) for pattern in GROUP_PATTERNS):
            errors.append(f"line {file_line}: group marker is not allowed")
        for forbidden in FORBIDDEN_TERMS:
            if forbidden in stripped:
                errors.append(f"line {file_line}: forbidden term `{forbidden}`")

    expected_pack_index = 1
    expected_original_number: int | None = None
    seen_numbers: set[int] = set()
    all_copied_lines: list[CopiedLine] = []

    for pack_position, pack in enumerate(packs):
        if pack.index != expected_pack_index:
            errors.append(f"line {pack.file_line}: expected pack {expected_pack_index:03d}, got {pack.index:03d}")
        expected_pack_index += 1

        body_text = [line.strip() for _, line in pack.body]
        if GLOBAL_REQUIREMENT not in body_text:
            errors.append(f"line {pack.file_line}: pack {pack.index:03d} missing global requirement line")

        numbers = [copied_line.number for copied_line in pack.copied_lines]
        expected_range = list(range(pack.start, pack.end + 1))
        if numbers != expected_range:
            errors.append(
                f"line {pack.file_line}: heading range {pack.start}-{pack.end} does not match numbered lines {describe_numbers(numbers)}"
            )

        if not numbers:
            errors.append(f"line {pack.file_line}: pack {pack.index:03d} has no numbered video lines")
        elif pack_position < len(packs) - 1 and len(numbers) != pack_size:
            errors.append(f"line {pack.file_line}: pack {pack.index:03d} expected {pack_size} lines, got {len(numbers)}")
        elif pack_position == len(packs) - 1 and len(numbers) > pack_size:
            errors.append(f"line {pack.file_line}: final pack {pack.index:03d} exceeds pack size {pack_size} with {len(numbers)} lines")

        for copied_line in pack.copied_lines:
            if expected_original_number is None:
                expected_original_number = copied_line.number
            if copied_line.number in seen_numbers:
                errors.append(f"line {copied_line.file_line}: duplicate original line {copied_line.number}")
            if copied_line.number != expected_original_number:
                errors.append(
                    f"line {copied_line.file_line}: expected original line {expected_original_number}, got {copied_line.number}"
                )
                expected_original_number = copied_line.number
            seen_numbers.add(copied_line.number)
            expected_original_number += 1
            all_copied_lines.append(copied_line)

    if source_feed is not None:
        source_lines = load_source_feed_lines(source_feed)
        source_numbers = sorted(source_lines)
        copied_numbers = [copied_line.number for copied_line in all_copied_lines]
        if copied_numbers != source_numbers:
            errors.append(
                f"copied line numbers do not match source feed: expected {describe_numbers(source_numbers)}, got {describe_numbers(copied_numbers)}"
            )
        for copied_line in all_copied_lines:
            expected_text = source_lines.get(copied_line.number)
            if expected_text is None:
                errors.append(f"line {copied_line.file_line}: copied line {copied_line.number} not found in source feed")
            elif copied_line.text != expected_text:
                errors.append(f"line {copied_line.file_line}: copied line {copied_line.number} differs from source feed")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate source-true-guoman copy-pack files.")
    parser.add_argument("copy_pack_file", help="Markdown file containing paste-ready copy packs")
    parser.add_argument("--source-feed", help="Canonical faithful feed file to compare copied lines against")
    parser.add_argument("--pack-size", type=int, default=5, help="Expected pack size, default 5")
    args = parser.parse_args()

    if args.pack_size < 1:
        parser.error("--pack-size must be a positive integer")

    root = Path(__file__).resolve().parents[1]
    copy_pack_path = Path(args.copy_pack_file).expanduser().resolve()
    source_feed_path = Path(args.source_feed).expanduser().resolve() if args.source_feed else None
    errors = validate_copy_packs(copy_pack_path, root, args.pack_size, source_feed_path)

    if errors:
        print("Copy-pack validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Copy-pack validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run validator tests again**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_validate_copy_packs_accepts_valid_five_line_pack_file
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_validate_copy_packs_rejects_missing_requirement_per_pack
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_validate_copy_packs_rejects_reset_duplicate_or_missing_numbers
```

Expected: all commands report `OK`.

- [ ] **Step 5: Commit**

```bash
git add tests/test_init_workspace.py scripts/validate_copy_packs.py
git commit -m "feat: add copy pack validator"
```

---

### Task 4: Lock Source Comparison And Forbidden Workflow Terms

**Files:**
- Modify: `tests/test_init_workspace.py`
- Modify if needed: `scripts/validate_copy_packs.py`
- Modify if needed: `SKILL.md`

- [ ] **Step 1: Add source-feed comparison and forbidden-term tests**

Append these methods inside `SkillTextRulesTests`:

```python
    def test_validate_copy_packs_compares_against_source_feed_when_provided(self) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"
        with tempfile.TemporaryDirectory() as temp_dir:
            source_feed = Path(temp_dir) / "feed.md"
            source_feed.write_text(
                "\n".join(
                    [
                        "## 视频投喂块",
                        requirement,
                        "1 日 内 大殿 林夜 坐在王座上 中景 + 平视 固定镜头 环境音：低鸣",
                        "2 日 内 大殿 林夜 抬眼 中景 + 平视 镜头前推 环境音：衣袖轻响",
                    ]
                ),
                encoding="utf-8",
            )
            copy_pack = Path(temp_dir) / "copy-packs.md"
            copy_pack.write_text(
                "\n".join(
                    [
                        "### 投喂包 001｜原始行 1-2",
                        requirement,
                        "1 日 内 大殿 林夜 坐在王座上 中景 + 平视 固定镜头 环境音：低鸣",
                        "2 日 内 大殿 林夜 被错误改写 中景 + 平视 镜头前推 环境音：衣袖轻响",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(root / "scripts" / "validate_copy_packs.py"),
                    str(copy_pack),
                    "--source-feed",
                    str(source_feed),
                    "--pack-size",
                    "2",
                ],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("copied line 2 differs from source feed", result.stdout)

    def test_validate_copy_packs_rejects_legacy_group_and_workflow_terms(self) -> None:
        root = Path(__file__).resolve().parents[1]
        requirement = "统一要求：【不要字幕、不要配乐，只保留环境音、系统提示音、动作音效和必要对白】3D国漫，国风仙侠，轻喜剧反差，角色表演夸张但身份连续，16:9。"
        with tempfile.TemporaryDirectory() as temp_dir:
            copy_pack = Path(temp_dir) / "legacy-copy-packs.md"
            copy_pack.write_text(
                "\n".join(
                    [
                        "### 投喂包 001｜原始行 1-2",
                        requirement,
                        "### 第1组",
                        "segment S01 15秒 Canvas MP4 首帧 尾帧 续接 承接",
                        "1 日 内 大殿 林夜 坐在王座上 中景 + 平视 固定镜头 环境音：低鸣",
                        "2 日 内 大殿 林夜 抬眼 中景 + 平视 镜头前推 环境音：衣袖轻响",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(root / "scripts" / "validate_copy_packs.py"), str(copy_pack), "--pack-size", "2"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("group marker is not allowed", result.stdout)
            self.assertIn("forbidden term `segment`", result.stdout)
            self.assertIn("forbidden term `S01`", result.stdout)
            self.assertIn("forbidden term `Canvas`", result.stdout)
            self.assertIn("forbidden term `MP4`", result.stdout)
            self.assertIn("forbidden term `首帧`", result.stdout)
            self.assertIn("forbidden term `尾帧`", result.stdout)
            self.assertIn("forbidden term `续接`", result.stdout)
            self.assertIn("forbidden term `承接`", result.stdout)

    def test_copy_packager_routes_to_copy_pack_validator(self) -> None:
        root = Path(__file__).resolve().parents[1]
        skill_text = root.joinpath("SKILL.md").read_text(encoding="utf-8")
        agent_text = root.joinpath("agents", "copy-packager.md").read_text(encoding="utf-8")
        validator_path = root.joinpath("scripts", "validate_copy_packs.py")

        self.assertTrue(validator_path.is_file())
        for text in (skill_text, agent_text):
            self.assertIn("scripts/validate_copy_packs.py", text)
            self.assertIn("--pack-size", text)
```

- [ ] **Step 2: Run tests**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_validate_copy_packs_compares_against_source_feed_when_provided
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_validate_copy_packs_rejects_legacy_group_and_workflow_terms
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_copy_packager_routes_to_copy_pack_validator
```

Expected: all commands report `OK`. If `test_copy_packager_routes_to_copy_pack_validator` fails, extend the copy-pack route in `SKILL.md` with the exact command:

```markdown
Run `python scripts/validate_copy_packs.py <copy-pack-file> --source-feed <feed-file> --pack-size <N>` after saving the artifact.
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_init_workspace.py scripts/validate_copy_packs.py SKILL.md agents/copy-packager.md
git commit -m "feat: validate copy pack source and workflow terms"
```

---

### Task 5: Metadata, Full Validation, And Clean Install

**Files:**
- Modify if stale: `agents/openai.yaml`
- Review: `SKILL.md`
- Review: `agents/copy-packager.md`
- Review: `references/copy-pack-format.md`
- Review: `scripts/validate_copy_packs.py`
- Install target: `C:\Users\20931\.codex\skills\source-true-guoman`

- [ ] **Step 1: Refresh `agents/openai.yaml` if needed**

Run:

```bash
Get-Content -Raw -Encoding UTF8 -LiteralPath 'agents\openai.yaml'
```

If the metadata feels stale after copy-pack support, replace it with:

```yaml
interface:
  display_name: "Source True Guoman"
  short_description: "原著保真3D国漫短剧资产、连续投喂稿与复制投喂包"
  default_prompt: "Use $source-true-guoman to turn this novel chapter into source-faithful 3D guoman asset prompts, continuous video feed blocks, and optional paste-ready copy packs."

policy:
  allow_implicit_invocation: true
```

- [ ] **Step 2: Run targeted copy-pack tests**

Run:

```bash
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_copy_packager_contract_preserves_non_compression_and_wrapper_boundary
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_copy_pack_format_defines_paste_ready_wrapper_shape
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_canonical_format_keeps_copy_packs_out_of_video_feed
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_validate_copy_packs_accepts_valid_five_line_pack_file
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_validate_copy_packs_rejects_missing_requirement_per_pack
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_validate_copy_packs_rejects_reset_duplicate_or_missing_numbers
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_validate_copy_packs_compares_against_source_feed_when_provided
python -m unittest tests.test_init_workspace.SkillTextRulesTests.test_validate_copy_packs_rejects_legacy_group_and_workflow_terms
```

Expected: every command reports `OK`.

- [ ] **Step 3: Run full validation**

Run:

```bash
python -m unittest discover -s tests -p "test_*.py"
$env:PYTHONUTF8='1'; python C:\Users\20931\.codex\skills\.system\skill-creator\scripts\quick_validate.py E:\source-true-guoman
git diff --check
git status --short
git diff --stat
```

Expected:

```text
OK
Skill is valid!
```

`git diff --check` prints no errors. `git status --short` shows only files changed by this plan before the final commit.

- [ ] **Step 4: Commit final metadata or validation adjustments**

If Step 1 changed `agents/openai.yaml` or Step 3 required small fixes, run:

```bash
git add agents/openai.yaml SKILL.md agents/copy-packager.md references/copy-pack-format.md scripts/validate_copy_packs.py tests/test_init_workspace.py references/format.md agents/production-runner.md
git commit -m "chore: finalize copy packager metadata"
```

If there are no file changes after Task 4, skip this commit.

- [ ] **Step 5: Install the updated skill without leaving stale old files**

Run this PowerShell command from `E:\source-true-guoman`:

```powershell
$source = (Resolve-Path '.').Path
$dest = 'C:\Users\20931\.codex\skills\source-true-guoman'
$destParent = Split-Path -Parent $dest
if (-not (Test-Path -LiteralPath $destParent)) {
    New-Item -ItemType Directory -Path $destParent | Out-Null
}
if (Test-Path -LiteralPath $dest) {
    $resolvedDest = (Resolve-Path -LiteralPath $dest).Path
    if ($resolvedDest -ne 'C:\Users\20931\.codex\skills\source-true-guoman') {
        throw "Refusing to remove unexpected path: $resolvedDest"
    }
    Remove-Item -LiteralPath $dest -Recurse -Force
}
New-Item -ItemType Directory -Path $dest | Out-Null
$items = @('SKILL.md', 'agents', 'references', 'scripts')
foreach ($item in $items) {
    Copy-Item -LiteralPath (Join-Path $source $item) -Destination $dest -Recurse -Force
}
Write-Host "Installed source-true-guoman to $dest"
```

Expected:

```text
Installed source-true-guoman to C:\Users\20931\.codex\skills\source-true-guoman
```

- [ ] **Step 6: Validate the installed copy**

Run:

```bash
$env:PYTHONUTF8='1'; python C:\Users\20931\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\20931\.codex\skills\source-true-guoman
Test-Path 'C:\Users\20931\.codex\skills\source-true-guoman\agents\copy-packager.md'
Test-Path 'C:\Users\20931\.codex\skills\source-true-guoman\scripts\validate_copy_packs.py'
```

Expected:

```text
Skill is valid!
True
True
```

- [ ] **Step 7: Final repo status**

Run:

```bash
git status --short --branch
git log --oneline -5
```

Expected: branch is ahead by the new commits and the repo working tree is clean. Installed-copy changes under `C:\Users\20931\.codex\skills\source-true-guoman` are outside this repo and not tracked here.

---

## Self-Review Checklist

- Spec coverage: routing, `copy-packager`, `copy-pack-format`, default 5-line packs, configurable pack size, repeated `统一要求`, relevant references, original numbering, and separate validation are all covered.
- Canonical feed safety: `scripts/validate_feed.py` stays strict and unchanged; canonical `## 视频投喂块` still has one global `统一要求` and continuous numbering.
- No old grouping regression: tests and docs reject `第N组`, `15秒`, `segment`, `S01/S02`, `keyframe`, `Canvas`, `MP4`, `首帧`, `尾帧`, `续接`, and `承接`.
- User friction solved: copy packs carry paste-ready local `上传参考图` with `场景1 / 角色1 / 音色1` bindings, but only in a separate copy artifact.
- No overdesign: one agent, one reference file, one validator script; no service, no database, no hidden state.
- Clean install: installed skill folder is removed and recopied after validation, so stale old skill files do not remain.
