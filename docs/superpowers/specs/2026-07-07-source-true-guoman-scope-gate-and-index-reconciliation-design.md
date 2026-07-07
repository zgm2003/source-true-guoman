# Source True Guoman 生产范围门禁与累计索引回填设计

## 背景

`source-true-guoman` 已经具备正式生产链路：

```text
source-indexer -> asset-bible -> image-generator(optional) -> faithful-feed -> feed-auditor -> copy-packager
```

现有规则已经强调源文保真、正式生产前必须确认运镜库和画幅比例、正式多章任务要做 `requested output range + next 3 chapters` 的 forward index，并且早期匿名角色如果后文命名或变重要，应合并为一个稳定资产。

但长篇小说生产仍有两个关键缺口：

1. 用户可能一口气丢整本小说，直接说“跑生产”。如果不先确认生产章数，模型可能一次跑太多导致判断变粗、资产变乱；如果只跑太少，又可能因为前扫不足而漏掉后续身份。
2. 用户分批生产时，后续章节会扩展 forward index。新证据可能证明前面某个“NPC/弟子/黑衣人/路人”其实是后面有名字、有对白、有功能的人物。当前规则有“应合并”的理念，但缺少强制的累计索引对账、资产改名、旧母稿修正、复制包重生和 manifest 迁移流程。

这份设计把这些问题合并为一个更完整的长篇生产控制机制：**生产范围门禁 + 累计索引回填 + 阶段感知下一步推荐**。

## 目标

- 当用户提交整本或超过 3 章的文本，且没有明确生产范围时，必须先问“跑几章”，推荐先跑 3 章。
- 把“生产章数”纳入正式生产参数门禁，与运镜库和画幅比例同级。
- 将默认正式生产切片从“5 章”调整为“推荐 3 章起跑”；超过 3 章默认不自动跑，除非用户明确指定范围或明确选择全本分批。
- 用户明确只跑 1 章时，仍执行 `1章输出 + 后3章身份前扫`，但只交付第 1 章内容。
- 用户后续继续生产时，索引范围要累计扩展，而不是只看当前请求片段。
- 每次扩展索引后，必须执行“索引回填对账”：检查新证据是否改变旧章节的角色标准名、匿名角色归属、资产等级、场景/道具归属或别名映射。
- 如果新证据修正了旧判断，必须更新 `source-index`、`asset-bible`、canonical mother feed、copy packs，并按需要迁移或废弃旧图片资产。
- 所有更名、合并、废弃、重生都必须有 source/index 证据锚点。
- 每个生产阶段完成后都要给用户一个明确的下一步建议，不让用户自己猜后续流程。

## 非目标

- 不做故事压缩、改写、洗稿或剧情摘要替代。
- 不自动把全文一次性生产完，除非用户明确要求并确认风险。
- 不泄漏 forward index 的未来剧情到当前交付的 feed/copy packs。
- 不把复制包当作源头修改；所有回填必须先改 canonical mother feed。
- 不在没有证据时强行合并疑似同一人物。
- 不用模糊规则批量改名；每个改名/合并都需要有明确证据和迁移记录。

## 推荐方案

采用两层门禁：

```text
请求解析
-> 正式生产参数门禁
-> 生产范围门禁
-> 累计索引扩展
-> 索引回填对账
-> asset-bible 更新
-> 可选 image-generator 资产迁移/重生
-> faithful-feed 更新
-> feed-auditor
-> copy-packager
-> next-step recommender
```

### 被考虑但不采用的方案

1. 继续默认 5 章生产。
   - 优点：比 3 章吞吐更高。
   - 缺点：用户丢整本时更容易失控；长篇前几章通常身份密集，5 章一口气做资产判断更容易错。
   - 决策：不采用为默认。

2. 只在聊天里提醒用户推荐 3 章，不改 skill 规则。
   - 优点：改动少。
   - 缺点：没有门禁和测试，后续 agent 容易忘。
   - 决策：不采用。

3. 永远只跑 1 章。
   - 优点：单次质量最高。
   - 缺点：上下文太短，很多后续命名和资产复用判断会漏。
   - 决策：不采用。推荐 3 章起跑，并保留 `+3章` forward index。

