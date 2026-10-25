"""Tests for statusline.py. `install` does not link a test_* file.

Run: python3 -B -m unittest discover -s user/claude (tools/check runs it).
"""

import json
import re
import tempfile
import unittest
from pathlib import Path
from typing import Any

from statusline import (
    ALERT,
    BLANK,
    CACHE_WIDTH,
    CONTEXT_WIDTH,
    DEFAULT_CONFIG,
    FIVE_HOUR_WIDTH,
    FIVE_HOURS,
    GREEN,
    OK,
    SEVEN_DAY_WIDTH,
    SEVEN_DAYS,
    TRACK,
    WARN,
    Costs,
    PriceList,
    PromptCache,
    RateWindow,
    Session,
    Span,
    bar_spans,
    cache_column,
    compact_window,
    context_column,
    cost_spans,
    costs_of,
    passed_part,
    read_costs,
    read_prices,
    response_usages,
    short_path,
    status_line,
    tokens,
    until,
    width,
    window_column,
    window_level,
)

NOW = 1_800_000_000
OPUS = {"display_name": "Opus 5.5", "id": "claude-opus-5-5"}
RATE_LIMITS = {
    "five_hour": {"used_percentage": 63.5, "resets_at": NOW + 7530},
    "seven_day": {
        "used_percentage": 84.2,
        "resets_at": NOW + 3 * 86400 + 4 * 3600 + 100,
    },
}
ESCAPE = re.compile(r"\033\[[0-9;]*m")


def list_prices() -> PriceList:
    """The prices in prices.json, which the sums below use."""
    prices = read_prices()
    assert prices is not None
    return prices


def line(
    data: dict[str, Any], branch: str | None = None, compact_limit: int | None = None
) -> str:
    """The status line for the input `data`, with colours, for the home
    directory /home/me."""
    return status_line(
        Session.from_json(data), branch, compact_limit, NOW, home="/home/me"
    )


def lines(
    data: dict[str, Any], branch: str | None = None, compact_limit: int | None = None
) -> list[str]:
    """The status line's lines for the input `data`, without colours, and with
    blank cells as spaces."""
    plain = ESCAPE.sub("", line(data, branch, compact_limit))
    return plain.replace(BLANK, " ").split("\n")


def text(spans: list[Span]) -> str:
    return "".join(span.text for span in spans)


def context(total: int, size: int | None = 1_000_000) -> dict[str, Any]:
    """A context_window after a response: current_usage is set."""
    return {
        "total_input_tokens": total,
        "context_window_size": size,
        "current_usage": {},
    }


