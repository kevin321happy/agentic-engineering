# Contributing

All changes must preserve the public/private boundary, include deterministic tests for behavior changes, and pass the local quality commands:

```bash
uv run pytest -q
uv run ruff check .
uv run mypy src
```

LLM output is advisory. Workflow routing, evidence validity, gate decisions, and write permissions must remain deterministic and testable.
