---
name: learn-from-corrections
description: Read after you fix a bug or make another significant correction to earlier work (duplicate code, over-engineering, a wrong abstraction or kind of object, a wrong doc), whoever found it; before you tag a talk or make a release; and when the user asks for a milestone review.
---

# Learn from each correction

A correction is a change to earlier work that makes it better: a bug fixed,
or a design, a structure or a doc improved. It is significant when it
changes how the work is made or organised, not a typo or a better word.

Perfect work from the start is not the goal: a rule for each possible
mistake makes a list with no end. The goal is to stop a kind of problem that
comes back, at the lowest cost in context.

## At each correction

1. **Ask two whys.** Why was the work done that way? Why was it not caught
   sooner: by a tool, a review, or a rule read before the action?
2. **Look for a rule that already says it,** in the always-loaded
   instructions, the skills and the project's docs. If one exists, ask why
   it did not act: it was not loaded, it is not read at the action, or its
   words do not match the case.
3. **Search for the same problem** in the work now (`rg`, a small script). If
   you find more, correct them in the same change: the kind will come back.
4. **Compare it with both watchlists** (below), the whole of each. Look for a
   likeness from any angle. It is a match only if you can name a cause that
   the two share (a habit, a gap in what is tested or reviewed, a rule not
   read at the action), and one lesson stops both. If you are not sure of
   the link, it is not a match.
5. **Sort the correction:**
   - **It will come back:** a match in step 4; or the cause is general (a
     framework, a tool, a habit, a process), step 2 found a rule that did
     not act, step 3 found more, or a bug failed with no error. Make the
     lesson now (the ladder, below), and delete each entry that the lesson
     stops.
   - **Cost of doing business:** do nothing more. Most corrections are here.
   - **Not sure:** add an entry to the watchlist where it is true.
6. **Tell the user** the two whys, the group and what you did, in a few
   lines; in one line for a cost of doing business.

## The ladder

Put the lesson as low as it can go. Each step up costs more context:

1. Make the problem impossible: a design or a structure that cannot have it.
2. A tool finds it (a lint rule, a type check, a test, a validator), with a
   message that states the rule. Only where a tool can see the problem.
3. A rule, with an example, where it is read before the action: a practices
   skill, a review skill, a project's doc. Most design lessons go here.
4. A rule in an always-loaded file: only for a rule that holds for most work.

If a rule already exists (step 2), change it: move it to where it is read,
add the case as an example, or make a tool find it. Do not add a second copy.
Put a new rule in the most general place where it is true (`user/AGENTS.md`
or a skill for all work; a project's docs for that project).

## The watchlists

There are two, and each comparison reads both:

- The project's `docs/watchlist.md`, for a problem of that project.
- `watchlist.md` beside this file, for a problem that can happen in any
  project. It is in agent-house: before you write to it, ask the user, and
  make the change in an agent-house worktree. If you cannot read it, tell the
  user, and compare with the project's list only.

The first line of the project's list is the project's last milestone:
`Last milestone: YYYY-MM-DD, <commit>`. Each entry is a few lines: the date;
what changed; why the work was done that way; why it was not caught sooner; a
link (a commit or a task). Give it no class: a later reader finds the
likeness. Keep at most about 20 entries in each list.

## At a milestone

Do this before you tag a talk or make a release, and when the user asks for a
milestone review (for example, at the end of a phase of work):

1. Read both watchlists. A list that does not exist yet is empty.
2. Read the project's history since its last milestone: the commit in the
   first line of the project's list; if there is none, the last tag; if
   there is no tag, all the history. Read the log (`git log <commit>..`);
   open a commit's diff only when its message does not show the correction.
3. Also read the work that is not committed (`git status`, `git diff HEAD`),
   and the corrections of this session.
4. Look for corrections that are alike when side by side, with a shared
   cause as in step 4 of "At each correction". Make a lesson for each group
   (the ladder).
5. Delete the oldest entries that have no match until each list is short
   again.
6. Write the date and the last commit that you read (`HEAD`) in the first
   line of the project's list. If the list does not exist, make it.
7. Tell the user the range that you read (and if it included work that is
   not committed), the groups and the lessons, or that there were none.
