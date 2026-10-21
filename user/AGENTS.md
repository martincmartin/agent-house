## General

- Write or rewrite technical text with the rules of ASD-STE100 Simplified Technical English so it is clear, unambiguous, and free of AI slop.  Use for documentation, READMEs, runbooks, procedures, error messages, release notes, incident reports, and API guides.  Use the standard's 53 rules: 20/25-word sentence limits, one word one meaning, simple tenses, active voice, condition before command.
- If you're unsure about something, it's okay to admit it. Just say you don’t know.
- When asked to generate or evaluate options, think step by step, explicitly consider and discuss alternatives, and at the end rank them and explain why.  Prefer data and quantitative over qualitative.
- In all Markdown files, use LaTeX where appropriate, both inline (single dollar sign) and display/block (double dollar sign).
- In Markdown, give each RGB colour value a swatch and a plain description: `<span style="display:inline-block;width:1.5em;height:1.5em;background:#RRGGBB;border:1px solid #888;vertical-align:middle">&nbsp;</span> #RRGGBB, a dark navy blue`. GitHub strips the swatch, so the description must stand alone.
- Before you save a memory, show it to the user and offer to put it in an
  AGENTS.md instead. Suggest the most general AGENTS.md where the rule is still
  true (for example `~/Develop/agent-house/user/AGENTS.md` for all work,
  `~/Develop/slidev/AGENTS.md` for all Slidev projects, or a repo's or talk's
  own AGENTS.md), and give the exact text to add. Save a memory only if the user
  prefers that. When a memory's rule moves into an AGENTS.md, delete the memory.


## Tasks

A task that requires significant investigation, or that requires an important
decision that should be documented, gets its own directory,
`tasks/YYYY-MM-DD-short-description/`.  A code review generally doesn't need a
task directory.

- Put it in the tasks/ of the project that is its primary topic. If a task is
  mainly about one sub-project, put it there, even if it also makes incidental
  changes to shared files outside that project. If no one project is its primary
  topic, use the smallest project that contains everything the task changes.
- **Start.** Read `instructions.md` if it exists. Write `PLAN.md`: each option you
  consider, its pros and cons (with data where you can), and why you chose one.
- **The task directory is for a reader who may revisit the decision.** It holds
  the options, comparisons, evidence, and the code and tools that produced them.
  It must still work after the project changes, so it keeps its own copies of
  what it used, and they are not updated later.
- **The project (docs, code, content) is for a reader who works within the
  decision.** Everything there helps the reader understand the current state of
  the project, what is there. Do not describe rejected options or history there,
  with one exception: if a reader could be tempted to "improve" something with
  an obvious alternative that was tried and was worse, say so in a sentence or
  two ("not an oversight") and point to the task directory.  Keep the
  documentation (see "## Docs" below) up to date while you work, so it always
  reflects changes you made in e.g. code, tools, content, etc.  It should
  reflect what a future reader needs to work within the decision, including
  why. Copy tools that will help future tasks into the project; this duplication
  is expected.
- If you are not sure where something belongs, ask the user.
- If the project later changes something a task decided, add a dated line to
  that task's README.

## Docs

Each project has two kinds of documentation. `docs/` is for a reader who works
within the decisions. `tasks/` is for a reader who revisits one (see Tasks). A
project can be a repository, a sub-project or a talk. Each has its own
`AGENTS.md` and `docs/`.

**The structure.**

- A project's `AGENTS.md` has an index, "read before you act": for each doc,
  the action that must make you read it first. The index says _when_.
- `docs/README.md` lists each doc and what it holds. It says _what_, and
  holds nothing else.
- Each doc starts with what it covers, when to read it, and links to the
  relevant tasks.
- A doc gives the current rules and a summary of why: the qualities that
  decided each choice. It does not describe the rejected options. It links the
  relevant tasks for more depth.
- Keep each fact in one place, and link to it. Do not copy a value that code
  or a config file holds: name the file. If you quote a value, say it is an
  example.
- Keep the rule separate from the current choice. A current choice (a theme,
  a venue) is an example that meets the rule, not the rule.
- Put what is true of one sub-project in that sub-project's `docs/`.

**Before you act.**

- Read the docs that the index gives for that action. Apply Chesterton's
  Fence: before you remove or change something whose purpose you do not know,
  find out why it is there. Look in the docs, then in the tasks that they
  link.
- Before you write an analysis, re-read the docs on its topic, cite them, and
  say what is new.

**Keep the docs current.**

- In the same change as the code, update each doc that describes what you
  changed: behaviour, names, commands, files, keys or values. Search `docs/`,
  the READMEs and the `AGENTS.md` files for each name that you changed.
