import os
from typing import List, Optional
from PIL import Image, ImageDraw, ImageFont

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

    def render_page(self, page: PageLayout, total_pages: int) -> Image.Image:
        """Renders a single PageLayout onto a PIL Image of width x height."""
        w, h = self.config.width, self.config.height
        mx, my = self.config.margin_x, self.config.margin_y

        img = Image.new("RGB", (w, h), self.theme.background)
        draw = ImageDraw.Draw(img)

        curr_y = my

        for line in page.lines:
            if line.is_empty:
                curr_y += line.height
                continue

            if line.is_hr:
                hr_y = curr_y + line.height // 2
                draw.line([(mx, hr_y), (w - mx, hr_y)], fill=self.theme.hr_color, width=1)
                curr_y += line.height
                continue

            if line.is_math_block and line.math_img is not None:
                # Math formula block card
                box_x1 = mx
                box_x2 = w - mx
                box_y1 = curr_y
                box_y2 = curr_y + line.height

                # Draw formula card background & border
                draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=self.theme.math_card_bg)
                draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline=self.theme.math_card_border, width=1)

                # Paste formula image centered horizontally and vertically
                m_img = line.math_img
                paste_x = box_x1 + (box_x2 - box_x1 - m_img.width) // 2
                paste_y = box_y1 + (line.height - m_img.height) // 2

                # Alpha composite
                if m_img.mode == "RGBA":
                    img.paste(m_img, (paste_x, paste_y), mask=m_img.split()[3])
                else:
                    img.paste(m_img, (paste_x, paste_y))

                curr_y += line.height
                continue

            if line.is_code:
                box_x1 = mx
                box_x2 = w - mx
                box_y1 = curr_y
                box_y2 = curr_y + line.height

                draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=self.theme.code_bg)
                draw.line([(box_x1, box_y1), (box_x1, box_y2)], fill=self.theme.code_border, width=1)
                draw.line([(box_x2, box_y1), (box_x2, box_y2)], fill=self.theme.code_border, width=1)

                if line.box_start:
                    draw.line([(box_x1, box_y1), (box_x2, box_y1)], fill=self.theme.code_border, width=1)
                    if line.box_lang:
                        badge_font = self.fm.get_font(9, "mono")
                        badge_text = line.box_lang.upper()
                        bw = draw.textlength(badge_text, font=badge_font)
                        draw.text(
                            (box_x2 - bw - 6, box_y1 + 2),
                            badge_text,
                            font=badge_font,
                            fill=self.theme.footer_text,
                        )

                if line.box_end:
                    draw.line([(box_x1, box_y2), (box_x2, box_y2)], fill=self.theme.code_border, width=1)

                text_x = mx + line.x_offset
                for frag in line.fragments:
                    text_x = self.fm.draw_text(
                        draw=draw,
                        xy=(text_x, curr_y),
                        text=frag.text,
                        size=frag.font_size,
                        default_style="mono",
                        fill=self.theme.code_text,
                    )

                curr_y += line.height
                continue

            if line.is_quote:
                bar_x = mx + 2
                draw.line([(bar_x, curr_y), (bar_x, curr_y + line.height)], fill=self.theme.quote_bar, width=3)

                text_x = mx + line.x_offset
                for frag in line.fragments:
                    color = self.theme.accent if frag.style in (SpanStyle.BOLD, SpanStyle.BOLD_ITALIC) else self.theme.quote_text
                    st = "bold" if frag.style in (SpanStyle.BOLD, SpanStyle.BOLD_ITALIC) else "italic"
                    text_x = self.fm.draw_text(
                        draw=draw,
                        xy=(text_x, curr_y),
                        text=frag.text,
                        size=frag.font_size,
                        default_style=st,
                        fill=color,
                    )

                curr_y += line.height
                continue

            # Header / List item / Regular line
            text_x = mx + line.x_offset

            # Bullet
            if line.bullet_symbol:
                self.fm.draw_text(
                    draw=draw,
                    xy=(mx + line.bullet_x, curr_y),
                    text=line.bullet_symbol,
                    size=self.config.base_font_size,
                    default_style="bold",
                    fill=self.theme.accent,
                )

            # Line fragments
            for frag in line.fragments:
                if frag.is_math and frag.math_img is not None:
                    # Inline math formula image
                    m_img = frag.math_img
                    paste_y = curr_y + max(0, (line.height - m_img.height) // 2)
                    if m_img.mode == "RGBA":
                        img.paste(m_img, (int(text_x), int(paste_y)), mask=m_img.split()[3])
                    else:
                        img.paste(m_img, (int(text_x), int(paste_y)))
                    text_x += frag.width
                    continue

                # Normal text fragment
                st = self._style_name(frag.style)
                frag_w = self.fm.measure_text(frag.text, frag.font_size, st)

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
                        [text_x - 1, curr_y + 1, text_x + frag_w + 1, curr_y + line.height - 2],
                        fill=self.theme.inline_code_bg,
                    )
                else:
                    color = self.theme.text

                self.fm.draw_text(
                    draw=draw,
                    xy=(text_x, curr_y),
                    text=frag.text,
                    size=frag.font_size,
                    default_style=st,
                    fill=color,
                )

                if frag.style == SpanStyle.STRIKETHROUGH:
                    strike_y = curr_y + line.height // 2
                    draw.line([(text_x, strike_y), (text_x + frag_w, strike_y)], fill=color, width=1)

                text_x += frag_w

            curr_y += line.height

        # Render footer (page number)
        if self.config.show_footer and total_pages > 0:
            footer_font = self.fm.get_font(9, "regular")
            footer_text = f"{page.page_number}/{total_pages}"
            fw = draw.textlength(footer_text, font=footer_font)
            fx = w - mx - fw
            fy = h - my - 10

            draw.line([(mx, fy - 2), (w - mx, fy - 2)], fill=self.theme.hr_color, width=1)
            draw.text((fx, fy), footer_text, font=footer_font, fill=self.theme.footer_text)

        return img

    def render_markdown(self, markdown_text: str) -> List[Image.Image]:
        """Parses markdown, computes layout, and returns a list of rendered PIL Images."""
        from .parser import parse_markdown

        blocks = parse_markdown(markdown_text)
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
                img.save(filepath, format="JPEG", quality=self.config.jpeg_quality)
            elif ext == "bmp":
                img.save(filepath, format="BMP")
            else:
                img.save(filepath, format="PNG")

            saved_paths.append(filepath)

        return saved_paths
