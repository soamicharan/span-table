from dataclasses import dataclass
from rich.markup import Tag, _parse


@dataclass
class StyleToken:
    tag: Tag

@dataclass
class TextToken:
    text: str

    def pad_width(self, width: int):
        pad = max(0, width - len(self.text))
        if pad:
            self.text += ' ' * pad

class MarkupText:
    def __init__(self, markup: str):
        self._tokens: list[StyleToken | TextToken] = []
        self._parse(markup)

    def _parse(self, markup: str):
        for _, text, tag in _parse(markup):
            if text is not None:
                for line in text.split('\n'):
                    if line == '':
                        continue
                    self._tokens.append(TextToken(f" {line} "))
            else:
                self._tokens.append(StyleToken(tag))

    @property
    def plain(self) -> str:
        return "\n".join(l.text for l in self.text_tokens)

    @property
    def markup(self) -> str:
        markup_text = ""
        for idx in range(len(self._tokens)):
            if idx > 0:
                if isinstance(self._tokens[idx - 1], TextToken) and isinstance(self._tokens[idx], TextToken):
                    markup_text += "\n"

            if isinstance(self._tokens[idx], TextToken):
                markup_text += self._tokens[idx].text
            else:
                markup_text += f"[{self._tokens[idx].tag.name}]"

        return markup_text

    @property
    def text_tokens(self) -> list[TextToken]:
        return [token for token in self._tokens if isinstance(token, TextToken)]
    
    def pad_width(self, width: int):
        for token in self.text_tokens:
            token.pad_width(width)

    def append_empty_lines(self, count: int, width: int):
        for _ in range(count):
            self._tokens.append(TextToken(" " * width))