## 功能一：生产范围门禁

### 触发条件

满足任一条件时触发：

- 用户提交文本或项目源文检测到超过 3 章。
- 用户说“整本”“全文”“全书”“全本生产”“直接跑生产”，但没有明确生产范围。
- 用户给了小说目录/大文件/多章源文，但只提供运镜库和画幅比例，没有说跑几章。

### 不触发条件

- 用户明确说“跑第 1 章”“跑 1-3 章”“前三章”“跑第 5-7 章”。
- 用户明确说“全本分批，每批 3 章”或类似确定策略。
- 当前只是分析、索引、试读、烟测，不生成正式母稿和复制包。

### 门禁提示

当运镜库、画幅比例、生产章数都缺失时，使用合并提示：

```text
正式生产参数缺失：请先选择运镜库（小云雀 / libtv）、画幅比例（9:16竖屏 / 16:9横屏 / 21:9电影）和生产章数。检测到文本超过3章，建议先跑3章；你也可以指定 1-5 章、具体章节范围，或明确说全本分批。收到选择前，我不会生成连续投喂稿或复制包。
```

当只缺生产章数时，使用短提示：

```text
生产范围缺失：检测到文本超过3章。建议先跑3章；你也可以指定 1-5 章、具体章节范围，或明确说全本分批。收到选择前，我不会生成连续投喂稿或复制包。
```

### 默认解释

- 如果用户在门禁后回复“默认”，章数按 3 章。
- 如果用户在门禁后回复“前三章”，生产范围为第 1-3 章。
- 如果用户回复“先试一章”，生产范围为第 1 章，但 forward index 仍读第 1-4 章。
- 如果用户回复“全本分批”，默认每批 3 章，除非用户指定批大小。

### 生产范围与索引范围

例子：

```text
用户选择：跑第1章
交付范围：第1章
索引范围：第1-4章

用户选择：跑第2-3章
交付范围：第2-3章
索引范围：第2-6章

用户选择：跑前三章
交付范围：第1-3章
索引范围：第1-6章
```

forward index 只用于身份、连续性、资产复用和命名判断，不得把未来剧情泄漏进当前交付。

## 功能二：累计索引回填

### 核心原则

`source-index` 不是一次性产物，而是长篇生产的累计事实账本。每次新生产请求都必须先看旧索引，再扩展索引范围，并判断新证据是否改变旧产物。

### 累计索引范围计算

每次生产前计算：

```text
requested_output_range = 用户当前要求交付的章节
forward_index_range = requested_output_range + 后3章（如果源文存在）
existing_index_range = source-index 已读范围
required_cumulative_index_range = existing_index_range ∪ forward_index_range
```

如果 `required_cumulative_index_range` 包含旧索引未读章节，先补读这些章节并更新索引。

例子：

```text
第一次：用户跑第1章
旧索引：无
交付：第1章
forward：第1-4章
累计索引：第1-4章

第二次：用户跑第2-3章
旧索引：第1-4章
交付：第2-3章
forward：第2-6章
累计索引：第1-6章
```

### 索引回填对账门禁

更新索引后，必须在 `asset-bible` 和 `faithful-feed` 之前执行对账。

检查项：

- 早期匿名角色是否被后文命名。
- 早期一次性 NPC 是否变成命名低频角色、高频配角或主线功能角色。
- 同一人物是否出现别名、称号、职位变化或同音/错别字漂移。
- 已生成资产名是否仍符合 canonical source name。
- 旧母稿是否使用了临时名、错误名或一次性群像名。
- 旧 copy packs 是否绑定了旧资产名或旧路径。
- image manifest 是否还指向旧资产名。
- 旧图片是否可以沿用，还是必须废弃重生。

### 回填决策类型

对账结果分四类：

1. `无变化`
   - 新证据不影响旧产物。
   - 继续生产当前范围。

2. `索引别名补充`
   - 只是多了称号/别名，不影响资产标准名。
   - 更新 `source-index`，不改旧 feed 和图片。

