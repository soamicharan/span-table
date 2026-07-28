"""Tests for JunctionSegment: the individual junction-glyph builders and
the top/bottom-character merge rule table.

The merge_rules dict is the single most fragile part of this codebase --
any (top_char, bottom_char) pair NOT covered silently falls back to a
blank space (see test_merge_rules_fallback below), which produces a gap
in a border instead of an error. These tests exist to make every
currently-supported combination explicit and regression-proof, and to
flag (rather than hide) combinations that are still missing.
"""
import pytest
from rich import box as rich_box

from span_table.rich_span_table import JunctionSegment


class TestGlyphBuilders:
    def test_top_uses_box_top_divider(self, junction, box):
        seg = junction.top()
        assert seg.text == box.top_divider
        assert seg.border is True
        assert seg.border_type == "top"

    def test_bottom_uses_box_bottom_divider(self, junction, box):
        seg = junction.bottom()
        assert seg.text == box.bottom_divider
        assert seg.border_type == "bottom"

    def test_left_t_uses_box_row_left(self, junction, box):
        seg = junction.left_t()
        assert seg.text == box.row_left

    def test_right_t_uses_box_row_right(self, junction, box):
        seg = junction.right_t()
        assert seg.text == box.row_right

    @pytest.mark.xfail(
        reason="right_t() currently tags border_type='left' (copy/paste "
               "from left_t) instead of 'right' -- see review notes.",
        strict=True,
    )
    def test_right_t_border_type_should_be_right(self, junction):
        seg = junction.right_t()
        assert seg.border_type == "right"


class TestBlankSegments:
    def test_width_plus_padding(self, junction, box):
        line = junction.blank_segments(width=5, line_type="mid")
        # left border + (width + 2 spaces for panel padding) + right border
        assert line[0].text == box.mid_vertical
        assert line[1].text == " " * 7
        assert line[2].text == box.mid_vertical

    def test_line_type_is_set(self, junction):
        line = junction.blank_segments(width=3, line_type="mid")
        assert line.line_type == "mid"

    def test_zero_width(self, junction):
        line = junction.blank_segments(width=0, line_type="mid")
        assert line[1].text == "  "  # just the 2 padding spaces


class TestMergeRulesTable:
    """Each of these locks in one currently-supported pairing so a future
    refactor of the dict can't accidentally drop or rename an entry."""

    @pytest.mark.parametrize(
        "pair_name,expected_name",
        [
            (("mid_vertical", "mid_vertical"), "mid_vertical"),
            (("bottom_divider", "top_divider"), "row_cross"),
            (("row_horizontal", "row_horizontal"), "row_horizontal"),
            (("row_horizontal", "top_divider"), "top_divider"),
            (("bottom_divider", "row_horizontal"), "bottom_divider"),
            (("bottom_left", "top_left"), "row_left"),
            (("row_left", "row_left"), "row_left"),
            (("bottom_divider", "row_left"), "row_left"),
            (("bottom_divider", "row_right"), "row_right"),
            (("row_right", "row_right"), "row_right"),
            (("row_left", "top_divider"), "row_left"),
            (("row_right", "top_divider"), "row_right"),
            (("bottom_right", "top_right"), "row_right"),
            (("mid_vertical", "row_left"), "row_left"),
            (("mid_vertical", "row_right"), "row_right"),
        ],
    )
    def test_known_pair(self, box, pair_name, span_table_factory, data_2x2, expected_name):
        result = span_table_factory(data_2x2, spans=[])
        top_char = getattr(box, pair_name[0])
        bottom_char = getattr(box, pair_name[1])
        expected = getattr(box, expected_name)
        assert result.merge_junction_rule(top_char, bottom_char) == expected

    @pytest.mark.parametrize(
        "pair_name",
        [
            ("top_left", "top_left"),
            ("top_divider", "top_divider"),
            ("bottom_left", "row_left"),
            ("top_left", "row_left"),
            ("row_cross", "row_horizontal"),
            ("bottom_right", "bottom_right"),
            ("top_right", "top_right"),
        ],
    )
    def test_currently_unhandled_pairs_fall_back_to_space(self, span_table_factory, data_2x2, box, pair_name):
        """Documents CURRENT (buggy) behavior: unhandled corner/junction
        combinations silently become a blank space rather than raising.
        This test should start FAILING (in a good way) once each pair is
        added to merge_rules -- at that point, move it into
        TestMergeRulesTable.test_known_pair instead of deleting it."""

        result = span_table_factory(data_2x2, spans=[])
        top_char = getattr(box, pair_name[0])
        bottom_char = getattr(box, pair_name[1])
        result = result.merge_junction_rule(top_char, bottom_char)
        assert result == " "
