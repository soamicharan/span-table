from rich import box as rich_box
from rich.text import Text

from src.span_table.span import (
    extend_span, 
    check_span, 
    convert_cells_to_spans, 
    get_output_column_widths,
    get_output_row_heights,
)
from src.span_table.cell import make_cell, merge_all_cells
from src.span_table.markup_text import MarkupText
from src.span_table.types import SpanType, TableType
from typing import Annotated

TableMarkupType = Annotated[list[list[MarkupText]], 'Lists of list of markup type objects']

def check_table(data: TableType):
    if not type(data) is list:
        raise Exception("Table data must be a list of lists")

    if len(data) == 0:
        raise Exception("Table data must contain at least one row and one column")

    for i in range(len(data)):
        if not type(data[i]) is list:
            raise Exception("Table data must be a list of lists")
        
        if not len(data[i]) == len(data[0]):
            raise Exception("Each row must have the same number of columns")

def span_table(
    data: TableType,
    spans: list[SpanType],
    box: rich_box.Box = rich_box.SQUARE
) -> str:
    check_table(data=data)
    extended_spans = []
    for span in spans:
        check_span(data, span)
        extended_spans.append(extend_span(*span))

    text_data = [[MarkupText(cell) for cell in row] for row in data]
    spans = convert_cells_to_spans(text_data, extended_spans)
    widths = get_output_column_widths(text_data, spans)
    heights = get_output_row_heights(text_data, spans)
    cells = [
        make_cell(text_data, span, widths, heights, box)
        for span in spans
    ]
    cells = list(sorted(cells))
    grid_table = merge_all_cells(cells, box)

    return grid_table