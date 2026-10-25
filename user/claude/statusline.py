"""Claude Code status line, in two lines.

On the left, a column for each gauge, with its text over a bar in eighths of a
cell: the prompt cache (time until cold, the tokens that a cold cache writes
again, and the session's misses), the context's tokens, and the 5-hour and
7-day rate limits, each with its pace and the time until it resets. On the
right: the model, its effort, the git branch and the directory, over the
session's cost and
what it was spent on, summed from the transcripts at list prices.

Claude Code sends the session's data as JSON on stdin
(https://code.claude.com/docs/en/statusline). A field that is absent is left
out: rate_limits comes only on Pro and Max plans, after the first response;
effort only for a model that supports it; prompt_cache after the first
response. The context's tokens are unknown before the first response, and
again after a compaction until the next one: then total_input_tokens is 0, and
the line shows "ctx ?".

Run it with -I, so that a module in the project's directory cannot shadow the
standard library: `python3 -I statusline.py`. It needs Python 3.10 or later.
How to turn it on: docs/statusline.md in agent-house.
"""

import json
import os
import subprocess
import sys
import time
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

RESET = "\033[0m"
DIM = "\033[2m"
CYAN = "\033[0;36m"
MAGENTA = "\033[0;35m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
RED = "\033[1;31m"
# 1/8 to 7/8 of a cell, filled from the left.
EIGHTHS = "▏▎▍▌▋▊▉"
# The braille pattern with no dots: one blank cell. Claude Code removes the
# spaces at the start of a status line, but not this.
BLANK = "⠀"

FIVE_HOURS = 5 * 3600
SEVEN_DAYS = 7 * 86400
CACHE_TTLS = {"5m": 300, "1h": 3600}

# Cells: the least width of each gauge's bar. For the context and the rate
# limits, it is the widest that the text can be, so that the bar always
# reaches the end of its text. A column is as wide as its text, so the cache's
# column grows when it shows its misses. test_statusline.py checks each one.
CACHE_WIDTH = 18  # "cache cold (1000k)"
CONTEXT_WIDTH = 9  # "ctx 1000k"
FIVE_HOUR_WIDTH = 15  # "5h 100%▲ ↻4h59m"
SEVEN_DAY_WIDTH = 16  # "7d 100%▲ ↻23h59m"

# Short names for the causes of a cache miss that Claude Code's docs give. A
# cause that is not here is shown with its own name.
SHORT_CAUSES = {
    "tools_changed": "tools",
    "system_prompt_changed": "prompt",
    "ttl_expired_5m": "ttl5m",
    "ttl_expired_1h": "ttl1h",
    "likely_server_side": "server",
}


@dataclass(frozen=True)
class Prices:
    """A model's list prices, in USD for a million tokens."""

    input: float
    output: float
    cache_read: float


@dataclass(frozen=True)
class PriceList:
    """The list prices of each model, by its id. A cache write costs
    `write_5m` times the input price for the 5-minute lifetime, and
    `write_1h` times for the 1-hour one. A response from a model that is not
    here, or in fast mode, is not split: its cost shows as "other"."""

    models: dict[str, Prices]
    write_5m: float
    write_1h: float


# Anthropic's price list, which the VS Code status band reads too
# (docs/status-band.md). Beside the script's real path, because it runs
# through the link that install made.
PRICES_FILE = Path(__file__).resolve().with_name("prices.json")


def read_prices(path: Path = PRICES_FILE) -> PriceList | None:
    """The prices in `path`; None if it cannot be read."""
    try:
        data = json.loads(path.read_text())
        return PriceList(
            models={
                model: Prices(
                    input=float(prices["input"]),
                    output=float(prices["output"]),
                    cache_read=float(prices["cache_read"]),
                )
                for model, prices in data["models"].items()
            },
            write_5m=float(data["cache_write_5m"]),
            write_1h=float(data["cache_write_1h"]),
        )
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


