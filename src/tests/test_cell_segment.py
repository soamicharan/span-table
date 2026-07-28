"""Unit tests for CellSegment -- the lowest-level building block.

These are pure, fast, no-Console-required tests. If these fail, nothing
built on top of CellSegment (CellLine, merges, full renders) can be
trusted, so this file should always be run/fixed first.
"""
from rich.segment import Segment
from rich.style import Style

from span_table.rich_span_table import CellSegment


class TestLen:
    def test_len_matches_text_length(self, make_segment):
        seg = make_segment("hello")
        assert len(seg) == 5

    def test_len_zero_for_empty_text(self, make_segment):
        seg = make_segment("")
        assert len(seg) == 0

    def test_len_counts_box_drawing_chars_as_one(self, make_segment):
        # box-drawing characters are single Python chars even though they
        # look "wide" -- len() must not double count them
        seg = make_segment("┌───┐")
        assert len(seg) == 5


class TestRtrim:
    def test_default_offset_removes_last_char(self, make_segment):
        seg = make_segment("hello")
        trimmed = seg.rtrim()
        assert trimmed.text == "hell"

    def test_custom_offset(self, make_segment):
        seg = make_segment("hello")
        trimmed = seg.rtrim(2)
        assert trimmed.text == "hel"

    def test_rtrim_preserves_border_flag_and_type(self, make_segment):
        seg = make_segment("┌───┐", border=True, border_type="top")
        trimmed = seg.rtrim()
        assert trimmed.border is True
        assert trimmed.border_type == "top"

    def test_rtrim_preserves_style(self, make_segment):
        style = Style(color="red")
        seg = make_segment("hello", style=style)
        trimmed = seg.rtrim()
        assert trimmed.style == style

    def test_rtrim_does_not_mutate_original(self, make_segment):
        seg = make_segment("hello")
        _ = seg.rtrim()
        assert seg.text == "hello"


class TestLtrim:
    def test_default_offset_removes_first_char(self, make_segment):
        seg = make_segment("hello")
        trimmed = seg.ltrim()
        assert trimmed.text == "ello"

    def test_custom_offset(self, make_segment):
        seg = make_segment("hello")
        trimmed = seg.ltrim(3)
        assert trimmed.text == "lo"

    def test_ltrim_full_length_yields_empty_string(self, make_segment):
        seg = make_segment("hello")
        trimmed = seg.ltrim(5)
        assert trimmed.text == ""
        assert len(trimmed) == 0

    def test_ltrim_preserves_border_flag_and_type(self, make_segment):
        seg = make_segment("───┐", border=True, border_type="top")
        trimmed = seg.ltrim()
        assert trimmed.border is True
        assert trimmed.border_type == "top"

    def test_ltrim_does_not_mutate_original(self, make_segment):
        seg = make_segment("hello")
        _ = seg.ltrim()
        assert seg.text == "hello"


class TestRepr:
    def test_repr_border_segment_includes_type(self, make_segment):
        seg = make_segment("┌", border=True, border_type="top")
        r = repr(seg)
        assert "border=True" in r
        assert "type=top" in r

    def test_repr_non_border_segment_is_just_text(self, make_segment):
        seg = make_segment("hi", border=False)
        assert repr(seg) == "'hi'"


class TestProperties:
    def test_text_property(self, make_segment):
        seg = make_segment("abc")
        assert seg.text == "abc"

    def test_style_property(self, make_segment):
        style = Style(bold=True)
        seg = make_segment("abc", style=style)
        assert seg.style == style

    def test_construct_from_raw_segment(self):
        raw = Segment("x", Style())
        seg = CellSegment(raw, border=False)
        assert seg.text == "x"
        assert seg.border is False
        assert seg.border_type is None
