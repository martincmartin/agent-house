---
name: quality-review
description: How to get a code-quality review from a review-quality-* subagent, or a general one when none fits, and where to save its report. Read when the user asks for a code-quality review.
---

# Code-quality review

Use the `review-quality-*` subagent that fits the project, for example
`review-quality-slidev` for a Slidev project.

If none fits, use a general-purpose subagent with the same delegation and the
same report rules (below). Tell it to review for correctness, maintainability
and simplicity; to consider alternatives, rank them and say why; and to report
the task directory, the files it read first, each finding with its evidence,
and the limits of the review. Say in the report that no specialist reviewer
fitted.

Pi has no subagents: there, do the review yourself, with those instructions,
and change no file while you review.

## The delegation

Give the reviewer this field explicitly:

- `TASK_DIR`: the absolute path of the active task directory, or say
  explicitly that there is no TASK_DIR, because there is no task for this
  change. If the task directory is ambiguous, ask the user. Never choose a
  task only because its directory is the newest.

Also tell the reviewer to:

- read the relevant files in TASK_DIR before it reviews. If there is no
  TASK_DIR, name the relevant docs for it to read;
- return the complete Markdown report, and write no files;
- name the task directory, or say that there is none, in the report.

## After the reviewer returns

- If it reports missing inputs ("REVIEW BLOCKED"), resolve them and call it
  again.
- Otherwise, save its complete report word for word, as
  `review-YYYY-MM-DD.md`: in TASK_DIR if there is one, else at the root of the
  project that it reviewed. If a file with that name exists, add a suffix to
  make the name unique. Never overwrite a review. Never save one in a directory
  whose files reach the harnesses, such as agent-house's `user/`.
- Tell the user where you saved the report.
