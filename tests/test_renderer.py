import os
import tempfile
from PIL import Image
import pytest

from dotmdcutter.models import PageConfig
from dotmdcutter.renderer import MarkdownRenderer
from dotmdcutter.themes import THEMES


@pytest.mark.parametrize("theme_name", list(THEMES.keys()))
def test_render_all_themes(theme_name):
    config = PageConfig(width=320, height=240, theme_name=theme_name)
    renderer = MarkdownRenderer(config)
    md = "# Заголовок\nТестовый текст **жирный** и `код`."
    images = renderer.render_markdown(md)
    assert len(images) >= 1
    assert images[0].size == (320, 240)


@pytest.mark.parametrize(
    "orientation,expected_size",
    [
        ("landscape", (320, 240)),
        ("portrait", (240, 320)),
    ],
)
def test_render_orientations(orientation, expected_size):
    w, h = expected_size
    config = PageConfig(width=w, height=h)
    renderer = MarkdownRenderer(config)
    images = renderer.render_markdown("# Тест ориентации\nПараграф текста.")
    assert len(images) == 1
    assert images[0].size == expected_size


@pytest.mark.parametrize("fmt", ["png", "jpg", "bmp"])
def test_export_formats(fmt):
    with tempfile.TemporaryDirectory() as tmp_dir:
        config = PageConfig(width=320, height=240, output_format=fmt)
        renderer = MarkdownRenderer(config)
        md = "## Заголовок раздела\n- Элемент 1\n- Элемент 2"
        paths = renderer.export_images(md, tmp_dir, prefix="test_")

        assert len(paths) >= 1
        for p in paths:
            assert os.path.isfile(p)
            with Image.open(p) as img:
                assert img.size == (320, 240)


@pytest.mark.parametrize(
    "scale,expected_size",
    [
        (1, (320, 240)),
        (2, (640, 480)),
        (3, (960, 720)),
    ],
)
def test_render_scale_factor(scale, expected_size):
    md = "# Заголовок с формулой $E = mc^2$\nПараграф с кодом `test`."
    cfg_base = PageConfig(width=320, height=240, scale=1)
    cfg_scaled = PageConfig(width=320, height=240, scale=scale)

    r_base = MarkdownRenderer(cfg_base)
    r_scaled = MarkdownRenderer(cfg_scaled)

    imgs_base = r_base.render_markdown(md)
    imgs_scaled = r_scaled.render_markdown(md)

    assert len(imgs_base) == len(imgs_scaled)
    assert imgs_scaled[0].size == expected_size