class StatusLineTest(unittest.TestCase):
    def test_typical(self) -> None:
        data = {
            "model": OPUS,
            "effort": {"level": "high"},
            "cost": {"total_cost_usd": 3.456},
            "context_window": context(123_456),
            "prompt_cache": {
                "warm": True,
                "ttl": "1h",
                "expires_at": NOW + 2537,
                "misses": 2,
                "last_miss_cause": {"causes": ["ttl_expired_1h"]},
            },
            "rate_limits": RATE_LIMITS,
            "workspace": {"current_dir": "/home/me/project"},
        }
        first, second = lines(data, branch="main", compact_limit=700_000)
        self.assertEqual(
            first,
            "cache 42m ✗2 ttl1h · ctx 123k  · 5h 64%▲ ↻2h05m  · 7d 84%▲ ↻3d4h"
            "    · Opus 5.5 high (main) ~/project",
        )
        # Each column's bar starts under its text; the cost under the model.
        for label in ("cache", "ctx", "5h", "7d"):
            column = first.index(label)
            with self.subTest(label=label):
                self.assertNotEqual(second[column], " ")
                self.assertTrue(column == 0 or second[column - 1] == " ")
        self.assertEqual(second.index("$3.46"), first.index("Opus"))
        self.assertIn(f"{GREEN}~/project", line(data, branch="main"))

    def test_minimal(self) -> None:
        self.assertEqual(lines({"model": {"display_name": "Haiku"}}), ["Haiku"])

    def test_null_fields(self) -> None:
        data = {
            "model": OPUS,
            "effort": None,
            "prompt_cache": None,
            "rate_limits": None,
        }
        self.assertEqual(lines(data), ["Opus 5.5"])

    def test_second_line_does_not_start_with_a_space(self) -> None:
        # Claude Code removes spaces at the start of a line, so an empty bar
        # must not start with one.
        data = {"model": OPUS, "context_window": context(0)}
        self.assertFalse(ESCAPE.sub("", line(data)).split("\n")[1].startswith(" "))

    def test_context_unknown_after_compact(self) -> None:
        data = {
            "model": OPUS,
            "context_window": {
                "total_input_tokens": 0,
                "context_window_size": 1_000_000,
                "current_usage": None,
            },
        }
        self.assertEqual(lines(data), ["ctx ?     · Opus 5.5", " " * CONTEXT_WIDTH])
        # After an idle compaction, current_usage is set, but the tokens are 0.
        data["context_window"] = context(0)
        self.assertEqual(lines(data), ["ctx ?     · Opus 5.5", " " * CONTEXT_WIDTH])

    def test_context_follows_compact_window(self) -> None:
        session = Session.from_json({"model": OPUS, "context_window": context(560_000)})
        compact = context_column(session, 700_000)
        self.assertEqual(compact.top[1].style, ALERT.text)
        assert compact.bar is not None
        # 560k of 700k is 80%: 57.6 of 72 eighths, so 58.
        self.assertEqual(
            text(bar_spans(compact.bar.segments, CONTEXT_WIDTH)),
            "█" * 7 + "▎" + BLANK,
        )
        self.assertEqual(context_column(session, None).top[1].style, WARN.text)

    def test_context_without_a_size_has_no_colour_and_no_fill(self) -> None:
        session = Session.from_json(
            {"model": OPUS, "context_window": context(1499, size=None)}
        )
        column = context_column(session, None)
        self.assertEqual([span.style for span in column.top], [""])
        assert column.bar is not None
        self.assertEqual(column.bar.segments, [])


class CacheTest(unittest.TestCase):
    def test_late_shows_recache_and_short_misses_above_the_bar(self) -> None:
        cache = {
            "warm": True,
            "ttl": "5m",
            "expires_at": NOW + 200,
            "misses": 2,
            "last_miss_cause": {"causes": ["tools_changed", "new_cause"]},
            "recache_tokens_if_cold": 412_000,
        }
        data = {"model": OPUS, "cost": {"total_cost_usd": 1}, "prompt_cache": cache}
        first, second = lines(data)
        self.assertEqual(first, "cache 3m (412k) ✗2 tools,new_cause · Opus 5.5")
        # The column, and its bar, grow to the width of the text.
        self.assertEqual(second.index("$1.00"), first.index("Opus"))
        self.assertIn(f"{WARN.text}3m", line(data))

    def test_bar_is_the_lifetime_passed(self) -> None:
        for left, expected in (
            (3600, BLANK * 18),
            (1800, "█" * 9 + BLANK * 9),
            (1, "█" * 18),
        ):
            with self.subTest(left=left):
                cache = PromptCache(True, NOW + left, 3600, 0, [], None, None)
                column = cache_column(cache, NOW, DEFAULT_CONFIG)
                assert column.bar is not None
                self.assertEqual(
                    text(bar_spans(column.bar.segments, CACHE_WIDTH)), expected
                )

    def test_unknown_ttl_has_no_fill(self) -> None:
        cache = PromptCache(True, NOW + 1800, None, 0, [], None, None)
        column = cache_column(cache, NOW, DEFAULT_CONFIG)
        assert column.bar is not None
        self.assertEqual(column.bar.segments, [])

    def test_early_is_green_and_hides_recache(self) -> None:
        cache = {
            "warm": True,
            "expires_at": NOW + 600,
            "recache_tokens_if_cold": 88_000,
        }
        data = {"model": OPUS, "prompt_cache": cache}
        self.assertIn(f"{OK.text}10m", line(data))
        self.assertNotIn("88k", line(data))

    def test_cold_is_red_and_full(self) -> None:
        for cache in (
            {"warm": False, "expires_at": None, "recache_tokens_if_cold": 88_000},
            {"warm": True, "expires_at": NOW - 10, "recache_tokens_if_cold": 88_000},
        ):
            with self.subTest(cache=cache):
                data = {"model": OPUS, "prompt_cache": cache}
                self.assertEqual(
                    lines(data),
                    ["cache cold (88k)   · Opus 5.5", "█" * CACHE_WIDTH],
                )
                self.assertIn(f"{ALERT.solid.fg}█", line(data))


