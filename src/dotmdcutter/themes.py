import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from PIL import Image, ImageDraw, ImageFont

try:
    from fontTools.ttLib import TTFont
    _FONTTOOLS_AVAILABLE = True
except ImportError:
    _FONTTOOLS_AVAILABLE = False


@dataclass
class Theme:
    name: str
    background: Tuple[int, int, int]
    text: Tuple[int, int, int]
    header1: Tuple[int, int, int]
    header2: Tuple[int, int, int]
    header3: Tuple[int, int, int]
    accent: Tuple[int, int, int]
    code_bg: Tuple[int, int, int]
    code_border: Tuple[int, int, int]
    code_text: Tuple[int, int, int]
    inline_code_bg: Tuple[int, int, int]
    inline_code_text: Tuple[int, int, int]
    quote_bar: Tuple[int, int, int]
    quote_text: Tuple[int, int, int]
    footer_text: Tuple[int, int, int]
    hr_color: Tuple[int, int, int]
    math_card_bg: Tuple[int, int, int] = (24, 28, 36)
    math_card_border: Tuple[int, int, int] = (50, 56, 68)


THEMES: Dict[str, Theme] = {
    "dark": Theme(
        name="dark",
        background=(18, 18, 22),
        text=(230, 235, 240),
        header1=(88, 166, 255),
        header2=(121, 192, 255),
        header3=(165, 214, 255),
        accent=(88, 166, 255),
        code_bg=(28, 32, 40),
        code_border=(50, 56, 68),
        code_text=(240, 140, 70),
        inline_code_bg=(36, 40, 50),
        inline_code_text=(255, 170, 100),
        quote_bar=(88, 166, 255),
        quote_text=(160, 172, 185),
        footer_text=(100, 110, 125),
        hr_color=(50, 56, 68),
        math_card_bg=(24, 28, 36),
        math_card_border=(50, 56, 68),
    ),
    "light": Theme(
        name="light",
        background=(255, 255, 255),
        text=(24, 28, 32),
        header1=(9, 105, 218),
        header2=(18, 120, 230),
        header3=(31, 111, 235),
        accent=(9, 105, 218),
        code_bg=(244, 246, 249),
        code_border=(216, 222, 228),
        code_text=(160, 48, 20),
        inline_code_bg=(235, 238, 242),
        inline_code_text=(175, 45, 15),
        quote_bar=(9, 105, 218),
        quote_text=(87, 96, 106),
        footer_text=(130, 140, 150),
        hr_color=(218, 222, 228),
        math_card_bg=(248, 250, 252),
        math_card_border=(218, 222, 228),
    ),
    "eink": Theme(
        name="eink",
        background=(255, 255, 255),
        text=(0, 0, 0),
        header1=(0, 0, 0),
        header2=(0, 0, 0),
        header3=(0, 0, 0),
        accent=(0, 0, 0),
        code_bg=(240, 240, 240),
        code_border=(0, 0, 0),
        code_text=(0, 0, 0),
        inline_code_bg=(230, 230, 230),
        inline_code_text=(0, 0, 0),
        quote_bar=(0, 0, 0),
        quote_text=(30, 30, 30),
        footer_text=(70, 70, 70),
        hr_color=(0, 0, 0),
        math_card_bg=(245, 245, 245),
        math_card_border=(0, 0, 0),
    ),
    "amber": Theme(
        name="amber",
        background=(12, 9, 4),
        text=(255, 176, 0),
        header1=(255, 215, 60),
        header2=(255, 195, 30),
        header3=(255, 176, 0),
        accent=(255, 200, 40),
        code_bg=(28, 20, 8),
        code_border=(90, 60, 15),
        code_text=(255, 220, 100),
        inline_code_bg=(36, 26, 10),
        inline_code_text=(255, 220, 100),
        quote_bar=(255, 176, 0),
        quote_text=(200, 140, 0),
        footer_text=(150, 100, 0),
        hr_color=(90, 60, 15),
        math_card_bg=(20, 15, 6),
        math_card_border=(90, 60, 15),
    ),
    "matrix": Theme(
        name="matrix",
        background=(8, 14, 8),
        text=(51, 255, 51),
        header1=(150, 255, 150),
        header2=(100, 255, 100),
        header3=(51, 255, 51),
        accent=(0, 255, 128),
        code_bg=(15, 28, 15),
        code_border=(30, 70, 30),
        code_text=(180, 255, 180),
        inline_code_bg=(20, 38, 20),
        inline_code_text=(180, 255, 180),
        quote_bar=(51, 255, 51),
        quote_text=(40, 200, 40),
        footer_text=(30, 140, 30),
        hr_color=(30, 70, 30),
        math_card_bg=(12, 22, 12),
        math_card_border=(30, 70, 30),
    ),
}


def get_theme(name: str) -> Theme:
    return THEMES.get(name.lower(), THEMES["dark"])


_FONT_CACHE: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}
_CMAP_CACHE: Dict[str, Set[int]] = {}


def load_font_cmap(path: Optional[str]) -> Set[int]:
    if not path or not _FONTTOOLS_AVAILABLE or not os.path.isfile(path):
        return set()
    if path in _CMAP_CACHE:
        return _CMAP_CACHE[path]
    try:
        tt = TTFont(path)
        cmap = set(tt.getBestCmap().keys())
        _CMAP_CACHE[path] = cmap
        return cmap
    except Exception:
        return set()


def find_system_font(font_names: List[str]) -> Optional[str]:
    """Try to find an existing font via fc-match or well-known locations."""
    if shutil.which("fc-match"):
        for name in font_names:
            try:
                out = subprocess.check_output(["fc-match", "-f", "%{file}", name], text=True).strip()
                if out and os.path.isfile(out):
                    return out
            except Exception:
                pass
    return None


def resolve_font_path(custom_path: Optional[str], style: str = "regular") -> Optional[str]:
    if custom_path and os.path.isfile(custom_path):
        return custom_path

    preferred = {
        "regular": [
            "/usr/share/fonts/google-noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
            "/usr/share/fonts/abattis-cantarell-fonts/Cantarell-Regular.otf",
        ],
        "bold": [
            "/usr/share/fonts/google-noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/abattis-cantarell-fonts/Cantarell-Bold.otf",
        ],
        "italic": [
            "/usr/share/fonts/google-noto/NotoSans-Italic.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Italic.ttf",
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Oblique.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        ],
        "mono": [
            "/usr/share/fonts/google-noto/NotoSansMono-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
            "/usr/share/fonts/dejavu-sans-mono-fonts/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ],
        "math": [
            "/usr/share/fonts/google-noto/NotoSansMath-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansMath-Regular.ttf",
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
            "/usr/share/fonts/symbola-fonts/Symbola.ttf",
        ],
        "emoji": [
            "/usr/share/fonts/google-noto-emoji-fonts/NotoEmoji-Regular.ttf",
            "/usr/share/fonts/google-noto-color-emoji-fonts/Noto-COLRv1.ttf",
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        ],
    }

    candidates = preferred.get(style, preferred["regular"])
    for path in candidates:
        if os.path.isfile(path):
            return path

    queries = {
        "regular": ["Noto Sans", "DejaVu Sans", "Liberation Sans", "sans-serif"],
        "bold": ["Noto Sans:weight=bold", "DejaVu Sans:weight=bold"],
        "italic": ["Noto Sans:slant=italic", "DejaVu Sans:slant=oblique"],
        "mono": ["Noto Sans Mono", "DejaVu Sans Mono", "monospace"],
        "math": ["Noto Sans Math", "Math", "DejaVu Sans"],
        "emoji": ["Noto Emoji", "Noto Color Emoji", "emoji"],
    }
    return find_system_font(queries.get(style, ["sans-serif"]))


class FontManager:
    """
    Manages fonts and provides multi-font fallback for Latin, Cyrillic,
    mathematical symbols, Greek letters, and Unicode emojis.
    """
    def __init__(self, regular_path: Optional[str] = None, mono_path: Optional[str] = None):
        self.regular_path = resolve_font_path(regular_path, "regular")
        self.bold_path = resolve_font_path(None, "bold") or self.regular_path
        self.italic_path = resolve_font_path(None, "italic") or self.regular_path
        self.mono_path = resolve_font_path(mono_path, "mono") or self.regular_path
        self.math_path = resolve_font_path(None, "math")
        self.emoji_path = resolve_font_path(None, "emoji")

        # Pre-load character maps for zero-overhead character routing
        self.reg_cmap = load_font_cmap(self.regular_path)
        self.mono_cmap = load_font_cmap(self.mono_path)
        self.math_cmap = load_font_cmap(self.math_path)
        self.emoji_cmap = load_font_cmap(self.emoji_path)

        # Fallback dummy image for measurement
        self._dummy_img = Image.new("RGB", (10, 10))
        self._dummy_draw = ImageDraw.Draw(self._dummy_img)

    def get_font(self, size: int, style: str = "regular") -> ImageFont.ImageFont:
        if style in ("bold", "bold_italic"):
            path = self.bold_path
        elif style == "italic":
            path = self.italic_path
        elif style in ("mono", "code"):
            path = self.mono_path
        elif style == "math":
            path = self.math_path or self.regular_path
        elif style == "emoji":
            path = self.emoji_path or self.regular_path
        else:
            path = self.regular_path

        key = (path or "default", size)
        if key in _FONT_CACHE:
            return _FONT_CACHE[key]

        font: ImageFont.ImageFont
        if path and os.path.isfile(path):
            try:
                font = ImageFont.truetype(path, size)
            except Exception:
                font = ImageFont.load_default()
        else:
            font = ImageFont.load_default()

        _FONT_CACHE[key] = font
        return font

    def get_font_for_char(self, char: str, size: int, default_style: str = "regular") -> ImageFont.ImageFont:
        code = ord(char)
        # Check emoji range and cmap
        if code in self.emoji_cmap and (code not in range(32, 127)):
            return self.get_font(size, "emoji")
        # Check math symbols and arrows (U+2190 to U+22FF, Greek, etc.)
        if code in self.math_cmap and (code not in self.reg_cmap or 0x2190 <= code <= 0x22FF or 0x25A0 <= code <= 0x25FF or 0x2700 <= code <= 0x27BF):
            return self.get_font(size, "math")
        return self.get_font(size, default_style)

    def chunk_text(self, text: str, size: int, default_style: str = "regular") -> List[Tuple[str, ImageFont.ImageFont]]:
        """Splits a string into chunks matching the best font for each character."""
        if not text:
            return []

        chunks: List[Tuple[str, ImageFont.ImageFont]] = []
        curr_text = ""
        curr_font: Optional[ImageFont.ImageFont] = None

        for c in text:
            font = self.get_font_for_char(c, size, default_style)
            if font != curr_font:
                if curr_text and curr_font is not None:
                    chunks.append((curr_text, curr_font))
                curr_text = c
                curr_font = font
            else:
                curr_text += c

        if curr_text and curr_font is not None:
            chunks.append((curr_text, curr_font))

        return chunks

    def measure_text(self, text: str, size: int, default_style: str = "regular") -> float:
        """Measures text length taking multi-font Unicode fallback into account."""
        if not text:
            return 0.0
        chunks = self.chunk_text(text, size, default_style)
        return sum(self._dummy_draw.textlength(chunk_text, font=chunk_font) for chunk_text, chunk_font in chunks)

    def draw_text(
        self,
        draw: ImageDraw.ImageDraw,
        xy: Tuple[float, float],
        text: str,
        size: int,
        default_style: str = "regular",
        fill: any = None,
    ) -> float:
        """Renders text with Unicode symbol and emoji fallback, returning advanced X coordinate."""
        x, y = xy
        if not text:
            return x

        chunks = self.chunk_text(text, size, default_style)
        for chunk_text, chunk_font in chunks:
            draw.text((x, y), chunk_text, font=chunk_font, fill=fill)
            x += draw.textlength(chunk_text, font=chunk_font)
        return x
