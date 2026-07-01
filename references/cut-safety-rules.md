# Cut Safety Rules

Use this reference only when the user asks about manual deletion, trimming, or compression risk.

## Output Boundary

- Return risk notes, not a rewritten compressed story.
- Identify deletions by exact feed line numbers.
- Add exact source spans when source text or source-index anchors are available.
- Leave final deletion choices to the user.

## Risk Levels

- Low risk: repeated visual pause, redundant ambient-only beat, or removable reaction that does not carry setup, result, reveal, dialogue, identity, or asset continuity.
- Medium risk: useful but non-load-bearing reaction, mood extension, or secondary beat whose removal may reduce clarity.
- High risk: lost setup, lost cause, dangling reaction, broken reveal, lost identity evidence, broken relationship evidence, broken asset continuity, missing payoff, or missing hook.

## Required Note Shape

```text
- Lines/source span:
  - Risk:
  - Why:
  - Safer boundary:
```

Do not produce a rewritten short version.
