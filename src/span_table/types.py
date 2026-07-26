from typing import Annotated

SpanType =  Annotated[list[tuple[int, int]], "List of tuples"]
TableType = Annotated[list[list[str]], "List of list of strings with rich markup"]

