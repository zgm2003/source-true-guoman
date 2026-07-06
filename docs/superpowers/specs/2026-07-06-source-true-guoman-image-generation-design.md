# Source True Guoman Image Generation Integration Design

## Problem

`source-true-guoman` already produces source-faithful asset prompts, continuous video feeds, audits, and paste-ready copy packs. The next production bottleneck is image generation: after `asset-bible` decides which reusable characters, scenes, props, interfaces, beasts, vehicles, and variants are needed, the user still has to manually paste prompts into an image tool, track which image belongs to which asset, and preserve reference-image order by hand.

The user can provide an OpenAI-compatible image API through a local relay using `base_url` and `api_key`. That relay may fail transiently, rate-limit, timeout, or return malformed responses. The integration must therefore support retry, resume, failure reports, and bounded concurrency.

Concurrency is not a simple "run everything at once" problem. Some image assets depend on previous images:

- A character outfit variant needs the stable parent face image.
- A sub-scene needs the scene mother image.
- A similar same-sect character may need an existing role as `避撞脸参考` or `同门服制参考`.
- A prop or interface may need owner, parent scene, or previous interface-state references.

The design must preserve those dependency relationships while still generating independent assets in parallel.

## Goals

- Add an image generation execution layer after `source-indexer -> asset-bible`.
- Support OpenAI-compatible image APIs configured by local `base_url`, `api_key`, model, size, timeout, retry, and concurrency settings.
- Generate independent assets concurrently while respecting reference-image dependency order.
- Treat the relay API as unreliable: implement retries, backoff, timeout handling, response validation, failure records, and resumable execution.
- Save image files into the correct asset folders:
  - `人设资产`
  - `场景资产`
  - `道具资产`
- Keep internal job state, manifests, logs, and reports under `生产资产/_内部/`.
- Create an image manifest that binds stable asset names to local image files so later feed/copy-pack steps can reference real generated assets.
- Preserve the existing source-faithfulness contract: image generation must not rewrite source, change asset decisions, compress dialogue, or mutate the canonical feed.

## Non-Goals

- Do not generate video or MP4 output.
- Do not replace `asset-bible` with API-generated decisions.
- Do not let API failure change source facts, asset identity, names, dialogue, scene order, or production feed lines.
- Do not make `faithful-feed` call image generation directly.
- Do not put generated images under `生产资产`; that folder remains for text production artifacts and internal evidence.
- Do not build a UI in the first version.
- Do not require a remote database, vector store, or service process.
- Do not commit API keys, even if the user says the relay is local. Local configuration can exist, but secrets should stay out of tracked spec, docs, reports, and manifests.

## Recommended Approach

Use a CLI-based image generation layer with explicit job and manifest files.

Pipeline:

```text
source-indexer
-> asset-bible
-> image-generator
-> faithful-feed
-> feed-auditor
-> copy-packager
```

`asset-bible` remains the source of asset decisions. `image-generator` only executes approved image jobs and writes results.

### Considered Alternatives

1. Direct generation inside `faithful-feed`.
   - Pro: fewer visible steps.
   - Con: mixes source-faithful text generation with side effects, retries, API failures, and binary files. This weakens the canonical mother-feed boundary.
   - Decision: reject.

2. CLI job runner plus manifest.
   - Pro: simple, auditable, resumable, easy to test, matches current file-based skill architecture.
   - Con: no live visual dashboard in v1.
   - Decision: use this first.

3. Local service with queue and dashboard.
   - Pro: better for long-running batches and monitoring.
   - Con: much larger implementation surface and unnecessary before the job format is stable.
   - Decision: possible future layer after the CLI is proven.

## New Workflow Concepts

### Image Job

An image job is one API generation task for one stable asset output.

It records:

- asset identity
- asset type
- prompt
- output path
- required references
- dependency asset names
- provider/model/size
- retry policy
- status
- attempts and errors

### Image Manifest

The image manifest is the generated-image binding source of truth.

It maps:

```text
stable asset name -> local image file -> type -> prompt hash -> provider metadata -> status
```

