import argparse
import os
import sys
from typing import List, Optional

from .models import PageConfig
from .renderer import MarkdownRenderer
from .themes import THEMES


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dotmdcutter",
        description="Pixel-perfect Markdown to 320x240 (or 240x320) image slicer for small displays, smartwatches, and microcontrollers.",
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        help="Path to the Markdown (.md) file to slice.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_dir",
        default=None,
        help="Directory to save generated images (default: <filename>_slices/)",
    )
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=320,
        help="Image width in pixels (default: 320)",
    )
    parser.add_argument(
        "-H",
        "--height",
        type=int,
        default=240,
        help="Image height in pixels (default: 240)",
    )
    parser.add_argument(
        "--orientation",
        choices=["landscape", "portrait"],
        default=None,
        help="Quick orientation: landscape (320x240) or portrait (240x320)",
    )
    parser.add_argument(
        "-t",
        "--theme",
        choices=list(THEMES.keys()),
        default="dark",
        help=f"Visual theme: {', '.join(THEMES.keys())} (default: dark)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["png", "jpg", "jpeg", "bmp"],
        default="png",
        help="Output image format: png, jpg, bmp (default: png)",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=13,
        help="Base font size in pixels (default: 13, optimal for 320x240)",
    )
    parser.add_argument(
        "--margin-x",
        type=int,
        default=10,
        help="Left and right margin in pixels (default: 10)",
    )
    parser.add_argument(
        "--margin-y",
        type=int,
        default=8,
        help="Top and bottom margin in pixels (default: 8)",
    )
    parser.add_argument(
        "--no-footer",
        action="store_true",
        help="Hide page number footer to maximize text space",
    )
    parser.add_argument(
        "--hr-pagebreak",
        action="store_true",
        help="Treat '---' horizontal rules as page breaks",
    )
    parser.add_argument(
        "--prefix",
        default="page_",
        help="Prefix for output image filenames (default: page_)",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the interactive PyQt6 graphical preview & export interface",
    )
    return parser


def run_cli(args: Optional[List[str]] = None) -> int:
    parser = create_parser()
    parsed = parser.parse_args(args)

    # If --gui requested or no arguments supplied, launch GUI
    if parsed.gui or (not parsed.input_file and len(sys.argv) <= 1):
        try:
            from .gui import run_gui
            return run_gui(parsed.input_file)
        except ImportError as e:
            print(f"[Error] Failed to launch GUI: {e}. Ensure PyQt6 is installed.", file=sys.stderr)
            return 1

    if not parsed.input_file:
        parser.print_help()
        return 1

    if not os.path.isfile(parsed.input_file):
        print(f"[Error] Input file not found: {parsed.input_file}", file=sys.stderr)
        return 1

    # Orientation override
    width = parsed.width
    height = parsed.height
    if parsed.orientation == "portrait":
        width, height = 240, 320
    elif parsed.orientation == "landscape":
        width, height = 320, 240

    # Default output dir based on input file name
    base_name = os.path.splitext(os.path.basename(parsed.input_file))[0]
    output_dir = parsed.output_dir or f"{base_name}_slices"

    with open(parsed.input_file, "r", encoding="utf-8") as f:
        md_text = f.read()

    config = PageConfig(
        width=width,
        height=height,
        margin_x=parsed.margin_x,
        margin_y=parsed.margin_y,
        base_font_size=parsed.font_size,
        show_footer=not parsed.no_footer,
        theme_name=parsed.theme,
        output_format=parsed.format,
    )

    renderer = MarkdownRenderer(config)
    print(f"[*] Processing '{parsed.input_file}' ({width}x{height}, theme: {parsed.theme}, format: {parsed.format})...")

    saved_files = renderer.export_images(
        markdown_text=md_text,
        output_dir=output_dir,
        prefix=parsed.prefix,
    )

    print(f"[+] Successfully sliced into {len(saved_files)} images in '{output_dir}':")
    for fpath in saved_files[:5]:
        print(f"    - {fpath}")
    if len(saved_files) > 5:
        print(f"    ... and {len(saved_files) - 5} more files.")

    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