3. `标准名升级`
   - 早期“某弟子/NPC/黑衣人/路人”等被证据证明是后文命名角色。
   - 更新 `source-index`、`asset-bible`、母稿和复制包。
   - 资产图片如果视觉仍可沿用，执行文件和 manifest 的标准名迁移。

4. `资产废弃重生`
   - 早期资产按一次性 NPC 生成了错误脸、错误服制、错误身份气质，不能代表后文命名角色。
   - 旧图片保留但标记 deprecated，不再作为 canonical asset。
   - 新 canonical asset 进入 image jobs，后续复制包绑定新路径。

### 资产迁移规则

如果旧图可沿用：

```text
旧资产名：黑衣弟子_一次性造型
新标准名：沈砚_青云宗内门弟子造型
动作：重命名文件、更新 image-manifest、记录 alias/deprecated_name
```

如果旧图不可沿用：

```text
旧资产名：黑衣弟子_一次性造型
新标准名：沈砚_青云宗内门弟子造型
动作：旧图标记 deprecated，新标准名进入 image-jobs，生成新图
```

manifest 需要支持迁移记录：

```json
{
  "asset_name": "沈砚_青云宗内门弟子造型",
  "path": "人设资产/沈砚_青云宗内门弟子造型.png",
  "status": "done",
  "aliases": ["黑衣弟子_一次性造型"],
  "migration_reason": "ch06 reveals early black-clothed disciple is 沈砚",
  "evidence_anchor": "ch06 scene ..."
}
```

旧资产条目可以保留为：

```json
{
  "asset_name": "黑衣弟子_一次性造型",
  "status": "deprecated",
  "replaced_by": "沈砚_青云宗内门弟子造型",
  "last_error": "identity upgraded by later source evidence"
}
```

### 旧母稿与复制包修正

任何回填影响旧 feed 时，必须遵守 canonical artifact policy：

```text
先更新 canonical mother feed
-> re-run feed audit
-> regenerate copy packs
```

禁止直接改 copy packs。

修正内容包括：

- `## 资产提示词` 中的资产名。
- 视频行中人物名称、资产引用或可见身份描述。
- copy packs 中的 `上传参考图` 绑定。
- 内部 audit report 中的连续性说明。

### 已交付产物的可追溯记录

每次回填要在内部写入一份变更账：

```text
生产资产/_内部/reconciliation-log.md
```

记录：

- 触发请求。
- 原交付范围与新交付范围。
- 旧索引范围与新累计索引范围。
- 被升级/合并/废弃/重命名的角色或资产。
- 证据锚点。
- 被更新的文件。
- 是否需要用户确认。

## 功能三：阶段感知下一步推荐系统

### 核心原则

`source-true-guoman` 不应该只在正式投喂稿完成后机械输出固定三选一。每个阶段完成后，系统都应根据当前产物状态推荐用户最可能需要的下一步，保持生产链路连续。

推荐系统的目标不是替用户自动执行，而是降低用户决策成本：

```text
我已经完成什么
当前还缺什么
最推荐下一步做什么
另外可选什么
哪些步骤现在不能做，为什么
```

除非用户已经明确选择下一步，否则推荐只给建议，不自动执行。

### 推荐输入状态

推荐器应读取或判断：

- canonical mother feed 是否存在并通过审计。
- copy packs 是否存在并通过校验。
- asset-bible 是否存在。
- image jobs 是否存在。
- image-manifest 是否存在。
- 图片资产是否全部 `done`，是否有 `failed/blocked/deprecated`。
- 风格确认波次是否完成，用户是否确认风格基准。
- storyboard/contact sheet 是否可运行。
- 是否存在索引回填待处理项。
- 用户最近是否提到“时长、删减、节奏、平台、投放、分镜、站位、画面不稳、继续下一章”等意图。

### 阶段推荐矩阵

#### 1. 正式母稿与复制包完成后

如果图片未生成或未验证：

```text
推荐：自动化生图
原因：当前已有母稿、asset-bible 和复制包，但还没有真实本地图片资产；先生成图片才能让后续分镜、站位 QA 和复制包图片绑定可靠。
```

可选项：

1. 自动化生图
2. 安全剪辑
3. 视频增强

#### 2. 风格预览图生成后

此时不推荐全量分镜，也不推荐继续全量生图，必须先让用户确认风格。

