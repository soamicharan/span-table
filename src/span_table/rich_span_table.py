from __future__ import annotations

from rich.segment import Segment, Segments
from rich.console import Console, ConsoleOptions
from rich.panel import Panel
from rich import box as rich_box
from rich.style import Style

from span_table.types import TableType, SpanType
from span_table.span import (
    extend_span, 
    check_span, 
    convert_cells_to_spans, 
    get_span,
    get_column_widths,
    get_row_heights,
)

from typing import Literal

console = Console()

def render_segments(lines):
    console.print(Segments([i.segment if isinstance(i, CellSegment) else i for i in lines]))

class CellSegment:
    def __init__(self, segment: Segment, border: bool, border_type: Literal['top', 'left', 'right', 'bottom'] | None = None):
        self.segment = segment
        self.border = border
        self.border_type = border_type

    @property
    def text(self) -> str:
        return self.segment.text

    @property
    def style(self) -> Style:
        return self.segment.style

    def __repr__(self):
        if self.border:
            return f"<'{self.text}' border={self.border} type={self.border_type}>"
        else:
            return f"'{self.text}'"

    def rtrim(self, offset=1) -> CellSegment:
        return CellSegment(Segment(self.text[:-offset], self.style), self.border, self.border_type)

    def ltrim(self, offset=1) -> CellSegment:
        return CellSegment(Segment(self.text[offset:], self.style), self.border, self.border_type)

    def __len__(self) -> int:
        return len(self.text)

class CellLine(list):
    def __init__(self, line: list[CellSegment], line_type: Literal['top', 'mid', 'bottom'], junction: JunctionSegment):
        super().__init__(line)
        self.line = line
        self.line_type = line_type
        self.junction = junction

    def copy(self):
        return CellLine(super().copy(), line_type=self.line_type, junction=self.junction)

    def __and__(self, cell_line: CellLine) -> bool:
        """Check line types are mergable or not"""
        pair = (self.line_type, cell_line.line_type)
        return self.line_type == cell_line.line_type or pair == ('bottom', 'mid')

    def __lshift__(self, cell_line: CellLine):
        """Column wise merge given cell line"""
        if len(self) == 0:
            self.extend(cell_line.line)
            return 
        if self[-1].border_type == 'top':
            if cell_line.line_type == 'top':
                # Merge '┌───────┐' + '┌───────┐' = ('┌───────' + '┬' + '───────┐')
                self[-1] = self[-1].rtrim()
                self.append(self.junction.top())
                self.append(cell_line[0].ltrim())
            elif cell_line.line_type == 'mid':
                # Merge '┌───────┐' + '│ Some Content │' = ('┌───────' + '┤' + ' Some Content │')
                self[-1] = self[-1].rtrim()
                self.append(self.junction.right_t())
                self.extend(cell_line[1:])
            elif cell_line.line_type == 'bottom':
                # Merge '┌───────┐' + '└───────┘' should not occur
                return 

        elif self[-1].border_type == 'right':
            if cell_line.line_type == 'top':
                # Merge '│ Some Content │' + '┌───────┐' = ('│ Some Content' + '├' + '───────┐')
                self.pop()
                self.append(self.junction.left_t())
                self.append(cell_line[0].ltrim())
            elif cell_line.line_type == 'mid':
                # Merge '│ Some Content │' + '│ Other Content │' = ('│ Some Content │' + ' Other Content │')
                self.extend(cell_line[1:])
            elif cell_line.line_type == 'bottom':
                # Merge '│ Some Content │' + '└───────┘' = ('│ Some Content' + '├' + '───────┘')
                self.pop()
                self.append(self.junction.left_t())
                self.append(cell_line[0].ltrim())

        elif self[-1].border_type == 'bottom':
            if cell_line.line_type == 'top':
                # Merge '└───────┘' + '┌───────┐' should not occur
                return None
            
            elif cell_line.line_type == 'mid':
                # Merge '└───────┘' + '│ Some Content │' = ('└───────' + '┤' + ' Some Content │')
                self[-1] = self[-1].rtrim()
                self.append(self.junction.right_t())
                self.extend(cell_line[1:])
            elif cell_line.line_type == 'bottom':
                # Merge '└───────┘' + '└───────┘' = ('└───────' + '┴' + '───────┘')
                self[-1] = self[-1].rtrim()
                self.append(self.junction.bottom())
                self.append(cell_line[0].ltrim())
        
