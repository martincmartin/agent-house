"""Tests for statusline.py. `install` does not link a test_* file.

Run: python3 -B -m unittest discover -s user/claude (tools/check runs it).
"""

import re
import unittest
from typing import Any

from statusline import (
    ALERT,
    BLANK,
    CACHE_WIDTH,
    CONTEXT_WIDTH,
    DEFAULT_CONFIG,
    FIVE_HOUR_WIDTH,
    FIVE_HOURS,
    OK,
    SEVEN_DAY_WIDTH,
    SEVEN_DAYS,
    TRACK,
    WARN,
    PromptCache,
    RateWindow,
    Session,
    Span,
    bar_spans,
    cache_column,
    compact_window,
    context_column,
    passed_part,
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


def line(
    data: dict[str, Any], branch: str | None = None, compact_limit: int | None = None
) -> str:
    """The status line for the input `data`, with colours."""
    return status_line(Session.from_json(data), branch, compact_limit, NOW)


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
        }
        first, second = lines(data, branch="main", compact_limit=700_000)
        self.assertEqual(
            first,
            "cache 42m ✗2 ttl1h · ctx 123k  · 5h 64%▲ ↻2h05m  · 7d 84%▲ ↻3d4h"
            "    · Opus 5.5 high (main)",
        )
        # Each column's bar starts under its text; the cost under the model.
        for label in ("cache", "ctx", "5h", "7d"):
            column = first.index(label)
            with self.subTest(label=label):
                self.assertNotEqual(second[column], " ")
                self.assertTrue(column == 0 or second[column - 1] == " ")
        self.assertEqual(second.index("$3.46"), first.index("Opus"))

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
                cache = PromptCache(True, NOW + left, 3600, 0, [], None)
                column = cache_column(cache, NOW, DEFAULT_CONFIG)
                assert column.bar is not None
                self.assertEqual(
                    text(bar_spans(column.bar.segments, CACHE_WIDTH)), expected
                )

    def test_unknown_ttl_has_no_fill(self) -> None:
        cache = PromptCache(True, NOW + 1800, None, 0, [], None)
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
                PromptCache(False, None, None, 0, [], 999_999), NOW, DEFAULT_CONFIG
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


class FormatTest(unittest.TestCase):
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
