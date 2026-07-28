import random

import pytest
from rich import box as rich_box
from rich.console import Console
from rich.style import Style

from span_table.rich_span_table import CellSegment, CellLine, JunctionSegment, SpanTable
from span_table.rich_span_table import span_table as span_table_fn


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def render_to_text(renderable, width: int = 80) -> str:
    """Render a Rich renderable to plain text (no ANSI), for exact-string
    golden-output comparisons."""
    console = Console(width=width, force_terminal=False, legacy_windows=False)
    with console.capture() as capture:
        console.print(renderable)
    return capture.get()


def render_lines(renderable, width: int = 80) -> list[str]:
    """Same as render_to_text but pre-split into lines with trailing
    newline/whitespace stripped from the block (not per-line, since
    trailing spaces inside borders can be meaningful)."""
    text = render_to_text(renderable, width=width)
    return text.rstrip("\n").split("\n")


@pytest.fixture
def render():
    return render_to_text


@pytest.fixture
def render_grid():
    return render_lines


# ---------------------------------------------------------------------------
# Junction / box fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def box():
    return rich_box.SQUARE


@pytest.fixture
def plain_style():
    return Style()


@pytest.fixture
def junction(box, plain_style):
    return JunctionSegment(box, plain_style)


@pytest.fixture
def make_junction():
    """Factory version, for tests that need a custom box/style."""
    def _make(box_=rich_box.SQUARE, style=None):
        return JunctionSegment(box_, style if style is not None else Style())
    return _make


# ---------------------------------------------------------------------------
# CellSegment / CellLine builders
# ---------------------------------------------------------------------------

@pytest.fixture
def make_segment():
    from rich.segment import Segment

    def _make(text, border=False, border_type=None, style=None):
        return CellSegment(Segment(text, style), border=border, border_type=border_type)

    return _make


@pytest.fixture
def make_line(junction):
    def _make(segments, line_type="mid"):
        return CellLine(list(segments), line_type=line_type, junction=junction)

    return _make


# ---------------------------------------------------------------------------
# Sample table data
# ---------------------------------------------------------------------------

@pytest.fixture
def data_2x2():
    return [["A", "B"], ["C", "D"]]


@pytest.fixture
def data_3x3():
    return [
        ["A", "B", "C"],
        ["D", "E", "F"],
        ["G", "H", "I"],
    ]


@pytest.fixture
def span_table_factory():
    """Returns the span_table() constructor function under test."""
    return span_table_fn


# ---------------------------------------------------------------------------
# Randomized span generation for fuzz tests
# ---------------------------------------------------------------------------

def random_valid_spans(rows: int, cols: int, n_spans: int, seed: int) -> list:
    """Generate up to n_spans non-overlapping rectangular spans as
    ((start_row, start_col), (end_row, end_col)) tuples, skipping any
    that would collide with an already-placed span or degenerate to a
    single cell."""
    rng = random.Random(seed)
    occupied = set()
    spans = []

    attempts = 0
    while len(spans) < n_spans and attempts < n_spans * 20:
        attempts += 1
        r0 = rng.randint(0, rows - 1)
        c0 = rng.randint(0, cols - 1)
        r1 = rng.randint(r0, min(rows - 1, r0 + 1))
        c1 = rng.randint(c0, min(cols - 1, c0 + 1))

        if (r0, c0) == (r1, c1):
            continue  # not actually a span

        cells = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
        if cells & occupied:
            continue

        occupied |= cells
        spans.append(((r0, c0), (r1, c1)))

    return spans


@pytest.fixture
def random_spans():
    return random_valid_spans
