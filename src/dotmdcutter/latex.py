import io
import re
from typing import Dict, Optional, Tuple
import numpy as np
from PIL import Image

_LATEX_AVAILABLE = True
try:
    from matplotlib import mathtext
    from matplotlib.font_manager import FontProperties
except ImportError:
    _LATEX_AVAILABLE = False


_FORMULA_CACHE: Dict[Tuple[str, int, str, Optional[int]], Optional[Image.Image]] = {}


def is_latex_available() -> bool:
    return _LATEX_AVAILABLE


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def clean_latex(formula: str) -> str:
    s = formula.strip()
    if s.startswith("$$") and s.endswith("$$") and len(s) >= 4:
        s = s[2:-2].strip()
    elif s.startswith("$") and s.endswith("$") and len(s) >= 2:
        s = s[1:-1].strip()
    elif s.startswith(r"\[") and s.endswith(r"\]") and len(s) >= 4:
        s = s[2:-2].strip()
    elif s.startswith(r"\(") and s.endswith(r"\)") and len(s) >= 4:
        s = s[2:-2].strip()

    if not s:
        return ""

    # Common macro aliases frequently emitted by LLMs / KaTeX / MathJax
    # Use word boundary / non-alpha lookahead to prevent replacing prefixes like \left -> \leqft
    s = re.sub(r"\\implies(?![a-zA-Z])", r"\\Longrightarrow", s)
    s = re.sub(r"\\iff(?![a-zA-Z])", r"\\Longleftrightarrow", s)
    s = re.sub(r"\\impliedby(?![a-zA-Z])", r"\\Longleftarrow", s)
    s = re.sub(r"\\le(?![a-zA-Z])", r"\\leq", s)
    s = re.sub(r"\\ge(?![a-zA-Z])", r"\\geq", s)
    s = re.sub(r"\\ne(?![a-zA-Z])", r"\\neq", s)
    s = re.sub(r"\\LaTeX(?![a-zA-Z])", r"\\mathrm{LaTeX}", s)
    s = re.sub(r"\\operatorname\s*\{([^}]+)\}", r"\\mathrm{\1}", s)
    s = re.sub(r"\\operatorname\s*\\([a-zA-Z]+)", r"\\\1", s)

    # Mathtext enters LaTeX math rendering mode when enclosed in $...$
    return f"${s}$"


def render_latex_to_image(
    formula: str,
    font_size: int = 13,
    color_hex: str = "#E6EDF3",
    max_width: Optional[int] = None,
    dpi: int = 120,
) -> Optional[Image.Image]:
    """
    Renders a LaTeX math expression into a transparent PIL RGBA Image.
    Uses pure alpha mask extraction from grayscale luminance to eliminate
    any background color contamination or white halos.
    Scales down proportionally if max_width is exceeded.
    Returns None if matplotlib is unavailable or if formula syntax is invalid.
    """
    if not _LATEX_AVAILABLE:
        return None

    cleaned = clean_latex(formula)
    if not cleaned:
        return None

    cache_key = (cleaned, font_size, color_hex, max_width, dpi)
    if cache_key in _FORMULA_CACHE:
        cached = _FORMULA_CACHE[cache_key]
        return cached.copy() if cached is not None else None

    buf = io.BytesIO()
    prop = FontProperties(size=font_size)

    try:
        mathtext.math_to_image(
            cleaned,
            buf,
            prop=prop,
            dpi=dpi,
            format="png",
            color="black",
        )
        buf.seek(0)
        raw_gray = Image.open(buf).convert("L")
        arr = np.array(raw_gray)

        # Mathtext renders black glyphs on white (255) background.
        # Alpha is strictly 255 - luminance.
        alpha = (255 - arr).astype(np.uint8)

        # Parse target hex color to RGB
        c_hex = color_hex.lstrip("#")
        if len(c_hex) == 6:
            r = int(c_hex[0:2], 16)
            g = int(c_hex[2:4], 16)
            b = int(c_hex[4:6], 16)
        else:
            r, g, b = 230, 235, 240

        rgba = np.zeros((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
        rgba[:, :, 0] = r
        rgba[:, :, 1] = g
        rgba[:, :, 2] = b
        rgba[:, :, 3] = alpha

        img = Image.fromarray(rgba, mode="RGBA")

        # Scale down if exceeds max_width
        if max_width and img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = max(1, int(img.height * ratio))
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        _FORMULA_CACHE[cache_key] = img
        return img.copy()
    except Exception:
        # Invalid LaTeX syntax or unsupported mathtext command
        _FORMULA_CACHE[cache_key] = None
        return None