@dataclass(frozen=True)
class Config:
    """The numbers that a user can tune."""

    # A rate-limit window is ahead of pace when its use is ahead of the part
    # of the window that has passed, and more than this percentage. The floor
    # hides the mark early in a window, when a few requests are ahead of the
    # short time that has passed.
    pace_min_used: int = 10
    # A window that is ahead of pace is yellow: at its average rate so far, it
    # runs out before it resets. It is red when it runs out within this part
    # of the window: 0.1 is 30 minutes of 5 hours, or 17 hours of 7 days.
    alert_within: float = 0.1
    # Seconds: in its last seconds, the prompt cache turns yellow and shows
    # the tokens that the next request re-sends if it goes cold.
    cache_warning: int = 300


DEFAULT_CONFIG = Config()


@dataclass(frozen=True)
class Paint:
    """A colour of a bar: as the text colour, for the filled part of a
    glyph, and as the background, for the rest of its cell."""

    fg: str
    bg: str


def colour256(index: int) -> Paint:
    return Paint(f"\033[38;5;{index}m", f"\033[48;5;{index}m")


# The empty part of a bar: the terminal's bright black.
TRACK = Paint("\033[90m", "\033[100m")


@dataclass(frozen=True)
class Level:
    """How much a gauge needs attention. `text` is the terminal's own colour,
    for text. `solid` and `shade` are a bar's colours (256-colour), the shade
    greyer than the solid."""

    text: str
    solid: Paint
    shade: Paint


OK = Level(GREEN, colour256(34), colour256(65))
WARN = Level(YELLOW, colour256(178), colour256(137))
ALERT = Level(RED, colour256(160), colour256(131))


@dataclass(frozen=True)
class Span:
    """Text in one style: SGR escapes, or "" for none. Each character that
    the status line uses is one terminal cell wide, so a span's width is its
    length."""

    text: str
    style: str = ""


SEPARATOR = Span(" · ", DIM)
# Between two columns on the second line.
GAP = Span("   ")


def render(spans: list[Span]) -> str:
    return "".join(
        f"{span.style}{span.text}{RESET}" if span.style else span.text for span in spans
    )


def width(spans: list[Span]) -> int:
    return sum(len(span.text) for span in spans)


@dataclass(frozen=True)
class Bar:
    """A bar's segments, in order: each one is filled from the end of the one
    before it to its own end, a fraction of the bar. The ends must not
    decrease. After the last end, the track. `cells` is its least width."""

    segments: list[tuple[float, Paint]]
    cells: int


@dataclass(frozen=True)
class Column:
    """A column of the status line: its text on the first line, over a bar,
    or over more text."""

    top: list[Span]
    bottom: list[Span] = field(default_factory=list)
    bar: Bar | None = None


@dataclass(frozen=True)
class RateWindow:
    used_percentage: float
    resets_at: int | None


@dataclass(frozen=True)
class PromptCache:
    warm: bool
    expires_at: int | None
    # Seconds that the cache stays warm after a request; None if not known.
    ttl: int | None
    misses: int | None
    miss_causes: list[str]
    # Tokens written to the cache again by the requests counted as misses.
    miss_recache_tokens: int | None
    recache_tokens_if_cold: int | None


@dataclass(frozen=True)
class Session:
    """The fields of Claude Code's input that the status line shows."""

    model: str
    model_id: str
    effort: str | None
    directory: str | None
    transcript: Path | None
    cost_usd: float | None
    # None while Claude Code does not know the count.
    context_tokens: int | None
    context_window_size: int | None
    cache: PromptCache | None
    five_hour: RateWindow | None
    seven_day: RateWindow | None

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Session":
        model = data.get("model") or {}
        effort = data.get("effort") or {}
        workspace = data.get("workspace") or {}
        cost = data.get("cost") or {}
        context = data.get("context_window") or {}
        cache = data.get("prompt_cache")
        limits = data.get("rate_limits") or {}
        return cls(
            model=model.get("display_name") or "",
            model_id=model.get("id") or "",
            effort=effort.get("level"),
            directory=workspace.get("current_dir") or data.get("cwd"),
            transcript=Path(data["transcript_path"])
            if data.get("transcript_path")
            else None,
            cost_usd=cost.get("total_cost_usd"),
            # 0 means not known: the context always holds the system prompt.
            context_tokens=context.get("total_input_tokens") or None,
            context_window_size=context.get("context_window_size"),
            cache=_prompt_cache(cache)
            if cache and cache.get("warm") is not None
            else None,
            five_hour=_rate_window(limits.get("five_hour")),
            seven_day=_rate_window(limits.get("seven_day")),
        )


