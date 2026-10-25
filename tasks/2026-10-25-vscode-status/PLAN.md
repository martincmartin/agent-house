# A status line for the VS Code panel

The Claude Code status line (`user/claude/statusline.py`) shows the context,
the 5-hour and 7-day rate limits, the cost breakdown and more, in the CLI.
The user now works mainly in the VS Code extension's graphical panel. There,
the only view of the rate limits is a sidebar panel with two bars and rounded
"resets in" times, which takes much horizontal space. This task finds how to
show the same information in the VS Code panel, with bars.

## The user's requirements (2026-10-25)

- **VS Code first.** The CLI line stays as it is, for the CLI. The VS Code
  version is a rewrite, not a wrapper. If both stay in use, the Python can
  later call the VS Code version; YAGNI for now.
- **Do not call the Python** from the VS Code version.
- **No terminal mode** (`claudeCode.useTerminal`). The panel typesets LaTeX,
  and terminal mode does not. This is the dealbreaker.
- **Do not show again what the panel's footer shows:** the model, the effort
  and the cache's time to live. The footer does not show the context's size,
  so the context stays.
- **The context's limit is the smaller of the context window and the
  model's `autoCompactWindow`** in `settings.json` (`modelSettings`), for
  example 500k of a 1M window.
- **Bars,** as in the CLI line and in the extension's own usage panel.

## Evidence

Found on 2026-10-25, with the extension 2.1.310, from its docs, its bundle
(`~/.vscode/extensions/anthropic.claude-code-2.1.310-darwin-arm64`) and the
mod API's declarations that the `plugin-authoring` skill writes.

- **The panel does not run the `statusLine` command.** In the bundle,
  `statusLine` is only in the settings schema. The docs do not say so either
  way.
- **A mod (a plugin with a hooks module) can draw in the panel.** In the
  panel's code, from the top: toasts, an inline `Pane`, the `AbovePrompt`
  band, the plugins' status lines (`$.ui.status`), and the prompt box with
  its footer.
- **The declarations say that `AbovePrompt` is raised on the terminal and
  desktop only,** but the panel's code draws it. The probe tests which is
  right. A `Pane` is raised on every surface.
- **A mod cannot change the footer in VS Code.** `PromptHint` and
  `SessionMode` are raised on the terminal and desktop only.
- **The data a mod can read:**
  - `$.session.usage()`: the context (`tokens`, `window`), the rate-limit
    windows (`percentUsed` to one decimal, `resetsAt` as ISO 8601), and the
    total cost (`usd` only, with no split).
  - `session.measure`: an event when one of these changes.
  - `turn.step`: the usage of each step, with the model and the agent. It has
    the four token counts only: no split of thinking from output, and no
    split of 1-hour from 5-minute cache writes. It counts only from when the
    mod loads.
  - `$.fs.read`: any path, but it rejects a file over 4 MiB. A long
    session's transcripts can be larger (16 MB on 2026-10-24,
    `docs/statusline.md`).
  - `$.process.run`: a command with no shell. The declarations say "CLI
    only".
  - `$.clock.every`: a timer, in place of `refreshInterval`.
- **A module imports only code files** (`.ts`, `.tsx`, `.js` and so on), not
  `.json`. A data file must be read with `$.fs.read`.
- **The VS Code surface's elements** are `Box`, `Text`, `Button`, `Input`,
  `Select`, `Svg`, `Link`, `Code` and `Markdown`. `Box` has `width` (cells or
  a percentage), `height` and `backgroundColor`. `Svg` takes an SVG document
  and a size in CSS pixels.

## Options

### 1: a mod that draws a band above the prompt box (chosen)

- Pro: it keeps the panel, and so LaTeX. It takes about two rows of height
  and no width.
- Pro: each window's panel draws it, so it works with one window for each
  session.
- Con: the logic is in TypeScript and in Python while the CLI line stays in
  use. They can differ; the user accepts that.
- Con: if VS Code does not draw `AbovePrompt`, it must be an inline `Pane`.

### 2: a VS Code extension in VS Code's own status bar

- Pro: it shows when the Claude panel is closed.
- Con: one short line of text and icons, with no real bars and almost no
  colour. A hover can show a formatted tooltip.
