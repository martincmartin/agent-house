# The VS Code status band

**Covers:** the status band in the VS Code panel: where it is, how to turn it
on, how it is tested, and the facts about the plugin API that it depends on.
**Read before** you change the band (`plugins/status-band/`) or the repo's
plugin list (`.claude-plugin/marketplace.json`), and read its legend too.
**Tasks:** `tasks/2026-10-25-vscode-status/` (the options, the probe, and why
a band with SVG bars).

## What it is

The VS Code extension's panel does not run the `statusLine` command, so the
CLI's status line ([`statusline.md`](statusline.md)) does not show there. The
band is a Claude Code plugin with a hooks module (a "mod") that draws the
same gauges above the prompt box in the panel: the prompt cache, the context,
the 5-hour and 7-day rate limits, and the session's cost. It draws only on
the `vscode` surface; the CLI has its own line.

What each part means is in the `statusline-legend` skill
(`user/claude/skills/statusline-legend/SKILL.md`), with the CLI line. When you
change what the band shows, change the legend in the same change.

- `hooks/gauges.ts`: the rules, as pure functions: the levels, the pace, the
  text, the SVG bars and the cost of each response. They follow
  `statusline.py`.
- `hooks/prices.ts`: reads the list prices from `user/claude/prices.json`,
  which the CLI line reads too ([`statusline.md`](statusline.md#how-the-cost-is-split)).
  The band reads the file of its own checkout on each refresh. When a
  refresh fails, the band shows the error under its last gauges.
- `hooks/transcript.ts`: the reads of the session's transcripts.
- `hooks/register.tsx`: the hooks, and the drawing of the band.
- `types/index.d.ts`: the state contract: what the band draws.
- `tests/band.test.tsx`: the tests.

## Turn it on

The repo is a plugin source (a "marketplace" in Claude Code's words). Run this
once, by hand:

```bash
claude plugin marketplace add ~/Develop/agent-house/main
claude plugin install status-band@agent-house
```

Claude Code reads a plugin of a folder marketplace from that folder, not from
a copy. So an edit in the linked checkout reaches a session after
`/reload-plugins`, with no reinstall. `install` does not run these commands:
it does not edit Claude Code's settings
([`harnesses.md`](harnesses.md#files-for-one-harness)), and it runs before
Claude Code is installed.

## Test it

`tools/check` runs `claude plugin validate` on the repo and on the band,
`claude plugin test` on the band, and `tsc` with the band's `tsconfig.json`.

`tsc` needs the plugin API's types, in `.claude-plugin/types/`. Claude Code
writes them when a session loads the plugin, and git ignores them. A
worktree that no session loaded has none, so `tools/check` uses those of the
main checkout, where the installed plugin runs. When neither has them, it
fails and says so: start a session in VS Code, or run `/reload-plugins`.

## Facts about the plugin API

Found with Claude Code 2.1.310 on 2026-10-25, with a probe in VS Code
(`tasks/2026-10-25-vscode-status/`). These facts are easy to get wrong:

- **VS Code draws the `AbovePrompt` band,** although the API's declarations
  say "terminal and desktop only". It does not draw a mod's changes to the
  footer (`PromptHint`), and it docks a `Pane` beside the conversation.
- **A `Box` width takes a whole percentage only:** the panel refuses
  `"14.8%"`. So the bars are `Svg`.
- **VS Code does not draw every theme colour key:** `warning` drew grey. So
  the colours are hex.
- **`$.fs.read` refuses a file over 4 MiB, and `$.process.run` cuts its
  output at 4 MiB** (`isStdoutTruncated`). A long session's transcripts are
  larger, so the band reads each transcript from where the last read stopped,
  with `tail -c`, and keeps only complete lines.
- **`$.config.list()` does not give `autoCompactWindow`,** so the band reads
  `settings.json`.
- **A mod gets no prompt-cache state.** The band takes the time of the main
  transcript's last response, and the lifetime of the cache entries that the
  last writer wrote. It does not get the misses (`prompt_cache.misses`), so it
  shows no miss cost.
- **The validator refuses a hook that passes `$` to a function** that is not
  at the top of a file of the plugin. And `on` registers a hook only while
  `register` runs, not from inside a hook.
- **The state contract must import nothing.** It declares the parts of the
  API's types that it needs. An atom with a `shape` is declared `Shaped<T>`.
  When `View` changes, change the shape tag (`view-2`) in `register.tsx` and
  the tests: a stored value with another tag reads as absent.