def _prompt_cache(data: dict[str, Any]) -> PromptCache:
    last_miss = data.get("last_miss_cause") or {}
    return PromptCache(
        warm=data["warm"],
        expires_at=data.get("expires_at"),
        ttl=CACHE_TTLS.get(data.get("ttl") or ""),
        misses=data.get("misses"),
        miss_causes=last_miss.get("causes") or [],
        miss_recache_tokens=data.get("miss_recache_tokens"),
        recache_tokens_if_cold=data.get("recache_tokens_if_cold"),
    )


def _rate_window(data: dict[str, Any] | None) -> RateWindow | None:
    if not data or data.get("used_percentage") is None:
        return None
    return RateWindow(
        used_percentage=data["used_percentage"], resets_at=data.get("resets_at")
    )


def level_of(value: int, limit: int) -> Level:
    """OK below half of `limit`, WARN below 80%, ALERT from 80%."""
    if value * 100 >= limit * 80:
        return ALERT
    if value * 2 >= limit:
        return WARN
    return OK


def tokens(count: int) -> str:
    """A token count as 412k or 1M."""
    if count >= 1_000_000 and count % 1_000_000 == 0:
        return f"{count // 1_000_000}M"
    return f"{(count + 500) // 1000}k"


def until(moment: int, now: int) -> str:
    """The time from `now` until `moment`, in epoch seconds: 3d4h, 2h05m or 12m."""
    left = max(moment - now, 0)
    days, hours, minutes = left // 86400, left % 86400 // 3600, left % 3600 // 60
    if days:
        return f"{days}d{hours}h"
    if hours:
        return f"{hours}h{minutes:02d}m"
    return f"{minutes}m"


def bar_spans(segments: list[tuple[float, Paint]], cells: int) -> list[Span]:
    """A bar of `cells` cells, in eighths of a cell. Where two segments meet
    inside a cell, its glyph is the first one's colour, on the second one's
    background. A cell shows at most two segments."""
    ends = [
        (round(min(max(end, 0.0), 1.0) * cells * 8), paint) for end, paint in segments
    ]

    def paint_at(eighth: int) -> Paint:
        return next((paint for end, paint in ends if eighth < end), TRACK)

    spans: list[Span] = []
    for first in range(0, cells * 8, 8):
        left = paint_at(first)
        filled = next(
            (step for step in range(1, 8) if paint_at(first + step) != left), 8
        )
        if filled < 8:
            span = Span(EIGHTHS[filled - 1], left.fg + paint_at(first + 7).bg)
        elif left == TRACK:
            span = Span(BLANK, TRACK.bg)
        else:
            span = Span("█", left.fg)
        if spans and spans[-1].style == span.style:
            spans[-1] = Span(spans[-1].text + span.text, span.style)
        else:
            spans.append(span)
    return spans


def passed_part(limit: RateWindow, length: int, now: int) -> float | None:
    """The part of the window that has passed, from 0 to 1; None if its reset
    time is not known."""
    if limit.resets_at is None:
        return None
    return 1 - min(max(limit.resets_at - now, 0), length) / length


def window_level(limit: RateWindow, passed: float | None, config: Config) -> Level:
    """OK on or behind pace, WARN ahead of it, ALERT when it runs out soon.
    Without a reset time, the level of the use alone."""
    if passed is None:
        return level_of(round(limit.used_percentage), 100)
    used = limit.used_percentage / 100
    if limit.used_percentage <= config.pace_min_used or used <= passed:
        return OK
    # At the average rate so far, the part of the window until it runs out.
    runs_out_in = (1 - used) * passed / used
    return ALERT if runs_out_in < config.alert_within else WARN


