import re
from typing import List
from .models import BlockType, InlineSpan, MarkdownBlock, SpanStyle


_INLINE_REGEX = re.compile(
    r"(`(?P<code>[^`]+)`)"
    r"|((?<!\\)\$(?!\s)(?P<math>[^$\n]+?)(?<!\s)\$)"
    r"|(\*\*\*(?P<bi>[^*]+)\*\*\*)"
    r"|(\*\*(?P<bold>[^*]+)\*\*)"
    r"|(\*(?P<italic>[^*]+)\*)"
    r"|(~~(?P<strike>[^~]+)~~)"
)


def parse_inline_spans(text: str) -> List[InlineSpan]:
    """Parse inline formatting (bold, italic, inline code, strike, inline LaTeX) into spans."""
    if not text:
        return []

    spans: List[InlineSpan] = []
    last_idx = 0

    for match in _INLINE_REGEX.finditer(text):
        start, end = match.span()
        if start > last_idx:
            spans.append(InlineSpan(text=text[last_idx:start], style=SpanStyle.NORMAL))

        if match.group("code"):
            spans.append(InlineSpan(text=match.group("code"), style=SpanStyle.CODE))
        elif match.group("math"):
            spans.append(InlineSpan(text=match.group("math"), style=SpanStyle.MATH))
        elif match.group("bi"):
            spans.append(InlineSpan(text=match.group("bi"), style=SpanStyle.BOLD_ITALIC))
        elif match.group("bold"):
            spans.append(InlineSpan(text=match.group("bold"), style=SpanStyle.BOLD))
        elif match.group("italic"):
            spans.append(InlineSpan(text=match.group("italic"), style=SpanStyle.ITALIC))
        elif match.group("strike"):
            spans.append(InlineSpan(text=match.group("strike"), style=SpanStyle.STRIKETHROUGH))

        last_idx = end

    if last_idx < len(text):
        spans.append(InlineSpan(text=text[last_idx:], style=SpanStyle.NORMAL))

    return spans