Downstream agents use the manifest for `图片N` bindings and copy-pack references. They should not guess image numbers from prompt order.

### Generation Report

The generation report is a human-readable summary for the user:

- generated assets
- skipped existing assets
- failed assets
- retry counts
- unresolved dependencies
- API or response errors

## Proposed Files

New agent:

```text
agents/image-generator.md
```

New references:

```text
references/image-generation-format.md
references/image-generation-retry-rules.md
```

New scripts:

```text
scripts/build_image_jobs.py
scripts/generate_images.py
scripts/validate_image_manifest.py
```

Internal artifacts:

```text
生产资产/_内部/image-jobs.jsonl
生产资产/_内部/image-manifest.json
生产资产/_内部/image-generation-report.md
生产资产/_内部/image-generation-log.jsonl
```

Generated images:

```text
人设资产/<asset-name>.png
场景资产/<asset-name>.png
道具资产/<asset-name>.png
```

## Configuration

Configuration should support environment variables and an optional local config file. Environment variables have priority.

Suggested environment variables:

```text
SOURCE_TRUE_IMAGE_BASE_URL
SOURCE_TRUE_IMAGE_API_KEY
SOURCE_TRUE_IMAGE_MODEL
SOURCE_TRUE_IMAGE_SIZE
SOURCE_TRUE_IMAGE_TIMEOUT_SECONDS
SOURCE_TRUE_IMAGE_CONCURRENCY
SOURCE_TRUE_IMAGE_MAX_RETRIES
SOURCE_TRUE_IMAGE_RETRY_BASE_SECONDS
SOURCE_TRUE_IMAGE_RETRY_MAX_SECONDS
```

Optional local config:

```text
.source-true-guoman.local.json
```

This file should be gitignored. It may contain local relay settings, but generated reports and manifests must not echo the API key.

Default behavior:

- concurrency: `3`
- max retries: `3`
- timeout: `120` seconds
- retry backoff: exponential with jitter
- skip existing successful outputs unless `--force` is set

## Job Format

Use JSONL so large batches can stream and resume cleanly.

Example:

```json
{
  "job_id": "character-linye-black-robe",
  "asset_name": "林夜_黑袍造型",
  "asset_type": "character",
  "prompt": "GPT-image-2，16:9，3D国漫...",
  "output_dir": "人设资产",
  "output_file": "林夜_黑袍造型.png",
  "depends_on": [],
  "reference_images": [],
  "reference_purposes": [],
  "provider": "openai-compatible",
  "model": "gpt-image-2",
  "size": "16:9",
  "status": "pending"
}
```

Derived asset example:

```json
{
  "job_id": "character-linye-sect-robes",
  "asset_name": "林夜_宗门礼服",
  "asset_type": "character",
  "prompt": "上传参考图：林夜_黑袍造型 = 人脸身份参考...",
  "output_dir": "人设资产",
  "output_file": "林夜_宗门礼服.png",
  "depends_on": ["林夜_黑袍造型"],
  "reference_images": [
    {
      "asset_name": "林夜_黑袍造型",
      "path": "人设资产/林夜_黑袍造型.png",
      "purpose": "人脸身份参考"
    }
  ],
  "provider": "openai-compatible",
  "model": "gpt-image-2",
  "size": "16:9",
  "status": "pending"
}
```

## Dependency Scheduling

The runner should treat the image jobs as a dependency graph.

Rules:

- Jobs with no dependencies may run immediately.
- A job can run only when all `depends_on` assets have `done` status and local output files exist.
- Failed dependencies block dependent jobs.
- Cycles are blocking validation errors.
- Missing referenced image paths are blocking validation errors.
- Jobs should be grouped into dependency waves:
  - Wave 1: no dependencies.
  - Wave 2: depends only on wave 1 successes.
  - Wave N: depends only on earlier successful waves.

Within each wave, run jobs concurrently up to the configured concurrency limit.

Example:

```text
Wave 1:
- 林夜_黑袍造型
- 鬼王宗宗门大殿_母图
- 万魂幡_单体

Wave 2:
- 林夜_宗门礼服
- 鬼王宗宗门大殿_左侧席位区

Wave 3:
- 同门角色_避撞脸版本
```