class JunctionSegment:
    def __init__(self, box: rich_box.Box, border_style: Style):
        self.box = box
        self.border_style = border_style

    def top(self) -> CellSegment:
        return CellSegment(Segment(self.box.top_divider, self.border_style), border=True, border_type='top')

    def bottom(self) -> CellSegment:
        return CellSegment(Segment(self.box.bottom_divider, self.border_style), border=True, border_type='bottom')

    def left_t(self) -> CellSegment:
        return CellSegment(Segment(self.box.row_left, self.border_style), border=True, border_type='left')

    def right_t(self) -> CellSegment:
        return CellSegment(Segment(self.box.row_right, self.border_style), border=True, border_type='left')

    def blank_segments(self, width, line_type: Literal['top', 'mid', 'bottom']) -> CellLine:
        return CellLine([
            CellSegment(Segment(self.box.mid_vertical, self.border_style), border=True, border_type='left'),
            CellSegment(Segment(' ' * (width + 2)), border=True, border_type="top"),
            CellSegment(Segment(self.box.mid_vertical, self.border_style), border=True, border_type='right'),
        ], line_type=line_type, junction=self)
    
class Cell:
    def __init__(self, row: int, column: int, text: str, box: rich_box.Box = rich_box.SQUARE, border_style: Style = None):
        self.row = row
        self.column = column
        self.text = text
        self.box = box
        self.border_style = border_style
        self.rich_obj = Panel.fit(self.text, box=self.box, border_style=self.border_style)
        self.width = console.measure(self.rich_obj).minimum - 4
        opts = console.options.update(width=console.measure(self.rich_obj).minimum)
        segments = console.render_lines(self.rich_obj, opts)
        self.height = len(segments) - 2
        self.cell_lines: list[CellLine] = []


    def update_renderable(self, width: int, height: int, junction: JunctionSegment):
        self.rich_obj = Panel(self.text, box=self.box, width=width + 4, height=height + 2, border_style=self.border_style)
        self.width = width
        self.height = height
        opts = console.options.update(width=width + 4)
        segments = console.render_lines(self.rich_obj, opts)
        self.cell_lines = [CellLine([CellSegment(segments[0][0], border=True, border_type='top')], line_type="top", junction=junction)]
        for line in segments[1:-1]:
            self.cell_lines.append(CellLine([
                CellSegment(line[0], border=True, border_type='left'),
                *[
                    CellSegment(line_seg, border=False)
                    for line_seg in line[1:-1]
                ],
                CellSegment(line[-1], border=True, border_type='right')
            ], line_type="mid", junction=junction))
        self.cell_lines.append(CellLine([CellSegment(segments[-1][0], border=True, border_type='bottom')], line_type="bottom", junction=junction))