```text
推荐：确认风格基准
请先看第一个人设和第一个场景；确认后我再跑全量图片资产。未确认前不会生成依赖资产。
```

可选项：

1. 确认风格并继续全量生图
2. 调整人设风格
3. 调整场景风格

#### 3. 图片资产全量生成并验证后

如果 canonical feed 和图片 manifest 都可用：

```text
推荐：分镜/站位 QA
原因：图片资产已经齐了，下一步最该检查角色、场景、道具在真实镜头里的站位、遮挡、比例和连续性。
```

可选项：

1. 分镜/站位 QA - run `storyboard-contact-sheet`
2. 复制包绑定图片路径 - 如果复制包还没有绑定 manifest
3. 继续下一批章节 - 如果当前批次已完整通过

#### 4. 图片生成有失败或 blocked

推荐优先修复失败，而不是进入分镜。

```text
推荐：续跑/修复失败图片
原因：分镜 QA 需要真实图片引用；当前仍有 failed 或 blocked 图片资产，先修复能避免后续站位图缺素材。
```

可选项：

1. 续跑失败图片
2. 查看失败报告
3. 人工标记跳过并继续文本流程

#### 5. 分镜/contact sheet 完成后

如果发现站位或视觉问题：

```text
推荐：视频增强或资产修正
原因：分镜 QA 已暴露具体画面问题，应先修正母稿镜头或资产绑定，再重新审计和重生复制包。
```

如果分镜无明显问题：

```text
推荐：继续下一批章节
原因：当前批次文本、图片、分镜 QA 都已闭环，可以进入下一批生产，并执行累计索引回填。
```

可选项：

1. 继续下一批章节
2. 视频增强
3. 安全剪辑

#### 6. 索引回填发现旧资产/旧母稿需要修正

推荐必须优先处理回填，不允许跳到新生产。

```text
推荐：处理索引回填
原因：新章节证据改变了旧角色/资产判断；如果不先修正，后续图片、分镜和复制包会继续沿用错误身份。
```

可选项：

1. 沿用旧图并改名
2. 废弃旧图并重生
3. 暂停并人工确认疑似身份

#### 7. 用户提到平台时长、删减、节奏压力

推荐安全剪辑，不推荐直接让模型改短剧情。

```text
推荐：安全剪辑
原因：你提到时长/节奏/平台压力；我会按连续行号和原文跨度给删减风险与可剪边界，不改写剧情。
```

可选项：

1. 安全剪辑
2. 视频增强
3. 继续生图/分镜（如果素材链路未完成）

### 推荐输出格式

每个阶段完成后的最终回复都应包含一个简短状态块：

```text
当前状态：
- 母稿：已通过 / 未生成 / 需修正
- 复制包：已通过 / 未生成 / 需重生
- 图片资产：未生成 / 风格待确认 / 部分失败 / 已完成
- 分镜QA：未开始 / 已完成 / 需修正
- 索引回填：无待处理 / 有待处理

下一步建议（推荐优先）：
1. 推荐项 - 简短原因
2. 可选项
3. 可选项
```

如果某一步当前不能做，必须说明阻塞条件：

```text
暂不建议分镜 QA：图片资产还没有全部生成并验证。
```

### 推荐系统边界

- 推荐系统只建议，不自动执行，除非用户明确选择或前文已授权。
- 推荐不改变 canonical feed、asset-bible、source-index 或 manifest。
- 推荐不得绕过风格确认波次。
- 推荐不得在图片失败时假装可以完整分镜。
- 推荐不得把 copy packs 当作可直接修改源头。
- 推荐必须尊重索引回填优先级；有 confirmed reconciliation 时，先处理回填。

## 数据结构调整

### source-index 新增字段

角色条目增加：

```text
- Canonical name:
- Former temporary names:
- Aliases/titles:
- First anonymous appearance:
- Naming evidence:
- Upgrade status: none / suspected / confirmed / rejected
- Affected prior artifacts:
- Asset migration status:
- Evidence anchors:
```

索引头部增加：

```text
- Requested output ranges completed:
- Forward index ranges read:
- Cumulative index range:
- Missing source ranges:
- Reconciliation status:
```

