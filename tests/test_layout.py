import pytest
from dotmdcutter.layout import LayoutEngine
from dotmdcutter.models import PageConfig
from dotmdcutter.parser import parse_markdown
from dotmdcutter.themes import FontManager


@pytest.fixture
def font_manager():
    return FontManager()


def test_layout_word_wrapping(font_manager):
    config = PageConfig(width=320, height=240, base_font_size=13)
    engine = LayoutEngine(config, font_manager)

    long_text = "Это очень длинный абзац текста на русском языке, который гарантированно не поместится в одну строку экрана шириной всего 320 пикселей и должен быть аккуратно разбит на несколько строк без потери слов."
    blocks = parse_markdown(long_text)
    pages = engine.layout_blocks(blocks)

    assert len(pages) >= 1
    # Check that it got wrapped into multiple lines
    assert len(pages[0].lines) > 1
    # Check that total height fits in content height
    assert pages[0].total_height <= config.content_height


def test_layout_unbroken_long_word(font_manager):
    config = PageConfig(width=320, height=240, base_font_size=13)
    engine = LayoutEngine(config, font_manager)

    # Word longer than screen width (e.g. hash or long url)
    unbroken = "https://verylongdomainnameexamplewithoutanyspaceswhatsoevertocheckwrappingbehavior1234567890.com"
    blocks = parse_markdown(unbroken)
    pages = engine.layout_blocks(blocks)

    assert len(pages) >= 1
    assert len(pages[0].lines) > 1


def test_layout_page_height_bounds(font_manager):
    config = PageConfig(width=320, height=240, base_font_size=13)
    engine = LayoutEngine(config, font_manager)

    # Multi-paragraph document
    doc = "\n\n".join([f"Абзац номер {i}: текст описания процесса с пояснениями." for i in range(25)])
    blocks = parse_markdown(doc)
    pages = engine.layout_blocks(blocks)

    # Should generate multiple pages
    assert len(pages) > 1

    # Every single page must strictly obey content_height
    for p in pages:
        assert p.total_height <= config.content_height, f"Page {p.page_number} height {p.total_height} > {config.content_height}"


def test_empty_document(font_manager):
    config = PageConfig(width=320, height=240)
    engine = LayoutEngine(config, font_manager)
    blocks = parse_markdown("")
    pages = engine.layout_blocks(blocks)
    assert len(pages) == 1
    assert pages[0].page_number == 1
