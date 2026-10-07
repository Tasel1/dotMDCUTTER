from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

from .latex import render_latex_to_image, rgb_to_hex
from .models import BlockType, InlineSpan, MarkdownBlock, PageConfig, SpanStyle
from .themes import FontManager, get_theme


@dataclass
class FormattedToken:
    text: str
    style: SpanStyle
    font_size: int
    width: float
    is_whitespace: bool = False
    is_math: bool = False
    math_img: Optional[Image.Image] = None
    latex_code: str = ""


@dataclass
class LineFragment:
    text: str
    style: SpanStyle
    font_size: int
    width: float
    is_math: bool = False
    math_img: Optional[Image.Image] = None
    latex_code: str = ""


@dataclass
class RenderLine:
    fragments: List[LineFragment] = field(default_factory=list)
    x_offset: int = 0
    y_offset: int = 0
    height: int = 18
    base_height: int = 18
    bullet_symbol: Optional[str] = None
    bullet_x: int = 0
    is_header: bool = False
    header_level: int = 0
    is_quote: bool = False
    is_code: bool = False
    is_hr: bool = False
    is_empty: bool = False
    is_math_block: bool = False
    math_img: Optional[Image.Image] = None
    latex_code: str = ""
    box_start: bool = False
    box_end: bool = False
    box_lang: str = ""

    @property
    def total_width(self) -> float:
        return sum(f.width for f in self.fragments)


@dataclass
class PageLayout:
    page_number: int
    lines: List[RenderLine] = field(default_factory=list)
    total_height: int = 0


