from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class BlockType(str, Enum):
    HEADER = "header"
    PARAGRAPH = "paragraph"
    CODE_BLOCK = "code_block"
    BLOCKQUOTE = "blockquote"
    LIST_ITEM = "list_item"
    THEMATIC_BREAK = "thematic_break"
    PAGE_BREAK = "page_break"
    EMPTY_LINE = "empty_line"


class SpanStyle(str, Enum):
    NORMAL = "normal"
    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold_italic"
    CODE = "code"
    STRIKETHROUGH = "strikethrough"


@dataclass
class InlineSpan:
    text: str
    style: SpanStyle = SpanStyle.NORMAL


@dataclass
class MarkdownBlock:
    block_type: BlockType
    spans: List[InlineSpan] = field(default_factory=list)
    level: int = 1  # Header level (1-6) or list indent level
    code_lines: List[str] = field(default_factory=list)
    language: str = ""
    is_ordered: bool = False
    order_number: Optional[int] = None


@dataclass
class PageConfig:
    width: int = 320
    height: int = 240
    margin_x: int = 10
    margin_y: int = 8
    base_font_size: int = 13
    line_spacing: int = 3
    paragraph_spacing: int = 6
    show_footer: bool = True
    theme_name: str = "dark"
    output_format: str = "png"  # png, jpg, bmp
    jpeg_quality: int = 95
    custom_font_path: Optional[str] = None
    custom_mono_font_path: Optional[str] = None

    @property
    def content_width(self) -> int:
        return max(10, self.width - 2 * self.margin_x)

    @property
    def content_height(self) -> int:
        footer_reservation = 14 if self.show_footer else 0
        return max(10, self.height - 2 * self.margin_y - footer_reservation)
