import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from PIL import ImageFont


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
    ),
}


def get_theme(name: str) -> Theme:
    return THEMES.get(name.lower(), THEMES["dark"])


_FONT_CACHE: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}


def find_system_font(font_names: list[str]) -> Optional[str]:
    """Try to find an existing TTF font on the host system."""
    well_known_paths = [
        "/usr/share/fonts/google-noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in well_known_paths:
        if os.path.isfile(p):
            return p

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

    # Style-specific candidates
    preferred = {
        "regular": [
            "/usr/share/fonts/google-noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ],
        "bold": [
            "/usr/share/fonts/google-noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
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
    }

    candidates = preferred.get(style, preferred["regular"])
    for path in candidates:
        if os.path.isfile(path):
            return path

    return find_system_font(["Noto Sans", "DejaVu Sans", "Liberation Sans", "sans-serif"])


class FontManager:
    def __init__(self, regular_path: Optional[str] = None, mono_path: Optional[str] = None):
        self.regular_path = resolve_font_path(regular_path, "regular")
        self.bold_path = resolve_font_path(None, "bold") or self.regular_path
        self.italic_path = resolve_font_path(None, "italic") or self.regular_path
        self.mono_path = resolve_font_path(mono_path, "mono") or self.regular_path

    def get_font(self, size: int, style: str = "regular") -> ImageFont.ImageFont:
        if style == "bold":
            path = self.bold_path
        elif style == "italic":
            path = self.italic_path
        elif style == "mono" or style == "code":
            path = self.mono_path
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
