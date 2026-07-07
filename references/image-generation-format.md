# Image Generation Format

Use this file when creating image generation jobs, manifests, and reports.

## Files

- Jobs: `生产资产/_内部/image-jobs.jsonl`
- Manifest: `生产资产/_内部/image-manifest.json`
- Report: `生产资产/_内部/image-generation-report.md`

Generated image files go to:

- `人设资产/<asset-name>.png`
- `场景资产/<asset-name>.png`
- `道具资产/<asset-name>.png`

Do not write generated images under `生产资产`.

Image QA gate: image generation must start with environment preflight, then a 风格确认波次 that generates only 第一个场景和第一个人设. Stop and ask for 用户确认风格基准 before generating dependent assets. After confirmation, later characters must upload 人设风格基准参考; later scenes, props, and interfaces must upload 场景风格基准参考 plus any asset-family mother image. Do not write fixed style bans: 不要写死非Q版、非玩具感、非卡通低龄化. 如果用户选择 Q版, the first confirmed scene/character baselines define the Q版 style and later images follow those references. Reference-dependent jobs must use 真实上传/编码参考图; prompt-only reference is forbidden. character with identity props remains a character asset: `鬼财神_财神殿执掌者铁算盘造型` belongs in `人设资产`, not `道具资产`. Asset family: `天机一型手机_三视图` is the phone mother asset; system mall, Douyin UI, and phone screen variants must reference it and keep body, camera, border, screen ratio, and material consistent.

## Commands

```bash
python scripts/build_image_jobs.py --asset-bible 生产资产/_内部/asset-bible.md --out 生产资产/_内部/image-jobs-style-preview.jsonl --style-stage preview
python scripts/generate_images.py --jobs 生产资产/_内部/image-jobs-style-preview.jsonl --manifest 生产资产/_内部/image-manifest.json --resume
# Stop for 用户确认风格基准. After approval:
python scripts/build_image_jobs.py --asset-bible 生产资产/_内部/asset-bible.md --out 生产资产/_内部/image-jobs.jsonl --style-stage confirmed
$env:SOURCE_TRUE_STYLE_CONFIRMED='1'; python scripts/generate_images.py --jobs 生产资产/_内部/image-jobs.jsonl --manifest 生产资产/_内部/image-manifest.json --resume
python scripts/validate_image_manifest.py 生产资产/_内部/image-manifest.json --jobs 生产资产/_内部/image-jobs.jsonl
```

## Job JSONL Shape

Each line is one image job:

```json
{"job_id":"character-linye-black-robe","asset_name":"林夜_黑袍造型","asset_type":"character","prompt":"GPT-image-2，16:9，3D国漫，角色三视图，白色背景。","output_dir":"人设资产","output_file":"林夜_黑袍造型.png","depends_on":[],"reference_images":[],"provider":"openai-compatible","model":"gpt-image-2","size":"16:9","status":"pending"}
```

Required fields:

- `job_id`
- `asset_name`
- `asset_type`
- `prompt`
- `output_dir`
- `output_file`
- `depends_on`
- `reference_images`
- `provider`
- `model`
- `size`
- `status`

`depends_on` contains stable asset names. `reference_images` contains objects with `asset_name`, `path`, and `purpose`.

## Manifest Shape

Manifest `status` values are `done`, `failed`, `blocked`, `renamed`, and `deprecated`. Reconciliation migrations must preserve traceability:

- Canonical `renamed` assets include `previous_asset_name`, `aliases`, `migration_reason`, and `evidence_anchor`.
- Former-name `renamed` tombstones include `replaced_by`, `migration_reason`, and `evidence_anchor`.
- `deprecated` former assets include `replaced_by`, `migration_reason`, and `evidence_anchor`.
- Copy packs bind only canonical non-deprecated assets unless the line explicitly needs a migration review note.

```json
{
  "version": 1,
  "provider": "openai-compatible",
  "base_url_label": "local-relay",
  "assets": [
    {
      "asset_name": "林夜_黑袍造型",
      "asset_type": "character",
      "path": "人设资产/林夜_黑袍造型.png",
      "status": "done",
      "prompt_hash": "sha256:example",
      "model": "gpt-image-2",
      "size": "16:9",
      "attempts": 1,
      "depends_on": [],
      "references": [],
      "previous_asset_name": "",
      "aliases": [],
      "replaced_by": "",
      "migration_reason": "",
      "evidence_anchor": ""
    }
  ]
}
```

Do not include API keys in manifests, logs, reports, or copy packs.

## Copy Pack Binding

Copy packs may use manifest paths:

```text
上传参考图：
- 角色1 = 林夜_黑袍造型 = 人设资产/林夜_黑袍造型.png
```

Copy packs must not invent image paths. If manifest status is missing, failed, or blocked, write:

```text
- 角色1 = 林夜_黑袍造型 = 需人工确认（image-generator failed or blocked）
```
