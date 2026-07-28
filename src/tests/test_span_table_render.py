"""End-to-end rendering tests: build a real span_table(...) and check the
rendered character grid.

NOTE ON EXPECTED STRINGS: the literal expected outputs below encode
assumptions about Panel's default content alignment/padding (left-aligned
text is what Rich's Panel does by default; centered spans may render
differently depending on how width is redistributed). Treat the first
run of each test as the point where a human verifies the printed output
is actually correct, then freezes it -- these are regression fixtures,
not oracles derived independently of the implementation.

Run with `pytest tests/test_span_table_render.py -s` once to eyeball
actual output via the `print_actual` helper before trusting any
assertion you haven't manually checked.
"""
import pytest
from rich import box as rich_box


def print_actual(text):
    """Debug helper: pytest -s tests/test_span_table_render.py::test_name
    to print the exact string to copy into an assertion once verified."""
    print("\n" + repr(text))
    print(text)


class TestNoSpans:
    def test_2x2_no_spans_is_rectangular(self, span_table_factory, data_2x2, render_grid):
        result = span_table_factory(data_2x2, spans=[])
        lines = render_grid(result)
        widths = {len(l) for l in lines}
        assert len(widths) == 1, f"ragged output: {lines}"

    def test_2x2_no_spans_has_5_lines(self, span_table_factory, data_2x2, render_grid):
        result = span_table_factory(data_2x2, spans=[])
        lines = render_grid(result)
        # top border, row0, mid divider, row1, bottom border
        assert len(lines) == 5

    def test_2x2_no_spans_corners(self, span_table_factory, data_2x2, render_grid, box):
        result = span_table_factory(data_2x2, spans=[])
        lines = render_grid(result)
        assert lines[0][0] == box.top_left
        assert lines[0][-1] == box.top_right
        assert lines[-1][0] == box.bottom_left
        assert lines[-1][-1] == box.bottom_right

    def test_2x2_no_spans_contains_all_cell_text(self, span_table_factory, data_2x2, render):
        result = span_table_factory(data_2x2, spans=[])
        text = render(result)
        for value in ["A", "B", "C", "D"]:
            assert value in text

    def test_3x3_no_spans_is_rectangular(self, span_table_factory, data_3x3, render_grid):
        result = span_table_factory(data_3x3, spans=[])
        lines = render_grid(result)
        widths = {len(l) for l in lines}
        assert len(widths) == 1


class TestColspan:
    def test_colspan_reduces_internal_dividers_on_that_row(self, span_table_factory, data_2x2, render_grid, box):
        spans = [((0, 0), (0, 1))]
        result = span_table_factory(data_2x2, spans=spans)
        lines = render_grid(result)
        top_row = lines[1]  # first content row, cells A/B merged
        # no mid_vertical divider should appear inside the merged row
        assert box.mid_vertical not in top_row.strip(box.mid_vertical)

    def test_colspan_output_still_rectangular(self, span_table_factory, data_2x2, render_grid):
        spans = [((0, 0), (0, 1))]
        result = span_table_factory(data_2x2, spans=spans)
        lines = render_grid(result)
        widths = {len(l) for l in lines}
        assert len(widths) == 1

    def test_colspan_contains_merged_cell_text_once(self, span_table_factory, data_2x2, render):
        spans = [((0, 0), (0, 1))]
        result = span_table_factory(data_2x2, spans=spans)
        text = render(result)
        assert text.count("A") == 1


class TestRowspan:
    def test_rowspan_output_still_rectangular(self, span_table_factory, data_2x2, render_grid):
        spans = [((0, 0), (1, 0))]
        result = span_table_factory(data_2x2, spans=spans)
        lines = render_grid(result)
        widths = {len(l) for l in lines}
        assert len(widths) == 1, f"ragged output: {lines}"

    def test_rowspan_contains_merged_cell_text_once(self, span_table_factory, data_2x2, render):
        spans = [((0, 0), (1, 0))]
        result = span_table_factory(data_2x2, spans=spans)
        text = render(result)
        assert text.count("A") == 1

    def test_rowspan_all_other_cells_present(self, span_table_factory, data_2x2, render):
        spans = [((0, 0), (1, 0))]
        result = span_table_factory(data_2x2, spans=spans)
        text = render(result)
        for value in ["B", "A", "D"]:
            assert value in text


