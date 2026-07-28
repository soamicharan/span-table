"""Randomized invariant tests.

These don't assert exact expected output (too tedious to hand-compute
for arbitrary layouts); instead they check properties that must hold for
ANY valid span layout:

  - rendering doesn't crash
  - output is rectangular (no ragged lines)
  - every line starts/ends with a recognized border character (no stray
    blank space from an unhandled junction combo)
  - total rendered width is stable regardless of span shape, for a fixed
    column-width table (spans shouldn't change the overall table width)

Because these are randomized, a failure should be turned into a fixed
regression test (with the exact seed's span layout hardcoded) in
test_span_table_render.py rather than just re-run until green.
"""
import pytest


BORDER_ROWS, BORDER_COLS = 4, 4
N_SEEDS = 25


def _border_chars(box):
    return set(
        box.top_left + box.top_right + box.bottom_left + box.bottom_right
        + box.mid_vertical + box.row_left + box.row_right
        + box.top + box.bottom + box.row_horizontal
        + box.top_divider + box.bottom_divider + box.row_cross
    )


@pytest.mark.parametrize("seed", range(N_SEEDS))
class TestRandomLayouts:
    def test_does_not_crash(self, seed, span_table_factory, random_spans, render_grid):
        rows, cols = BORDER_ROWS, BORDER_COLS
        data = [[f"{r}{c}" for c in range(cols)] for r in range(rows)]
        spans = random_spans(rows, cols, n_spans=3, seed=seed)
        render_grid(span_table_factory(data, spans=spans))  # should not raise

    def test_output_is_rectangular(self, seed, span_table_factory, random_spans, render_grid):
        rows, cols = BORDER_ROWS, BORDER_COLS
        data = [[f"{r}{c}" for c in range(cols)] for r in range(rows)]
        spans = random_spans(rows, cols, n_spans=3, seed=seed)
        lines = render_grid(span_table_factory(data, spans=spans))
        widths = {len(l) for l in lines}
        assert len(widths) == 1, f"seed={seed} spans={spans} ragged output: {lines}"

    def test_no_stray_blank_edges(self, seed, span_table_factory, random_spans, render_grid, box):
        rows, cols = BORDER_ROWS, BORDER_COLS
        data = [[f"{r}{c}" for c in range(cols)] for r in range(rows)]
        spans = random_spans(rows, cols, n_spans=3, seed=seed)
        lines = render_grid(span_table_factory(data, spans=spans))
        chars = _border_chars(box)
        for line in lines:
            assert line[0] in chars, f"seed={seed} spans={spans} bad left edge: {line!r}"
            assert line[-1] in chars, f"seed={seed} spans={spans} bad right edge: {line!r}"

    def test_width_independent_of_span_shape(self, seed, span_table_factory, random_spans, render_grid):
        """Merging cells should redistribute existing column widths, not
        change the table's overall width, for a fixed data grid."""
        rows, cols = BORDER_ROWS, BORDER_COLS
        data = [[f"{r}{c}" for c in range(cols)] for r in range(rows)]

        baseline_lines = render_grid(span_table_factory(data, spans=[]))
        baseline_width = len(baseline_lines[0])

        spans = random_spans(rows, cols, n_spans=3, seed=seed)
        spanned_lines = render_grid(span_table_factory(data, spans=spans))
        spanned_width = len(spanned_lines[0])

        assert spanned_width == baseline_width, (
            f"seed={seed} spans={spans} width changed: "
            f"{baseline_width} -> {spanned_width}"
        )


class TestManySmallSpans:
    """Stress the merge machinery with a higher span density on a bigger
    grid, since small n_spans on a 4x4 grid may not exercise every
    junction combination."""

    @pytest.mark.parametrize("seed", range(10))
    def test_dense_span_layout_does_not_crash(self, seed, span_table_factory, random_spans, render_grid):
        rows, cols = 6, 6
        data = [[f"{r}{c}" for c in range(cols)] for r in range(rows)]
        spans = random_spans(rows, cols, n_spans=8, seed=seed)
        lines = render_grid(span_table_factory(data, spans=spans))
        widths = {len(l) for l in lines}
        assert len(widths) == 1, f"seed={seed} spans={spans} ragged output"
