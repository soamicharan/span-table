from src.span_table.span import (
    get_span_column_count,
    get_span_row_count, 
    get_span_char_height, 
    get_span_char_width
)
from typing import Literal
from dataclasses import dataclass
from rich.box import Box
from src.span_table.types import SpanType, TableType

@dataclass
class Cell:
    text: str
    row: int
    column: int
    row_count: int
    column_count: int

    def __lt__(self, other):
        return [self.row, self.column] < [other.row, other.column]
    
    @property
    def left_sections(self):
        lines = self.text.split('\n')
        sections = 0

        for i in range(len(lines)):
            if lines[i].startswith('+'):
                sections += 1
        sections -= 1

        return sections

    @property
    def right_sections(self):
        lines = self.text.split('\n')
        sections = 0
        for i in range(len(lines)):
            if lines[i].endswith('+'):
                sections += 1
        return sections - 1

    @property
    def top_sections(self):
        top_line = self.text.split('\n')[0]
        sections = len(top_line.split('+')) - 2

        return sections

    @property
    def bottom_sections(self):
        bottom_line = self.text.split('\n')[-1]
        sections = len(bottom_line.split('+')) - 2

        return sections

def resolve_border(
        box: Box, 
        row: int, 
        col: int, 
        total_row: int, 
        total_col: int, 
        span: SpanType, 
        corner: Literal['top_left', 'top_right', 'bottom_left', 'bottom_right']
):
    if corner == "top_left":
        if row == 0 and col == 0:
            return box.top_left
        elif 0 < row and col == 0:
            return box.row_left
        elif  row == 0 and 0 < col:
            return box.top_divider
        else:
            return box.row_cross
    elif corner == "top_right":
        if len(span) > 1:
            row, col = span[0][0], span[-1][1]
        if row == 0 and col == (total_col - 1):
            return box.top_right
        elif row > 0 and col == (total_col - 1):
            return box.row_right
        elif row == 0 and col < (total_col - 1):
            return box.top_divider
        else:
            return box.row_cross
    elif corner == "bottom_left":
        if len(span) > 1:
            row, col = span[-1][0], span[0][1]
        if row == (total_row - 1) and col == 0:
            return box.bottom_left
        elif row == (total_row - 1) and col > 0:
            return box.bottom_divider
        elif row < (total_row - 1) and col == 0:
            return box.row_left
        else:
            return box.row_cross
    elif corner == "bottom_right":
        if len(span) > 1:
            row, col = span[-1]
        if row == (total_row - 1) and col == (total_col - 1):
            return box.bottom_right
        elif row == (total_row - 1) and col < (total_col - 1):
            return box.bottom_divider
        elif row < (total_row - 1) and col == (total_col - 1):
            return box.row_right
        else:
            return box.row_cross
      

def make_cell(table: TableType, span: SpanType, widths: list[int], heights: list[int], box: Box) -> Cell:
    width = get_span_char_width(span, widths)
    height = get_span_char_height(span, heights)
    text_row = span[0][0]
    text_column = span[0][1]
    text = table[text_row][text_column]
    total_cols = len(widths)
    total_rows = len(heights)

    lines = text.plain.split("\n")
    text.pad_width(width)

    height_difference = height - len(lines)
    text.append_empty_lines(height_difference, width)
    output = [
        ''.join([
            resolve_border(box, text_row, text_column, total_rows, total_cols, span, 'top_left'), 
            (width * box.row_horizontal),
            resolve_border(box, text_row, text_column, total_rows, total_cols, span, 'top_right')
        ])
    ]

    for line in text.markup.split('\n'):
        output.append(box.mid_vertical + line + box.mid_vertical)

    symbol = box.row_horizontal

    output.append(
        ''.join([
            resolve_border(box, text_row, text_column, total_rows, total_cols, span, 'bottom_left'), 
            width * symbol, 
            resolve_border(box, text_row, text_column, total_rows, total_cols, span, 'bottom_right')
        ])
    )

    text = "\n".join(output)
    row_count = get_span_row_count(span)
    column_count = get_span_column_count(span)
    return Cell(text=text, row=text_row, column=text_column, row_count=row_count, column_count=column_count)


