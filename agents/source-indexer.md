# Source Indexer Agent

Use this specialist when source reading is the bottleneck: long chapters, multi-chapter continuity, confusing aliases, likely typos, suspected same people, recurring locations, or source facts that later agents must cite.

## 淇濈湡濂戠害 / 保真契约

- 鍘熶綔澶氬皯瀛楀氨淇濈暀澶氬皯瀛? 原作多少字就保留多少字.
- 涓嶅緱鐢?AI 甯敤鎴峰帇缂┿€佹鎷€佹敼鐭€佹鼎鑹插師浣滃鐧芥垨鍓ф儏. 不得由 AI 帮用户压缩.
- 瀵圭櫧蹇呴』浠庡師鏂囪憳鍙栵細涓嶆敼鍐欙紝涓嶈ˉ鍐欙紝涓嶆彁鍓嶆尓鐢? 对白必须从原文摘取.
- 涓嶄富鍔ㄦ坊鍔犵珯璧枫€佽捣韬€佽藩涓嬨€佽蛋鍔ㄣ€佹姮鎵嬨€佹敹璧锋硶鍣? 閬撳叿鍔ㄤ綔蹇呴』鏈夊師鏂囦緷鎹? 不主动添加站起、起身、跪下、走动、抬手、收起法器.

## Inputs

- Requested source scope only.
- Existing `source-index.md` when present.
- Existing asset files or user-provided image references when they affect identity.

## Output

Create or update `鐢熶骇璧勴骇/source-index.md` unless the user explicitly asks for a visible root-level working index. Use `references/source-index-format.md`.

Do not output a video feed. do not output a synopsis replacement. Do not summarize chapters as a replacement for source coverage. Use evidence anchors for every merge, correction, relationship claim, reveal handling, face reference, scene reference, reusable asset decision, outfit/state change, and unresolved doubt.

Scope mode policy: 正式多章任务必须先预扫完整请求范围. 局部烟测必须显式标记已阅读范围. 局部烟测资产不得当作全局定稿. 姝ｅ紡澶氱珷浠诲姟蹇呴』鍏堥鎵畬鏁磋姹傝寖鍥? 灞€閮ㄧ儫娴嬪繀椤绘樉寮忔爣璁板凡闃呰鑼冨洿. 灞€閮ㄧ儫娴嬭祫浜т笉寰楀綋浣滃叏灞€瀹氱.

## Procedure

1. Mark `绱㈠紩鐘舵€乣, `璇锋眰鑼冨洿`, `宸查槄璇昏寖鍥碻, `鏈槄璇昏寖鍥碻, and evidence basis before any character or asset decision.
2. For formal multi-chapter work must pre-scan the whole requested scope before deciding identity, recurrence, scene reuse, or final asset value.
3. For smoke tests, label `灞€閮ㄧ儫娴媊, list exact read span and unread span, and write `Do not promote smoke-test assets to global final decisions.`
4. Record characters, aliases, factions, speaking roles, first/later appearances, relationships, posture facts, outfit/state changes, and asset binding candidates.
5. Track anonymous-to-named upgrade cases: early `寮熷瓙/NPC/榛戣。浜?渚嶅コ/瀹堝崼/璺汉` becomes one stable role if later named, recurring, speaking, or plot-bearing.
6. Record scene mother locations and sub-locations, keeping interior/exterior, material logic, lighting logic, and parent-child scene relationships separate.
7. Record props, interfaces, beasts, vehicles, voice roles, sects, realms, techniques, systems, titles, and suspicious spelling drift.
8. Keep uncertain merges as `suspected same asset`; do not merge or assert confirmation without source evidence.
9. every merge, correction, relationship claim, reveal handling, face reference, scene reference, or reusable asset decision must cite an evidence anchor.
10. Keep the index compact enough to consult while writing feed lines.
