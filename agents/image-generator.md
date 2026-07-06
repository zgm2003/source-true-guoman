# Image Generator Agent

Use this specialist after `asset-bible` exists and the user wants to generate images, batch-generate assets, connect `base_url` and `api_key`, or run image jobs concurrently.

## 保真契约

- 原作多少字就保留多少字.
- 不得由 AI 帮用户压缩、概括、改短、润色原作对白或剧情.
- 对白必须从原文摘取：不改写，不补写，不提前挪用.
- 不主动添加站起、起身、跪下、走动、抬手、收起法器; 道具动作必须有原文依据.

## Boundary

image-generator only executes approved image jobs from `asset-bible`. It must not rewrite source, change asset identity, compress dialogue, alter feed lines, or invent new production assets.

The generated-image binding source of truth is `生产资产/_内部/image-manifest.json`.

Generated image files belong in:

- `人设资产`
- `场景资产`
- `道具资产`

Internal jobs, logs, reports, and manifests belong under `生产资产/_内部/`.

Image QA gate: image generation must start with environment preflight, then a 风格确认波次 that generates only 第一个场景和第一个人设. Stop and ask for 用户确认风格基准 before generating dependent assets. After confirmation, later characters must upload 人设风格基准参考; later scenes, props, and interfaces must upload 场景风格基准参考 plus any asset-family mother image. Do not write fixed style bans: 不要写死非Q版、非玩具感、非卡通低龄化. 如果用户选择 Q版, the first confirmed scene/character baselines define the Q版 style and later images follow those references. Reference-dependent jobs must use 真实上传/编码参考图; prompt-only reference is forbidden. character with identity props remains a character asset: `鬼财神_财神殿执掌者铁算盘造型` belongs in `人设资产`, not `道具资产`. Asset family: `天机一型手机_三视图` is the phone mother asset; system mall, Douyin UI, and phone screen variants must reference it and keep body, camera, border, screen ratio, and material consistent.

## Required References

- Read `references/image-generation-format.md` before creating jobs or manifests.
- Read `references/image-generation-retry-rules.md` before running API calls, retry, resume, or dependency scheduling.

## Inputs

- `生产资产/_内部/asset-bible.md` or a saved feed package containing `## 资产提示词`.
- Existing generated images when referenced by asset-bible.
- Local OpenAI-compatible relay settings from environment variables.

## Output

- `生产资产/_内部/image-jobs.jsonl`
- `生产资产/_内部/image-manifest.json`
- `生产资产/_内部/image-generation-report.md`
- Generated images under `人设资产`, `场景资产`, or `道具资产`.

## Procedure

1. Run environment preflight: confirm base URL, API key, `SOURCE_TRUE_IMAGE_REFERENCE_MODE=data-url`, workspace root, output folders, and concurrency settings.
2. Build the style preview jobs with `python scripts/build_image_jobs.py --asset-bible 生产资产/_内部/asset-bible.md --out 生产资产/_内部/image-jobs-style-preview.jsonl --style-stage preview`.
3. Generate only the preview jobs, show the first scene and first character images, and stop for 用户确认风格基准.
4. After user approval, build the full jobs with `--style-stage confirmed`; set `SOURCE_TRUE_STYLE_CONFIRMED=1` before running the full generation.
5. Validate jobs before generation: unique ids, stable asset names, supported output folders, existing dependencies, no cycles, and no output under `生产资产`.
6. Schedule jobs by dependency waves. Jobs in the same wave may run concurrently; jobs with `depends_on` wait for successful parent images.
7. Use the configured OpenAI-compatible provider. Treat the relay as unreliable.
8. Retry retryable failures with exponential backoff and jitter. Do not retry non-retryable configuration, authentication, style-confirmation, or job-validation errors.
9. Save successful API outputs as local `.png` files.
10. Update `image-manifest.json` after each completed, failed, or blocked job.
11. Write a generation report with failures first, then blocked jobs, then successes.
12. Never write API keys into manifest or report.
13. Use `--resume` to skip already successful outputs; without `--resume`, run jobs from the current job file.

## Copy-Pack Boundary

copy-packager may read `image-manifest.json` for `上传参考图` bindings. Copy packs must not invent image paths. Missing or failed images must be marked `需人工确认（image-generator failed or blocked）`.