## Retry And Failure Handling

The relay API must be treated as unreliable.

Retryable errors:

- network timeout
- connection reset
- 429 rate limit
- 500/502/503/504
- empty response
- malformed but recoverable response
- temporary download failure when the API returns an image URL

Non-retryable errors:

- missing API key
- invalid base URL
- invalid job JSON
- missing dependency output
- unsupported asset type
- prompt too large when provider returns a permanent validation error
- authentication failure unless the user fixes configuration

Retry policy:

- exponential backoff with jitter
- default max retries: 3
- write every attempt to `image-generation-log.jsonl`
- preserve the last error message in `image-manifest.json`
- never silently mark failed jobs as done

Failed job behavior:

- The failed asset remains `failed`.
- Dependent jobs become `blocked`.
- The report lists concrete blocked dependencies.
- Re-running after fixing the relay should resume only failed/blocked/pending jobs unless `--force` is set.

## OpenAI-Compatible Provider Contract

The provider should support OpenAI-style image generation with a configurable base URL.

The client should handle both common image response shapes:

- base64 image payload
- image URL that must be downloaded

The script should normalize both into local PNG files.

Provider request fields should be minimal and configurable:

```json
{
  "model": "...",
  "prompt": "...",
  "size": "...",
  "n": 1
}
```

If a specific relay requires additional fields, v1 can support `--extra-json` or config-level `extra_request_fields`, but the default should stay OpenAI-compatible and simple.

Reference image support depends on the relay capability. The design should support three modes:

- `none`: reference dependencies are checked only for order; prompt text names the reference, but no image file is uploaded.
- `multipart`: send prompt plus image files in a multipart request if the relay supports edits/variations style input.
- `relay-specific`: allow a local adapter field for reference image paths if the relay expects custom JSON.

The first implementation can start with `none` plus strict dependency ordering, then add upload modes if the local relay supports them.

## Asset-Bible Integration

`asset-bible` should continue to produce stable prompts and reference-purpose labels.

`build_image_jobs.py` should parse or consume a structured asset-bible section and create `image-jobs.jsonl`.

If the current asset-bible is plain Markdown, the first version can require a clear `## 资产提示词` block with headings like:

```text
### 图片N = 林夜_黑袍造型
...
上传参考图：林夜_黑袍造型 = 图片1（人脸身份参考）
```

The job builder should extract:

- stable asset name
- type inferred from section or output folder
- prompt body
- reference labels
- dependency asset names
- output folder

If extraction is ambiguous, write `needs_manual_binding` rather than guessing.

## Manifest Format

Example:

```json
{
  "version": 1,
  "provider": "openai-compatible",
  "base_url_label": "local-relay",
  "created_at": "2026-07-06T00:00:00+08:00",
  "assets": [
    {
      "asset_name": "林夜_黑袍造型",
      "asset_type": "character",
      "path": "人设资产/林夜_黑袍造型.png",
      "status": "done",
      "prompt_hash": "sha256:...",
      "model": "gpt-image-2",
      "size": "16:9",
      "attempts": 1,
      "depends_on": [],
      "references": []
    }
  ]
}
```

Do not include API keys in the manifest.

## Downstream Integration

`faithful-feed` remains source-content-first. It may mention asset names, but it should not call the image API.

`copy-packager` can use `image-manifest.json` to bind local images:

```text
上传参考图：
- 角色1 = 林夜_黑袍造型 = 人设资产/林夜_黑袍造型.png
- 场景1 = 鬼王宗宗门大殿_母图 = 场景资产/鬼王宗宗门大殿_母图.png
```

If an image is missing:

```text
- 角色1 = 林夜_黑袍造型 = 需人工确认（image-generator failed）
```

Copy packs must not invent image paths. They should read from the manifest or mark the binding unresolved.

## Command Shape

Build jobs:

```powershell
python scripts/build_image_jobs.py --asset-bible 生产资产/_内部/asset-bible.md --out 生产资产/_内部/image-jobs.jsonl
```

