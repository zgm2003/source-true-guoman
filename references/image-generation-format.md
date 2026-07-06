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

## Commands

```bash
python scripts/build_image_jobs.py --asset-bible 生产资产/_内部/asset-bible.md --out 生产资产/_内部/image-jobs.jsonl
python scripts/generate_images.py --jobs 生产资产/_内部/image-jobs.jsonl --manifest 生产资产/_内部/image-manifest.json --resume
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
      "references": []
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
