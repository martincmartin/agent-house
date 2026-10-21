# Trim `user/AGENTS.md`

`user/AGENTS.md` loads in every session, in every project and every harness.
Claude Code's `/usage` flagged always-loaded instructions as a cost, so this
task asks: what can move into skills or subagents, what can be cut, and what
can be simpler?

`inputs/user-AGENTS.md` is the file before this task: 10,912 bytes (10,910
characters), about 2.7k tokens.

Sizes in this plan come from `wc -c` (bytes) or Python's `len` (characters).
They differ by a few for text with non-ASCII letters. Token figures are
estimates at 4 bytes a token, not tokenizer counts: a tokenizer can count a
run of spaces as fewer tokens than this, so the savings from removing table
padding can be smaller than estimated.

`inputs/scan.py` `inputs/scan.py` counted tool use in the 50
most recent Claude Code transcripts (2026-09-26 to 2026-10-21, 25 days). The
counts, and how each was made, are in `inputs/scan-results.md`.

## The constraint: skills load only on a trigger

In those 50 sessions the Skill tool ran 2 times. There were 3,848 Reads and 890
Edits. `python-programming` loaded once, though much of the work was Python.
The `slidev` skill file was opened 10 times, each time because the stem
`AGENTS.md` index says "before you edit a deck file, read the `slidev` skill".

This sample suggests that a skill loads reliably only when the user names
it, or when an always-loaded line names the action that requires it. It is
an inference from one sample, not a measurement. A rule that applies to
nearly every edit must stay in `user/AGENTS.md`. A rule that moves to a skill
leaves a trigger line: "Before you X, read the Y skill."

Subagents were considered for the doc-sync search and found not worth it: the
search takes about two greps inline, a subagent starts cold, Claude Code
discourages spawning one unless the user asks, and Pi has no subagents.

## Decisions

| Change | Est. tokens saved | Why |
| --- | --- | --- |
| "Code-quality reviews" → `quality-review` skill, with a trigger line | ~250 | It runs only when the user asks, so the trigger is reliable. About half of it repeated the subagent's own "Required inputs". |
| RGB swatch rule → stem `docs/theme.md` | ~80 | Outside `~/Develop/slidev/`, no Markdown file in `~/Develop` holds a hex colour. The stem index sends colour work to `docs/theme.md`. |
| Shorten "inspect the repository and preserve its existing conventions" to "preserve its existing conventions" | ~5 | First cut, because the harness prompts say it. Restored after the second review: that was checked only for Claude Code, not for Codex, OpenCode or Pi. |
| Cut "think step by step", the STE100 list of text kinds, the "53" | ~60 | Current models reason by default. "Technical text" covers the list. |
| Cut "As with everything, the costs … catching bugs early" | ~30 | "As independent as practical" already says it. |
| Merge Code design rules: names + rename; fact + computation; side table + shared mutable object; shorter independence rule | ~120 | Same rules, fewer words. |
| Commit sequence made explicit: commit, rebase on `main`, fast-forward `main`, push only when asked | ~0 | The user had to spell the sequence out. |
| Memory rule says it is for harnesses with memories, and that `~/Develop/slidev/AGENTS.md` may not exist yet | ~0 | The repo's rule: say when a rule is for one harness. The file did not exist. |
| Add "Before you write or change Python, read the `python-programming` skill." | −15 | It loaded once in 25 days without a trigger. |
| Indexes and README lists of files as bulleted lists, not tables, in agent-house and stem; a rule for it in Docs | ~400 in stem `docs/README.md` alone (4,293 → 2,715 chars) | Prettier pads each table cell to the widest one. `table_to_list.py` made the lists, and checked that each cell's text is still there. The user asked for it. |
| Reflow to 80 columns, one space after a full stop, fix "indepenent" | ~0 | Consistency. Tasks and Docs: same words, reflowed only, except the list rule above. |

Result: 9454 chars, about 2.3k tokens. The quality-review skill adds about
40 tokens to the skill list.

## Tasks and Docs (about 1k tokens): option A, applied

The first proposal moved "The structure" and the task mechanics into a
`project-docs` skill, loaded "before you add, rename or remove a doc". The
user's objection: nearly every change to a project changes a doc, and an edit
can change _what_ a doc holds (its `docs/README.md` entry) or _when_ to read
it (the `AGENTS.md` index). The docs are a general, explicit version of
memories. So the rules are needed at each edit, not only when a doc is made.

