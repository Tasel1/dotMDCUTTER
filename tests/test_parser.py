import pytest
from dotmdcutter.models import BlockType, SpanStyle
from dotmdcutter.parser import parse_inline_spans, parse_markdown


def test_parse_inline_spans_plain():
    spans = parse_inline_spans("Простой русский текст")
    assert len(spans) == 1
    assert spans[0].text == "Простой русский текст"
    assert spans[0].style == SpanStyle.NORMAL


def test_parse_inline_spans_mixed():
    spans = parse_inline_spans("Hello **мир** и `код` и ~~зачеркнуто~~!")
    styles = [s.style for s in spans]
    texts = [s.text for s in spans]

    assert SpanStyle.BOLD in styles
    assert SpanStyle.CODE in styles
    assert SpanStyle.STRIKETHROUGH in styles

    assert "мир" in texts
    assert "код" in texts
    assert "зачеркнуто" in texts


def test_parse_inline_spans_nested_math():
    spans = parse_inline_spans(r"**Шаг 7 ($r \approx R$):**")
    assert len(spans) == 3
    assert spans[0].text == "Шаг 7 ("
    assert spans[0].style == SpanStyle.BOLD
    assert spans[1].text == r"r \approx R"
    assert spans[1].style == SpanStyle.MATH
    assert spans[2].text == "):"
    assert spans[2].style == SpanStyle.BOLD


def test_parse_headers():
    md = "# Заголовок 1\n## Заголовок 2\n### Заголовок 3"
    blocks = parse_markdown(md)
    assert len(blocks) == 3
    assert blocks[0].block_type == BlockType.HEADER and blocks[0].level == 1
    assert blocks[1].block_type == BlockType.HEADER and blocks[1].level == 2
    assert blocks[2].block_type == BlockType.HEADER and blocks[2].level == 3


def test_parse_code_blocks():
    md = "```python\nimport sys\nprint('hi')\n```"
    blocks = parse_markdown(md)
    assert len(blocks) == 1
    assert blocks[0].block_type == BlockType.CODE_BLOCK
    assert blocks[0].language == "python"
    assert blocks[0].code_lines == ["import sys", "print('hi')"]


def test_parse_lists():
    md = "- Пункт 1\n- Пункт 2\n1. Первый\n2. Второй"
    blocks = parse_markdown(md)
    assert len(blocks) == 4
    assert blocks[0].block_type == BlockType.LIST_ITEM and not blocks[0].is_ordered
    assert blocks[1].block_type == BlockType.LIST_ITEM and not blocks[1].is_ordered
    assert (
        blocks[2].block_type == BlockType.LIST_ITEM
        and blocks[2].is_ordered
        and blocks[2].order_number == 1
    )
    assert (
        blocks[3].block_type == BlockType.LIST_ITEM
        and blocks[3].is_ordered
        and blocks[3].order_number == 2
    )


def test_parse_page_breaks():
    md = "Текст 1\n---page---\nТекст 2\n<!-- pagebreak -->\nТекст 3"
    blocks = parse_markdown(md)
    break_blocks = [b for b in blocks if b.block_type == BlockType.PAGE_BREAK]
    assert len(break_blocks) == 2


def test_parse_hr_as_pagebreak():
    md = "Раздел 1\n---\nРаздел 2"
    blocks_normal = parse_markdown(md, hr_as_pagebreak=False)
    assert any(b.block_type == BlockType.THEMATIC_BREAK for b in blocks_normal)

    blocks_pb = parse_markdown(md, hr_as_pagebreak=True)
    assert any(b.block_type == BlockType.PAGE_BREAK for b in blocks_pb)