### asset-bible 新增字段

资产条目增加：

```text
- Canonical asset name:
- Previous asset names:
- Migration action: none / rename / deprecated / regenerate
- Replaced by:
- Source-index evidence:
- Prior feed lines affected:
```

### image-manifest 新增状态

允许状态扩展：

```text
done
failed
blocked
deprecated
renamed
```

新增字段：

```text
aliases
previous_asset_name
replaced_by
migration_reason
evidence_anchor
```

### recommendation-state 新增内部状态

可选增加内部文件：

```text
生产资产/_内部/recommendation-state.json
```

记录最近一次推荐依据：

```json
{
  "mother_feed": "passed",
  "copy_packs": "passed",
  "images": "style_preview_done",
  "storyboard": "not_started",
  "reconciliation": "none",
  "recommended_next": "confirm_style_baseline",
  "blocked_next": [
    {
      "action": "storyboard-contact-sheet",
      "reason": "image assets are not fully generated"
    }
  ]
}
```

该文件不是必须的第一阶段实现；第一阶段可以只在聊天最终回复中输出状态块。

## Agent 与文件改动范围

### Orchestrator: `SKILL.md`

需要新增：

- 生产章数门禁。
- 推荐 3 章起跑。
- 全本分批默认每批 3 章。
- 后续批次必须执行累计索引回填。
- 如果回填影响旧产物，先修母稿，再审计，再重生复制包。
- 每个阶段完成后调用下一步推荐规则，不只在母稿完成后固定输出三选一。

### `agents/source-indexer.md`

需要新增：

- 累计索引范围计算。
- 回填对账门禁。
- 匿名角色升级的迁移记录。
- 后续证据改变旧资产判断时必须标记 affected artifacts。

### `references/source-index-format.md`

需要新增：

- cumulative index range 字段。
- reconciliation status 字段。
- anonymous-to-named upgrade ledger。
- asset migration ledger。

### `agents/asset-bible.md`

需要新增：

- 读取 reconciliation 结果。
- 不允许在未处理 confirmed upgrade 时继续写新资产。
- 支持 rename/deprecate/regenerate 三种资产迁移建议。

### `references/asset-bible-format.md`

需要新增资产迁移字段。

### `scripts` 层

可以分两阶段实现：

第一阶段只加规则和测试，不做自动文件迁移脚本。

第二阶段增加确定性脚本：

```text
scripts/validate_reconciliation.py
scripts/migrate_asset_names.py
scripts/recommend_next_steps.py
```

`validate_reconciliation.py` 检查 confirmed upgrade 是否已经反映到 index/bible/feed/copy packs。

`migrate_asset_names.py` 只处理明确的 manifest/file rename，不自动判断剧情身份。

`recommend_next_steps.py` 可在第二阶段读取工作区状态并输出推荐项；第一阶段先用规则文本和测试约束 agent 回复即可。

## 错误处理与用户确认

以下情况必须停下问用户：

- 新证据只能证明“疑似同一人”，不能确认。
- 旧图是否可沿用无法判断。
- 改名会覆盖已有文件。
- manifest 中旧资产有多个下游依赖，自动迁移风险高。
- 旧母稿已被用户手工改过，无法安全重写。

推荐提示：

```text
索引回填发现早期资产需要处理：`黑衣弟子_一次性造型` 在第6章证据中升级为 `沈砚_青云宗内门弟子造型`。旧图是否沿用需要确认。请选择：沿用并改名 / 废弃旧图并重生 / 暂不处理。
```

## 测试策略

### 文档规则测试

在 `tests/test_init_workspace.py` 中增加断言：

- `SKILL.md` 包含生产章数门禁。
- `SKILL.md` 明确超过 3 章先问章数，推荐 3 章。
- `source-indexer.md` 包含累计索引范围计算。
- `source-index-format.md` 包含 reconciliation status 和 upgrade ledger。
- `asset-bible.md` 包含 rename/deprecated/regenerate 迁移规则。
- `SKILL.md` 包含阶段感知下一步推荐规则。
- 图片完成后推荐 `storyboard-contact-sheet`，图片失败时推荐续跑/修复失败图片。
- 有 confirmed reconciliation 时推荐先处理索引回填。