Sorted by when a rule fires:

- **At each edit:** current rules and why, no rejected options, the "not an
  oversight" exception; one fact in one place; rule apart from current choice;
  sub-project facts in its own `docs/`; update docs in the same change; search
  for changed names; a wrong doc is fixed or reported; the dated line in a
  task's README; run the doc check. Also a rule the file lacks: when an edit
  changes what a doc holds, or when to read it, update its first lines, its
  `docs/README.md` entry and the `AGENTS.md` index. The current text says this
  only for adding, renaming or removing a doc.
- **Before you act:** read the index's docs, Chesterton's Fence, cite the docs
  in an analysis.
- **Only when you make something:** the layout of a doc's first lines, of
  `docs/README.md` and of the index (an existing project shows all three); the
  contents of `PLAN.md`; a task keeps copies of its inputs; copy useful tools
  into the project.

Options:

| Option | Est. tokens per session | Risk |
| --- | --- | --- |
| A. One section, "Docs and tasks", ordered by when each rule fires; duplicates merged; the edit-time rule added; no skill | ~860 (saves ~280) | None: all rules stay loaded. |
| B. A, with the make-only rules in a `project-docs` skill | ~710 + ~40 listing (saves ~390) | A new project or task may miss the templates. |
| C. As now (Tasks, Docs and the memory bullet: 4,554 chars) | ~1,140 | The edit-time README and index rule is missing. Two bullets say the same thing. |
| D. All of it in a skill, triggered "before you edit any file" | ~40 listing + a read in nearly every session | Fires almost always, so it costs more than A. |

Ranking: A, then B, C, D. B saves about 110 tokens more than A, but adds a
file to keep and a rule that may not load. The make-only rules are short, and
an existing project shows most of them. Recommendation: A, and fold the memory
rule into it, because docs and memories hold the same kind of fact.

The user chose A. It was applied from the draft below, with two changes.
The memory rule keeps its examples of where a rule can go, because they show
the levels. The no-history rule covers the whole project (its docs, code and
content), as before, not only `docs/`: the draft had narrowed it.
Result: `user/AGENTS.md` is 8715 chars, about 2.2k tokens.

Draft for A (replaces "Tasks", "Docs" and the memory bullet of "General"):

```markdown
## Docs and tasks

The docs are the project's memory. Put what a future agent needs in the
project, not in a harness's memory. If your harness keeps memories (Claude
Code does): before you save one, show it to the user and offer to put it in
the most general AGENTS.md or doc where it is still true, with the exact text.
Save a memory only if the user prefers that. When a memory's rule moves into
a file, delete the memory.

A project (a repository, a sub-project or a talk) has its own `AGENTS.md` and
two kinds of documentation, for two readers:

- `docs/` is for a reader who works within the decisions. A doc gives the
  current rules and a summary of why: the qualities that decided each choice.
  It does not describe rejected options or history, with one exception: if a
  reader could be tempted to "improve" something with an obvious alternative
  that was tried and was worse, say so in a sentence or two ("not an
  oversight") and link the task.
- `tasks/YYYY-MM-DD-short-description/` is for a reader who revisits a
  decision. It holds the options, comparisons and evidence, and its own copies
  of the code, tools and inputs that produced them, so that it still works
  after the project changes. Nothing in it is updated later.

The `AGENTS.md` index, "read before you act", says _when_ to read each doc.
`docs/README.md` says _what_ each doc holds, and nothing else. Each doc starts
with what it covers, when to read it, and its tasks. Write the index and
`docs/README.md` as bulleted lists, not tables: Prettier pads each table cell
with spaces to the width of the widest, which can double the file's tokens.

**Before you act.** Read the docs that the index gives for the action. Apply
Chesterton's Fence: before you remove or change something whose purpose you
do not know, find out why it is there, in the docs and then in their tasks.
Before you write an analysis, re-read the docs on its topic, cite them, and
say what is new.

**With each change.**

- In the same change, update each doc that describes what you changed:
  behaviour, names, commands, files, keys or values. Search `docs/`, the
  READMEs and the `AGENTS.md` files for each name that you changed.
- If the change alters what a doc holds, update its first lines and its
  `docs/README.md` entry. If it alters when to read the doc, update the
  `AGENTS.md` index. Do the same when you add, rename or remove a doc.
- Keep each fact in one place, and link to it. Do not copy a value that code
  or a config file holds: name the file. If you quote a value, say it is an
  example. Keep the rule separate from the current choice: a current choice
  (a theme, a venue) is an example that meets the rule.
- Put what is true of one sub-project in that sub-project's `docs/`.
- If you find a doc that is wrong, fix it in the same change or tell the user.
- If the change alters something a task decided, add a dated line to that
  task's README.
- If the project has a doc check, run it before you commit.

**Tasks.** Work that needs significant investigation, or an important decision
that should be documented, gets a task directory. A code review usually does
not. Put it in the project that is its primary topic, even if it also changes
shared files. If no project is the primary topic, use the smallest project
that contains everything it changes. If you are not sure where something
belongs, ask the user. Start: read `instructions.md` if it exists, and write
`PLAN.md`: each option, its pros and cons (with data where you can), and why
you chose one. Copy into the project the tools that will help future tasks;
this duplication is expected.
```