def parse_markdown(markdown_text: str, hr_as_pagebreak: bool = False) -> List[MarkdownBlock]:
    """
    Parses a Markdown string into a sequence of structured MarkdownBlock elements,
    with full support for math blocks ($$ ... $$) and Unicode symbols.
    """
    lines = markdown_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: List[MarkdownBlock] = []

    in_code_block = False
    code_lines: List[str] = []
    code_lang = ""

    in_math_block = False
    math_lines: List[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for fenced code block start/end
        if stripped.startswith("```") or stripped.startswith("~~~"):
            if in_code_block:
                # End of code block
                blocks.append(
                    MarkdownBlock(
                        block_type=BlockType.CODE_BLOCK,
                        code_lines=code_lines,
                        language=code_lang,
                    )
                )
                code_lines = []
                code_lang = ""
                in_code_block = False
            else:
                # Start of code block
                in_code_block = True
                code_lang = stripped[3:].strip()
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Check for block math ($$ ... $$)
        if stripped.startswith("$$"):
            if in_math_block:
                blocks.append(
                    MarkdownBlock(
                        block_type=BlockType.MATH_BLOCK,
                        latex_code="\n".join(math_lines),
                    )
                )
                math_lines = []
                in_math_block = False
                i += 1
                continue
            elif stripped.endswith("$$") and len(stripped) > 2:
                # Single line block math: $$ formula $$
                formula = stripped[2:-2].strip()
                blocks.append(
                    MarkdownBlock(
                        block_type=BlockType.MATH_BLOCK,
                        latex_code=formula,
                    )
                )
                i += 1
                continue
            else:
                # Multi-line block math starts
                in_math_block = True
                math_lines = []
                i += 1
                continue

        if in_math_block:
            if stripped == "$$":
                blocks.append(
                    MarkdownBlock(
                        block_type=BlockType.MATH_BLOCK,
                        latex_code="\n".join(math_lines),
                    )
                )
                math_lines = []
                in_math_block = False
            else:
                math_lines.append(line)
            i += 1
            continue

        # Check for explicit page break markers
        if stripped.lower() in ("---page---", "---break---", "<!-- pagebreak -->", "\\newpage", "[pagebreak]"):
            blocks.append(MarkdownBlock(block_type=BlockType.PAGE_BREAK))
            i += 1
            continue

        # Check for thematic break / horizontal rule
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            if hr_as_pagebreak:
                blocks.append(MarkdownBlock(block_type=BlockType.PAGE_BREAK))
            else:
                blocks.append(MarkdownBlock(block_type=BlockType.THEMATIC_BREAK))
            i += 1
            continue

        # Empty line
        if not stripped:
            blocks.append(MarkdownBlock(block_type=BlockType.EMPTY_LINE))
            i += 1
            continue

        # Headers (# H1, ## H2, etc.)
        header_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if header_match:
            level = len(header_match.group(1))
            header_text = header_match.group(2).strip()
            blocks.append(
                MarkdownBlock(
                    block_type=BlockType.HEADER,
                    level=level,
                    spans=parse_inline_spans(header_text),
                )
            )
            i += 1
            continue

        # Blockquote (> text)
        if stripped.startswith(">"):
            quote_text = line.lstrip()[1:].strip()
            blocks.append(
                MarkdownBlock(
                    block_type=BlockType.BLOCKQUOTE,
                    spans=parse_inline_spans(quote_text),
                )
            )
            i += 1
            continue

        # Unordered list (- item, * item, + item)
        ul_match = re.match(r"^(\s*)[-*+]\s+(.*)$", line)
        if ul_match:
            indent = len(ul_match.group(1)) // 2
            item_text = ul_match.group(2).strip()
            blocks.append(
                MarkdownBlock(
                    block_type=BlockType.LIST_ITEM,
                    level=indent,
                    is_ordered=False,
                    spans=parse_inline_spans(item_text),
                )
            )
            i += 1
            continue

        # Ordered list (1. item, 2. item)
        ol_match = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
        if ol_match:
            indent = len(ol_match.group(1)) // 2
            num = int(ol_match.group(2))
            item_text = ol_match.group(3).strip()
            blocks.append(
                MarkdownBlock(
                    block_type=BlockType.LIST_ITEM,
                    level=indent,
                    is_ordered=True,
                    order_number=num,
                    spans=parse_inline_spans(item_text),
                )
            )
            i += 1
            continue

        # Regular paragraph text (accumulate until empty line or next block)
        para_lines = [stripped]
        while i + 1 < len(lines):
            next_line = lines[i + 1]
            next_stripped = next_line.strip()
            if not next_stripped:
                break
            if next_stripped.startswith(("#", "```", "~~~", "$$", ">", "-", "*", "+")) or re.match(r"^\d+\.\s+", next_stripped):
                break
            if re.match(r"^(-{3,}|\*{3,}|_{3,})$", next_stripped):
                break
            if next_stripped.lower() in ("---page---", "---break---", "<!-- pagebreak -->", "\\newpage", "[pagebreak]"):
                break
            para_lines.append(next_stripped)
            i += 1

        full_para = " ".join(para_lines)
        blocks.append(
            MarkdownBlock(
                block_type=BlockType.PARAGRAPH,
                spans=parse_inline_spans(full_para),
            )
        )
        i += 1

    # Close any unclosed code or math block
    if in_code_block and code_lines:
        blocks.append(
            MarkdownBlock(
                block_type=BlockType.CODE_BLOCK,
                code_lines=code_lines,
                language=code_lang,
            )
        )
    if in_math_block and math_lines:
        blocks.append(
            MarkdownBlock(
                block_type=BlockType.MATH_BLOCK,
                latex_code="\n".join(math_lines),
            )
        )

    return blocks