class LayoutEngine:
    def __init__(self, config: PageConfig, font_manager: FontManager):
        self.config = config
        self.fm = font_manager
        self.theme = get_theme(config.theme_name)

    def _style_name(self, style: SpanStyle) -> str:
        if style in (SpanStyle.BOLD, SpanStyle.BOLD_ITALIC):
            return "bold"
        elif style == SpanStyle.ITALIC:
            return "italic"
        elif style == SpanStyle.CODE:
            return "mono"
        return "regular"

    def _measure_text(self, text: str, size: int, style: SpanStyle) -> float:
        style_str = self._style_name(style)
        return self.fm.measure_text(text, size, style_str)

    def _tokenize_spans(
        self, spans: List[InlineSpan], font_size: int
    ) -> List[FormattedToken]:
        tokens: List[FormattedToken] = []
        for span in spans:
            raw_text = span.text
            if not raw_text:
                continue

            # Inline math formula span
            if span.style == SpanStyle.MATH:
                color_hex = rgb_to_hex(self.theme.header1)
                # Render inline formula
                math_im = render_latex_to_image(
                    formula=raw_text,
                    font_size=font_size,
                    color_hex=color_hex,
                    max_width=self.config.content_width,
                )
                if math_im is not None:
                    tokens.append(
                        FormattedToken(
                            text=raw_text,
                            style=SpanStyle.MATH,
                            font_size=font_size,
                            width=float(math_im.width),
                            is_whitespace=False,
                            is_math=True,
                            math_img=math_im,
                            latex_code=raw_text,
                        )
                    )
                    continue
                else:
                    # Fallback to plain text if invalid syntax
                    raw_text = f"${raw_text}$"
                    span.style = SpanStyle.CODE

            # Normal text tokenization
            idx = 0
            while idx < len(raw_text):
                char = raw_text[idx]
                if char.isspace():
                    ws_start = idx
                    while idx < len(raw_text) and raw_text[idx].isspace():
                        idx += 1
                    ws_str = " "
                    w = self._measure_text(ws_str, font_size, span.style)
                    tokens.append(
                        FormattedToken(
                            text=ws_str,
                            style=span.style,
                            font_size=font_size,
                            width=w,
                            is_whitespace=True,
                        )
                    )
                else:
                    word_start = idx
                    while idx < len(raw_text) and not raw_text[idx].isspace():
                        idx += 1
                    word_str = raw_text[word_start:idx]
                    w = self._measure_text(word_str, font_size, span.style)
                    tokens.append(
                        FormattedToken(
                            text=word_str,
                            style=span.style,
                            font_size=font_size,
                            width=w,
                            is_whitespace=False,
                        )
                    )
        return tokens

    def _calc_line_height(
        self, fragments: List[LineFragment], default_line_h: int
    ) -> int:
        h = default_line_h
        for f in fragments:
            if f.is_math and f.math_img:
                h = max(h, f.math_img.height + 4)
        return h

    def _wrap_tokens_to_lines(
        self,
        tokens: List[FormattedToken],
        max_width: int,
        line_height: int,
        x_offset: int = 0,
        bullet_symbol: Optional[str] = None,
        bullet_x: int = 0,
        is_header: bool = False,
        header_level: int = 0,
        is_quote: bool = False,
    ) -> List[RenderLine]:
        lines: List[RenderLine] = []
        current_fragments: List[LineFragment] = []
        current_width = 0.0

        for token in tokens:
            if not current_fragments and token.is_whitespace:
                continue

            if current_width + token.width <= max_width:
                current_fragments.append(
                    LineFragment(
                        text=token.text,
                        style=token.style,
                        font_size=token.font_size,
                        width=token.width,
                        is_math=token.is_math,
                        math_img=token.math_img,
                        latex_code=token.latex_code,
                    )
                )
                current_width += token.width
            else:
                if token.is_whitespace:
                    continue

                if current_fragments:
                    is_first_line = len(lines) == 0
                    line_h = self._calc_line_height(current_fragments, line_height)
                    lines.append(
                        RenderLine(
                            fragments=current_fragments,
                            x_offset=x_offset,
                            height=line_h,
                            base_height=line_height,
                            bullet_symbol=bullet_symbol if is_first_line else None,
                            bullet_x=bullet_x if is_first_line else 0,
                            is_header=is_header,
                            header_level=header_level,
                            is_quote=is_quote,
                        )
                    )
                    current_fragments = []
                    current_width = 0.0

                if token.is_math:
                    # Single math formula is placed on new line
                    current_fragments.append(
                        LineFragment(
                            text=token.text,
                            style=token.style,
                            font_size=token.font_size,
                            width=token.width,
                            is_math=True,
                            math_img=token.math_img,
                            latex_code=token.latex_code,
                        )
                    )
                    current_width = token.width
                elif token.width > max_width:
                    # Break long word character by character
                    sub_str = ""
                    for char in token.text:
                        char_w = self._measure_text(char, token.font_size, token.style)
                        if current_width + char_w > max_width and sub_str:
                            sub_w = self._measure_text(
                                sub_str, token.font_size, token.style
                            )
                            lines.append(
                                RenderLine(
                                    fragments=[
                                        LineFragment(
                                            text=sub_str,
                                            style=token.style,
                                            font_size=token.font_size,
                                            width=sub_w,
                                        )
                                    ],
                                    x_offset=x_offset,
                                    height=line_height,
                                    is_header=is_header,
                                    header_level=header_level,
                                    is_quote=is_quote,
                                )
                            )
                            sub_str = char
                            current_width = char_w
                        else:
                            sub_str += char
                            current_width += char_w
                    if sub_str:
                        sub_w = self._measure_text(
                            sub_str, token.font_size, token.style
                        )
                        current_fragments.append(
                            LineFragment(
                                text=sub_str,
                                style=token.style,
                                font_size=token.font_size,
                                width=sub_w,
                            )
                        )
                else:
                    current_fragments.append(
                        LineFragment(
                            text=token.text,
                            style=token.style,
                            font_size=token.font_size,
                            width=token.width,
                        )
                    )
                    current_width = token.width

        if current_fragments:
            is_first_line = len(lines) == 0
            line_h = self._calc_line_height(current_fragments, line_height)
            lines.append(
                RenderLine(
                    fragments=current_fragments,
                    x_offset=x_offset,
                    height=line_h,
                    base_height=line_height,
                    bullet_symbol=bullet_symbol if is_first_line else None,
                    bullet_x=bullet_x if is_first_line else 0,
                    is_header=is_header,
                    header_level=header_level,
                    is_quote=is_quote,
                )
            )

        return lines

    def layout_blocks(self, blocks: List[MarkdownBlock]) -> List[PageLayout]:
        """
        Transforms parsed blocks into paginated pages that strictly fit within PageConfig bounds.
        Guarantees no line of text is sliced in half.
        """
        base_sz = self.config.base_font_size
        content_w = self.config.content_width
        content_h = self.config.content_height

        font_regular = self.fm.get_font(base_sz, "regular")
        reg_metrics = font_regular.getmetrics()
        reg_line_h = reg_metrics[0] + reg_metrics[1] + self.config.line_spacing

        mono_sz = max(10, base_sz - 1)
        font_mono = self.fm.get_font(mono_sz, "mono")
        mono_metrics = font_mono.getmetrics()
        mono_line_h = mono_metrics[0] + mono_metrics[1] + 2

        pages: List[PageLayout] = []
        current_page_lines: List[RenderLine] = []
        current_page_h = 0

        def finish_page():
            nonlocal current_page_lines, current_page_h
            while current_page_lines and current_page_lines[-1].is_empty:
                current_page_h -= current_page_lines[-1].height
                current_page_lines.pop()

            if current_page_lines:
                pages.append(
                    PageLayout(
                        page_number=len(pages) + 1,
                        lines=current_page_lines,
                        total_height=current_page_h,
                    )
                )
                current_page_lines = []
                current_page_h = 0

        def add_space(spacing_h: int):
            nonlocal current_page_h
            if current_page_h == 0 or spacing_h <= 0:
                return
            if current_page_lines and current_page_lines[-1].is_empty:
                prev = current_page_lines[-1]
                if prev.height < spacing_h:
                    diff = spacing_h - prev.height
                    if current_page_h + diff <= content_h:
                        prev.height = spacing_h
                        current_page_h += diff
                return

            if current_page_h + spacing_h <= content_h:
                current_page_lines.append(RenderLine(is_empty=True, height=spacing_h))
                current_page_h += spacing_h

        for block in blocks:
            if block.block_type == BlockType.PAGE_BREAK:
                finish_page()
                continue

            if block.block_type == BlockType.EMPTY_LINE:
                add_space(max(3, base_sz // 3))
                continue

            if block.block_type == BlockType.THEMATIC_BREAK:
                hr_h = 10
                if current_page_h + hr_h > content_h:
                    finish_page()
                current_page_lines.append(RenderLine(is_hr=True, height=hr_h))
                current_page_h += hr_h
                continue

            if block.block_type == BlockType.MATH_BLOCK:
                color_hex = rgb_to_hex(self.theme.header1)
                math_im = render_latex_to_image(
                    formula=block.latex_code,
                    font_size=base_sz + 1,
                    color_hex=color_hex,
                    max_width=content_w - 12,
                )
                if math_im is not None:
                    card_h = math_im.height + 10
                    # Keep whole math card on new page if doesn't fit
                    if (
                        current_page_h > 0
                        and card_h <= content_h
                        and current_page_h + card_h > content_h
                    ):
                        finish_page()

                    current_page_lines.append(
                        RenderLine(
                            is_math_block=True,
                            math_img=math_im,
                            latex_code=block.latex_code,
                            height=card_h,
                        )
                    )
                    current_page_h += card_h
                    add_space(self.config.paragraph_spacing)
                    continue
                else:
                    # Fallback to code block if LaTeX fails
                    block.block_type = BlockType.CODE_BLOCK
                    block.code_lines = [f"$${block.latex_code}$$"]
                    block.language = "latex"

            if block.block_type == BlockType.HEADER:
                h_size = (
                    base_sz + 4
                    if block.level == 1
                    else (base_sz + 2 if block.level == 2 else base_sz + 1)
                )
                h_font = self.fm.get_font(h_size, "bold")
                h_metrics = h_font.getmetrics()
                h_line_h = h_metrics[0] + h_metrics[1] + 3

                for sp in block.spans:
                    if sp.style == SpanStyle.NORMAL:
                        sp.style = SpanStyle.BOLD

                tokens = self._tokenize_spans(block.spans, h_size)
                h_lines = self._wrap_tokens_to_lines(
                    tokens=tokens,
                    max_width=content_w,
                    line_height=h_line_h,
                    x_offset=0,
                    is_header=True,
                    header_level=block.level,
                )

                total_h_needed = (
                    sum(l.height for l in h_lines)
                    + reg_line_h
                    + self.config.paragraph_spacing
                )
                if current_page_h > 0 and current_page_h + total_h_needed > content_h:
                    finish_page()

                for l in h_lines:
                    if current_page_h + l.height > content_h:
                        finish_page()
                    current_page_lines.append(l)
                    current_page_h += l.height

                add_space(max(3, self.config.paragraph_spacing // 2))
                continue

            if block.block_type == BlockType.PARAGRAPH:
                tokens = self._tokenize_spans(block.spans, base_sz)
                p_lines = self._wrap_tokens_to_lines(
                    tokens=tokens,
                    max_width=content_w,
                    line_height=reg_line_h,
                    x_offset=0,
                )

                for l in p_lines:
                    if current_page_h + l.height > content_h:
                        finish_page()
                    current_page_lines.append(l)
                    current_page_h += l.height

                add_space(self.config.paragraph_spacing)
                continue

            if block.block_type == BlockType.BLOCKQUOTE:
                quote_indent = 12
                avail_w = content_w - quote_indent
                quote_spans = []
                for sp in block.spans:
                    if sp.style in (SpanStyle.MATH, SpanStyle.CODE):
                        new_style = sp.style
                    elif sp.style in (SpanStyle.BOLD, SpanStyle.BOLD_ITALIC):
                        new_style = SpanStyle.BOLD_ITALIC
                    else:
                        new_style = SpanStyle.ITALIC
                    quote_spans.append(InlineSpan(text=sp.text, style=new_style))

                tokens = self._tokenize_spans(quote_spans, base_sz)
                q_lines = self._wrap_tokens_to_lines(
                    tokens=tokens,
                    max_width=avail_w,
                    line_height=reg_line_h,
                    x_offset=quote_indent,
                    is_quote=True,
                )

                total_q_h = sum(l.height for l in q_lines)
                if (
                    current_page_h > 0
                    and total_q_h <= content_h
                    and current_page_h + total_q_h > content_h
                ):
                    finish_page()

                for l in q_lines:
                    if current_page_h + l.height > content_h:
                        finish_page()
                    current_page_lines.append(l)
                    current_page_h += l.height

                add_space(self.config.paragraph_spacing)
                continue

            if block.block_type == BlockType.LIST_ITEM:
                indent_level = block.level
                bullet_x = indent_level * 12
                bullet_str = f"{block.order_number}." if block.is_ordered else "•"
                bullet_w = self._measure_text(bullet_str + " ", base_sz, SpanStyle.BOLD)
                text_x = int(bullet_x + bullet_w)
                avail_w = content_w - text_x

                tokens = self._tokenize_spans(block.spans, base_sz)
                li_lines = self._wrap_tokens_to_lines(
                    tokens=tokens,
                    max_width=avail_w,
                    line_height=reg_line_h,
                    x_offset=text_x,
                    bullet_symbol=bullet_str,
                    bullet_x=bullet_x,
                )

                for l in li_lines:
                    if current_page_h + l.height > content_h:
                        finish_page()
                    current_page_lines.append(l)
                    current_page_h += l.height

                add_space(max(2, self.config.paragraph_spacing // 3))
                continue

            if block.block_type == BlockType.CODE_BLOCK:
                card_padding = 6
                avail_code_w = content_w - 2 * card_padding
                code_lines = block.code_lines or [""]

                badge_w = (
                    (self._measure_text(block.language.upper(), 9, SpanStyle.CODE) + 14)
                    if block.language
                    else 0
                )

                wrapped_code_lines: List[str] = []
                for l_idx, cl in enumerate(code_lines):
                    if not cl:
                        wrapped_code_lines.append("")
                        continue

                    max_line_w = (
                        (avail_code_w - badge_w)
                        if (l_idx == 0 and badge_w > 0)
                        else avail_code_w
                    )

                    cl_w = self._measure_text(cl, mono_sz, SpanStyle.CODE)
                    if cl_w <= max_line_w:
                        wrapped_code_lines.append(cl)
                    else:
                        sub = ""
                        curr_limit = max_line_w
                        for c in cl:
                            if (
                                self._measure_text(sub + c, mono_sz, SpanStyle.CODE)
                                > curr_limit
                            ):
                                wrapped_code_lines.append(sub)
                                sub = "  -> " + c
                                curr_limit = avail_code_w
                            else:
                                sub += c
                        if sub:
                            wrapped_code_lines.append(sub)

                total_code_h = len(wrapped_code_lines) * mono_line_h + 2 * card_padding
                if (
                    current_page_h > 0
                    and total_code_h <= content_h
                    and current_page_h + total_code_h > content_h
                ):
                    finish_page()

                for idx, cl_text in enumerate(wrapped_code_lines):
                    is_start = idx == 0
                    is_end = idx == len(wrapped_code_lines) - 1

                    line_h = (
                        mono_line_h
                        + (card_padding if is_start else 0)
                        + (card_padding if is_end else 0)
                    )

                    if current_page_h + line_h > content_h:
                        finish_page()
                        is_start = True

                    frag = LineFragment(
                        text=cl_text,
                        style=SpanStyle.CODE,
                        font_size=mono_sz,
                        width=self._measure_text(cl_text, mono_sz, SpanStyle.CODE),
                    )

                    current_page_lines.append(
                        RenderLine(
                            fragments=[frag] if cl_text else [],
                            x_offset=card_padding,
                            height=mono_line_h,
                            is_code=True,
                            box_start=is_start,
                            box_end=is_end,
                            box_lang=block.language if is_start else "",
                        )
                    )
                    current_page_h += line_h

                add_space(self.config.paragraph_spacing)
                continue

        finish_page()
        if not pages:
            pages.append(PageLayout(page_number=1, lines=[], total_height=0))

        return pages
