import io
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

    # Common macro aliases frequently emitted by LLMs
    aliases = {
        r"\implies": r"\Longrightarrow",
        r"\iff": r"\Longleftrightarrow",
        r"\impliedby": r"\Longleftarrow",
        r"\le": r"\leq",
        r"\ge": r"\geq",
        r"\ne": r"\neq",
    }
    for macro, repl in aliases.items():
        s = s.replace(macro, repl)

    # Mathtext enters LaTeX math rendering mode when enclosed in $...$
    return f"${s}$"


def render_latex_to_image(
    formula: str,
    font_size: int = 13,
    color_hex: str = "#E6EDF3",
    max_width: Optional[int] = None,
    dpi: int = 110,
) -> Optional[Image.Image]:
    """
    Renders a LaTeX math expression into a transparent PIL RGBA Image.
    Scales down proportionally if max_width is exceeded.
    Returns None if matplotlib is unavailable or if formula syntax is invalid.
    """
    if not _LATEX_AVAILABLE:
        return None

    cleaned = clean_latex(formula)
    if not cleaned:
        return None

    cache_key = (cleaned, font_size, color_hex, max_width)
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
            color=color_hex,
        )
        buf.seek(0)
        raw_img = Image.open(buf).convert("RGBA")

        # Make the mathtext white background transparent
        arr = np.array(raw_img)
        # Identify background pixels (white/near-white from matplotlib rasterizer)
        is_bg = (arr[:, :, 0] > 240) & (arr[:, :, 1] > 240) & (arr[:, :, 2] > 240)
        arr[is_bg, 3] = 0
        img = Image.fromarray(arr)

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
