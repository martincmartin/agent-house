# Transcript scan results

Aggregate counts only. No transcript text is kept here, and the repo is
public. Each run takes the 50 most recently changed transcripts in
`~/.claude/projects/`, so a later run sees a different sample.

## Run 1: 2026-10-21, about 11:20 (the numbers in `PLAN.md`)

`scan.py` without the skill-file count.

- 50 sessions over 25.1 days (2026-09-26 to 2026-10-21), in 4 project
  directories: 41 in `stem/watches`, 6 in `stem/work1/watches`, 2 in
  `stem2/watches`, 1 in `stem3/watches`.
- Skill tool calls: `python-programming` 1, `dataviz` 1.
- Slash commands: `/compact` 255, `/clear` 48, `/model` 10, `/doctor` 3.
- Tool calls: Bash 28,424, Read 3,848, Edit 890, Write 657, ToolSearch 72,
  Monitor 68, WebFetch 43, other tools fewer. MCP tool calls: 0.
- `slidev` skill file opened directly: 10. This came from a one-off count, not
  `scan.py`: the number of transcript lines with a `tool_use` that names
  `skills/slidev/SKILL.md`.

## Run 2: 2026-10-21, about 13:30

`scan.py` with the skill-file count (one count for each tool call that names a
skill's `SKILL.md`).

- 50 sessions over 25.2 days.
- Skill tool calls: `python-programming` 1, `dataviz` 1.
- Skill files opened directly: `slidev` 15, `docs-audit` 6, `quality-review`
  4, `python-programming` 1, others 1 each.

Run 2 includes this task's own sessions. They read and edited the `slidev` and
`quality-review` skill files as files, so its counts overstate how often an
agent opened a skill to follow it.

## What the counts support

In both samples the Skill tool ran twice in 50 sessions, while the `slidev`
skill file was opened directly at least 10 times. The stem `AGENTS.md` names
that skill as a trigger ("before you edit a deck file"). This is one sample
and an inference, not a measurement of how often a harness loads a skill.
