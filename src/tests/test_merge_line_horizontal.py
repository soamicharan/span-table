"""Tests for SpanTable.merge_line_horizontal in isolation, bypassing
SpanTable.__init__ (which needs a real table + span module) since this
function only depends on self.junction / self.box / self.border_style.

merge_line_horizontal merges the BOTTOM line of one physical table row
with the TOP line of the next. Two invariants must hold for any input:

  1. total character count is preserved (nothing dropped, nothing
     duplicated), and
  2. border-vs-border overlaps produce a junction glyph via
     merge_junction_rule, while non-border (actual cell content, from a
     rowspan cell still mid-content) passes through unchanged and does
     NOT get truncated based on merge_sequence length.

Known bug under test: when a wide non-border top_segment sits above a
narrower bottom_segment, the current implementation computes
`merge_sequence = top_segment.text` (the FULL text) and then does
`top_segment.ltrim(len(merge_sequence))`, collapsing top_segment to ''
and setting bottom_segment = None -- discarding whatever portion of
bottom_segment wasn't actually "under" top_segment instead of carrying
it to the next iteration.
"""
import pytest
from rich import box as rich_box
from rich.segment import Segment
from rich.style import Style

from span_table.rich_span_table import CellSegment, CellLine, JunctionSegment, SpanTable


def make_span_table_stub(box_=rich_box.SQUARE, style=None):
    """Construct a SpanTable instance without running __init__, since we
    only need merge_line_horizontal's dependencies."""
    st = object.__new__(SpanTable)
    st.box = box_
    st.border_style = style if style is not None else Style()
    st.junction = JunctionSegment(st.box, st.border_style)
    return st


def seg(text, border=False, border_type=None):
    return CellSegment(Segment(text), border=border, border_type=border_type)


def line(segments, line_type="mid", junction=None):
    return CellLine(list(segments), line_type=line_type, junction=junction)


def total_len(cell_line):
    return sum(len(s) for s in cell_line)


class TestBorderVsBorderMerge:
    def test_equal_length_single_segments_merge_to_junction(self, box):
        st = make_span_table_stub(box)
        top = line([seg("└────", border=True, border_type="bottom")],
                   line_type="bottom", junction=st.junction)
        bottom = line([seg("┌────", border=True, border_type="top")],
                      line_type="top", junction=st.junction)

        merged = st.merge_line_horizontal(top, bottom)

        assert total_len(merged) == 5
        assert "".join(s.text for s in merged)[0] == box.row_left

    def test_matching_boundaries_produce_cross_junction(self, box):
        st = make_span_table_stub(box)
        top = line(
            [seg("────", border=True, border_type="bottom"),
             seg("┘", border=True, border_type="bottom")],
            line_type="bottom", junction=st.junction,
        )
        bottom = line(
            [seg("─┬", border=True, border_type="top"),
             seg("───", border=True, border_type="top")],
            line_type="top", junction=st.junction,
        )
        merged = st.merge_line_horizontal(top, bottom)
        assert total_len(merged) == 5


class TestContentOverBorderMerge:
    """The suspected-buggy path: a non-border content segment (from a
    row-spanning cell) sitting above one or more border segments."""

    def test_content_segment_appended_verbatim(self, box):
        st = make_span_table_stub(box)
        top = line([seg("hello", border=False)], line_type="mid", junction=st.junction)
        bottom = line([seg("┌────", border=True, border_type="top")],
                      line_type="top", junction=st.junction)

        merged = st.merge_line_horizontal(top, bottom)
        texts = [s.text for s in merged]
        assert "hello" in texts

    @pytest.mark.xfail(
        reason="Known bug: content segment wider than the paired border "
               "segment causes the remainder of bottom_segment's *sibling* "
               "segments to be dropped instead of carried forward. See "
               "review notes on merge_line_horizontal / pending_eat fix.",
        strict=False,
    )
    def test_wide_content_over_two_split_border_segments_preserves_length(self, box):
        st = make_span_table_stub(box)
        # top: a single 10-char content run (as if from a rowspan cell)
        top = line([seg("0123456789", border=False)], line_type="mid", junction=st.junction)
        # bottom: two adjacent 5-char border segments (as if two columns
        # meet directly beneath the rowspan cell)
        bottom = line(
            [
                seg("┌────", border=True, border_type="top"),
                seg("┌────", border=True, border_type="top"),
            ],
            line_type="top", junction=st.junction,
        )

        merged = st.merge_line_horizontal(top, bottom)

        # nothing should be silently dropped: total output width must
        # equal the wider of the two operands (10), not less
        assert total_len(merged) == 10

    @pytest.mark.xfail(
        reason="Same root cause as above, verified via segment count "
               "instead of raw length: the second bottom border segment "
               "should still appear in the output.",
        strict=False,
    )
    def test_second_bottom_segment_not_lost(self, box):
        st = make_span_table_stub(box)
        top = line([seg("0123456789", border=False)], line_type="mid", junction=st.junction)
        bottom = line(
            [
                seg("┌────", border=True, border_type="top"),
                seg("┌────", border=True, border_type="top"),
            ],
            line_type="top", junction=st.junction,
        )
        merged = st.merge_line_horizontal(top, bottom)
        # the merged line should still be internally consistent -- e.g.
        # re-joining its text should not be shorter than input due to a
        # dropped segment
        rejoined = "".join(s.text for s in merged)
        assert len(rejoined) == 10


class TestNoInputDropped:
    """General invariant tests independent of the specific bug above --
    good smoke tests for any future rewrite of this function."""

    @pytest.mark.parametrize(
        "top_texts,bottom_texts",
        [
            (["ab"], ["ab"]),
            (["a", "b"], ["ab"]),
            (["ab"], ["a", "b"]),
            (["a", "b", "c"], ["a", "bc"]),
        ],
    )
    def test_total_length_preserved_for_equal_width_borders(self, box, top_texts, bottom_texts):
        st = make_span_table_stub(box)
        top = line(
            [seg(t, border=True, border_type="bottom") for t in top_texts],
            line_type="bottom", junction=st.junction,
        )
        bottom = line(
            [seg(t, border=True, border_type="top") for t in bottom_texts],
            line_type="top", junction=st.junction,
        )
        merged = st.merge_line_horizontal(top, bottom)
        expected_width = sum(len(t) for t in top_texts)
        assert total_len(merged) == expected_width
