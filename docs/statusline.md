# The Claude Code status line

**Covers:** what `user/claude/statusline.py` shows, how to turn it on, how it
is tested, and the facts about Claude Code's input that it depends on.
**Read before** you change the status line.
**Tasks:** `tasks/2026-10-24-per-harness-files/` (why it is in
`user/claude/`, and why only Claude Code has one).

## What it shows

One line, for example:

```text
Opus 5.5 high (main) · $3.46 · ctx 123k · cache 42m · 5h 64%▲ ↻2h05m · 7d 84%▲ ↻3d4h
```

- **The model, its effort and the git branch** of the working directory.
- **The session's cost.**
- **The context, in tokens.** Its colour is against the model's
  `autoCompactWindow` in `settings.json` (`modelSettings`), else against the
  context window. `ctx ?` means that Claude Code does not know the count yet.
- **The prompt cache:** the time until it goes cold, or `cold`. In its last
  minutes, and when cold, the tokens that the next request writes again, in
  parentheses. Then `✗` and the session's cache misses, with the last miss's
  cause when Claude Code gives one.
- **The 5-hour and 7-day rate limits:** the percentage used, and the time until
  each resets. `▲` means that the use is ahead of the part of the window that
  has passed, and above a floor, so that the window runs out before it resets.

`Config` in `statusline.py` holds the numbers that you can tune: the pace
floor, and when the cache turns yellow.

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

- **After `/compact`, the context's size is not known.**
  `context_window.current_usage` is `null`, and `total_input_tokens` is `0`,
  until the next response. The script shows `ctx ?`, not `ctx 0k`. The same is
  true before the first response of a session.
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