def merge_cells(cell1: Cell, cell2: Cell, direction: Literal["RIGHT", "TOP", "BOTTOM", "LEFT"], box: Box):
    cell1_lines = cell1.text.split("\n")
    cell2_lines = cell2.text.split("\n")
    if direction == "RIGHT":
        for i in range(len(cell1_lines)):
            sub = cell1_lines[i][-1]
            if cell1_lines[i][-1] == box.mid_vertical and cell2_lines[i][0] == box.row_cross:
                sub = box.row_left
            elif cell1_lines[i][-1] == box.row_cross and cell2_lines[i][0] == box.mid_vertical:
                sub = box.row_right
            elif cell1_lines[i][-1] == box.row_cross and (cell2_lines[i][0] == box.top_left or cell2_lines[i][0] == box.top_divider):
                sub = box.top_divider
            
            cell1_lines[i] = cell1_lines[i][:-1] + sub + cell2_lines[i][1:]
        cell1.text = "\n".join(cell1_lines)
        cell1.column_count += cell2.column_count

    elif direction == "TOP":
        if cell1_lines[0].count('+') > cell2_lines[-1].count('+'):
            cell2_lines.pop(-1)
        else:
            cell1_lines.pop(0)
        cell2_lines.extend(cell1_lines)
        cell1.text = "\n".join(cell2_lines)
        cell1.row_count += cell2.row_count
        cell1.row = cell2.row
        cell1.column = cell2.column

    elif direction == "BOTTOM":
        merged_cells = ""
        for top_char, bottom_char in zip(cell1_lines[-1], cell2_lines[0]):
            if top_char == box.row_cross and bottom_char == box.row_horizontal:
                merged_cells += box.bottom_divider
            elif top_char == box.row_horizontal and bottom_char == box.row_cross:
                merged_cells += box.top_divider
            else:
                merged_cells += top_char
        cell1_lines[-1] = merged_cells
        cell1_lines.extend(cell2_lines[1:])
        cell1.text = "\n".join(cell1_lines)
        cell1.row_count += cell2.row_count

    elif direction == "LEFT":
        for i in range(len(cell1_lines)):
            sub = cell1_lines[i]
            if cell1_lines[i][0] == box.mid_vertical and cell2_lines[i][-1] == box.row_cross:
                sub = box.row_right + sub[1:]
            elif cell1_lines[i][0] == box.row_cross and cell2_lines[i][-1] == box.mid_vertical:
                sub = box.row_left + sub[1:]

            cell1_lines[i] = cell2_lines[i][0:-1] + sub
        cell1.text = "\n".join(cell1_lines)
        cell1.column_count += cell2.column_count
        cell1.row = cell2.row
        cell1.column = cell2.column
    
def merge_all_cells(cells: list[Cell], box: Box) -> str:
    current = 0
    while len(cells) > 1:
        count = 0
        while count < len(cells):
            cell1 = cells[current]
            cell2 = cells[count]
            merge_direction = get_merge_direction(cell1, cell2)
            if not merge_direction == "NONE":
                merge_cells(cell1, cell2, merge_direction, box)
                if current > count:
                    current -= 1

                cells.pop(count)
            else:
                count += 1

        current += 1
        if current >= len(cells):
            current = 0

    return cells[0].text

def get_merge_direction(cell1: Cell, cell2: Cell) -> Literal["RIGHT", "TOP", "BOTTOM", "LEFT", "NONE"]:
    cell1_left = cell1.column
    cell1_right = cell1.column + cell1.column_count
    cell1_top = cell1.row
    cell1_bottom = cell1.row + cell1.row_count
    cell2_left = cell2.column
    cell2_right = cell2.column + cell2.column_count
    cell2_top = cell2.row
    cell2_bottom = cell2.row + cell2.row_count

    if (cell1_right == cell2_left and cell1_top == cell2_top and
            cell1_bottom == cell2_bottom and
            cell1.right_sections >= cell2.left_sections):
        return "RIGHT"

    elif (cell1_left == cell2_left and cell1_right == cell2_right and
            cell1_top == cell2_bottom and
            cell1.top_sections >= cell2.bottom_sections):
        return "TOP"

    elif (cell1_left == cell2_left and
          cell1_right == cell2_right and
          cell1_bottom == cell2_top and
          cell1.bottom_sections >= cell2.top_sections):
        return "BOTTOM"

    elif (cell1_left == cell2_right and
          cell1_top == cell2_top and
          cell1_bottom == cell2_bottom and
          cell1.left_sections >= cell2.right_sections):
        return "LEFT"

    else:
        return "NONE"