- Con: only Claude Code has the rate limits, so a mod must write them to a
  file for the extension. That is option 1's work, plus a VSIX to build and
  install.

It can be added to option 1 later, for the rate limits, which are the same
for the whole account. Not now: the panel is always open.

### Rejected

- **Terminal mode:** it does not typeset LaTeX.
- **A mod that calls `statusline.py`:** the user does not want it.
- **An extension that gets the rate limits from Anthropic by itself:** the
  endpoint has no docs, and it needs the user's login token.

## The probe

[probe/](probe/) is a mod of about 300 lines. It answers these questions:

- Does the VS Code panel draw `AbovePrompt`, `$.ui.status` and an inline
  `Pane` (`/probe-pane`)?
- Which bar looks best in the panel: Unicode eighth blocks in `Text`, a `Box`
  with a background, or `Svg`?
- What do `$.session.usage()`, `session.measure` and `turn.step` give in a
  real session, and does the countdown move with `$.clock.every`?
- Can `$.fs.read` read a file outside the working directory
  (`~/.claude/settings.json`, for `autoCompactWindow`) and the transcript?
- Does `$.process.run` work in the VS Code extension?
- Does `$.config.list()` give `autoCompactWindow`?

It writes what it finds to `probe-report.json` in its folder, and the band
shows the values.

## Results

From `probe-report.json`, 2026-10-25, in this VS Code session (2.1.310):

- **VS Code draws `AbovePrompt`.** The hook ran with `surface: "vscode"`,
  so the declarations that say "terminal and desktop only" are behind.
  `$.session.surfaces()` gave `["vscode"]`.
- **A `Box` width takes a whole percentage only.** `"14.8%"` made the panel
  refuse the band: `Box prop "width" must be a number or a percentage`.
  `"15%"` is accepted.
- **`$.process.run` works in the extension** (`printenv HOME`, `git branch`),
  although the declarations say "CLI only".
- **`$.fs.read` reads outside the working directory** and outside the mod:
  `~/.claude/settings.json`, and this session's transcript (1.66M chars).
- **`$.config.list()` does not give `autoCompactWindow`.** It gave only
  `autoCompact`, `switchModelsOnFlag` and `model`. The mod must read it from
  `settings.json`.
- **`$.session.usage()`** gave the context (147,617 of 1,000,000 tokens,
  15%), both rate limits (`five_hour` 20%, `seven_day` 74%, with
  `resetsAt` to the second), and the cost (`usd` only).
- **`$.clock.every` ticks** every 5 s, and the report is written each time.

- **`turn.step` gives each request's usage,** with the model, when the step
  ends: for example `input_tokens` 2, `output_tokens` 572,
  `cache_read_input_tokens` 153,892, `cache_creation_input_tokens` 776.
- **`session.measure` fires,** with `changed` naming `context`,
  `rateLimits` and `cost`.

- **The bars,** from the user's screenshot of the band:
  - **Unicode eighth blocks in `Text`:** the glyphs do not fill the line's
    height, so the filled part is lower than its background, with a step at
    the partial cell. A bar of 20 cells is very wide in the panel's font.
  - **A `Box` with a background:** a full row high, so heavy. The theme key
    `success` drew an olive green, but `warning` drew grey: VS Code does not
    map every theme key to a colour. A hex colour avoids this.
  - **`Svg`:** rounded ends, the right colours (hex), and the look of the
    extension's own usage panel. Chosen.
  - With three bars, the 5h and 7d rows were too wide, and the `Svg` wrapped
    to the next line.
  - The panel puts the label "From the status-probe plugin" above the band.
- **A `Pane` is placed `dock` in VS Code,** not `inline`
  (`$.ui.open` gave `{"isPlaced": true}`).

