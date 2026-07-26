# span-table

`span-table` is a lightweight Python helper for rendering ASCII tables with merged cells using Rich-style markup.

## Features

- Render table layouts with custom merged spans
- Support multi-line cell content
- Uses `rich` box styles for flexible borders
- Compatible with Python `>=3.14`

## Installation

```bash
pip install span-table
```

## Quick Start

```python
from span_table import span_table
from rich import print

table = [
    ["Header 1", "Header 2", "Header3", "Header 4"],
    ["row 1", "column 2", "column 3", "column 4"],
    ["row 2", "Cells span columns.", "", ""],
    ["row 3", "Cells\nspan rows.", "- Cells\n- contain\n- blocks", ""],
    ["row 4", "", "", ""]
]

# Spans are defined as ((start_row, start_col), (end_row, end_col)) with zero-based indexes
my_spans = [
    ((2, 1), (2, 3)),
    ((3, 1), (4, 1)),
    ((3, 2), (4, 3)),
]

print(span_table(table, my_spans))
```

This renders:

```text
┌──────────┬────────────┬──────────┬──────────┐
│ Header 1 │ Header 2   │ Header3  │ Header 4 │
├──────────┼────────────┼──────────┼──────────┤
│ row 1    │ column 2   │ column 3 │ column 4 │
├──────────┼────────────┴──────────┴──────────┤
│ row 2    │ Cells span columns.              │
├──────────┼────────────┬─────────────────────┤
│ row 3    │ Cells      │ - Cells             │
├──────────┤ span rows. │ - contain           │
│ row 4    │            │ - blocks            │
└──────────┴────────────┴─────────────────────┘
```

## Advanced Usage

```python
from span_table import span_table
from rich import print

table = [
    ["Time", "[on red]Height[/]", "", "[on green]Weight[/]", ""],
    ["", "Total", "Change", "Total", "Change"],
    ["15:30", "1", "2", "3", "4"]
]

spans = [
    ((0, 0), (1, 0)),
    ((0, 1), (0, 2)),
    ((0, 3), (0, 4))
]

print(span_table(table, spans))
```

This renders:

```text
┌───────┬────────────────┬────────────────┐
│ Time  │<red bg> Height │<Green BG>Weight│
│       ├───────┬────────┼───────┬────────┤
│       │ Total │ Change │ Total │ Change │
├───────┼───────┼────────┼───────┼────────┤
│ 15:30 │ 1     │ 2      │ 3     │ 4      │
└───────┴───────┴────────┴───────┴────────┘
```

## API

### `span_table(data, spans, box=rich_box.SQUARE) -> str`

Render a text table with optional merged cells.

- `data`: `list[list[str]]` — table rows and columns
- `spans`: `list[tuple[tuple[int, int], tuple[int, int]]]` — list of merge regions
- `box`: `rich.box.Box` — optional Rich box style such as `box.SQUARE`

### Span rules

- Each span is a rectangular region defined by a start and end coordinate
- Coordinates are zero-based: `(row_index, column_index)`
- Spans can cover a single cell or multiple cells
- Spans must be within the table bounds

## Rich markup support

Cell values may include Rich markup tags such as `[bold]`, `[italic]`, or color tags but does not support emoji yet. The library preserves markup while measuring text layout.

## Notes

- Ensure each row has the same number of columns
- Non-merged cells may be omitted from `spans`
- The library automatically fills any cells not included in spans as standard individual cells
