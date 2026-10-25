# A status line for the VS Code panel

The question, the options, the evidence and the decisions are in
[PLAN.md](PLAN.md). [probe/](probe/) is the test mod that collected the
evidence, as it was when it ran. Its `probe-report.json` has the home
directory as `~`, and `<project>` and `<session>` for the project and the
session's id: the repo is public.

- 2026-10-25: `install` now installs the plugins, and `tools/check` uses a
  copy of the plugin API's types, not those of the main checkout. The
  reasons are in [PLAN.md](PLAN.md), at the end.