### 行为级 fixture 测试

新增小型样本文本：

```text
第1章：黑衣弟子短暂出现。
第2章：用户当前请求继续生产。
第6章：揭示黑衣弟子名叫沈砚，并承担后续剧情功能。
```

测试期望：

- 第一次跑第1章，索引范围为第1-4章。
- 第二次跑第2-3章，索引范围扩展到第1-6章。
- 第6章证据触发第1章匿名角色升级。
- `source-index` 记录 canonical name、former temporary name、evidence anchor。
- `asset-bible` 不再生成 `黑衣弟子_一次性造型` 作为 canonical asset。
- 如果旧资产存在，迁移状态必须是 rename/deprecated/regenerate 之一。

### 校验脚本测试

如果实现 `validate_reconciliation.py`，测试：

- confirmed upgrade 未改母稿时失败。
- manifest 仍引用旧 canonical name 时失败。
- copy packs 直接改过但 mother feed 未改时失败。
- suspected merge 被当作 confirmed merge 时失败。
- 所有回填完成后通过。

### 推荐系统测试

如果实现 `recommend_next_steps.py`，测试：

- 母稿和复制包完成但图片缺失时，推荐自动化生图。
- 风格预览图完成但未确认时，推荐确认风格基准。
- 图片全部完成且 mother feed 可用时，推荐分镜/站位 QA。
- 图片有 failed/blocked 时，不推荐分镜，推荐续跑失败图片。
- 有 confirmed reconciliation 时，推荐索引回填优先于继续下一章。
- 用户最近提到时长/删减/平台压力时，推荐安全剪辑。

## 接受标准

- 用户丢整本或超过 3 章时，系统不会直接生产，而是要求确认生产章数，推荐 3 章。
- 用户明确只跑 1 章时，交付只包含 1 章，但索引读取到后 3 章用于身份判断。
- 后续继续跑章节时，索引范围累计扩展，而不是覆盖旧索引。
- 新证据能反向修正旧章节的匿名 NPC、别名、资产等级和标准名。
- 已有旧资产不会默默沿用错误名字；必须 rename、deprecated 或 regenerate。
- 旧母稿和复制包不会出现旧名和新名混用。
- 所有修改都有证据锚点和内部 reconciliation log。
- 每个阶段完成后都有状态感知的下一步建议，用户无需自己判断下一步做什么。
- 图片资产完成后会推荐是否进入分镜/站位 QA；图片失败时会先推荐修复失败图片。
- 测试覆盖规则文本、索引格式、资产迁移策略和至少一个匿名角色后续命名的回填样例。

## 分阶段实施建议

### Phase 1：规则与格式

- 修改 `SKILL.md`、`source-indexer.md`、`source-index-format.md`、`asset-bible.md`、`asset-bible-format.md`。
- 增加文档规则测试。
- 不做自动文件迁移，只要求 agent 产出 reconciliation log 和阶段感知下一步建议。

### Phase 2：确定性校验

- 增加 `validate_reconciliation.py`。
- 增加 `recommend_next_steps.py`。
- 检查 confirmed upgrade 是否完整反映到 index/bible/feed/copy packs/manifest。
- 用脚本根据工作区状态生成推荐项。
- 增加 fixture 测试。

### Phase 3：辅助迁移脚本

- 增加 `migrate_asset_names.py`。
- 只处理确定的文件重命名和 manifest alias/deprecated 状态。
- 剧情身份判断仍由 source-index evidence 驱动，不交给脚本猜测。

## 开放问题

1. 全本分批时默认每批是否固定 3 章，还是允许在首次确认后设置为 3-5 章？
2. 旧图片可沿用但文件名已在用户外部工具中使用时，是重命名文件，还是保留旧文件并在 manifest 中把新标准名指向旧路径？
3. 已交付给用户的旧复制包是否保留历史版本，还是总是覆盖生成最新版本？
4. 如果 forward index 读到重大未来剧透，内部索引必须知道，但当前 copy pack 不能泄漏；是否需要额外的 `future_reveal_private` 标记来防止误写进交付件？
