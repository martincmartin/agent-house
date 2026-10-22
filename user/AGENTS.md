## General

- Write or rewrite technical text with the rules of ASD-STE100 Simplified
  Technical English, so that it is clear, unambiguous and free of AI slop. Use
  the standard's rules: 20/25-word sentence limits, one word one meaning,
  simple tenses, active voice, condition before command.
- If you're unsure about something, it's okay to admit it. Just say you don't
  know.
- When asked to generate or evaluate options, explicitly consider and discuss
  alternatives, and at the end rank them and explain why. Prefer data and
  quantitative over qualitative.
- In all Markdown files, use LaTeX where appropriate, both inline (single
  dollar sign) and display/block (double dollar sign).

## Docs and tasks

The docs are the project's memory. Put what a future agent needs in the
project, not in a harness's memory. If your harness keeps memories (Claude
Code does): before you save one, show it to the user and offer to put it in
the most general AGENTS.md or doc where it is still true (for example
`user/AGENTS.md` in the agent-house repo for all work: your user-level
instructions file links to it; `~/Develop/slidev/AGENTS.md` for all Slidev
projects, which you create if it does not exist yet, or a project's own
AGENTS.md or doc), with the exact text.
Save a memory only if the user prefers that. When a memory's rule moves into a
file, delete the memory.

A project (a repository, a sub-project or a talk) has its own `AGENTS.md` and
`docs/`, and two kinds of documentation, for two readers:

- The project (its docs, code and content) is for a reader who works within
  the decisions. A doc gives the current rules and a summary of why: the
  qualities that decided each choice. Do not describe rejected options or
  history in the project, with one exception: if a reader could be tempted to
  "improve" something with an obvious alternative that was tried and was
  worse, say so in a sentence or two ("not an oversight") and link the task.
- `tasks/YYYY-MM-DD-short-description/` is for a reader who revisits a
  decision. It holds the options, comparisons and evidence, and its own copies
  of the code, tools and inputs that produced them, so that it still works
  after the project changes. Its evidence and copies are never updated later.
  The one later change is a dated line in its README (see "With each
  change").

The `AGENTS.md` index, "read before you act", says _when_ to read each doc:
the action that must make you read it first. `docs/README.md` says _what_ each
doc holds, and nothing else. Each doc starts with what it covers, when to read
it, and its tasks. Write an index, and a README's list of docs or files, as a
bulleted list, not a table: Prettier pads each table cell with spaces to the
width of the widest, and every session that reads the file pays for the
padding. A list has none, and wraps at the line width.

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
not. Put it in the project that is its primary topic: if it is mainly about
one sub-project, put it there, even if it also changes shared files outside
it. If no project is the primary topic, use the smallest project that contains
everything it changes. If you are not sure where something belongs, ask the
user. Start: read `instructions.md` if it exists, and write `PLAN.md`: each
option, its pros and cons (with data where you can), and why you chose one.
Copy into the project the tools that will help future tasks; this duplication
is expected.

## Coding

- On an existing project, preserve its existing conventions.
- Do not add a dependency when the standard library or an existing project
  dependency is sufficient.
- All else being equal, prefer the simplest tool for the job. For example,
  render text with HTML, not SVG. Do not let a check's current limits decide
  the tool: if a check blocks a good design, change the check.
- Before you plan, write or review code in a subject that has a skill, read that
  skill: `python-practices` for Python, `slidev-practices` for a Slidev deck.
- Identify the repository's canonical validation command. Prefer it over
  inventing a new validation workflow. Run it to validate types, formatting,
  etc.
- If a change makes validation take significantly longer, find out why, and
  find how to make validation faster. First, make each speed-up that keeps the
  same thoroughness: each failure before the speed-up must also fail after it.
  If these speed-ups do not remove most of the slowdown, propose options that
  make validation faster but less thorough. For each option, give the time
  that it saves and the value of the checks that it reduces. Do not do these
  options. Ask the user.
- Turn off a check only where it is wrong, at the narrowest scope. Prefer one
  line (`eslint-disable-next-line`, `# noqa: X`). Else put a matching enable
  at the end of the block, even when the block is the whole file. Turn a check
  off for a set of files only in the config, with a comment, when the reason
  holds for every file it matches. Name the rule and give the reason. Delete a
  disable that no longer suppresses anything. Where the tools allow, make the
  project's validation enforce this, and fail on a lint warning.
- Never commit until the user explicitly approves the commit.
- You usually work in a git worktree on a branch. Keep the history of `main`
  linear: before you start work that changes files, rebase on the latest
  `main`. Do not rebase for work that only reads, such as a review: it would
  change the checkout under review. When the user approves a commit, commit on
  your branch, rebase it on `main`, and fast-forward `main` to it. Push only
  when the user asks.

## Reviews

When the user asks for a code review, read the `review-general` skill. For a
simplicity review (over-engineering, duplication), read `review-simplify` too.

## Code design

These rules hold for all code, when you plan it, write it and review it.

- Use descriptive names. Do not use one-letter names, except `x`, `y`, and `z`
  for coordinates. For example, use `index`, not `i`. Use ALL_CAPS only for
  constants at file scope. When a name stops describing what it holds, rename
  it (for example, `wheel_gaps` that also holds the balance).
- Refer to a thing by an object, not by a string. Use a string only to show or
  export a name, as a `name` field. Never look up an object by its name. A dict
  keyed by the names of things shows that the things must be objects.
- Keep each fact and each computation in one place. Do not store a value that
  you can compute from other stored values: compute it in a property or a
  method. If two places compute the same number (a check and a quick
  pre-check, for example), make one function and call it from both. Keep a
  link between objects as a field on the object (for example, `driven` and
  `driver`), not in a separate list of pairs.
- When cases differ only in data, write one general component or function,
  and give each case its data declaratively (in a slide's frontmatter, a table
  or a config file), not a special component for each case. The mechanism is
  then in one place. Cases that differ in behaviour can need code of their
  own.
- Keep an object's fixed data on the object. Keep the data that one run of an
  algorithm computes (positions, scores, visited flags) in a side table: a dict
  keyed by the object, made new for each run. Do not add fields for an
  algorithm to fill in later. Do not share one mutable object between two
  users that each write to it: give each user its own side table.
- Give each function and constructor its inputs as parameters. Do not read
  module globals that callers change. Never change a module's attributes
  (`setattr`) to change what its functions do. Put the numbers that a caller
  can tune in a frozen value object. Keep the default as a constant, and make
  variants from it.
- When you refactor a script that writes a file, make sure the file is
  byte-identical before and after.
- Delete a field or a function that nothing reads.
- Make strings only at the point of output. Results hold objects, and a report
  turns them into text when it prints.
- If another program reads a tool's output, give the tool a machine-readable
  output, such as `--json`. Do not parse its human-readable text.
- Make each class, file and module as independent as practical. If it depends
  on its caller, make the contract explicit: check its inputs and raise an
  error when they are wrong, and document what code cannot enforce.
- An object that holds resources gives callers a way to release them. A second
  request to release does nothing, and after release the object refuses to
  work. If construction fails, free whatever was already made.
