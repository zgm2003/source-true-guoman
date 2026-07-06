# Image Generation Retry Rules

Use this file when calling the local OpenAI-compatible image relay.

## Retryable errors

- network timeout
- connection reset
- HTTP 429
- HTTP 500
- HTTP 502
- HTTP 503
- HTTP 504
- empty response
- malformed response that may be transient
- temporary image URL download failure

## Non-retryable errors

- missing API key
- invalid base URL
- invalid job JSON
- missing dependency output
- unsupported output folder
- cyclic dependencies
- authentication failure
- permanent provider validation error

## Backoff

Use exponential backoff with jitter. Default settings:

- max retries: `3`
- base delay seconds: `1.0`
- max delay seconds: `20.0`

## Dependency Failure

Failed dependencies block dependent jobs. Blocked jobs must record which stable asset names blocked them.

## Resume

On resume, skip manifest assets with `status = done` and an existing local image path. Retry `failed`, `blocked`, and `pending` jobs after dependency validation.

## Secret Handling

Do not log API keys. Reports should state whether configuration was present, not reveal secret values.
