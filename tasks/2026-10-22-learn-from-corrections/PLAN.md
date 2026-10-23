# Learn from each correction

We often change earlier work because it was worse than it should be. A test,
a deploy, a review, the user or we ourselves find the problem. Some problems
are bugs. Many are not: duplicate or near-duplicate code, over-engineering, a
dict with string keys where a class should be, a wrong abstraction, a doc
that says something false or says it twice. Books such as _Code Complete_,
_The Pragmatic Programmer_, _Design Patterns_ and _Clean Code_ are mostly
about this second kind.

This task asks what to do after such a correction: when to ask why the work
was done that way and why it was not caught sooner, when the answer becomes
a rule, a check or a change of design, and how to see a kind of problem that
comes back slowly, without filling the always-loaded instructions with
narrow rules.

**A correction** here is a change to earlier work that makes it better, not
new work. It is significant when it changes how the work is made or
organised: a bug, a design, a structure, a rule. A typo, a better word or a
small style fix is not significant.

## The constraints

- **Always-loaded text costs every session.** `user/AGENTS.md` loads in
  every session of every project, and so does each skill's description. A
  skill's body loads only when something starts it: the user names it, or a
  line in the context (an always-loaded line, or its description) names the
  action that needs it (`tasks/2026-10-21-trim-user-agents-md/PLAN.md`). So a
  narrow rule in `user/AGENTS.md` costs much, and a skill costs only its
  trigger.
- **A session does not remember earlier sessions.** "This is the third time
  for this kind of problem" is possible only if something written says so.
- **A problem has no one class.** One problem is a member of many classes, as
  the animals of Borges's "Celestial Emporium of Benevolent Knowledge" are. If
  each problem gets a class when it is found, a later one of the same kind can
  get another class, and the match is lost. So the match must be made when a
  new problem is compared with the old ones, not when the old ones are filed.
- **Perfect work from the start is not the goal.** A rule for each possible
  mistake makes a list that has no end. It pushes useful text out of the
  context, and it makes work slow.
- **Many rules exist already.** `user/AGENTS.md` ("Code design") and the
  practices skills already say, for example, "keep each fact in one place"
  and how to choose the kind of class. When such a rule did not stop a
  problem, one more rule will not help. The lesson is about why the rule did
  not act.

## The evidence: two days of work (2026-10-22 and 2026-10-23)

Each correction, why the work was done that way, and why it was not caught
sooner. 1 to 7 are bugs, in `slidev/stem`. 8 to 10 are not bugs.

1. **The callouts showed before their click on GitHub Pages.** A comment
   before a component's root element makes a second root in a production
   build, and Vue drops the class and `v-click` that the slide gives the
   component. Why: `slidev dev` hides it. Not caught: validation builds the
   deck, but checks only navigation, not what shows. The same mistake was in
   3 files.
2. **A link to one slide gave GitHub's 404 page.** Pages uses only the
   `404.html` at the site's root. Why: the docs said "links to one slide
   work", from belief, not a test. Not caught: nothing loaded a link from a
   server that acts as Pages does.
3. **The article's prerender timed out in CI.** Why: a step took 25 s on a
   12-core Mac, and more on a 4-core runner with no GPU. Not caught: only the
   publish workflow runs the prerender.
4. **Two lint disables had no enable,** so each turned the rule off for the
   rest of its template. Why: nothing asks for the enable. Not caught: ESLint
   does not check this by default. The same mistake was in 2 files.
5. **A lint warning never failed validation** (`eslint .` exits 0 on
   warnings), so every rule set to "warn" was in effect off. Found while
   testing the fix for 4.
6. **An earlier commit undid the commit before it.** A worktree's index was
   stale after `main` moved in another worktree, and the stale index was
   committed.
7. **The favicon fix worked in a build but not in `pnpm dev`** (2026-10-23).
   The fix for the Pages favicon used `%BASE_URL%`, which only a build
   replaces. Why: the fix was checked with a build only. Not caught: no check
   loads the favicon in dev. This is bug 1 the other way round.