def window_column(
    name: str, length: int, cells: int, limit: RateWindow, now: int, config: Config
) -> Column:
    """A rate-limit window: "5h 64%▲ ↻2h05m", over a bar of its use and of the
    part of the window that has passed. ▲ marks a use ahead of pace. The bar
    is solid to the lower of the two, and shaded between them."""
    passed = passed_part(limit, length, now)
    level = window_level(limit, passed, config)
    used = round(limit.used_percentage)
    top = [Span(f"{name} "), Span(f"{used}%", level.text)]
    fraction = limit.used_percentage / 100
    segments = [(fraction, level.solid)]
    if limit.resets_at is not None and passed is not None:
        if level is not OK:
            top.append(Span("▲", RED))
        top += [Span(" "), Span(f"↻{until(limit.resets_at, now)}", DIM)]
        segments = [
            (min(fraction, passed), level.solid),
            (max(fraction, passed), level.shade),
        ]
    return Column(top, bar=Bar(segments, cells))


def misses(cache: PromptCache) -> list[Span]:
    """The session's cache misses, with short names for the last one's
    causes."""
    if not cache.misses:
        return []
    spans = [Span(f"✗{cache.misses}", WARN.text)]
    if cache.miss_causes:
        causes = ",".join(SHORT_CAUSES.get(cause, cause) for cause in cache.miss_causes)
        spans += [Span(" "), Span(causes, DIM)]
    return spans


def cache_column(cache: PromptCache, now: int, config: Config) -> Column:
    """The time until the cache goes cold, yellow in its last minutes, or
    "cold". In its last minutes, or when cold, the tokens that the next
    request re-sends. Then the misses. The bar is the part of the cache's
    lifetime that has passed: it is full when the cache goes cold."""
    top = [Span("cache ")]
    if cache.warm and cache.expires_at is not None and cache.expires_at > now:
        left = cache.expires_at - now
        level = WARN if left < config.cache_warning else OK
        top.append(Span(until(cache.expires_at, now), level.text))
        segments = [(1 - left / cache.ttl, level.solid)] if cache.ttl else []
    else:
        left, level = 0, ALERT
        top.append(Span("cold", ALERT.text))
        segments = [(1.0, ALERT.solid)]
    if cache.recache_tokens_if_cold is not None and left < config.cache_warning:
        top += [Span(" "), Span(f"({tokens(cache.recache_tokens_if_cold)})", DIM)]
    missed = misses(cache)
    if missed:
        top += [Span(" "), *missed]
    return Column(top, bar=Bar(segments, CACHE_WIDTH))


def context_column(session: Session, compact_limit: int | None) -> Column:
    """The context's tokens, against the auto-compact window, else the context
    window."""
    limit = compact_limit or session.context_window_size
    segments: list[tuple[float, Paint]] = []
    if session.context_tokens is None:
        top = [Span("ctx "), Span("?", DIM)]
    elif not limit:
        top = [Span(f"ctx {tokens(session.context_tokens)}")]
    else:
        level = level_of(session.context_tokens, limit)
        top = [Span("ctx "), Span(tokens(session.context_tokens), level.text)]
        segments = [(session.context_tokens / limit, level.solid)]
    return Column(top, bar=Bar(segments, CONTEXT_WIDTH))


@dataclass(frozen=True)
class Costs:
    """What a session's responses cost, in USD, at list prices. Thinking is
    output, but apart from `output`."""

    input: float = 0.0
    cache_write: float = 0.0
    cache_read: float = 0.0
    output: float = 0.0
    thinking: float = 0.0

    @property
    def total(self) -> float:
        return (
            self.input
            + self.cache_write
            + self.cache_read
            + self.output
            + self.thinking
        )


