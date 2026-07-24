#!/usr/bin/env python3
"""Build the 12x12 DF TrueType font from the SVG Glyphs layer."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import pathops
from lxml import etree
from svgpathtools import Arc, CubicBezier, Line, QuadraticBezier, parse_path


SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
NS = {"svg": SVG_NS, "inkscape": INKSCAPE_NS}

SOURCE_SVG = Path("smooth-cp437_df-12x12_src.svg")
OUTPUT_TTF = Path("smooth-cp437_12x12_df.ttf")
LAYER_NAME = "Glyphs"
GRID_COLS = 16
GRID_ROWS = 16
FONTFORGE_EXECUTABLE = "fontforge"
EXPECTED_POPULATED_CELLS = 253
EXPECTED_OUTPUT_NONEMPTY_CELLS = 253
CELL_TRIM_LEFT = 0.0
CELL_TRIM_TOP = 0.0
CELL_TRIM_RIGHT = 0.0
CELL_TRIM_BOTTOM = 0.0

FONT_NAME = "SmoothCP437-12x12DF"
FONT_FAMILY = "Smooth CP437 12x12 DF"
FONT_FULL_NAME = "Smooth CP437 12x12 DF"
FONT_WEIGHT = "Book"
FONT_VERSION = "1.000"
FONT_EM = 1200
FONT_ASCENT = 1000
FONT_DESCENT = 200
GLYPH_ADVANCE = 1200
OS2_VENDOR = "CODX"
OS2_WEIGHT = 400
OS2_WIDTH = 5
OS2_TYPO_ASCENT = 1000
OS2_TYPO_DESCENT = -200
OS2_WIN_ASCENT = 1000
OS2_WIN_DESCENT = 200
HHEA_ASCENT = 1000
HHEA_DESCENT = -200
PANOSE = (2, 11, 6, 9, 2, 2, 5, 2, 2, 4)
SFNT_NAMES = (
    ("English (US)", "Family", "Smooth CP437 12x12 DF"),
    ("English (US)", "SubFamily", "Regular"),
    ("English (US)", "UniqueID", "Smooth CP437 12x12 DF Regular"),
    ("English (US)", "Fullname", "Smooth CP437 12x12 DF"),
    ("English (US)", "Version", "Version 1.000"),
    ("English (US)", "PostScriptName", "SmoothCP437-12x12DF"),
)

CP437_DISPLAY_CODEPOINTS = [
    0x0000,
    0x263A,
    0x263B,
    0x2665,
    0x2666,
    0x2663,
    0x2660,
    0x2022,
    0x25D8,
    0x25CB,
    0x25D9,
    0x2642,
    0x2640,
    0x266A,
    0x266B,
    0x263C,
    0x25BA,
    0x25C4,
    0x2195,
    0x203C,
    0x00B6,
    0x00A7,
    0x25AC,
    0x21A8,
    0x2191,
    0x2193,
    0x2192,
    0x2190,
    0x221F,
    0x2194,
    0x25B2,
    0x25BC,
    0x0020,
    0x0021,
    0x0022,
    0x0023,
    0x0024,
    0x0025,
    0x0026,
    0x0027,
    0x0028,
    0x0029,
    0x002A,
    0x002B,
    0x002C,
    0x002D,
    0x002E,
    0x002F,
    0x0030,
    0x0031,
    0x0032,
    0x0033,
    0x0034,
    0x0035,
    0x0036,
    0x0037,
    0x0038,
    0x0039,
    0x003A,
    0x003B,
    0x003C,
    0x003D,
    0x003E,
    0x003F,
    0x0040,
    0x0041,
    0x0042,
    0x0043,
    0x0044,
    0x0045,
    0x0046,
    0x0047,
    0x0048,
    0x0049,
    0x004A,
    0x004B,
    0x004C,
    0x004D,
    0x004E,
    0x004F,
    0x0050,
    0x0051,
    0x0052,
    0x0053,
    0x0054,
    0x0055,
    0x0056,
    0x0057,
    0x0058,
    0x0059,
    0x005A,
    0x005B,
    0x005C,
    0x005D,
    0x005E,
    0x005F,
    0x0060,
    0x0061,
    0x0062,
    0x0063,
    0x0064,
    0x0065,
    0x0066,
    0x0067,
    0x0068,
    0x0069,
    0x006A,
    0x006B,
    0x006C,
    0x006D,
    0x006E,
    0x006F,
    0x0070,
    0x0071,
    0x0072,
    0x0073,
    0x0074,
    0x0075,
    0x0076,
    0x0077,
    0x0078,
    0x0079,
    0x007A,
    0x007B,
    0x007C,
    0x007D,
    0x007E,
    0x2302,
    0x00C7,
    0x00FC,
    0x00E9,
    0x00E2,
    0x00E4,
    0x00E0,
    0x00E5,
    0x00E7,
    0x00EA,
    0x00EB,
    0x00E8,
    0x00EF,
    0x00EE,
    0x00EC,
    0x00C4,
    0x00C5,
    0x00C9,
    0x00E6,
    0x00C6,
    0x00F4,
    0x00F6,
    0x00F2,
    0x00FB,
    0x00F9,
    0x00FF,
    0x00D6,
    0x00DC,
    0x00A2,
    0x00A3,
    0x00A5,
    0x20A7,
    0x0192,
    0x00E1,
    0x00ED,
    0x00F3,
    0x00FA,
    0x00F1,
    0x00D1,
    0x00AA,
    0x00BA,
    0x00BF,
    0x2310,
    0x00AC,
    0x00BD,
    0x00BC,
    0x00A1,
    0x00AB,
    0x00BB,
    0x2591,
    0x2592,
    0x2593,
    0x2502,
    0x2524,
    0x2561,
    0x2562,
    0x2556,
    0x2555,
    0x2563,
    0x2551,
    0x2557,
    0x255D,
    0x255C,
    0x255B,
    0x2510,
    0x2514,
    0x2534,
    0x252C,
    0x251C,
    0x2500,
    0x253C,
    0x255E,
    0x255F,
    0x255A,
    0x2554,
    0x2569,
    0x2566,
    0x2560,
    0x2550,
    0x256C,
    0x2567,
    0x2568,
    0x2564,
    0x2565,
    0x2559,
    0x2558,
    0x2552,
    0x2553,
    0x256B,
    0x256A,
    0x2518,
    0x250C,
    0x2588,
    0x2584,
    0x258C,
    0x2590,
    0x2580,
    0x03B1,
    0x00DF,
    0x0393,
    0x03C0,
    0x03A3,
    0x03C3,
    0x00B5,
    0x03C4,
    0x03A6,
    0x0398,
    0x03A9,
    0x03B4,
    0x221E,
    0x03C6,
    0x03B5,
    0x2229,
    0x2261,
    0x00B1,
    0x2265,
    0x2264,
    0x2320,
    0x2321,
    0x00F7,
    0x2248,
    0x00B0,
    0x2219,
    0x00B7,
    0x221A,
    0x207F,
    0x00B2,
    0x25A0,
    0x00A0,
]


@dataclass(frozen=True)
class Bounds:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def center_x(self) -> float:
        return (self.min_x + self.max_x) / 2

    @property
    def center_y(self) -> float:
        return (self.min_y + self.max_y) / 2


def path_bounds(path_data: str) -> Bounds:
    path = parse_path(path_data)
    if not path:
        raise ValueError("path has no coordinates")

    min_x, max_x, min_y, max_y = path.bbox()
    return Bounds(min_x, min_y, max_x, max_y)


def parse_style(style: str | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    if not style:
        return parsed
    for part in style.split(";"):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def element_fill_rule(element: etree._Element) -> str:
    values = parse_style(element.get("style"))
    return element.get("fill-rule") or values.get("fill-rule") or "nonzero"


def path_fill_type(fill_rule: str) -> pathops.FillType:
    if fill_rule.lower() == "evenodd":
        return pathops.FillType.EVEN_ODD
    return pathops.FillType.WINDING


def svg_path_to_pathops(path_data: str, fill_rule: str) -> pathops.Path:
    parsed = parse_path(path_data)
    output = pathops.Path()
    output.fillType = path_fill_type(fill_rule)

    for subpath in parsed.continuous_subpaths():
        if not subpath:
            continue
        output.moveTo(float(subpath[0].start.real), float(subpath[0].start.imag))
        for segment in subpath:
            if isinstance(segment, Line):
                output.lineTo(float(segment.end.real), float(segment.end.imag))
            elif isinstance(segment, QuadraticBezier):
                output.quadTo(
                    float(segment.control.real),
                    float(segment.control.imag),
                    float(segment.end.real),
                    float(segment.end.imag),
                )
            elif isinstance(segment, CubicBezier):
                output.cubicTo(
                    float(segment.control1.real),
                    float(segment.control1.imag),
                    float(segment.control2.real),
                    float(segment.control2.imag),
                    float(segment.end.real),
                    float(segment.end.imag),
                )
            elif isinstance(segment, Arc):
                for cubic in segment.as_cubic_curves():
                    output.cubicTo(
                        float(cubic.control1.real),
                        float(cubic.control1.imag),
                        float(cubic.control2.real),
                        float(cubic.control2.imag),
                        float(cubic.end.real),
                        float(cubic.end.imag),
                    )
            else:
                raise ValueError(f"unsupported SVG path segment: {type(segment).__name__}")
        output.close()

    return output


def rect_path(x0: float, y0: float, x1: float, y1: float) -> pathops.Path:
    path = pathops.Path()
    path.moveTo(x0, y0)
    path.lineTo(x1, y0)
    path.lineTo(x1, y1)
    path.lineTo(x0, y1)
    path.close()
    return path


def element_to_pathops(element: etree._Element) -> pathops.Path:
    tag = etree.QName(element).localname
    if tag == "path":
        return svg_path_to_pathops(element.get("d", ""), element_fill_rule(element))
    if tag == "rect":
        x = float(element.get("x", "0"))
        y = float(element.get("y", "0"))
        width = float(element.get("width", "0"))
        height = float(element.get("height", "0"))
        path = rect_path(x, y, x + width, y + height)
        path.fillType = path_fill_type(element_fill_rule(element))
        return path
    raise ValueError(f"unsupported SVG shape: {tag}")


def path_is_empty(path: pathops.Path) -> bool:
    return len(path.verbs) == 0


def clipped_element_path(element: etree._Element, clip_path: pathops.Path) -> pathops.Path:
    path = element_to_pathops(element)
    if path_is_empty(path):
        return pathops.Path()
    return pathops.op(path, clip_path, pathops.PathOp.INTERSECTION)


def svg_number(value: float) -> str:
    if abs(value) < 1e-9:
        value = 0.0
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


def pathops_to_svg_path_data(path: pathops.Path) -> str:
    commands: list[str] = []
    for command, points in path.segments:
        if command == "moveTo":
            (x, y), = points
            commands.append(f"M {svg_number(x)} {svg_number(y)}")
        elif command == "lineTo":
            (x, y), = points
            commands.append(f"L {svg_number(x)} {svg_number(y)}")
        elif command == "qCurveTo":
            (x1, y1), (x, y) = points
            commands.append(
                f"Q {svg_number(x1)} {svg_number(y1)} {svg_number(x)} {svg_number(y)}"
            )
        elif command == "curveTo":
            (x1, y1), (x2, y2), (x, y) = points
            commands.append(
                "C "
                f"{svg_number(x1)} {svg_number(y1)} "
                f"{svg_number(x2)} {svg_number(y2)} "
                f"{svg_number(x)} {svg_number(y)}"
            )
        elif command == "closePath":
            commands.append("Z")
        else:
            raise ValueError(f"unsupported pathops command: {command}")
    return " ".join(commands)


def rect_bounds(element: etree._Element) -> Bounds:
    x = float(element.get("x", "0"))
    y = float(element.get("y", "0"))
    width = float(element.get("width", "0"))
    height = float(element.get("height", "0"))
    return Bounds(x, y, x + width, y + height)


def parse_viewbox(root: etree._Element) -> tuple[float, float, float, float]:
    viewbox = root.get("viewBox")
    if not viewbox:
        width = float(root.get("width"))
        height = float(root.get("height"))
        return 0.0, 0.0, width, height

    parts = [float(part) for part in re.split(r"[\s,]+", viewbox.strip()) if part]
    if len(parts) != 4:
        raise ValueError(f"expected four viewBox values, got {viewbox!r}")
    return parts[0], parts[1], parts[2], parts[3]


def find_layer(root: etree._Element, layer_name: str) -> etree._Element:
    layers = root.xpath(".//svg:g[@inkscape:label]", namespaces=NS)
    matches = [
        layer
        for layer in layers
        if layer.get(f"{{{INKSCAPE_NS}}}label", "").lower() == layer_name.lower()
    ]
    if not matches:
        raise ValueError(f"could not find Inkscape layer {layer_name!r}")
    if len(matches) > 1:
        raise ValueError(f"found multiple Inkscape layers named {layer_name!r}")
    return matches[0]


def collect_cell_elements(
    source_svg: Path,
    layer_name: str,
    grid_cols: int,
    grid_rows: int,
) -> tuple[dict[int, list[etree._Element]], float, float]:
    root = etree.parse(str(source_svg)).getroot()
    min_x, min_y, width, height = parse_viewbox(root)
    cell_width = width / grid_cols
    cell_height = height / grid_rows
    layer = find_layer(root, layer_name)

    cells: dict[int, list[etree._Element]] = defaultdict(list)
    for element in layer:
        tag = etree.QName(element).localname
        if tag == "path":
            bounds = path_bounds(element.get("d", ""))
        elif tag == "rect":
            bounds = rect_bounds(element)
        else:
            continue

        col = int((bounds.center_x - min_x) // cell_width)
        row = int((bounds.center_y - min_y) // cell_height)
        col = max(0, min(grid_cols - 1, col))
        row = max(0, min(grid_rows - 1, row))
        cells[row * grid_cols + col].append(element)

    return cells, cell_width, cell_height


def write_cell_svgs(
    cells: dict[int, list[etree._Element]],
    cell_width: float,
    cell_height: float,
    grid_cols: int,
    output_dir: Path,
    trim_left: float,
    trim_top: float,
    trim_right: float,
    trim_bottom: float,
) -> dict[int, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    cell_svgs: dict[int, Path] = {}
    output_width = cell_width - trim_left - trim_right
    output_height = cell_height - trim_top - trim_bottom
    if output_width <= 0 or output_height <= 0:
        raise ValueError("cell trim leaves no importable glyph area")

    for cell_index, elements in cells.items():
        col = cell_index % grid_cols
        row = cell_index // grid_cols
        cell_x = col * cell_width + trim_left
        cell_y = row * cell_height + trim_top
        root = etree.Element(
            f"{{{SVG_NS}}}svg",
            nsmap={None: SVG_NS},
            width=f"{output_width:g}",
            height=f"{output_height:g}",
            viewBox=f"0 0 {output_width:g} {output_height:g}",
            overflow="hidden",
        )
        group = etree.SubElement(root, f"{{{SVG_NS}}}g", transform=f"translate({-cell_x:g} {-cell_y:g})")
        clip_path = rect_path(cell_x, cell_y, cell_x + output_width, cell_y + output_height)
        clipped_paths = []
        for element in elements:
            clipped = clipped_element_path(element, clip_path)
            if path_is_empty(clipped):
                continue
            clipped_paths.append(clipped)

        if not clipped_paths:
            continue

        for clipped in clipped_paths:
            etree.SubElement(
                group,
                f"{{{SVG_NS}}}path",
                d=pathops_to_svg_path_data(clipped),
                fill="#ffffff",
                **{"fill-rule": "nonzero"},
            )

        path = output_dir / f"cell_{cell_index:02X}.svg"
        etree.ElementTree(root).write(
            str(path),
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=False,
        )
        cell_svgs[cell_index] = path

    return cell_svgs


def write_fontforge_script(
    script_path: Path,
    output_ttf: Path,
    cell_svgs: dict[int, Path],
) -> None:
    script_path.write_text(
        "\n".join(
            [
                "import fontforge",
                "import os",
                "import sys",
                "",
                f"OUTPUT = {str(output_ttf)!r}",
                f"CP437 = {CP437_DISPLAY_CODEPOINTS!r}",
                f"CELL_SVGS = { {index: str(path) for index, path in cell_svgs.items()}!r}",
                f"EXPECTED_OUTPUT_NONEMPTY_CELLS = {EXPECTED_OUTPUT_NONEMPTY_CELLS!r}",
                f"FONT_NAME = {FONT_NAME!r}",
                f"FONT_FAMILY = {FONT_FAMILY!r}",
                f"FONT_FULL_NAME = {FONT_FULL_NAME!r}",
                f"FONT_WEIGHT = {FONT_WEIGHT!r}",
                f"FONT_VERSION = {FONT_VERSION!r}",
                f"FONT_EM = {FONT_EM!r}",
                f"FONT_ASCENT = {FONT_ASCENT!r}",
                f"FONT_DESCENT = {FONT_DESCENT!r}",
                f"GLYPH_ADVANCE = {GLYPH_ADVANCE!r}",
                f"OS2_VENDOR = {OS2_VENDOR!r}",
                f"OS2_WEIGHT = {OS2_WEIGHT!r}",
                f"OS2_WIDTH = {OS2_WIDTH!r}",
                f"OS2_TYPO_ASCENT = {OS2_TYPO_ASCENT!r}",
                f"OS2_TYPO_DESCENT = {OS2_TYPO_DESCENT!r}",
                f"OS2_WIN_ASCENT = {OS2_WIN_ASCENT!r}",
                f"OS2_WIN_DESCENT = {OS2_WIN_DESCENT!r}",
                f"HHEA_ASCENT = {HHEA_ASCENT!r}",
                f"HHEA_DESCENT = {HHEA_DESCENT!r}",
                f"PANOSE = {PANOSE!r}",
                f"SFNT_NAMES = {SFNT_NAMES!r}",
                "",
                "if len(CELL_SVGS) != EXPECTED_OUTPUT_NONEMPTY_CELLS:",
                "    raise SystemExit(",
                "        f'build has {len(CELL_SVGS)} importable cells; '",
                "        f'expected {EXPECTED_OUTPUT_NONEMPTY_CELLS}'",
                "    )",
                "",
                "font = fontforge.font()",
                "font.layers[1].is_quadratic = True",
                "font.encoding = 'UnicodeBmp'",
                "font.fontname = FONT_NAME",
                "font.familyname = FONT_FAMILY",
                "font.fullname = FONT_FULL_NAME",
                "font.weight = FONT_WEIGHT",
                "font.version = FONT_VERSION",
                "font.em = FONT_EM",
                "font.ascent = FONT_ASCENT",
                "font.descent = FONT_DESCENT",
                "font.os2_vendor = OS2_VENDOR",
                "font.os2_weight = OS2_WEIGHT",
                "font.os2_width = OS2_WIDTH",
                "font.os2_typoascent_add = 0",
                "font.os2_typodescent_add = 0",
                "font.os2_winascent_add = 0",
                "font.os2_windescent_add = 0",
                "font.hhea_ascent_add = 0",
                "font.hhea_descent_add = 0",
                "font.os2_typoascent = OS2_TYPO_ASCENT",
                "font.os2_typodescent = OS2_TYPO_DESCENT",
                "font.os2_typolinegap = 0",
                "font.os2_winascent = OS2_WIN_ASCENT",
                "font.os2_windescent = OS2_WIN_DESCENT",
                "font.os2_use_typo_metrics = 0",
                "font.os2_fstype = 0",
                "font.hhea_ascent = HHEA_ASCENT",
                "font.hhea_descent = HHEA_DESCENT",
                "font.hhea_linegap = 0",
                "font.os2_panose = PANOSE",
                "font.sfnt_names = SFNT_NAMES",
                "font.gasp_version = 0",
                "font.gasp = ((65535, ('antialias',)),)",
                "",
                "for index, codepoint in enumerate(CP437):",
                "    try:",
                "        glyph = font[codepoint]",
                "    except TypeError:",
                "        glyph = font.createChar(codepoint)",
                "    width = GLYPH_ADVANCE",
                "    empty = fontforge.layer()",
                "    empty.is_quadratic = True",
                "    glyph.foreground = empty",
                "    glyph.width = width",
                "    path = CELL_SVGS.get(index)",
                "    if path:",
                "        glyph.importOutlines(path)",
                "        glyph.foreground.is_quadratic = True",
                "        glyph.correctDirection()",
                "        glyph.round()",
                "        glyph.width = width",
                "",
                "built_glyphs = []",
                "for codepoint in CP437:",
                "    try:",
                "        built_glyphs.append(font[codepoint].glyphname)",
                "    except TypeError:",
                "        raise SystemExit(f'output is missing expected CP437 glyph U+{codepoint:04X}')",
                "if len(built_glyphs) != len(CP437) or len(set(built_glyphs)) != len(CP437):",
                "    raise SystemExit('output does not contain the expected 256 distinct CP437 glyphs')",
                "nonempty = sum(1 for codepoint in CP437 if len(font[codepoint].foreground))",
                "if nonempty != EXPECTED_OUTPUT_NONEMPTY_CELLS:",
                "    raise SystemExit(f'output has {nonempty} non-empty CP437 glyphs; expected {EXPECTED_OUTPUT_NONEMPTY_CELLS}')",
                "bad_widths = [font[codepoint].glyphname for codepoint in CP437 if font[codepoint].width != GLYPH_ADVANCE]",
                "if bad_widths:",
                "    raise SystemExit('output glyph advance mismatch: ' + ', '.join(bad_widths[:20]))",
                "bad_quadratic = [font[codepoint].glyphname for codepoint in CP437 if len(font[codepoint].foreground) and not font[codepoint].foreground.is_quadratic]",
                "if bad_quadratic:",
                "    raise SystemExit('output contains non-quadratic outlines: ' + ', '.join(bad_quadratic[:20]))",
                "",
                "for glyphname in ('.notdef', 'nonmarkingreturn'):",
                "    glyph = font.createChar(-1, glyphname)",
                "    glyph.unicode = -1",
                "    glyph.width = GLYPH_ADVANCE",
                "    empty = fontforge.layer()",
                "    empty.is_quadratic = True",
                "    glyph.foreground = empty",
                "",
                "font.generate(OUTPUT, flags=(\"opentype\",))",
                "font.close()",
                "",
            ]
        )
    )


def run_fontforge(fontforge_executable: str, script_path: Path, config_dir: Path) -> None:
    env = os.environ.copy()
    env["XDG_CONFIG_HOME"] = str(config_dir)
    subprocess.run(
        [fontforge_executable, "-lang=py", "-script", str(script_path)],
        check=True,
        env=env,
    )


def build_ttf(
    source_svg: Path,
    output_ttf: Path,
    layer_name: str,
    grid_cols: int,
    grid_rows: int,
    fontforge_executable: str,
) -> None:
    if len(CP437_DISPLAY_CODEPOINTS) != grid_cols * grid_rows:
        raise ValueError("CP437 display mapping must match the SVG grid size")
    if len(set(CP437_DISPLAY_CODEPOINTS)) != len(CP437_DISPLAY_CODEPOINTS):
        raise ValueError("CP437 display mapping contains duplicate Unicode codepoints")

    cells, cell_width, cell_height = collect_cell_elements(
        source_svg=source_svg,
        layer_name=layer_name,
        grid_cols=grid_cols,
        grid_rows=grid_rows,
    )
    if len(cells) != EXPECTED_POPULATED_CELLS:
        raise ValueError(
            f"source layer has {len(cells)} populated cells; expected {EXPECTED_POPULATED_CELLS}"
        )

    with tempfile.TemporaryDirectory(prefix="smooth-cp437-build-") as tmp:
        tmpdir = Path(tmp)
        fontforge_output = tmpdir / output_ttf.name

        cell_svgs = write_cell_svgs(
            cells=cells,
            cell_width=cell_width,
            cell_height=cell_height,
            grid_cols=grid_cols,
            output_dir=tmpdir / "cells",
            trim_left=CELL_TRIM_LEFT,
            trim_top=CELL_TRIM_TOP,
            trim_right=CELL_TRIM_RIGHT,
            trim_bottom=CELL_TRIM_BOTTOM,
        )
        if len(cell_svgs) != EXPECTED_OUTPUT_NONEMPTY_CELLS:
            raise ValueError(
                "cell trim leaves "
                f"{len(cell_svgs)} importable cells; expected {EXPECTED_OUTPUT_NONEMPTY_CELLS}"
            )
        script_path = tmpdir / "build_font.py"
        write_fontforge_script(
            script_path=script_path,
            output_ttf=fontforge_output.resolve(),
            cell_svgs=cell_svgs,
        )
        run_fontforge(
            fontforge_executable=fontforge_executable,
            script_path=script_path,
            config_dir=tmpdir / "fontforge-config",
        )

        output_ttf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fontforge_output, output_ttf)

    print(f"{source_svg}: layer {layer_name!r} -> {output_ttf}")
    print("font metrics/properties read from baked-in constants")
    print(
        "cell trim: "
        f"left={CELL_TRIM_LEFT:g}, top={CELL_TRIM_TOP:g}, "
        f"right={CELL_TRIM_RIGHT:g}, bottom={CELL_TRIM_BOTTOM:g}"
    )
    print(f"expected CP437 glyphs verified: {grid_cols * grid_rows}")
    print(f"glyph cells populated from source layer: {len(cells)} / {grid_cols * grid_rows}")
    print(f"non-empty glyphs after trim: {len(cell_svgs)} / {grid_cols * grid_rows}")


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: python3 scripts/build_12x12_df_ttf.py")

    for name, value in (("GRID_COLS", GRID_COLS), ("GRID_ROWS", GRID_ROWS)):
        if value <= 0:
            raise SystemExit(f"{name} must be positive")

    missing = [path for path in (SOURCE_SVG,) if not path.exists()]
    if missing:
        raise SystemExit("missing input file(s): " + ", ".join(str(path) for path in missing))

    build_ttf(
        source_svg=SOURCE_SVG,
        output_ttf=OUTPUT_TTF,
        layer_name=LAYER_NAME,
        grid_cols=GRID_COLS,
        grid_rows=GRID_ROWS,
        fontforge_executable=FONTFORGE_EXECUTABLE,
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc
