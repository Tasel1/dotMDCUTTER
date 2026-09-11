# Implementation Plan: dotMDCUTTER (Markdown to 320x240 Image Slicer)

## Overview
A high-performance, pixel-perfect tool for converting and slicing Markdown documents into 320x240 (landscape) or 240x320 (portrait) images (PNG, JPG, BMP). Designed for small displays, smartwatches, microcontrollers (ESP32/Arduino), and handheld cheat-sheets. Includes an intelligent line-aware pagination engine (no horizontal line-splitting), full Cyrillic/Russian and Latin typography, custom themes (Dark, Light, E-Ink, Terminal), a full CLI, and an interactive PyQt6 desktop GUI with live page preview.

## Architecture Decisions
- **Rendering Engine**: Pure Python with `Pillow` (`PIL`) and `Noto Sans`/`Noto Sans Mono` TrueType fonts. Zero heavy headless browser dependencies; instant rendering (<50ms per page) with 100% pixel control.
- **Pagination Strategy**: Block & Line aware pagination. Parses markdown into AST elements, wraps words at the character/pixel boundary, and fits lines strictly within `height - 2*margin - footer`. Pages break cleanly at word/line boundaries; explicit page breaks (`---page---`, `---break---`, `\newpage`) supported.
- **Dual Interface**:
  - `cli.py`: Fast batch rendering for terminal workflows, automated pipelines, or scripts.
  - `gui.py`: Polished PyQt6 application with interactive 320x240 pixel preview, zoom factor (1x, 2x, 3x), live re-rendering on font size/theme change, and page-by-page flipping.
- **Themes**:
  - `dark`: Deep dark (`#121212`), high readability contrast (`#E6EDF3`), accent headers.
  - `light`: Clean paper white (`#FFFFFF`), dark ink (`#1A1A1A`).
  - `eink`: Pure 1-bit style high-contrast black/white (`#000000` / `#FFFFFF`).
  - `amber`: Retro CRT amber (`#000000` / `#FFB000`).
  - `matrix`: Hacker green (`#000000` / `#00FF66`).

## Task Breakdown
1. **Foundation & Theme System**: Define themes, dimensions, fonts, and data structures.
2. **Markdown Parser & Tokenizer**: Parse headers, paragraphs, inline styles (bold/italic/code), code blocks, blockquotes, lists, rules, and page breaks.
3. **Layout & Paginator Engine**: Word-wrapping, height measurement, pagination, line-breaking without clipping.
4. **Pillow Canvas Renderer**: Render formatted pages to PIL Images, draw code cards, blockquotes, bullet points, headers, footers (`page / total`), export to PNG/JPG/BMP.
5. **Command Line Interface (CLI)**: Argument parser (`--width`, `--height`, `--orientation`, `--theme`, `--format`, `--font-size`, `--no-footer`, `--gui`).
6. **PyQt6 GUI Application**: Interactive window with live canvas preview, zoom, page slider, file selector, settings controls, and export button.
7. **Automated Test Suite**: Unit tests for parser, layout, rendering, file generation, and Russian Cyrillic handling.
8. **Documentation & Demo**: `README.md` and `sample.md` with full usage instructions.