def response_usages(lines: Iterable[str]) -> Iterator[tuple[str, dict[str, Any]]]:
    """The model and the usage of each response in a transcript's lines. A
    response that the transcript splits into entries repeats its usage in
    each, so only its first entry counts."""
    seen = set()
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue  # A line that Claude Code is still writing.
        message = entry.get("message") if isinstance(entry, dict) else None
        if entry.get("type") != "assistant" or not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict) or message.get("id") in seen:
            continue
        seen.add(message.get("id"))
        yield message.get("model") or "", usage


def costs_of(usages: Iterable[tuple[str, dict[str, Any]]], prices: PriceList) -> Costs:
    """The cost of the responses that `prices` covers."""
    input_cost = write = read = output = thinking = 0.0
    for model, usage in usages:
        price = prices.models.get(model)
        if price is None or usage.get("speed") not in (None, "standard"):
            continue
        creation = usage.get("cache_creation") or {}
        written_1h = creation.get("ephemeral_1h_input_tokens") or 0
        written_5m = (usage.get("cache_creation_input_tokens") or 0) - written_1h
        thought = (usage.get("output_tokens_details") or {}).get("thinking_tokens") or 0
        input_cost += (usage.get("input_tokens") or 0) * price.input
        write += (
            written_5m * prices.write_5m + written_1h * prices.write_1h
        ) * price.input
        read += (usage.get("cache_read_input_tokens") or 0) * price.cache_read
        output += ((usage.get("output_tokens") or 0) - thought) * price.output
        thinking += thought * price.output
    return Costs(*(cost / 1e6 for cost in (input_cost, write, read, output, thinking)))


def transcripts(transcript: Path) -> list[Path]:
    """The session's transcript, and its subagents' transcripts beside it."""
    return [transcript, *sorted(transcript.with_suffix("").glob("subagents/*.jsonl"))]


def read_costs(transcript: Path, prices: PriceList) -> Costs | None:
    """The costs in the session's transcripts; None if they cannot be read."""
    usages: list[tuple[str, dict[str, Any]]] = []
    try:
        for path in transcripts(transcript):
            with path.open() as lines:
                usages += response_usages(lines)
    except OSError:
        return None
    return costs_of(usages, prices)


def miss_cost(session: Session, prices: PriceList) -> float | None:
    """What the cache misses cost: their tokens, at the current model's write
    price for the cache's lifetime."""
    cache, price = session.cache, prices.models.get(session.model_id.split("[")[0])
    if cache is None or not cache.miss_recache_tokens or price is None:
        return None
    write = prices.write_5m if cache.ttl == CACHE_TTLS["5m"] else prices.write_1h
    return cache.miss_recache_tokens * write * price.input / 1e6


def cost_spans(
    session: Session, costs: Costs | None, prices: PriceList | None
) -> list[Span]:
    """The session's cost, then what it was spent on: "$17.19 = read 7.78 ·
    write 4.76 (miss 0.40) · out 2.91 · think 1.74". "other" is the part of
    Claude Code's total that the transcripts do not explain."""
    if session.cost_usd is None:
        return []
    spans = [Span(f"${session.cost_usd:.2f}")]
    if costs is None:
        return spans
    missed = None if prices is None else miss_cost(session, prices)
    parts = [
        ("in", costs.input, None),
        ("read", costs.cache_read, None),
        ("write", costs.cache_write, missed),
        ("out", costs.output, None),
        ("think", costs.thinking, None),
        ("other", session.cost_usd - costs.total, None),
    ]
    shown = [part for part in parts if part[1] >= 0.005]
    for index, (name, cost, within) in enumerate(shown):
        spans.append(SEPARATOR if index else Span(" = ", DIM))
        spans.append(Span(f"{name} {cost:.2f}"))
        if within is not None and within >= 0.005:
            spans.append(Span(f" (miss {within:.2f})", DIM))
    return spans