- **`$.ui.status` draws** its line in the panel ("status-probe: a plugin
  status line, tick 162").

- **`tail -c +N` through `$.process.run` reads a transcript from an
  offset** (1,272,015 chars after byte 1,000,000, not cut). **`$.process.run`
  cuts its output at 4,194,304 bytes** and sets `isStdoutTruncated`
  (`head -c 5000000 /dev/zero`).

## Decisions (2026-10-25, with the user)

- **The band, with `Svg` bars.** The user chose this layout: one row with a
  column for each gauge (the context, 5h, 7d), its text over a bar of 120
  by 6 CSS pixels; then a row with the cost and its breakdown. The colours,
  the pace and the shade follow the CLI line's rules.
- **The cost breakdown comes from the transcripts,** read as they grow:
  each read starts at the end of the last complete line, with `tail -c`,
  and a cut output is read again from where it stopped. A line over 4 MiB
  is dropped. This gives every split that the CLI line has. `turn.step` was
  rejected: it does not split thinking or the cache writes' lifetimes, and
  it counts only from when the mod loads.
- **The miss cost (`(miss …)`) is left out:** a mod does not get
  `prompt_cache.miss_recache_tokens`.
- **The prompt cache has a gauge, first, as in the CLI line:** the time
  until it goes cold (`cache 42m`), over a bar of the part of its lifetime
  that has passed. The footer shows the time too, but the user wants all of
  it in one place, and "cache" alone does not say what the bar measures.
  The footer does not show the bar. A mod gets
  no cache state from the API (only some hook events carry `cache_ttl`), so
  the band takes it from the main transcript: the last response's
  `timestamp`, plus the lifetime of the entries that the last writer wrote
  (`cache_creation.ephemeral_1h_input_tokens` or `ephemeral_5m_…`). The
  timestamp is when Claude Code wrote the response's first entry, so the
  expiry can be a few seconds late. The colours are the CLI's: yellow in the
  last 5 minutes, and a full red bar with "cold" after it.

## The band (status-band)

Written first in the dev-mods folder of the session, so that it reloaded on
each edit, then moved to `plugins/status-band/` (`docs/status-band.md` lists
its files). The user's screenshot of it is
[screenshot-band.png](screenshot-band.png) (before the cache gauge).

On this session's transcript (2026-10-25), its split was the Python's to
the last digit: read 2.7222, write 1.6418, out 1.1571, think 0.8446,
in 0.0008.

## Where it lives, and how it is installed

The options, on 2026-10-25:

- **A: the repo as a folder marketplace (chosen).** The plugin is in
  `plugins/status-band/`, and `.claude-plugin/marketplace.json` lists it. The
  user installs it once, by hand. Claude Code reads a plugin of a folder
  marketplace from that folder (the `plugin-authoring` skill's reference),
  so an edit in the linked checkout reaches a session after
  `/reload-plugins`, as an edit of the status line does.
- B: `CLAUDE_CODE_PLUGIN_DIRS`. VS Code must have it in its environment, and
  VS Code started from the Dock does not read the shell's profile.
- C: install from GitHub. Claude Code runs a copy, so each edit needs a push
  and `claude plugin update`.

Not in `user/claude/`: Claude Code loads a plugin only when it is installed,
so `install`'s links do nothing for it. `install` does not run the two
commands: it does not edit Claude Code's settings, and it runs before Claude
Code is installed.

## What tools/check runs

`claude plugin validate` (0.6 s), `claude plugin test` (0.9 s) and `tsc`
(1.0 s), measured on 2026-10-25, when `tools/check` took 15.7 s.

`tsc` needs the plugin API's types, which only a session that loads the
plugin writes (`claude plugin validate` does not). The options:

- **(a) Use the types of the main checkout, where the installed plugin runs
  (chosen).** `tools/check` fails, and says why, when there are none. The
  types describe the API of the Claude Code that runs, not the plugin's code,
  so a worktree can use them.
- (b) No `tsc`: a type error that the tests do not reach gets through.
- (c) A copy of the types in the repo (22,494 lines): stale after each
  release of Claude Code.

`tsc` is `npx -p typescript@5.9.3`: it needs the network once.

## The prices: one JSON file (2026-10-25, with the user)

`user/claude/prices.json` holds the list prices, and the CLI line and the
band both read it. JSON is the only format that Python 3.10 and the plugin
both read with no new dependency (YAML needs PyYAML, TOML needs Python 3.11,
CSV needs a parser in TypeScript). A plugin module cannot import a `.json`
file, so the band reads it with `$.fs.read`, from its own checkout
(`../../user/claude/prices.json` from the plugin's folder). The Python reads
it beside its real path. The refactor kept the CLI line's output
byte-identical (compared on one input with a transcript, rate limits and a
cache miss, also through a link), and both gave the same split of this
session's transcript.

## When prices.json is stale (2026-10-25, with the user)

The question: how to know of a new model, or a change of price. Anthropic
gives no feed of either. The options:

- **A: the band reads the pricing page once a day, and says when the file
  differs (chosen).** The page is in Markdown at
  `https://platform.claude.com/docs/en/about-claude/pricing.md`, with one
  table: "Model | Base input tokens | 5m cache writes | 1h cache writes |
  Cache hits and refreshes | Output tokens". The user asked for the check
  to run when the band runs, at most once a day. `tools/update-prices.ts`
  writes the file with the same reader. At the user's request, the agent
  ran it, and the file is its output.
- B: a scheduled job: one more thing to install, and it runs when no one
  looks.
- C: by hand, when someone notices: the way the Sonnet error below got in.

The reader refuses a table whose columns changed and a price that it cannot
read, so a change of the page fails loudly, not with wrong prices. On
2026-10-25 it read 19 models; it skips the rows of Haiku 5.5's prices that
depend on the prompt's length.

**Keep JSON, not the page's Markdown (with the user).** The user asked
whether to store the Markdown page instead. The Python would then need its
own reader of the table, a second copy of the parsing; JSON is read by both
with no reader of our own, and one line for each model makes a change one
line of a diff.

**The schema changed:** each model now has its own five prices
(`input`, `cache_write_5m`, `cache_write_1h`, `cache_read`, `output`), as the
page gives them. The ratios (1.25 and 2 times input) hold for every model on
the page today, but the page states the prices, not the rule.

## The Sonnet 5.5 cache read: $0.10, not $0.20

The first `prices.json` had $0.20, copied from a skill's notes. The page says
$0.10 (its footnote: Opus 5.5 and Sonnet 5.5 cache hits are 0.05 times input).
Claude Code's own cost (`lastModelUsage` in `~/.claude.json`, one project,
2026-10-25) decides it:

- Sonnet 5.5: 16 input, 4,647 output, 142,450 cache read, 58,149 cache write
  (5 minutes), costUSD 0.2061195. At $0.10: $0.2061195, exact. At $0.20:
  $0.2204.
- Opus 5.5: 16 input, 15,410 output, 492,205 cache read, 49,864 cache write
  (1 hour), costUSD 0.805617, exact at the page's prices.

The cost check of the CLI line ("to the cent") was of Opus, so it did not
find the Sonnet error.

## The plugin API's types: a copy in the repo (2026-10-25)

Option (a) above failed: Claude Code does not write `.claude-plugin/types/`
for an installed plugin, and not under `claude -p --plugin-dir` either. Only
the `plugin-authoring` skill writes them, into its own folder under
`/tmp/claude-<uid>/bundled-skills/<version>/`, when it loads. So the choice
is (c), with the user: `plugins/claude-code.d.ts` (849 KB), which
`tools/update-plugin-types` copies from the skill's folder. It is stale after
a release only in the parts that changed, and `tsc` then reports a mismatch
in the code that uses them.

## install installs the plugins (2026-10-25, with the user)

The earlier reasons not to do it were wrong. "It runs before Claude Code is
installed" over-generalized from one machine: `install` runs whenever anyone
runs it. "It does not edit Claude Code's settings" holds for the files that
`install` writes, but `claude plugin` is Claude Code's own command, and
Claude Code writes its own file; the rule in `docs/harnesses.md` now says so.

- A missing `claude` is reported, as a missing `python3` is.
- **`--no-plugins`** skips the step, for the cloud setup script: a cloud
  session has no VS Code panel. The user asked whether `--no-vs-code` was
  better; the step installs every plugin in the marketplace, not only the
  VS Code one, so the flag names what it skips.
- `tools/install-plugins.py` (Python 3.9, as `install` needs) reads the
  output of `claude plugin marketplace list --json` and
  `claude plugin list --json`. It adds the marketplace when it is absent, and
  installs each plugin that is absent. A marketplace of that name from
  elsewhere is reported and left as it is. A disabled plugin is left disabled.
