"""
dotmdcutter: Pixel-perfect Markdown to 320x240 image cutter.
"""

from .models import PageConfig, MarkdownBlock, InlineSpan, BlockType, SpanStyle
from .parser import parse_markdown
from .layout import LayoutEngine, PageLayout
from .renderer import MarkdownRenderer
from .themes import THEMES, Theme, get_theme

__version__ = "1.0.0"

__all__ = [
    "PageConfig",
    "MarkdownBlock",
    "InlineSpan",
    "BlockType",
    "SpanStyle",
    "parse_markdown",
    "LayoutEngine",
    "PageLayout",
    "MarkdownRenderer",
    "THEMES",
    "Theme",
    "get_theme",
]
