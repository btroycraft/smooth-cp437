#!/usr/bin/env python3
"""Build the IBM VGA TrueType font from the SVG Glyphs layer."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import build_12x12_df_ttf as builder


builder.SOURCE_SVG = Path("smooth-cp437_ibm-vga_src.svg")
builder.OUTPUT_TTF = Path("smooth-cp437_original.ttf")
builder.CELL_TRIM_LEFT = 1.0
builder.CELL_TRIM_TOP = 1.0
builder.CELL_TRIM_RIGHT = 1.0
builder.CELL_TRIM_BOTTOM = 1.0
builder.EXPECTED_OUTPUT_NONEMPTY_CELLS = 252
builder.FONT_NAME = "SmoothCP437Original"
builder.FONT_FAMILY = "Smooth CP437 Original"
builder.FONT_FULL_NAME = "Smooth CP437 Original"
builder.FONT_EM = 1200
builder.FONT_ASCENT = 900
builder.FONT_DESCENT = 300
builder.GLYPH_ADVANCE = 1200
builder.OS2_TYPO_ASCENT = 900
builder.OS2_TYPO_DESCENT = -300
builder.OS2_WIN_ASCENT = 900
builder.OS2_WIN_DESCENT = 300
builder.HHEA_ASCENT = 900
builder.HHEA_DESCENT = -300
builder.SFNT_NAMES = (
    ("English (US)", "Family", "Smooth CP437 Original"),
    ("English (US)", "SubFamily", "Regular"),
    ("English (US)", "UniqueID", "Smooth CP437 Original Regular"),
    ("English (US)", "Fullname", "Smooth CP437 Original"),
    ("English (US)", "Version", "Version 1.000"),
    ("English (US)", "PostScriptName", "SmoothCP437Original"),
)


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: python3 scripts/build_ibm_vga_ttf.py")
    builder.build_ttf(
        source_svg=builder.SOURCE_SVG,
        output_ttf=builder.OUTPUT_TTF,
        layer_name=builder.LAYER_NAME,
        grid_cols=builder.GRID_COLS,
        grid_rows=builder.GRID_ROWS,
        fontforge_executable=builder.FONTFORGE_EXECUTABLE,
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc
