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

    def _get_font(self, size: int, style: SpanStyle) -> ImageFont.ImageFont:
        if style in (SpanStyle.BOLD, SpanStyle.BOLD_ITALIC):
            return self.fm.get_font(size, "bold")
        elif style == SpanStyle.ITALIC:
            return self.fm.get_font(size, "italic")
        elif style == SpanStyle.CODE:
            return self.fm.get_font(size, "mono")
        return self.fm.get_font(size, "regular")

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

            if line.is_code:
                # Code card background & border
                box_x1 = mx
                box_x2 = w - mx
                box_y1 = curr_y
                box_y2 = curr_y + line.height

                # Draw card background
                draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=self.theme.code_bg)
                # Left & right border
                draw.line([(box_x1, box_y1), (box_x1, box_y2)], fill=self.theme.code_border, width=1)
                draw.line([(box_x2, box_y1), (box_x2, box_y2)], fill=self.theme.code_border, width=1)

                if line.box_start:
                    draw.line([(box_x1, box_y1), (box_x2, box_y1)], fill=self.theme.code_border, width=1)
                    if line.box_lang:
                        # Draw small language badge
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

                # Draw code text
                text_x = mx + line.x_offset
                for frag in line.fragments:
                    f = self._get_font(frag.font_size, frag.style)
                    draw.text((text_x, curr_y), frag.text, font=f, fill=self.theme.code_text)
                    fw = draw.textlength(frag.text, font=f)
                    text_x += fw

                curr_y += line.height
                continue

            if line.is_quote:
                # Vertical quote bar on the left
                bar_x = mx + 2
                draw.line([(bar_x, curr_y), (bar_x, curr_y + line.height)], fill=self.theme.quote_bar, width=3)

                text_x = mx + line.x_offset
                for frag in line.fragments:
                    f = self._get_font(frag.font_size, frag.style)
                    color = self.theme.accent if frag.style in (SpanStyle.BOLD, SpanStyle.BOLD_ITALIC) else self.theme.quote_text
                    draw.text((text_x, curr_y), frag.text, font=f, fill=color)
                    fw = draw.textlength(frag.text, font=f)
                    text_x += fw

                curr_y += line.height
                continue

            # Header / List item / Regular line
            text_x = mx + line.x_offset

            # Bullet
            if line.bullet_symbol:
                b_font = self.fm.get_font(self.config.base_font_size, "bold")
                b_x = mx + line.bullet_x
                draw.text((b_x, curr_y), line.bullet_symbol, font=b_font, fill=self.theme.accent)

            # Fragments
            for frag in line.fragments:
                font = self._get_font(frag.font_size, frag.style)
                frag_w = draw.textlength(frag.text, font=font)

                # Color determination
                if line.is_header:
                    if line.header_level == 1:
                        color = self.theme.header1
                    elif line.header_level == 2:
                        color = self.theme.header2
                    else:
                        color = self.theme.header3
                elif frag.style == SpanStyle.CODE:
                    color = self.theme.inline_code_text
                    # Draw inline code pill background
                    draw.rectangle(
                        [text_x - 1, curr_y + 1, text_x + frag_w + 1, curr_y + line.height - 2],
                        fill=self.theme.inline_code_bg,
                    )
                else:
                    color = self.theme.text

                draw.text((text_x, curr_y), frag.text, font=font, fill=color)

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

            # Subtle top hairline for footer
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
