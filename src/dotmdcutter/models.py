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
    MATH_BLOCK = "math_block"


class SpanStyle(str, Enum):
    NORMAL = "normal"
    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold_italic"
    CODE = "code"
    STRIKETHROUGH = "strikethrough"
    MATH = "math"


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
    latex_code: str = ""


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
    jpeg_quality: int = 98
    custom_font_path: Optional[str] = None
    custom_mono_font_path: Optional[str] = None
    scale: int = (
        1  # Resolution multiplier: 1=320x240, 2=640x480, 3=960x720 (Retina/HiDPI)
    )
    sharpen: bool = True  # Micro-sharpening filter for crisp text at 1x
    hr_as_pagebreak: bool = False

    @property
    def content_width(self) -> int:
        return max(10, self.width - 2 * self.margin_x)

    @property
    def content_height(self) -> int:
        footer_reservation = 14 if self.show_footer else 0
        return max(10, self.height - 2 * self.margin_y - footer_reservation)

    @property
    def pixel_width(self) -> int:
        return self.width * max(1, self.scale)

    @property
    def pixel_height(self) -> int:
        return self.height * max(1, self.scale)
