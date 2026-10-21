"""Rewrite each Markdown table in the given files as a bulleted list.

    python3 -I table_to_list.py FILE...

Each row becomes "- FIRST: LAST", or "- FIRST (MIDDLE): LAST" when a table has
three columns, wrapped at 80 columns. The header and separator rows are
dropped. A table with another number of columns is an error. It prints, for
each file, the characters before and after, and checks that every cell's text
is still in the file.
"""

import re
import sys
import textwrap
from pathlib import Path

WIDTH = 80
CELL_SPLIT = re.compile(r"(?<!\\)\|")


def cells(line: str) -> list[str]:
    return [cell.strip() for cell in CELL_SPLIT.split(line.strip())[1:-1]]


def item(row: list[str]) -> str:
    if len(row) == 2:
        text = f"{row[0]}: {row[1]}"
    elif len(row) == 3:
        text = f"{row[0]} ({row[1]}): {row[2]}"
    else:
        raise ValueError(f"a table with {len(row)} columns: {row}")
    return textwrap.fill(
        text,
        WIDTH,
        initial_indent="- ",
        subsequent_indent="  ",
        break_long_words=False,
        break_on_hyphens=False,
    )


def convert(text: str) -> tuple[str, list[str]]:
    output: list[str] = []
    every_cell: list[str] = []
    lines = text.split("\n")
    index = 0
    while index < len(lines):
        if not lines[index].startswith("|"):
            output.append(lines[index])
            index += 1
            continue
        table = []
        while index < len(lines) and lines[index].startswith("|"):
            table.append(cells(lines[index]))
            index += 1
        for row in table[2:]:
            every_cell.extend(row)
            output.append(item(row))
    return "\n".join(output), every_cell


def main() -> None:
    for name in sys.argv[1:]:
        path = Path(name)
        before = path.read_text()
        after, every_cell = convert(before)
        flat = " ".join(after.split())
        missing = [cell for cell in every_cell if " ".join(cell.split()) not in flat]
        if missing:
            raise SystemExit(f"{name}: cells lost: {missing}")
        path.write_text(after)
        print(f"{name}: {len(before)} -> {len(after)} chars")


if __name__ == "__main__":
    main()
