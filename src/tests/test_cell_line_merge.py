"""Tests for CellLine: column-wise merging of two cells' border/content
lines that sit side by side in the same table row.

__lshift__ handles four border_type states on the left operand
(top / right / bottom -- 'left' is not currently handled explicitly,
see TestLshiftUnhandledStates) crossed with three line_types on the
right operand (top / mid / bottom) = 12 branches. Each is tested below.
"""
import pytest
from rich.segment import Segment

from span_table.rich_span_table import CellSegment, CellLine


def text_of(line) -> str:
    return "".join(seg.text for seg in line)


class TestAnd:
    def test_same_line_type_is_compatible(self, make_line):
        a = make_line([], line_type="mid")
        b = make_line([], line_type="mid")
        assert (a & b) is True

    def test_top_top_compatible(self, make_line):
        a = make_line([], line_type="top")
        b = make_line([], line_type="top")
        assert (a & b) is True

    def test_bottom_mid_special_cased_compatible(self, make_line):
        a = make_line([], line_type="bottom")
        b = make_line([], line_type="mid")
        assert (a & b) is True

    def test_mid_bottom_reverse_order_not_covered(self, make_line):
        """__and__ only special-cases ('bottom', 'mid'), not the reverse.
        This documents current behavior -- flip the operand order and the
        result changes, which is a real asymmetry bug: __and__ should
        probably be symmetric."""
        a = make_line([], line_type="mid")
        b = make_line([], line_type="bottom")
        assert (a & b) is False

    def test_top_mid_incompatible(self, make_line):
        """A rowspan cell still emitting 'mid' content lines, positioned
        against a fresh physical row's 'top' line, is currently reported
        as INCOMPATIBLE. This is the suspected root cause of the
        rowspan-across-a-physical-row-boundary bug -- see
        test_span_table_render.py::test_rowspan_crossing_row_boundary."""
        a = make_line([], line_type="top")
        b = make_line([], line_type="mid")
        assert (a & b) is False

    def test_bottom_top_incompatible(self, make_line):
        a = make_line([], line_type="bottom")
        b = make_line([], line_type="top")
        assert (a & b) is False


class TestLshiftEmptyLeft:
    def test_lshift_onto_empty_extends(self, make_line, make_segment):
        left = make_line([], line_type="top")
        right = make_line([make_segment("┌───┐", border=True, border_type="top")], line_type="top")
        left << right
        assert text_of(left) == "┌───┐"


class TestLshiftTopBorderType:
    def test_top_plus_top(self, make_line, make_segment, box):
        left = make_line(
            [make_segment("┌───┐", border=True, border_type="top")], line_type="top"
        )
        right = make_line(
            [make_segment("┌───┐", border=True, border_type="top")], line_type="top"
        )
        left << right
        assert text_of(left) == f"┌───{box.top_divider}───┐"

    def test_top_plus_mid(self, make_line, make_segment, box):
        left = make_line(
            [make_segment("┌───┐", border=True, border_type="top")], line_type="top"
        )
        right = make_line(
            [
                make_segment("│", border=True, border_type="left"),
                make_segment(" xy ", border=False),
                make_segment("│", border=True, border_type="right"),
            ],
            line_type="mid",
        )
        left << right
        assert text_of(left) == f"┌───{box.row_right} xy │"

    def test_top_plus_bottom_is_noop(self, make_line, make_segment):
        """'┌───┐' followed by '└───┘' should never happen structurally;
        __lshift__ should not corrupt state if it's ever called this way."""
        left = make_line(
            [make_segment("┌───┐", border=True, border_type="top")], line_type="top"
        )
        original = text_of(left)
        right = make_line(
            [make_segment("└───┘", border=True, border_type="bottom")], line_type="bottom"
        )
        left << right
        assert text_of(left) == original  # unchanged


class TestLshiftRightBorderType:
    def test_right_plus_top(self, make_line, make_segment, box):
        left = make_line(
            [
                make_segment("│", border=True, border_type="left"),
                make_segment(" xy ", border=False),
                make_segment("│", border=True, border_type="right"),
            ],
            line_type="mid",
        )
        right = make_line(
            [make_segment("┌───┐", border=True, border_type="top")], line_type="top"
        )
        left << right
        assert text_of(left) == f"│ xy {box.row_left}───┐"

    def test_right_plus_mid_concatenates(self, make_line, make_segment):
        left = make_line(
            [
                make_segment("│", border=True, border_type="left"),
                make_segment(" xy ", border=False),
                make_segment("│", border=True, border_type="right"),
            ],
            line_type="mid",
        )
        right = make_line(
            [
                make_segment("│", border=True, border_type="left"),
                make_segment(" ab ", border=False),
                make_segment("│", border=True, border_type="right"),
            ],
            line_type="mid",
        )
        left << right
        assert text_of(left) == "│ xy │ ab │"

    def test_right_plus_bottom(self, make_line, make_segment, box):
        left = make_line(
            [
                make_segment("│", border=True, border_type="left"),
                make_segment(" xy ", border=False),
                make_segment("│", border=True, border_type="right"),
            ],
            line_type="mid",
        )
        right = make_line(
            [make_segment("└───┘", border=True, border_type="bottom")], line_type="bottom"
        )
        left << right
        assert text_of(left) == f"│ xy {box.row_left}───┘"


class TestLshiftBottomBorderType:
    def test_bottom_plus_top_is_noop(self, make_line, make_segment):
        left = make_line(
            [make_segment("└───┘", border=True, border_type="bottom")], line_type="bottom"
        )
        original = text_of(left)
        right = make_line(
            [make_segment("┌───┐", border=True, border_type="top")], line_type="top"
        )
        left << right
        assert text_of(left) == original

    def test_bottom_plus_mid(self, make_line, make_segment, box):
        left = make_line(
            [make_segment("└───┘", border=True, border_type="bottom")], line_type="bottom"
        )
        right = make_line(
            [
                make_segment("│", border=True, border_type="left"),
                make_segment(" xy ", border=False),
                make_segment("│", border=True, border_type="right"),
            ],
            line_type="mid",
        )
        left << right
        assert text_of(left) == f"└───{box.row_right} xy │"

    def test_bottom_plus_bottom(self, make_line, make_segment, box):
        left = make_line(
            [make_segment("└───┘", border=True, border_type="bottom")], line_type="bottom"
        )
        right = make_line(
            [make_segment("└───┘", border=True, border_type="bottom")], line_type="bottom"
        )
        left << right
        assert text_of(left) == f"└───{box.bottom_divider}───┘"


class TestLshiftUnhandledStates:
    @pytest.mark.xfail(
        reason="__lshift__ has no explicit branch for self[-1].border_type "
               "== 'left' (only 'top'/'right'/'bottom' are handled); a "
               "line ending in a bare left-border segment falls through "
               "all if/elif branches and silently does nothing.",
        strict=False,
    )
    def test_left_border_type_on_left_operand(self, make_line, make_segment):
        left = make_line(
            [make_segment("│", border=True, border_type="left")], line_type="mid"
        )
        right = make_line(
            [
                make_segment("│", border=True, border_type="left"),
                make_segment(" ab ", border=False),
                make_segment("│", border=True, border_type="right"),
            ],
            line_type="mid",
        )
        before_len = len(left)
        left << right
        assert len(left) > before_len, "left << right should have appended something"
