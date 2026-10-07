import os
import tempfile
import pytest
from PIL import Image

from dotmdcutter.latex import render_latex_to_image, clean_latex, is_latex_available
from dotmdcutter.models import PageConfig
from dotmdcutter.parser import parse_markdown
from dotmdcutter.renderer import MarkdownRenderer
from dotmdcutter.themes import FontManager


def test_clean_latex():
    assert clean_latex("$E = mc^2$") == "$E = mc^2$"
    assert clean_latex("$$E = mc^2$$") == "$E = mc^2$"
    assert clean_latex(r"\implies") == r"$\Longrightarrow$"
    assert clean_latex(r"\le") == r"$\leq$"
    assert clean_latex(r"\left( x \right)") == r"$\left( x \right)$"
    assert clean_latex(r"\operatorname{arctg}(x)") == r"$\mathrm{arctg}(x)$"
    assert clean_latex(r"\LaTeX") == r"$\mathrm{LaTeX}$"
    assert clean_latex("") == ""


def test_render_latex_inline():
    if not is_latex_available():
        pytest.skip("matplotlib not available")
    im = render_latex_to_image("E = mc^2", font_size=13, color_hex="#58A6FF")
    assert im is not None
    assert im.mode == "RGBA"
    assert im.width > 0 and im.height > 0

    im_left = render_latex_to_image(r"g_0 \left(\frac{R}{R+h}\right)^2", font_size=13)
    assert im_left is not None

    im_op = render_latex_to_image(r"\operatorname{arctg}(x)", font_size=13)
    assert im_op is not None


def test_render_latex_scaling():
    if not is_latex_available():
        pytest.skip("matplotlib not available")
    # Long formula with narrow max_width
    formula = (
        r"\sum_{i=1}^n \int_0^1 f(x, y, z) dx dy dz = \frac{A + B + C + D}{E + F + G}"
    )
    im = render_latex_to_image(
        formula, font_size=13, color_hex="#58A6FF", max_width=180
    )
    assert im is not None
    assert im.width <= 180


def test_unicode_symbols_measurement():
    fm = FontManager()
    text = "Формула: A → B ⇒ C, знаки: x ≤ 10 ≠ 5 ± 0.1, эмодзи: 🚀 🔥 💡"
    w = fm.measure_text(text, 13, "regular")
    assert w > 100


def test_render_page_with_latex_and_unicode():
    md = """# Тестовый документ 🚀

Формула энергии: $E = mc^2$.
Корни: $x = \\frac{-b \\pm \\sqrt{D}}{2a}$.

Блочная формула:
$$
\\int_0^1 x^2 dx = \\frac{1}{3}
$$

Список знаков:
- Стрелка: A → B ✅
- Неравенство: x ≤ 100 ≠ 0 🔥
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        cfg = PageConfig(width=320, height=240, theme_name="dark", output_format="png")
        renderer = MarkdownRenderer(cfg)
        paths = renderer.export_images(md, tmp_dir, prefix="math_")

        assert len(paths) >= 1
        for p in paths:
            assert os.path.isfile(p)
            with Image.open(p) as img:
                assert img.size == (320, 240)