- When you add, rename or remove a doc, update the `AGENTS.md` index and
  `docs/README.md` in the same change.
- If you find a doc that is wrong, fix it in the same change or tell the user.
- If the project has a doc check, run it before you commit.

## Coding

- On an existing project, inspect the repository and preserve its existing conventions.
- Do not add a dependency when the standard library or an existing project dependency is sufficient.
- All else being equal, prefer the simplest tool for the job. For example,
  render text with HTML, not SVG. Do not let a check's current limits decide
  the tool: if a check blocks a good design, change the check.
- Never commit after making a change.  Only commit after the user gives explicit approval to commit.
- Identify the repository's canonical validation command. Prefer it over inventing a new validation workflow.  Run it to validate types, formatting, etc.
- If a change makes validation take significantly longer, find out why, and
  find how to make validation faster. First, make each speed-up that keeps
  the same thoroughness: each failure before the speed-up must also fail
  after it. If these speed-ups do not remove most of the slowdown, propose
  options that make validation faster but less thorough. For each option,
  give the time that it saves and the value of the checks that it reduces.
  Do not do these options. Ask the user.
- You'll work in a git worktree on a branch.  We want a linear git history on
  main, so before you start a task, rebase on the latest main commit, and after
  you commit, rebase it on main.

## Code-quality reviews

When the user asks to review for code quality, invoke the relevant
`review-quality-*` subagent.

Include these fields explicitly in the subagent's delegation prompt:
- TASK_DIR: absolute path to the active task directory, or explicitly say there
  is no TASK_DIR if there is no task for this change.  If the task directory is
  ambiguous, ask the user.  Never select a task merely because its directory is
  newest.

Also explicitly instruct the reviewer to:
- If there's a TASK_DIR, read relevant files in TASK_DIR before reviewing,
  otherwise point reviewer to any relevant docs.
- Return the complete Markdown report without writing any files.
- Include the task directory, or lack of one, in the report.

After the reviewer returns:
- If it reports missing inputs, resolve them and invoke it again.
- Otherwise, save its complete report verbatim in TASK_DIR if there is one, or a
  new `review-[date].md` file, if that file already exists, add a suffix to make
  the filename unique.
- Never overwrite an existing review.
- Tell the user where the report was saved.

## Code design

- Use descriptive names. Do not use one-letter names, except `x`, `y`, and `z`
  for coordinates. For example, use `index`, not `i`. Use ALL_CAPS only for
  constants at file scope.
- Refer to a thing by an object, not by a string. Use a string only to show or
  export a name, as a `name` field. Never look up an object by its name. A dict
  keyed by the names of things shows that the things must be objects.
- Keep each fact in one place. Do not store a value that you can compute from
  other stored values: compute it in a property or a method. Keep a link
  between objects as a field on the object (for example, `driven` and
  `driver`), not in a separate list of pairs.
- Keep an object's fixed data on the object. Keep the data that one run of an
  algorithm computes (positions, scores, visited flags) in a side table: a dict
  keyed by the object, made new for each run. Do not add fields for an
  algorithm to fill in later.
- Give each function and constructor its inputs as parameters. Do not read
  module globals that callers change. Never change a module's attributes
  (`setattr`) to change what its functions do. Put the numbers that a caller
  can tune in a frozen value object. Keep the default as a constant, and make
  variants from it.
- When you refactor a script that writes a file, make sure the file is
  byte-identical before and after.
- Keep each computation in one place, as well as each fact. If two places
  compute the same number (a check and a quick pre-check, for example), make
  one function and call it from both.
- Delete a field or a function that nothing reads.
- When a name stops describing what it holds, rename it (for example,
  `wheel_gaps` that also holds the balance).
- Make strings only at the point of output. Results hold objects, and a report
  turns them into text when it prints.
- If another program reads a tool's output, give the tool a machine-readable
  output, such as `--json`. Do not parse its human-readable text.
- Make each class, file and module as indepenent as practical without
  significant extra effort.  If it depends on behaviour from a caller/user, make
  the contract as explicit as possible: check inputs and throw an
  exception/error if they're incorrect, make it easy for callers to dispose of
  things in the right way at the right time, and if there's no way to enforce it
  in code, document it clearly.  As with everything, the costs in terms of
  performance and maintainability must be balanced against catching bugs early.
- An object that holds resources gives callers a way to release them.  A second
  request to release does nothing, and after release the object refuses to work.
  If construction fails, free whatever was already made.
- Do not share one mutable object between two users that each write to it.  Keep
  each user's data in that user's own side table.