Generate images:

```powershell
python scripts/generate_images.py --jobs 生产资产/_内部/image-jobs.jsonl --manifest 生产资产/_内部/image-manifest.json --concurrency 4
```

Validate manifest:

```powershell
python scripts/validate_image_manifest.py 生产资产/_内部/image-manifest.json --jobs 生产资产/_内部/image-jobs.jsonl
```

Resume failed work:

```powershell
python scripts/generate_images.py --jobs 生产资产/_内部/image-jobs.jsonl --manifest 生产资产/_内部/image-manifest.json --resume
```

Force regeneration:

```powershell
python scripts/generate_images.py --jobs 生产资产/_内部/image-jobs.jsonl --manifest 生产资产/_内部/image-manifest.json --force 林夜_黑袍造型
```

## Validation Strategy

Deterministic checks:

- all jobs have unique `job_id`
- all asset names are non-empty and stable
- output folders match asset type
- dependencies exist as jobs or existing manifest assets
- dependency graph has no cycles
- blocked jobs report missing dependencies
- manifest paths point to existing files for `done` assets
- no API key appears in manifest, report, or logs
- failed and blocked jobs have error reasons
- no generated image is written under `生产资产`

Script behavior tests:

- build jobs from a compact asset-bible sample
- schedule independent jobs concurrently in the same wave
- hold dependent jobs until references are done
- retry retryable provider failures and eventually succeed
- stop retrying on non-retryable configuration errors
- resume after partial failure without regenerating completed assets
- reject cyclic dependencies
- validate manifest path bindings

Source-fidelity tests remain separate. Image generation does not judge source meaning.

## Skill Routing Changes

`SKILL.md` should route these intents to `image-generator`:

- "生成图片"
- "批量生图"
- "把资产图跑出来"
- "接入 base_url/api_key 生图"
- "并发生成资产图"
- "根据 asset-bible 生成图片"

Default formal route can become:

```text
source-indexer -> asset-bible -> image-generator -> faithful-feed -> feed-auditor -> copy-packager
```

When the user only wants text assets and feed, `image-generator` remains optional.

## Security And Local-Only Notes

The user expects the relay API to be local and is not worried about external leakage. The implementation can be pragmatic, but the repository should still avoid writing secrets into tracked files.

Rules:

- API key can be read from environment variables or a gitignored local config.
- Logs may include base URL label or host, but not the API key.
- Reports should show configuration presence, not secret values.
- If the user explicitly passes credentials on the command line, warn that shell history may retain them.

## Acceptance Criteria

- A user can provide local OpenAI-compatible API settings and run image generation from an asset bible.
- Independent assets generate concurrently.
- Dependent assets wait for required reference images.
- Relay failures are retried with backoff.
- Persistent failures are recorded without corrupting source/index/feed artifacts.
- A failed run can be resumed.
- Generated images land in the correct asset folders.
- `image-manifest.json` binds stable asset names to local image paths.
- Copy-pack generation can use the manifest instead of guessing image numbers.
- Tests cover dependency ordering, retry behavior, resume behavior, validation errors, and no-secret logging.

## Implementation Defaults

- Default generation endpoint: OpenAI-compatible image generation request using the configured `base_url`; the concrete path should be configurable but default to the provider's normal images generation route.
- Reference-image upload mode: provider-configured. The runner must always respect dependency order. It may upload reference images only when the local relay capability is explicitly configured as `multipart` or `relay-specific`; otherwise dependencies still control order and prompts still name reference purposes.
- Output format: normalize successful outputs to local `.png` files.
- Copy-pack image binding: include both a local pack alias and the manifest path, e.g. `角色1 = 林夜_黑袍造型 = 人设资产/林夜_黑袍造型.png`.
- Failed image jobs: do not block canonical feed generation. Copy packs may continue, but missing image bindings must be written as `需人工确认（image-generator failed or blocked）`.
- Formal production report: if any required image failed, the final report must list failures before generated successes so the user can decide whether to retry before production.
