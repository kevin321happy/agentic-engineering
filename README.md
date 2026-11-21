# Agentic Engineering Platform

English · [简体中文](README.zh-CN.md)

**A framework in development for teams that want AI to write code without letting it approve its own work.** Engineers define the expected behavior and acceptable risk. A coding agent proposes a change. The framework is being built to decide, from test results and explicit approvals, whether that change can move forward.

**Status: repository foundation.** You can install the Python package and run its repository checks today. The workflow engine, approval gates and coding-agent integrations are planned, not released. There is no runnable coding workflow yet.

## What a gate is for

Suppose an agent changes a list screen to show an empty state. The empty-list test passes, but there is no result for a list **with** items. The proposed feature workflow would keep the change pending and report the missing regression check. A plausible explanation from the agent is not a test result.

| Planned workflow | What the engineer specifies | What a reviewer should receive |
| --- | --- | --- |
| Feature development | Observable behavior, acceptance cases and scope | Each requirement linked to the actual change and its verification |
| Bug repair | Original symptom, expected behavior and paths that must not change | Root-cause evidence, a check of the original failure and regression results |

The design separates model suggestions from permission to act. A recorded approval should apply to a particular change, not grant permanent write access. Offline replay is planned so contributors can inspect both an approved run and a correctly blocked one without credentials.

## Try the current checkout

From the repository root, with Python 3.11+ and `uv`:

```sh
uv sync --locked --extra dev
uv run pytest -q
```

These tests check the repository contract; they do **not** validate an AI-generated patch. For contribution checks see [Contributing](CONTRIBUTING.md). For what belongs in a project-specific integration rather than the public package, see [the public/private boundary](docs/architecture/public-private-boundary.md).

[Security](SECURITY.md) · [MIT license](LICENSE)