class SpanTable:
    def __init__(self, data: TableType, spans: list[SpanType], box: rich_box.Box = rich_box.SQUARE, border_style: str | Style = None):
        self.data = data
        self.spans = spans
        self.box = box
        self.border_style = Style.parse(border_style) if isinstance(border_style, str) else border_style if border_style is not None else Style()
        self.junction = JunctionSegment(box, self.border_style)
        self.total_rows = len(self.data)
        self.total_columns = len(self.data[0])
        self.cell_map = {
            (row, col): Cell(row, col, data[row][col], box=box, border_style=self.border_style) 
            for row in range(self.total_rows) for col in range(self.total_columns)
        }
        self.column_widths = get_column_widths(data, self.cell_map, self.spans)
        self.row_heights = get_row_heights(data, self.cell_map, self.spans)
        self.segment_map = {}

    def update_renderables(self):
        for row in range(self.total_rows):
            for col in range(self.total_columns):
                span = get_span(self.spans, row, col)
                if span is None or len(span) == 1:
                    width, height = self.column_widths[col], self.row_heights[row]
                else:
                    start_row_idx, start_col_idx = span[0]
                    end_row_idx, end_col_idx = span[-1]
                    width = sum(
                        self.column_widths[start_col_idx:end_col_idx + 1]
                    ) + ((end_col_idx - start_col_idx) * 3)

                    height = max(
                        sum(self.row_heights[start_row_idx:end_row_idx + 1]),
                        self.cell_map[(row, col)].height
                    )
                    # width = sum(self.column_widths[span[0][1]:span[-1][1] + 1]) + ((span[-1][1] - span[0][1]) * 3)
                    # height = max(sum(self.row_heights[span[0][0]:span[-1][0] + 1]), self.cell_map[(row, col)].height) 

                self.cell_map[(row, col)].update_renderable(width=width, height=height, junction=self.junction)

    def merge_junction_rule(self, top_char: str, bottom_char: str) -> str:
        rules = {
            (self.box.mid_vertical, self.box.mid_vertical): self.box.mid_vertical,
            (self.box.bottom_divider, self.box.top_divider): self.box.row_cross,
            (self.box.row_horizontal, self.box.row_horizontal): self.box.row_horizontal,
            (self.box.row_horizontal, self.box.top_divider): self.box.top_divider,
            (self.box.bottom_divider, self.box.row_horizontal): self.box.bottom_divider,
            (self.box.bottom_left, self.box.top_left): self.box.row_left,
            (self.box.row_left, self.box.row_left): self.box.row_left,
            (self.box.bottom_divider, self.box.row_left): self.box.row_left,
            (self.box.bottom_divider, self.box.row_right): self.box.row_right,
            (self.box.row_right, self.box.row_right): self.box.row_right,
            (self.box.row_left, self.box.top_divider): self.box.row_left,
            (self.box.row_right, self.box.top_divider): self.box.row_right,
            (self.box.bottom_right, self.box.top_right): self.box.row_right,
            (self.box.mid_vertical, self.box.row_left): self.box.row_left,
            (self.box.mid_vertical, self.box.row_right): self.box.row_right,
        }
        return rules.get((top_char, bottom_char), ' ')

    def merge_row_columns(self, row_idx: int) -> list[CellLine]:
        row_segments = []
        row_height = self.row_heights[row_idx]
        for line_idx in range(row_height + 2):
            processed_cells = []
            line_type = 'top' if line_idx == 0 else ('bottom' if line_idx == row_height + 1 else 'mid')
            rowline_segments = CellLine([], line_type=line_type, junction=self.junction)
            for col_idx in range(self.total_columns):
                span = get_span(self.spans, row_idx, col_idx)
                row, col = span[0] if span is not None else (row_idx, col_idx)
                if (row, col) in processed_cells:
                    continue
                else:
                    processed_cells.append((row, col))

                peek_lines = self.segment_map[(row, col)]
                if len(rowline_segments) == 0:
                    if (line_type == 'top' and peek_lines[0].line_type != 'top') or (line_type == 'bottom' and peek_lines[0].line_type != 'bottom'):
                        line_segments = self.junction.blank_segments(width=self.cell_map[(row, col)].width, line_type='mid')
                    else:
                        line_segments = peek_lines.pop(0)

                    rowline_segments << line_segments
                    continue

                if not rowline_segments & peek_lines[0]:
                    line_segments = self.junction.blank_segments(width=self.cell_map[(row, col)].width, line_type='mid')
                else:
                    line_segments = peek_lines.pop(0)

                rowline_segments << line_segments
            row_segments.append(rowline_segments)
        return row_segments

    def merge_row_segments(self, row_segments: list[list[CellLine]]) -> list[CellLine]:
        merged_rows = []
        for row in row_segments:
            top_line = row[0]
            if not merged_rows:
                merged_rows.append(top_line)
            else:
                prev_bottom_line = merged_rows[-1]
                merged_rows[-1] = self.merge_line_horizontal(prev_bottom_line, top_line)
            merged_rows.extend(row[1:])
    
        return merged_rows

    def merge_line_horizontal(self, prev_bottom_line: CellLine, top_line: CellLine) -> CellLine:
        top, bottom = prev_bottom_line.copy(), top_line.copy()
        merged_line = []
        top_segment, bottom_segment = None, None
        while top or bottom or top_segment is not None or bottom_segment is not None:
            if top_segment is None:
                top_segment = top.pop(0) if len(top) > 0 else None
    
            if bottom_segment is None:
                bottom_segment = bottom.pop(0) if len(bottom) > 0 else None
    
            if top_segment is None:
                merged_line.append(bottom_segment)
                bottom_segment = None
                continue
            elif bottom_segment is None:
                merged_line.append(top_segment)
                top_segment = None
                continue
    
            if not top_segment.border:
                merged_line.append(top_segment)
                merge_sequence = top_segment.text
            else:
                merge_sequence = list(zip(top_segment.text, bottom_segment.text))
                merged_line.append(
                    CellSegment(
                        Segment(
                            ''.join(
                                self.merge_junction_rule(top_char, bottom_char) 
                                for top_char, bottom_char in merge_sequence
                            ),
                            self.border_style
                        ),
                        border=True
                    )
                )
    
            if len(top_segment) > len(bottom_segment):
                top_segment = top_segment.ltrim(len(merge_sequence))
                bottom_segment = None
            elif len(top_segment) < len(bottom_segment):
                bottom_segment = bottom_segment.ltrim(len(merge_sequence))
                top_segment = None
            else:
                top_segment, bottom_segment = None, None
            
        return CellLine(merged_line, line_type='top', junction=self.junction)

    def merge_cells(self):
        self.segment_map = {key: [segments.copy() for segments in value.cell_lines] for key, value in self.cell_map.items()}
        row_segments = []
        for row_idx in range(self.total_rows):
            row_segments.append(self.merge_row_columns(row_idx))

        merged_segments = self.merge_row_segments(row_segments)
        for line in merged_segments:
            for segment in line:
                yield segment.segment
            
            yield Segment.line()

    def __rich_console__(self, console: Console, options: ConsoleOptions):
        self.update_renderables()
        yield from self.merge_cells()

def span_table(data: TableType, spans: list[SpanType], box: rich_box.Box = rich_box.SQUARE, border_style: str | Style = None) -> SpanTable:
    extended_spans = []
    for span in spans:
        check_span(data, span)
        extended_spans.append(extend_span(*span))

    spans = convert_cells_to_spans(data, extended_spans)
    return SpanTable(data, spans, box=box, border_style=border_style)