def short_path(directory: str, home: str) -> str:
    """The directory, with ~ for the home directory `home`."""
    if home and (directory == home or directory.startswith(home + os.sep)):
        return "~" + directory[len(home) :]
    return directory


def session_column(
    session: Session,
    branch: str | None,
    costs: Costs | None,
    prices: PriceList | None,
    home: str,
) -> Column:
    """The model, its effort, the branch and the directory, over the cost."""
    top = [Span(session.model, CYAN)]
    if session.effort:
        top += [Span(" "), Span(session.effort, MAGENTA)]
    if branch:
        top += [Span(" "), Span(f"({branch})", RED)]
    if session.directory:
        # The green of the user's shell prompt.
        top += [Span(" "), Span(short_path(session.directory, home), GREEN)]
    return Column(top, cost_spans(session, costs, prices))


def compact_window(settings: dict[str, Any], model_id: str) -> int | None:
    """The model's auto-compact window in settings.json (modelSettings), for
    its id without a "[1m]" suffix."""
    model_settings = settings.get("modelSettings") or {}
    window_size = (model_settings.get(model_id.split("[")[0]) or {}).get(
        "autoCompactWindow"
    )
    return window_size if isinstance(window_size, int) else None


def grid(columns: list[Column]) -> str:
    """The columns side by side, each as wide as its widest line or its bar.
    Without a second line, only the first."""
    tops: list[Span] = []
    bottoms: list[Span] = []
    for index, column in enumerate(columns):
        if index:
            tops.append(SEPARATOR)
            bottoms.append(GAP)
        cells = max(
            width(column.top),
            width(column.bottom),
            column.bar.cells if column.bar else 0,
        )
        bottom = bar_spans(column.bar.segments, cells) if column.bar else column.bottom
        tops += [*column.top, Span(" " * (cells - width(column.top)))]
        bottoms += [*bottom, Span(" " * (cells - width(bottom)))]
    first, second = render(tops).rstrip(), render(bottoms).rstrip()
    return f"{first}\n{second}" if second else first


def status_line(
    session: Session,
    branch: str | None,
    compact_limit: int | None,
    now: int,
    costs: Costs | None = None,
    home: str = "",
    config: Config = DEFAULT_CONFIG,
    prices: PriceList | None = None,
) -> str:
    columns = []
    if session.cache is not None:
        columns.append(cache_column(session.cache, now, config))
    if session.context_tokens is not None or session.context_window_size is not None:
        columns.append(context_column(session, compact_limit))
    if session.five_hour is not None:
        columns.append(
            window_column(
                "5h", FIVE_HOURS, FIVE_HOUR_WIDTH, session.five_hour, now, config
            )
        )
    if session.seven_day is not None:
        columns.append(
            window_column(
                "7d", SEVEN_DAYS, SEVEN_DAY_WIDTH, session.seven_day, now, config
            )
        )
    columns.append(session_column(session, branch, costs, prices, home))
    return grid(columns)


def git_branch(directory: str | None) -> str | None:
    """The branch checked out in `directory`, or the short commit when HEAD is
    detached; None outside a repository."""
    where = ["-C", directory] if directory else []
    for query in (
        ["symbolic-ref", "--short", "HEAD"],
        ["rev-parse", "--short", "HEAD"],
    ):
        result = subprocess.run(
            ["git", "--no-optional-locks", *where, *query],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    return None


def read_settings() -> dict[str, Any]:
    path = (
        Path(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude")).expanduser()
        / "settings.json"
    )
    try:
        settings = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return settings if isinstance(settings, dict) else {}


def main() -> None:
    session = Session.from_json(json.load(sys.stdin))
    prices = read_prices()
    costs = (
        read_costs(session.transcript, prices)
        if session.transcript and prices
        else None
    )
    print(
        status_line(
            session,
            branch=git_branch(session.directory),
            compact_limit=compact_window(read_settings(), session.model_id),
            now=int(time.time()),
            costs=costs,
            home=str(Path.home()),
            prices=prices,
        )
    )


if __name__ == "__main__":
    main()
