import os
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .latex import render_latex_to_image, rgb_to_hex
from .layout import LayoutEngine, LineFragment, PageLayout, RenderLine
from .models import MarkdownBlock, PageConfig, SpanStyle
from .themes import FontManager, Theme, get_theme


class MarkdownRenderer:
    def __init__(self, config: PageConfig):
        self.config = config
        self.theme: Theme = get_theme(config.theme_name)
        self.fm = FontManager(config.custom_font_path, config.custom_mono_font_path)
        self.layout_engine = LayoutEngine(config, self.fm)

    def _style_name(self, style: SpanStyle) -> str:
        if style in (SpanStyle.BOLD, SpanStyle.BOLD_ITALIC):
            return "bold"
        elif style == SpanStyle.ITALIC:
            return "italic"
        elif style == SpanStyle.CODE:
            return "mono"
        return "regular"

    def _render_math_fragment(
        self,
        img: Image.Image,
        frag: LineFragment,
        text_x: float,
        curr_y: int,
        lh: int,
        scale: int,
    ) -> float:
        m_img = None
        if frag.latex_code:
            m_img = render_latex_to_image(
                formula=frag.latex_code,
                font_size=frag.font_size * scale,
                color_hex=rgb_to_hex(self.theme.header1),
                max_width=self.config.content_width * scale,
                dpi=120,
            )
        if m_img is None and frag.math_img is not None:
            if scale > 1:
                m_img = frag.math_img.resize(
                    (
                        frag.math_img.width * scale,
                        frag.math_img.height * scale,
                    ),
                    Image.Resampling.LANCZOS,
                )
            else:
                m_img = frag.math_img

        if m_img is not None:
            paste_y = curr_y + max(0, (lh - m_img.height) // 2)
            if m_img.mode == "RGBA":
                img.paste(
                    m_img,
                    (int(text_x), int(paste_y)),
                    mask=m_img.split()[3],
                )
            else:
                img.paste(m_img, (int(text_x), int(paste_y)))
            return text_x + m_img.width
        else:
            return text_x + frag.width * scale

    def render_page(self, page: PageLayout, total_pages: int) -> Image.Image:
        """Renders a single PageLayout onto a PIL Image of width x height (scaled by config.scale)."""
        scale = max(1, self.config.scale)
        w, h = self.config.pixel_width, self.config.pixel_height
        mx, my = self.config.margin_x * scale, self.config.margin_y * scale

        img = Image.new("RGB", (w, h), self.theme.background)
        draw = ImageDraw.Draw(img)

        curr_y = my

        for line in page.lines:
            lh = line.height * scale
            if line.is_empty:
                curr_y += lh
                continue

            if line.is_hr:
                hr_y = curr_y + lh // 2
                draw.line(
                    [(mx, hr_y), (w - mx, hr_y)],
                    fill=self.theme.hr_color,
                    width=max(1, 1 * scale),
                )
                curr_y += lh
                continue

            if line.is_math_block and (line.math_img is not None or line.latex_code):
                box_x1 = mx
                box_x2 = w - mx
                box_y1 = curr_y
                box_y2 = curr_y + lh

                # Draw formula card background & border
                draw.rectangle(
                    [box_x1, box_y1, box_x2, box_y2], fill=self.theme.math_card_bg
                )
                draw.rectangle(
                    [box_x1, box_y1, box_x2, box_y2],
                    outline=self.theme.math_card_border,
                    width=max(1, 1 * scale),
                )

                # Render formula image at native resolution for current scale
                m_img: Optional[Image.Image] = None
                if line.latex_code:
                    m_img = render_latex_to_image(
                        formula=line.latex_code,
                        font_size=(self.config.base_font_size + 1) * scale,
                        color_hex=rgb_to_hex(self.theme.header1),
                        max_width=(self.config.content_width - 12) * scale,
                        dpi=120,
                    )
                if m_img is None and line.math_img is not None:
                    if scale > 1:
                        m_img = line.math_img.resize(
                            (line.math_img.width * scale, line.math_img.height * scale),
                            Image.Resampling.LANCZOS,
                        )
                    else:
                        m_img = line.math_img

                if m_img is not None:
                    paste_x = box_x1 + (box_x2 - box_x1 - m_img.width) // 2
                    paste_y = box_y1 + (lh - m_img.height) // 2
                    if m_img.mode == "RGBA":
                        img.paste(
                            m_img, (int(paste_x), int(paste_y)), mask=m_img.split()[3]
                        )
                    else:
                        img.paste(m_img, (int(paste_x), int(paste_y)))

                curr_y += lh
                continue

            if line.is_code:
                box_x1 = mx
                box_x2 = w - mx
                box_y1 = curr_y
                box_y2 = curr_y + lh

                draw.rectangle(
                    [box_x1, box_y1, box_x2, box_y2], fill=self.theme.code_bg
                )
                line_w = max(1, 1 * scale)
                draw.line(
                    [(box_x1, box_y1), (box_x1, box_y2)],
                    fill=self.theme.code_border,
                    width=line_w,
                )
                draw.line(
                    [(box_x2, box_y1), (box_x2, box_y2)],
                    fill=self.theme.code_border,
                    width=line_w,
                )

                if line.box_start:
                    draw.line(
                        [(box_x1, box_y1), (box_x2, box_y1)],
                        fill=self.theme.code_border,
                        width=line_w,
                    )
                    if line.box_lang:
                        badge_font = self.fm.get_font(9 * scale, "mono")
                        badge_text = line.box_lang.upper()
                        bw = draw.textlength(badge_text, font=badge_font)
                        draw.text(
                            (box_x2 - bw - 6 * scale, box_y1 + 2 * scale),
                            badge_text,
                            font=badge_font,
                            fill=self.theme.footer_text,
                        )

                if line.box_end:
                    draw.line(
                        [(box_x1, box_y2), (box_x2, box_y2)],
                        fill=self.theme.code_border,
                        width=line_w,
                    )

                text_x = mx + line.x_offset * scale
                for frag in line.fragments:
                    text_x = self.fm.draw_text(
                        draw=draw,
                        xy=(text_x, curr_y),
                        text=frag.text,
                        size=frag.font_size * scale,
                        default_style="mono",
                        fill=self.theme.code_text,
                    )

                curr_y += lh
                continue

            if line.is_quote:
                bar_x = mx + 2 * scale
                bar_w = max(2, 3 * scale)
                draw.line(
                    [(bar_x, curr_y), (bar_x, curr_y + lh)],
                    fill=self.theme.quote_bar,
                    width=bar_w,
                )

                base_lh = (line.base_height or line.height) * scale
                text_y = curr_y + max(0, (lh - base_lh) // 2)

                text_x = mx + line.x_offset * scale
                for frag in line.fragments:
                    if frag.is_math and (frag.math_img is not None or frag.latex_code):
                        text_x = self._render_math_fragment(
                            img, frag, text_x, curr_y, lh, scale
                        )
                        continue

                    color = (
                        self.theme.accent
                        if frag.style in (SpanStyle.BOLD, SpanStyle.BOLD_ITALIC)
                        else self.theme.quote_text
                    )
                    st = (
                        "bold"
                        if frag.style in (SpanStyle.BOLD, SpanStyle.BOLD_ITALIC)
                        else "italic"
                    )
                    text_x = self.fm.draw_text(
                        draw=draw,
                        xy=(text_x, text_y),
                        text=frag.text,
                        size=frag.font_size * scale,
                        default_style=st,
                        fill=color,
                    )

                curr_y += lh
                continue

            # Header / List item / Regular line
            text_x = mx + line.x_offset * scale
            base_lh = (line.base_height or line.height) * scale
            text_y = curr_y + max(0, (lh - base_lh) // 2)

            # Bullet
            if line.bullet_symbol:
                bullet_sz = self.config.base_font_size * scale
                bullet_y = curr_y + max(0, (lh - bullet_sz) // 2)
                self.fm.draw_text(
                    draw=draw,
                    xy=(mx + line.bullet_x * scale, bullet_y),
                    text=line.bullet_symbol,
                    size=bullet_sz,
                    default_style="bold",
                    fill=self.theme.accent,
                )

            # Line fragments
            for frag in line.fragments:
                if frag.is_math and (frag.math_img is not None or frag.latex_code):
                    text_x = self._render_math_fragment(
                        img, frag, text_x, curr_y, lh, scale
                    )
                    continue

                # Normal text fragment
                st = self._style_name(frag.style)
                f_sz = frag.font_size * scale
                frag_w = self.fm.measure_text(frag.text, f_sz, st)

                if line.is_header:
                    if line.header_level == 1:
                        color = self.theme.header1
                    elif line.header_level == 2:
                        color = self.theme.header2
                    else:
                        color = self.theme.header3
                elif frag.style == SpanStyle.CODE:
                    color = self.theme.inline_code_text
                    draw.rectangle(
                        [
                            text_x - 1 * scale,
                            text_y + 1 * scale,
                            text_x + frag_w + 1 * scale,
                            text_y + base_lh - 2 * scale,
                        ],
                        fill=self.theme.inline_code_bg,
                    )
                else:
                    color = self.theme.text

                self.fm.draw_text(
                    draw=draw,
                    xy=(text_x, text_y),
                    text=frag.text,
                    size=f_sz,
                    default_style=st,
                    fill=color,
                )

                if frag.style == SpanStyle.STRIKETHROUGH:
                    strike_y = text_y + base_lh // 2
                    draw.line(
                        [(text_x, strike_y), (text_x + frag_w, strike_y)],
                        fill=color,
                        width=max(1, 1 * scale),
                    )

                text_x += frag_w

            curr_y += lh

        # Render footer (page number)
        if self.config.show_footer and total_pages > 0:
            footer_font = self.fm.get_font(9 * scale, "regular")
            footer_text = f"{page.page_number}/{total_pages}"
            fw = draw.textlength(footer_text, font=footer_font)
            fx = w - mx - fw
            fy = h - my - 10 * scale

            draw.line(
                [(mx, fy - 2 * scale), (w - mx, fy - 2 * scale)],
                fill=self.theme.hr_color,
                width=max(1, 1 * scale),
            )
            draw.text(
                (fx, fy), footer_text, font=footer_font, fill=self.theme.footer_text
            )

        # Micro-sharpening for crisp low-DPI text
        if self.config.sharpen:
            if scale == 1:
                img = img.filter(
                    ImageFilter.UnsharpMask(radius=0.7, percent=115, threshold=2)
                )
            elif scale == 2:
                img = img.filter(
                    ImageFilter.UnsharpMask(radius=0.8, percent=80, threshold=2)
                )

        return img

    def render_markdown(self, markdown_text: str) -> List[Image.Image]:
        """Parses markdown, computes layout, and returns a list of rendered PIL Images."""
        from .parser import parse_markdown

        blocks = parse_markdown(
            markdown_text, hr_as_pagebreak=self.config.hr_as_pagebreak
        )
        pages = self.layout_engine.layout_blocks(blocks)
        total_pages = len(pages)

        rendered_images: List[Image.Image] = []
        for p in pages:
            rendered_images.append(self.render_page(p, total_pages))

        return rendered_images

    def export_images(
        self,
        markdown_text: str,
        output_dir: str,
        prefix: str = "page_",
    ) -> List[str]:
        """Renders markdown and saves each page as an image file to output_dir."""
        os.makedirs(output_dir, exist_ok=True)
        images = self.render_markdown(markdown_text)
        saved_paths: List[str] = []

        ext = self.config.output_format.lower()
        if ext == "jpeg":
            ext = "jpg"

        digits = max(3, len(str(len(images))))

        for idx, img in enumerate(images, start=1):
            filename = f"{prefix}{idx:0{digits}d}.{ext}"
            filepath = os.path.join(output_dir, filename)

            if ext in ("jpg", "jpeg"):
                img.save(
                    filepath,
                    format="JPEG",
                    quality=self.config.jpeg_quality,
                    subsampling=0,
                )
            elif ext == "bmp":
                img.save(filepath, format="BMP")
            else:
                img.save(filepath, format="PNG", optimize=True)

            saved_paths.append(filepath)

        return saved_paths
