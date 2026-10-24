# The Claude Code status line

**Covers:** where the status line's legend is, how the cost is split, how to
turn the status line on, how it is tested, and the facts about Claude Code's
input that it depends on.
**Read before** you change the status line (`user/claude/statusline.py`), and
read its legend too.
**Tasks:** `tasks/2026-10-24-per-harness-files/` (why it is in
`user/claude/`, and why only Claude Code has one).

## What it shows

What each part of the line means (the gauges, their bars, colours and widths,
and what each part of the cost counts) is in the `statusline-legend` skill,
`user/claude/skills/statusline-legend/SKILL.md`. It is a skill so that a
session in any project can explain the line when the user asks. When you
change what the line shows, change the legend in the same change.

`Config` in `statusline.py` holds the numbers that you can tune: the pace
floor, when a rate limit turns red, and when the cache turns yellow.

## How the cost is split

The parts come from the token usage of each response in the transcripts, at
`PRICES`. `PRICES` holds the prices of each model, with the date that they
were read. When Anthropic changes its prices, update it. Reading this
session's transcripts (16 MB) took 40 ms on 2026-10-24.

In one session (2026-10-24), "other" was $2.08 of $21.93, compared with
`/usage`'s "Usage by model". $1.97 was Opus requests that the transcripts do
not have: 6.5M cache-read tokens, 38k cache-write, 14k output and 20k uncached
input. Two compactions explain the output; prompt suggestions probably explain
most of the reads, but that is not confirmed. $0.11 was Haiku, which WebFetch
and WebSearch use. Only OpenTelemetry's `api_request` events say which
subsystem (`query_source`) made each request. The transcripts' tokens at
`PRICES` gave `/usage`'s Opus cost to the cent, so the prices were right.

## Turn it on

`install` links the script to `~/.claude/statusline.py`. It does not edit
`~/.claude/settings.json`, because Claude Code writes that file
([`harnesses.md`](harnesses.md#files-for-one-harness)). Add this to it by
hand:

```json
"statusLine": {
  "type": "command",
  "command": "/opt/homebrew/bin/python3 -I ~/.claude/statusline.py",
  "refreshInterval": 60
}
```

- **The script needs Python 3.10 or later.** On macOS, `/usr/bin/python3` is
  3.9, so the command names Homebrew's Python. A cloud session has the script
  but not this entry, so it shows no status line.
- **`-I`** keeps a module in the project's directory from shadowing the
  standard library.
- **`refreshInterval`** runs the script again each 60 seconds, so that the
  countdowns move when no message arrives.

## Test it

`user/claude/test_statusline.py` tests the line for given inputs, at a fixed
time. `tools/check` runs it, with ruff and mypy. `install` does not link a
`test_*` file.

## Claude Code's input

Claude Code sends the session's data as JSON on stdin
([status line docs](https://code.claude.com/docs/en/statusline), read
2026-10-24). These facts are easy to get wrong:

- **After a compaction, the context's size is not known.**
  `total_input_tokens` is `0` until the next response. After `/compact`,
  `context_window.current_usage` is `null` too, but after an idle compaction
  it is not (seen on 2026-10-24). So the script shows `ctx ?` for `0`, not
  `ctx 0k`. The same is true before the first response of a session.
- **A compaction is not a cache miss.** `prompt_cache.misses` counts requests
  that wrote again what the cache already held, with no compaction to explain
  it. Claude Code counts a compaction in `expected_rebuilds`.
- **A warm cache after `/compact` is real.** The system prompt, the tools and
  the instructions do not change, so the next request reads them from the
  cache.
- **`prompt_cache.recache_tokens_if_cold` is `null` after a compaction,** until
  the next request.
- **`rate_limits` comes only on Pro and Max plans,** after the first response.
  Each window can be absent.
- **Claude Code removes the spaces at the start of a line** that the script
  prints (seen on 2026-10-24; the docs do not say so). So the empty part of a
  bar is braille blanks (U+2800), which show as empty cells: an empty bar at
  the start of the second line keeps its place.
