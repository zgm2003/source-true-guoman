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

1. Build image jobs from stable asset prompts and reference-purpose labels.
2. Validate jobs before generation: unique ids, stable asset names, supported output folders, existing dependencies, no cycles, and no output under `生产资产`.
3. Schedule jobs by dependency waves. Jobs in the same wave may run concurrently; jobs with `depends_on` wait for successful parent images.
4. Use the configured OpenAI-compatible provider. Treat the relay as unreliable.
5. Retry retryable failures with exponential backoff and jitter. Do not retry non-retryable configuration, authentication, or job-validation errors.
6. Save successful API outputs as local `.png` files.
7. Update `image-manifest.json` after each completed, failed, or blocked job.
8. Write a generation report with failures first, then blocked jobs, then successes.
9. Never write API keys into manifest or report.
10. Use `--resume` to skip already successful outputs; without `--resume`, run jobs from the current job file.

## Copy-Pack Boundary

copy-packager may read `image-manifest.json` for `上传参考图` bindings. Copy packs must not invent image paths. Missing or failed images must be marked `需人工确认（image-generator failed or blocked）`.