## Review of 2026-10-21

`review-2026-10-21.md` reviewed agent-house `1a42146` and the stem changes in
`work1`, not this worktree. Each finding was checked against the source.

| Finding | Verdict | Change |
| --- | --- | --- |
| 1. "A built deck has no `/print` route" | Agree. Slidev 53 adds `/print` to a build when `download` is `true`, `"true"` or `"auto"` (`serve-*.mjs`, `__SLIDEV_FEATURE_PRINT__`; `setup/routes.ts`). `?print=clicks` works in any build (`useNav.ts` reads the query). | `slidev` skill: the route exists only with `download`; `/N?print=clicks` always works. |
| 2. "A visual on more than one slide is one element" is too broad | Agree. The reason (each copy starts from its own last state) holds only for a visual that changes. | `slidev` skill: a visual that changes from one slide to the next is one element; a static one can be a copy. |
| 2. The direction rule lost "the layer decides that" | Disagree. That clause explained why no direction code is needed. The skill keeps it: "let the code that draws it move from what is on the screen now to the new target". | None. |
| 3. Permissions "enforce the limits" | Agree, in every harness: a subagent with a shell can write through it. | `docs/harnesses.md`: the limits block tools, not actions. |
| Rebase before every task | Agree: a rebase changes the checkout under review. | `user/AGENTS.md`: rebase before work that changes files; not for work that only reads. |
| stem `docs/README.md` holds more than _what_ | Agree. A past task (`tasks/2026-09-30-docs-organization/`) kept the summary there for people on GitHub; the root `README.md` serves them better. | The summary moved to the stem root `README.md`; "Docs and tasks" cut (it repeated the user-level rule); a dated line in that task's `README.md`. |
| The `slidev` skill is an outside dependency | Agree. | stem `docs/talks.md`, "Set up a clone": run agent-house `install`. |

The review was saved in `user/`, whose files reach every harness. It moved
here, word for word, and the `quality-review` skill now says never to save a
review in such a directory.

## Second review, 2026-10-21

`review-2026-10-21-2.md` reviewed this worktree and the stem changes.

| Finding | Verdict | Change |
| --- | --- | --- |
| 1. "Nothing in it is updated later" contradicts the dated line in a task's README | Agree. | `user/AGENTS.md`: a task's evidence and copies never change; the one later change is a dated line in its README. |
| 2. "Can double the file's tokens" is not measured | Agree. The 4-bytes-a-token estimate cannot support it: a tokenizer can count a run of spaces as one token. | `user/AGENTS.md`: lists, because padding costs every reader and a list wraps. The draft above keeps the old wording, as it was proposed. |
| 3. The scan cannot reproduce the 10 `slidev` reads, and the conclusion is stated too strongly | Agree. | `scan.py` now counts skill files opened directly. `inputs/scan-results.md` keeps both runs' counts and how each was made. The conclusion above is now an inference. |
| 4. No fallback when no `review-quality-*` subagent fits | Agree. The user chose a general fallback over a new general subagent (one more prompt to keep) and over asking each time (an interruption). | `quality-review` skill: a general-purpose subagent with the same delegation and report rules, and the report says no specialist fitted. |
| Limitations: "every harness already preserves conventions" is unverified | Agree: checked for Claude Code only. | The line is back, shorter. |

Units: the plan said "chars" for `wc -c` counts, which are bytes. Fixed above.
