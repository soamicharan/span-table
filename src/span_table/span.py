from span_table.types import TableType, SpanType

def check_span(data: TableType, span: SpanType):
    if not len(span) == 2 or not len(span[0]) == 2 or not len(span[1]) == 2:
        raise Exception("Span must be tuple of tuples in format ((start row index, start column index), (end row index, end column index))")
    
    start_span, end_span = span
    if not (start_span[0] <= end_span[0] and start_span[1] <= end_span[1]):
        raise Exception('Spans must be rectangular in shape.')

    if not (0 <= start_span[0] <= end_span[0] < len(data)) or not (0 <= start_span[1] <= end_span[1] < len(data[0])):
        raise Exception(f"{span} is out of bounds.")

def extend_span(start: tuple[int, int], end: tuple[int, int]) -> SpanType:
    extended_span = []
    for row_idx in range(start[0], end[0] + 1):
        for col_idx in range(start[1], end[1] + 1):
            extended_span.append((row_idx, col_idx))

    return extended_span

def get_span(spans: list[SpanType], row: int, column: int) -> SpanType | None:
    for i in range(len(spans)):
        if (row, column) in spans[i]:
            return spans[i]

    return None

def convert_cells_to_spans(data: TableType, spans: list[SpanType]) -> list[SpanType]:
    new_spans = []
    for row in range(len(data)):
        for column in range(len(data[0])):
            span = get_span(spans, row, column)
            if not span:
                new_spans.append([(row, column)])
    
    new_spans.extend(spans)
    new_spans = list(sorted(new_spans))
    return new_spans

def get_span_column_count(span: SpanType) -> int:
    return max((span[-1][1] - span[0][1]) + 1, 1)

def get_span_row_count(span: SpanType) -> int:
    return max((span[-1][0] - span[0][0]) + 1, 1)


def get_column_widths(table: TableType, cell_map,  spans: list[SpanType]) -> list[int]:
    widths = [3 for _ in range(len(table[0]))]
    for row in range(len(table)):
        for column in range(len(table[row])):
            span = get_span(spans, row, column)
            column_count = get_span_column_count(span)
            text_row = span[0][0]
            text_column = span[0][1]
            text_cell = cell_map.get((text_row, text_column))
            length = text_cell.width
            if column_count == 1:
                widths[column] = max(length, widths[column])
            else:
                end_column = text_column + column_count
                available_space = sum(widths[text_column:end_column]) + column_count - 1
                while length > available_space:
                    for i in range(text_column, end_column):
                        widths[i] += 1
                        available_space = sum(widths[text_column:end_column]) + column_count - 1
                        if length <= available_space:
                            break
    return widths

def get_row_heights(table: TableType, cell_map, spans: list[SpanType]) -> list[int]:
    heights = [-1 for _ in table]
    for row in range(len(table)):
        for column in range(len(table[row])):
            text_cell = cell_map.get((row, column))
            span = get_span(spans, row, column)
            row_count = get_span_row_count(span)
            height = text_cell.height
            if row_count == 1:
                heights[row] = max(height, heights[row])
    
    for row in range(len(table)):
        for column in range(len(table[row])):
            text_cell = cell_map.get((row, column))
            span = get_span(spans, row, column)
            row_count = get_span_row_count(span)
            height = text_cell.height
            if row_count > 1:
                text_row = span[0][0]
                text_column = span[0][1]
                end_row = text_row + row_count
                text_cell = cell_map.get((text_row, text_column))
                height = text_cell.height - (row_count - 1)
                add_row = 0
                while height > sum(heights[text_row:end_row]):
                    heights[text_row + add_row] += 1
                    if add_row + 1 < row_count:
                        add_row += 1
                    else:
                        add_row = 0
    return [max(1, i) for i in heights]