class WindowTest(unittest.TestCase):
    def test_level_follows_pace(self) -> None:
        cases = [
            # Behind or on pace: OK, however much is used.
            (90, 0.95, OK),
            (50, 0.5, OK),
            # Under the floor: OK.
            (8, 0.01, OK),
            # Ahead of pace: runs out before the reset.
            (64, 0.59, WARN),
            # 84% used at 60%: runs out in 0.114 of the window.
            (84, 0.6, WARN),
            # 90% used at 60%: runs out in 0.067 of the window.
            (90, 0.6, ALERT),
            (100, 0.5, ALERT),
        ]
        for used, passed, expected in cases:
            with self.subTest(used=used, passed=passed):
                level = window_level(RateWindow(used, None), passed, DEFAULT_CONFIG)
                self.assertIs(level, expected)

    def test_without_reset_time_the_level_follows_use(self) -> None:
        limit = RateWindow(64.5, None)
        self.assertIsNone(passed_part(limit, FIVE_HOURS, NOW))
        self.assertIs(window_level(limit, None, DEFAULT_CONFIG), WARN)
        limits = {"seven_day": {"used_percentage": 64.5}}
        first = lines({"model": OPUS, "rate_limits": limits})[0]
        self.assertEqual(first, "7d 64%" + " " * 10 + " · Opus 5.5")

    def test_behind_pace_shades_the_time_passed(self) -> None:
        # 25% used, 50% passed, 16 cells: solid to 4 cells, shaded to 8.
        limit = RateWindow(25, NOW + SEVEN_DAYS // 2)
        column = window_column("7d", SEVEN_DAYS, 16, limit, NOW, DEFAULT_CONFIG)
        assert column.bar is not None
        spans = bar_spans(column.bar.segments, 16)
        self.assertEqual(
            [(span.text, span.style) for span in spans],
            [
                ("████", OK.solid.fg),
                ("████", OK.shade.fg),
                (BLANK * 8, TRACK.bg),
            ],
        )
        self.assertNotIn("▲", text(column.top))

    def test_ahead_of_pace_shades_the_use_beyond_it(self) -> None:
        # 75% used, 50% passed: solid to 8 cells, shaded to 12, and ▲.
        limit = RateWindow(75, NOW + SEVEN_DAYS // 2)
        column = window_column("7d", SEVEN_DAYS, 16, limit, NOW, DEFAULT_CONFIG)
        assert column.bar is not None
        spans = bar_spans(column.bar.segments, 16)
        self.assertEqual(
            [(span.text, span.style) for span in spans],
            [
                ("█" * 8, WARN.solid.fg),
                ("████", WARN.shade.fg),
                (BLANK * 4, TRACK.bg),
            ],
        )
        self.assertIn("▲", text(column.top))

    def test_pace_needs_more_than_the_floor(self) -> None:
        # 8% used, about 6% of the window passed: under the floor, no mark.
        limits = {"five_hour": {"used_percentage": 8, "resets_at": NOW + 17_000}}
        first = lines({"model": OPUS, "rate_limits": limits})[0]
        self.assertTrue(first.startswith("5h 8% ↻4h43m "))


class BarTest(unittest.TestCase):
    def test_eighths(self) -> None:
        cases = {
            0: BLANK * 10,
            0.01: "▏" + BLANK * 9,
            0.5: "█████" + BLANK * 5,
            1: "█" * 10,
            1.2: "█" * 10,
        }
        for fraction, expected in cases.items():
            with self.subTest(fraction=fraction):
                self.assertEqual(text(bar_spans([(fraction, OK.solid)], 10)), expected)

    def test_a_boundary_inside_a_cell_uses_the_next_colour_as_background(
        self,
    ) -> None:
        # Solid to 3/8 of the first cell, then shade to the end of the second.
        spans = bar_spans([(3 / 16, OK.solid), (1.0, OK.shade)], 2)
        self.assertEqual(spans[0].text, "▍")
        self.assertEqual(spans[0].style, OK.solid.fg + OK.shade.bg)
        self.assertEqual((spans[1].text, spans[1].style), ("█", OK.shade.fg))

    def test_each_bar_is_as_wide_as_the_widest_text_of_its_gauge(self) -> None:
        widest = {
            CACHE_WIDTH: cache_column(
                PromptCache(False, None, None, 0, [], None, 999_999),
                NOW,
                DEFAULT_CONFIG,
            ).top,
            CONTEXT_WIDTH: context_column(
                Session.from_json({"model": OPUS, "context_window": context(999_999)}),
                None,
            ).top,
            FIVE_HOUR_WIDTH: window_column(
                "5h",
                FIVE_HOURS,
                FIVE_HOUR_WIDTH,
                RateWindow(100, NOW + 5 * 3600 - 1),
                NOW,
                DEFAULT_CONFIG,
            ).top,
            SEVEN_DAY_WIDTH: window_column(
                "7d",
                SEVEN_DAYS,
                SEVEN_DAY_WIDTH,
                RateWindow(100, NOW + 86400 - 1),
                NOW,
                DEFAULT_CONFIG,
            ).top,
        }
        for cells, spans in widest.items():
            with self.subTest(text=text(spans)):
                self.assertEqual(width(spans), cells)


def response(id: str, model: str = "claude-opus-5-5", **usage: Any) -> str:
    """A transcript line for one response."""
    entry = {"type": "assistant", "message": {"id": id, "model": model, "usage": usage}}
    return json.dumps(entry)


class CostTest(unittest.TestCase):
    def test_each_response_counts_once(self) -> None:
        lines = [
            response("a", output_tokens=10),
            response("a", output_tokens=10),
            json.dumps({"type": "user", "message": {"content": "hi"}}),
            '{"type": "assistant", "mess',  # A line still being written.
            response("b", output_tokens=5),
        ]
        self.assertEqual(
            [usage["output_tokens"] for _, usage in response_usages(lines)], [10, 5]
        )

    def test_categories_at_list_prices(self) -> None:
        usage = {
            "input_tokens": 1_000_000,
            "cache_creation_input_tokens": 3_000_000,
            "cache_creation": {"ephemeral_1h_input_tokens": 2_000_000},
            "cache_read_input_tokens": 10_000_000,
            "output_tokens": 1_000_000,
            "output_tokens_details": {"thinking_tokens": 250_000},
        }
        # Opus 5.5: $4 input, $20 output, $0.20 cache read; writes 1.25x
        # (5 minutes) and 2x (1 hour) the input price.
        self.assertEqual(
            costs_of([("claude-opus-5-5", usage)], list_prices()),
            Costs(
                input=4.0,
                cache_write=4.0 * (1.25 + 2 * 2),
                cache_read=2.0,
                output=15.0,
                thinking=5.0,
            ),
        )

    def test_reads_the_prices_file(self) -> None:
        prices = list_prices()
        self.assertEqual((prices.write_5m, prices.write_1h), (1.25, 2.0))
        self.assertIn("claude-opus-5-5", prices.models)

    def test_prices_that_cannot_be_read_are_none(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prices.json"
            self.assertIsNone(read_prices(path))
            path.write_text('{"models": []}')
            self.assertIsNone(read_prices(path))
            path.write_text("{")
            self.assertIsNone(read_prices(path))

    def test_unknown_models_and_fast_mode_are_not_priced(self) -> None:
        usages: list[tuple[str, dict[str, Any]]] = [
            ("claude-unknown", {"output_tokens": 1_000_000}),
            ("claude-opus-5-5", {"output_tokens": 1_000_000, "speed": "fast"}),
        ]
        self.assertEqual(costs_of(usages, list_prices()), Costs())

    def test_reads_the_subagents_transcripts_too(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            transcript = Path(directory) / "session.jsonl"
            transcript.write_text(response("a", output_tokens=1_000_000) + "\n")
            (Path(directory) / "session" / "subagents").mkdir(parents=True)
            (Path(directory) / "session" / "subagents" / "agent-1.jsonl").write_text(
                response("b", "claude-sonnet-5-5", output_tokens=1_000_000) + "\n"
            )
            self.assertEqual(read_costs(transcript, list_prices()), Costs(output=30.0))
            self.assertIsNone(
                read_costs(Path(directory) / "missing.jsonl", list_prices())
            )

    def test_breakdown(self) -> None:
        data = {
            "model": OPUS,
            "cost": {"total_cost_usd": 18.0},
            "prompt_cache": {
                "warm": True,
                "ttl": "1h",
                "expires_at": NOW + 3000,
                "miss_recache_tokens": 100_000,
            },
        }
        costs = Costs(
            input=0.001, cache_write=4.0, cache_read=8.0, output=3.0, thinking=2.0
        )
        # The miss: 100k tokens at 2x $4 a million. "other": 18 - 17.001.
        self.assertEqual(
            text(cost_spans(Session.from_json(data), costs, list_prices())),
            "$18.00 = read 8.00 · write 4.00 (miss 0.80) · out 3.00 · think 2.00"
            " · other 1.00",
        )
        self.assertEqual(
            text(cost_spans(Session.from_json(data), None, list_prices())), "$18.00"
        )


class FormatTest(unittest.TestCase):
    def test_short_path(self) -> None:
        self.assertEqual(
            [
                short_path(directory, "/home/me")
                for directory in ("/home/me", "/home/me/a/b", "/home/meg", "/tmp")
            ],
            ["~", "~/a/b", "/home/meg", "/tmp"],
        )
        self.assertEqual(short_path("/tmp", ""), "/tmp")

    def test_tokens(self) -> None:
        self.assertEqual(
            [tokens(count) for count in (0, 499, 500, 123_456, 999_999, 1_000_000)],
            ["0k", "0k", "1k", "123k", "1000k", "1M"],
        )

    def test_until(self) -> None:
        self.assertEqual(
            [
                until(NOW + left, NOW)
                for left in (-5, 59, 720, 7530, 3 * 86400 + 4 * 3600)
            ],
            ["0m", "0m", "12m", "2h05m", "3d4h"],
        )


class CompactWindowTest(unittest.TestCase):
    def test_reads_the_model_settings(self) -> None:
        settings = {
            "modelSettings": {"claude-opus-5-5": {"autoCompactWindow": 700_000}}
        }
        self.assertEqual(compact_window(settings, "claude-opus-5-5[1m]"), 700_000)
        self.assertIsNone(compact_window(settings, "claude-sonnet-5-5"))
        self.assertIsNone(compact_window({}, "claude-opus-5-5"))


if __name__ == "__main__":
    unittest.main()