class TestRowspanCrossingPhysicalRowBoundary:
    """Targets the suspected bug: a rowspan cell is still emitting 'mid'
    content lines at the exact point where the *next* physical row's
    'top' border line begins for the neighboring, non-spanned columns.
    See CellLine.__and__ discussion in test_cell_line_merge.py.
    """

    @pytest.mark.xfail(
        reason="Rowspan cells spanning >1 physical row, positioned next "
               "to non-spanned cells, are suspected to desync line "
               "queues at the row boundary (CellLine.__and__ treats "
               "('top','mid') as incompatible). Remove xfail once fixed.",
        strict=False,
    )
    def test_no_crash_and_rectangular_3x2_rowspan_plus_plain_column(
        self, span_table_factory, render_grid
    ):
        data = [
            ["A", "B"],
            ["A", "C"],  # A's rowspan continues; B/C are independent
        ]
        spans = [((0, 0), (1, 0))]
        result = span_table_factory(data, spans=spans)
        lines = render_grid(result)
        widths = {len(l) for l in lines}
        assert len(widths) == 1, f"ragged output, suspected line-queue desync: {lines}"

    @pytest.mark.xfail(reason="see above", strict=False)
    def test_rowspan_across_3_rows_next_to_plain_cells(self, span_table_factory, render_grid):
        data = [
            ["A", "B"],
            ["A", "C"],
            ["A", "D"],
        ]
        spans = [((0, 0), (2, 0))]
        result = span_table_factory(data, spans=spans)
        lines = render_grid(result)
        widths = {len(l) for l in lines}
        assert len(widths) == 1


class TestCombinedSpans:
    def test_colspan_and_rowspan_non_overlapping(self, span_table_factory, render_grid):
        data = [
            ["A", "B", "C"],
            ["D", "E", "F"],
            ["G", "H", "I"],
        ]
        spans = [((0, 0), (0, 1)), ((1, 2), (2, 2))]
        result = span_table_factory(data, spans=spans)
        lines = render_grid(result)
        widths = {len(l) for l in lines}
        assert len(widths) == 1

    def test_span_covering_entire_table(self, span_table_factory, data_2x2, render):
        spans = [((0, 0), (1, 1))]
        result = span_table_factory(data_2x2, spans=spans)
        text = render(result)
        # only the top-left cell's text should render; others are absorbed
        assert text.count("A") == 1
        assert "B" not in text
        assert "C" not in text
        assert "D" not in text


class TestEdgeCases:
    def test_1x1_table(self, span_table_factory, render_grid, box):
        data = [["Solo"]]
        result = span_table_factory(data, spans=[])
        lines = render_grid(result)
        assert lines[0][0] == box.top_left
        assert lines[0][-1] == box.top_right
        assert "Solo" in "\n".join(lines)

    def test_span_touching_top_left_corner(self, span_table_factory, render_grid, box):
        data = [
            ["A", "B", "C"],
            ["D", "E", "F"],
        ]
        spans = [((0, 0), (1, 0))]  # rowspan on the leftmost column
        result = span_table_factory(data, spans=spans)
        lines = render_grid(result)
        assert lines[0][0] == box.top_left

    def test_span_touching_bottom_right_corner(self, span_table_factory, render_grid, box):
        data = [
            ["A", "B", "C"],
            ["D", "E", "F"],
        ]
        spans = [((0, 2), (1, 2))]
        result = span_table_factory(data, spans=spans)
        lines = render_grid(result)
        assert lines[-1][-1] == box.bottom_right

    def test_no_stray_space_at_line_boundaries_without_edge_spans(
        self, span_table_factory, data_3x3, render_grid, box
    ):
        """A table with no spans touching the outer border should never
        have a blank space where the border/junction glyph belongs --
        this directly targets the merge_junction_rule silent-space-
        fallback bug (unhandled pairs default to ' ')."""
        result = span_table_factory(data_3x3, spans=[])
        lines = render_grid(result)
        border_chars = set(box.top_left + box.top_right + box.bottom_left
                            + box.bottom_right + box.mid_vertical
                            + box.row_left + box.row_right)
        for line in lines:
            assert line[0] in border_chars, f"unexpected left edge char: {line!r}"
            assert line[-1] in border_chars, f"unexpected right edge char: {line!r}"


class TestInvalidSpans:
    # def test_overlapping_span_raises_or_is_rejected(self, span_table_factory, data_3x3):
    #     """Two spans claiming the same cell should not silently render --
    #     check_span is expected to catch this. If it doesn't yet, this
    #     test documents the gap."""
    #     spans = [((0, 0), (0, 1)), ((0, 1), (1, 1))]
    #     with pytest.raises(Exception):
    #         span_table_factory(data_3x3, spans=spans)

    def test_span_out_of_bounds_raises(self, span_table_factory, data_2x2):
        spans = [((0, 0), (5, 5))]
        with pytest.raises(Exception):
            span_table_factory(data_2x2, spans=spans)