8. **This plan's trigger was in two places**, `user/AGENTS.md` and the
   skill's description. Not a bug: a design problem. Why: the trim task says
   "leave a trigger line", and the plan followed it without asking where the
   line belongs. Not caught: the rule "keep each fact in one place" exists
   (`user/AGENTS.md`, "Docs and tasks"), but it is written for docs, and
   nothing made the plan's author apply it to a skill. The user found it.
9. **This plan's skill description was about 500 characters,** most of it
   on what the skill does, not when to read it. Why: the other skills'
   descriptions do the same. Not caught: no rule says what a description
   holds. The same problem is in all 5 agent-house skills (115 to about 700
   characters). The user found it.
10. **`TopLevel`, a subclass of `HTMLParser`, was written as a dataclass**
    (`slidev/stem`'s `tools/vuecheck.py`). Not a bug: it worked. Why: a
    habit. Not caught at first: the `python-practices` skill says how to
    choose the kind of class, and it was loaded. Found when the code was
    read against the skill.

**Groups that show only side by side:**

- **What people use is not what we test** (1, 2, 3 and 7): dev against a
  build, a local server against Pages, a Mac against a CI runner, and a
  build against dev. No narrow class ("Vue root comments", "Pages 404")
  shows it.
- **A rule existed and did not act** (8 and 10). Another rule would not have
  helped. The questions are where the rule is, when it is read, and whether
  its words match the case.

**A rule of three in space, not in time:** for 1, 4 and 9, a search found
more of the same problem at once.

## Decision 1: when to reflect

- **A. At each correction.** Ask the two whys, and sort the correction
  (decision 2). The context is fresh, and it takes a minute. It sees one
  correction at a time, so it misses a pattern that needs several side by
  side.
- **B. At a milestone** (before a talk is tagged or a release is made, or
  when the user asks). Read the watchlists and the corrections since the last
  milestone, and look for groups. It sees corrections side by side. Alone, it
  is late: the context of each one is gone, and a change that was easy at
  once is now work.
- **C. Only when the user asks.** No cost, but the user must remember, and
  most corrections get no reflection.
- **D. A and B.** A gives the fresh answer and the watchlist entry; B finds
  the groups.

**Chosen: D.** A alone misses groups (1, 2, 3 and 7 are a group only side by
side); B alone loses the context.

**The milestones are a tag, a release, and a request from the user.** A tag
and a release are each one clear action that a session does. The user knows
when a phase of work ends and another starts; a session does not. So the user
can ask for a milestone review at any time ("do a milestone review", or the
skill's name). "A task ends" is not a milestone: a session seldom knows that a
task has ended, so that trigger would fire at random or never. Each milestone
needs a trigger of its own, as the correction does (the review, finding 1):
in the skill's description (below, "Where the trigger goes"), and, for a
talk, a line in the doc that is read before the tag (`slidev/stem`'s
`docs/talks.md`, "Tag, rebuild or retire a talk").

**Where the trigger goes: in the skill's `description:` only.** Every
harness puts each skill's name and description in every session's context,
as `user/AGENTS.md` is (the Agent Skills standard; seen in Claude Code; the
other three harnesses from their docs, not tested). So a description costs
the same as a line in `user/AGENTS.md`, and it keeps all of the skill in one
file: someone else can install the skill alone, and a reader who changes it
finds everything there. One difference can remain: `user/AGENTS.md` reads as
an instruction, and a description as an entry in a list of skills. The trim
task's sample (`tasks/2026-10-21-trim-user-agents-md/PLAN.md`, "The
constraint") is weak evidence for that difference: the skill that loaded
once in 50 sessions had a description that said what it held, not when to
read it. So the plan tests it (below, "The test").

**The description says only when to read the skill.** Every session loads it,
and its one job is to start the skill at the right time. What the skill does
is in its body, which loads only with the skill (correction 9).

**A project's watchlist records its last milestone,** in its first line: the
date and the project's commit. A tag marks a milestone in git, but a request
from the user leaves no mark, and the review needs "the corrections since the
last milestone". The review reads the line, and writes a new one when it
ends. The shared list has no such line: its commits are in agent-house, not
in the project whose history the review reads.

## Decision 2: when a correction becomes a lesson, and where the lesson goes

**Sort each correction into one of three groups:**

- **It will come back.** Make the lesson now. Signs: the cause is general (a
  framework, a tool, a habit, a process; not one file or one feature); **a
  search finds more of the same problem now** (the grep test); a rule
  already exists and did not act; or, for a bug, it failed with no error. The
  grep test is the one objective sign, and it often meets the rule of three
  at once (1, 4 and 9).
- **Cost of doing business.** Make the correction. Do nothing more. Most
  corrections are here.
- **Not sure.** Add an entry to the watchlist (decision 3).

**Put the lesson as low on this ladder as it can go.** Each step up costs
more context:

1. **Make the problem impossible:** a design or a structure that cannot have
   it (a type in place of a dict with string keys; one function in place of
   two copies).
2. **A tool finds it:** a lint rule, a type check, a test, a validator, with
   a message that states the rule. It costs no context until it fails, and
   then it teaches at the right time. Use it where a tool can see the
   problem. Most design problems (duplication, over-engineering, a wrong
   abstraction) a tool cannot see.
3. **A rule where it is read before the action:** a practices skill, a review
   skill, a project's doc. Most design lessons go here. Give an example: a
   rule that names the case is easier to apply than an abstract rule.
4. **A rule in an always-loaded file** (`user/AGENTS.md`, a project's
   `AGENTS.md`). Only for a rule that holds for most work.

**Before you add a rule, look for one that already says it.** If one exists,
the lesson is a change to that rule: move it to where it is read before the
action, add the case as an example, or make a tool find it. Do not add a
second copy (8 and 10).

Options for the bar:

- **A. A fixed count:** a lesson after the third time a kind of problem
  comes. It is simple, but it needs a class for each problem (the Borges
  problem) and a memory across sessions.
- **B. Judgement with signs** (the list above), with the grep test as the one
  objective sign. It needs no class and no memory. It can be wrong, but the
  watchlist catches a "not sure" that comes back.
- **C. A lesson for every correction.** It fills the context, and most
  lessons are never used again.

**Chosen: B.** A count is good only where classes are fixed, and here they
are not. The ladder keeps the cost of a wrong "it will come back" low: a
design change or a tool costs no context, and a rule in a scoped skill costs
context only for its action.

## Decision 3: how to see a kind of problem that comes back slowly

- **A. A watchlist (chosen).** A short file of "not sure" corrections. Each
  entry: the date, what changed, why the work was done that way, why it was
  not caught sooner, and a link (a commit or a task). No class. When a new
  correction comes, before it is sorted, read the whole list, and look for a
  likeness to any entry, from any angle. A match makes a lesson (decision 2),
  and the entries go. The list stays short: at most about 20 entries; at a
  milestone, delete the oldest entry that has no match. Pros: bounded; read
  only when needed; the match is made fresh, from any angle. Cons: the
  entries must be written and pruned.
- **B. A log of every correction.** Complete, but it grows with no end, and
  no one reads it all. A search needs a keyword, which is a class.
- **C. Lines in each commit message** ("done so because", "not caught
  because"). No new file, and the milestone review (decision 1) can read
  them with `git log`. A search needs a keyword, and a history rewrite loses
  them. Good as an input to the milestone review, weak alone.
- **D. Nothing.** No cost; a slow pattern is never seen.

**Chosen: A, with C as an optional input to the milestone review.**

**Read the list for each correction, before it is sorted** (the review,
finding 2). If only a "not sure" correction reads it, one sorted as "it will
come back" or "cost of doing business" is never compared, and the entry that
it would settle stays. This is the Borges point again: the match is made when
a new problem is compared with the old ones. The cost is small: at most about
20 short entries, about 1 000 to 2 000 tokens.

**A match needs a shared cause** (the review, finding 3). Look from any
angle, so that no fixed class hides a likeness. But make a lesson and delete
an entry only when you can name a cause that the two have in common (a
habit, a gap in what is tested or reviewed, a rule that is not read at the
action), and say how one lesson stops both. 1, 2, 3 and 7 pass: one gap
(what people use is not what we test), and one lesson (test what the reader
uses: the build on a server that acts as the host, and dev). The prerender
bug and the lint-disable bug do not: "both are about validation" names no
common cause. If the link is not clear, keep the entry.

**Where the watchlists go:** as for docs, the most general place where an
entry is true.

- A project's own corrections go in the project's `docs/watchlist.md`.
- A correction that can happen in any project (6, a stale index after work
  in another worktree; 8, one fact in two places) goes in the shared list,
  `watchlist.md` in the skill's own directory
  (`user/skills/learn-from-corrections/`). `install` links that directory,
  so each harness finds the list beside `SKILL.md`, from a session in any
  project. A path into an agent-house checkout would not work in a cloud
  session (the review, finding 4).

**Read both lists; write to one.** A project's problem can have a cause in
common with a shared entry, so each comparison reads both. A write to the
shared list is a change to agent-house, from a session in another project, so
it goes through an agent-house worktree (agent-house's `AGENTS.md`). The
skill asks the user before it writes there. If the shared list cannot be
read, say so to the user, and compare with the project's list only.

## The proposed text

No change to `user/AGENTS.md`: the trigger is in the skill's description.

### `slidev/stem`'s `docs/talks.md`, "Tag, rebuild or retire a talk"

A sentence at the end of the "Tag a talk that you give" item:

```markdown
Before you tag, also do the milestone review of the `learn-from-corrections`
skill.
```

### `user/skills/learn-from-corrections/SKILL.md`

```markdown
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
```

## Not chosen

- Bugs only (the first version of this plan): most corrections are not bugs
  (8 to 10), and the books on making good code are mostly about the others.
- A fixed count (three of a kind): it needs fixed classes.
- A log of every correction: it grows with no end, and a search needs a
  class.
- Reflection only when the user asks: most corrections would get none.
- "A task ends" as a milestone: a session seldom knows when it is.
- The trigger in `user/AGENTS.md` as well as in the description: one fact in
  two places (8), and the skill is no longer complete in itself.
- The shared watchlist in agent-house's `docs/`: a session of another project
  has no path to it that works in every harness and in a cloud session.

## The review (2026-10-23)

`review-general-2026-10-23.md` reviewed the first version of this plan, which
was about bugs only. Its four findings hold for corrections too, and are in
the text above:

1. The milestone review had no always-loaded trigger: added, for a tag, a
   release and a request from the user, in the skill's description.
2. Only a "not sure" bug read the watchlist: now each correction does, before
   it is sorted.
3. A likeness "in any way" was enough to make a lesson and delete an entry:
   now a match needs a shared cause.
4. The plan did not say how to find and read both lists: the shared list is
   now in the skill's directory, and each comparison reads both.

Changes after the review, from the user:

- The scope is every significant correction, not only bugs, and checks are
  one step of the ladder, not its centre. The task and the skill are renamed
  (from `bug-reflection`).
- The user can ask for a milestone review at any time, for example at the
  end of a phase of work. So a project's watchlist records its last
  milestone: a request leaves no tag in git.
- The trigger is in the skill's description only, and the description says
  only when to read the skill.
- The report to the user for a cost of doing business is one line, so that a
  small correction does not make noise.

## The second review (2026-10-23)

`review-general-2026-10-23-second.md` reviewed this version. Its two findings
are in the text above ("At a milestone"):

1. A project with no milestone line and no tag had no start for the history:
   now it reads all of it, and a missing list is empty. The log is small
   enough: `slidev/stem` has 198 commits and no tag, and its one-line log is
   about 14 KB. A diff is opened only where the message does not show the
   correction.
2. A milestone review that the user asks for before a commit did not see the
   work that is not committed: now it reads that work and the session's
   corrections, and says so. The milestone line keeps the last commit read.

## The test

Is a description a trigger as good as a line in `user/AGENTS.md`? About two
weeks after the skill is installed, use the trim task's method on the
session transcripts: count the corrections, and the times the skill loaded
after one; and count the tags. Look at each kind of finder (a test, a
deploy, a review, the user, the agent itself) apart. Two cases are the most
likely to be missed: a bug that a failed test finds during other work, and a
design correction that the agent makes on its own. If the skill loads after
few corrections, that is the evidence for a line in `user/AGENTS.md`.
