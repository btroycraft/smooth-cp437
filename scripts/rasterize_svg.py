#!/usr/bin/env python3
"""Rasterize a standardized CP437 SVG sheet by vector area coverage."""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

try:
    import pathops
    from lxml import etree
    from PIL import Image
    from svgpathtools import Arc, CubicBezier, Line, QuadraticBezier, parse_path
except ImportError as exc:
    raise SystemExit(
        "missing dependency: "
        f"{exc.name}. Install the local environment with "
        "`.venv/bin/python -m pip install skia-pathops svgpathtools lxml Pillow` "
        "and run this script with `.venv/bin/python`."
    ) from exc


SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
NS = {"svg": SVG_NS, "inkscape": INKSCAPE_NS}

Color = tuple[int, int, int]
RgbaColor = tuple[int, int, int, int]
Matrix = tuple[float, float, float, float, float, float]

IDENTITY: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
DEFAULT_BACKGROUND: Color = (255, 0, 255)
DEFAULT_GLYPH_COLOR: Color = (255, 255, 255)
DEFAULT_OVERLAY_COLOR: Color = (192, 192, 192)
AREA_EPSILON = 1e-9
STANDARD_GLYPH_LAYER = "Glyphs"
STANDARD_OVERLAY_LAYER = "Overlay"
RASTER_MODES = ("majority", "average")


@dataclass(frozen=True)
class ComputedStyle:
    fill: Color | None
    fill_rule: str
    fill_opacity: float
    display: str
    visibility: str


@dataclass(frozen=True)
class StyledPath:
    path: pathops.Path
    color: Color


@dataclass(frozen=True)
class SheetGeometry:
    min_x: float
    min_y: float
    width: float
    height: float
    cell_width: float
    cell_height: float


STYLE_DEFAULT = ComputedStyle(
    fill=DEFAULT_GLYPH_COLOR,
    fill_rule="nonzero",
    fill_opacity=1.0,
    display="inline",
    visibility="visible",
)


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


def parse_color(value: str | None, inherited: Color | None) -> Color | None:
    if value is None:
        return inherited

    value = value.strip()
    if value.lower() == "none":
        return None
    if value.startswith("#"):
        hex_value = value[1:]
        if len(hex_value) == 3:
            return tuple(int(ch * 2, 16) for ch in hex_value)  # type: ignore[return-value]
        if len(hex_value) == 6:
            return (
                int(hex_value[0:2], 16),
                int(hex_value[2:4], 16),
                int(hex_value[4:6], 16),
            )

    rgb_match = re.fullmatch(
        r"rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)",
        value,
        flags=re.IGNORECASE,
    )
    if rgb_match:
        return tuple(max(0, min(255, int(channel))) for channel in rgb_match.groups())  # type: ignore[return-value]

    raise ValueError(f"unsupported SVG fill color: {value!r}")


def parse_float(value: str | None, inherited: float) -> float:
    if value is None:
        return inherited
    return float(value.strip())


def computed_style(element: etree._Element, inherited: ComputedStyle) -> ComputedStyle:
    values = parse_style(element.get("style"))

    for key in ("fill", "fill-rule", "fill-opacity", "display", "visibility"):
        attr = element.get(key)
        if attr is not None:
            values[key] = attr

    return ComputedStyle(
        fill=parse_color(values.get("fill"), inherited.fill),
        fill_rule=values.get("fill-rule", inherited.fill_rule).lower(),
        fill_opacity=parse_float(values.get("fill-opacity"), inherited.fill_opacity),
        display=values.get("display", inherited.display).lower(),
        visibility=values.get("visibility", inherited.visibility).lower(),
    )


def matmul(left: Matrix, right: Matrix) -> Matrix:
    la, lb, lc, ld, le, lf = left
    ra, rb, rc, rd, re, rf = right
    return (
        la * ra + lc * rb,
        lb * ra + ld * rb,
        la * rc + lc * rd,
        lb * rc + ld * rd,
        la * re + lc * rf + le,
        lb * re + ld * rf + lf,
    )


def translate(tx: float, ty: float = 0.0) -> Matrix:
    return (1.0, 0.0, 0.0, 1.0, tx, ty)


def scale(sx: float, sy: float | None = None) -> Matrix:
    if sy is None:
        sy = sx
    return (sx, 0.0, 0.0, sy, 0.0, 0.0)


def rotate(angle_degrees: float, cx: float | None = None, cy: float | None = None) -> Matrix:
    radians = math.radians(angle_degrees)
    cos_a = math.cos(radians)
    sin_a = math.sin(radians)
    rotation: Matrix = (cos_a, sin_a, -sin_a, cos_a, 0.0, 0.0)
    if cx is None or cy is None:
        return rotation
    return matmul(translate(cx, cy), matmul(rotation, translate(-cx, -cy)))


def parse_numbers(value: str) -> list[float]:
    return [
        float(part)
        for part in re.split(r"[\s,]+", value.strip())
        if part
    ]


def parse_transform(transform_value: str | None) -> Matrix:
    if not transform_value:
        return IDENTITY

    matrix = IDENTITY
    for match in re.finditer(r"([A-Za-z]+)\(([^)]*)\)", transform_value):
        name = match.group(1).lower()
        values = parse_numbers(match.group(2))

        if name == "matrix":
            if len(values) != 6:
                raise ValueError(f"matrix() expects 6 values: {transform_value!r}")
            next_matrix = tuple(values)  # type: ignore[assignment]
        elif name == "translate":
            if len(values) not in {1, 2}:
                raise ValueError(f"translate() expects 1 or 2 values: {transform_value!r}")
            next_matrix = translate(values[0], values[1] if len(values) == 2 else 0.0)
        elif name == "scale":
            if len(values) not in {1, 2}:
                raise ValueError(f"scale() expects 1 or 2 values: {transform_value!r}")
            next_matrix = scale(values[0], values[1] if len(values) == 2 else None)
        elif name == "rotate":
            if len(values) not in {1, 3}:
                raise ValueError(f"rotate() expects 1 or 3 values: {transform_value!r}")
            next_matrix = rotate(values[0], values[1], values[2]) if len(values) == 3 else rotate(values[0])
        else:
            raise ValueError(f"unsupported SVG transform: {name!r}")

        matrix = matmul(next_matrix, matrix)

    return matrix


def transform_point(point: complex, matrix: Matrix) -> tuple[float, float]:
    a, b, c, d, e, f = matrix
    x = float(point.real)
    y = float(point.imag)
    return (a * x + c * y + e, b * x + d * y + f)


def fill_type(fill_rule: str) -> pathops.FillType:
    if fill_rule == "evenodd":
        return pathops.FillType.EVEN_ODD
    if fill_rule in {"nonzero", "winding"}:
        return pathops.FillType.WINDING
    raise ValueError(f"unsupported SVG fill-rule: {fill_rule!r}")


def path_is_empty(path: pathops.Path) -> bool:
    return len(path.verbs) == 0


def svg_path_to_pathops(path_data: str, matrix: Matrix, rule: str) -> pathops.Path:
    parsed = parse_path(path_data)
    output = pathops.Path()
    output.fillType = fill_type(rule)

    for subpath in parsed.continuous_subpaths():
        if not subpath:
            continue

        output.moveTo(*transform_point(subpath[0].start, matrix))
        for segment in subpath:
            if isinstance(segment, Line):
                output.lineTo(*transform_point(segment.end, matrix))
            elif isinstance(segment, CubicBezier):
                output.cubicTo(
                    *transform_point(segment.control1, matrix),
                    *transform_point(segment.control2, matrix),
                    *transform_point(segment.end, matrix),
                )
            elif isinstance(segment, QuadraticBezier):
                output.quadTo(
                    *transform_point(segment.control, matrix),
                    *transform_point(segment.end, matrix),
                )
            elif isinstance(segment, Arc):
                for cubic in segment.as_cubic_curves():
                    output.cubicTo(
                        *transform_point(cubic.control1, matrix),
                        *transform_point(cubic.control2, matrix),
                        *transform_point(cubic.end, matrix),
                    )
            else:
                raise ValueError(f"unsupported SVG path segment: {type(segment).__name__}")

        # SVG fill implicitly closes open subpaths.
        output.close()

    return output


def rect_to_pathops(element: etree._Element, matrix: Matrix, rule: str) -> pathops.Path:
    x = float(element.get("x", "0"))
    y = float(element.get("y", "0"))
    width = float(element.get("width", "0"))
    height = float(element.get("height", "0"))
    if width < 0 or height < 0:
        raise ValueError("rect width and height must be non-negative")

    points = [
        complex(x, y),
        complex(x + width, y),
        complex(x + width, y + height),
        complex(x, y + height),
    ]
    output = pathops.Path()
    output.fillType = fill_type(rule)
    output.moveTo(*transform_point(points[0], matrix))
    for point in points[1:]:
        output.lineTo(*transform_point(point, matrix))
    output.close()
    return output


def parse_viewbox(root: etree._Element) -> tuple[float, float, float, float]:
    viewbox = root.get("viewBox")
    if viewbox:
        values = parse_numbers(viewbox)
        if len(values) != 4:
            raise ValueError(f"expected four viewBox values, got {viewbox!r}")
        return values[0], values[1], values[2], values[3]

    width = float(root.get("width"))
    height = float(root.get("height"))
    return 0.0, 0.0, width, height


def find_layer(root: etree._Element, layer_name: str) -> etree._Element | None:
    layers = root.xpath(".//svg:g[@inkscape:label]", namespaces=NS)
    for layer in layers:
        if layer.get(f"{{{INKSCAPE_NS}}}label", "").lower() == layer_name.lower():
            return layer
    return None


def available_layer_names(root: etree._Element) -> list[str]:
    return [
        layer.get(f"{{{INKSCAPE_NS}}}label", "")
        for layer in root.xpath(".//svg:g[@inkscape:label]", namespaces=NS)
    ]


def require_populated_layer(root: etree._Element, layer_name: str) -> str:
    layer = find_layer(root, layer_name)
    if layer is not None and layer.xpath(".//svg:path|.//svg:rect", namespaces=NS):
        return layer_name

    raise ValueError(
        f"could not find populated layer {layer_name!r}; available layers: "
        + ", ".join(repr(name) for name in available_layer_names(root))
    )


def populated_overlay_layer(root: etree._Element) -> str | None:
    layer = find_layer(root, STANDARD_OVERLAY_LAYER)
    if layer is not None and layer.xpath(".//svg:path|.//svg:rect", namespaces=NS):
        return STANDARD_OVERLAY_LAYER
    return None


def walk_shapes(
    element: etree._Element,
    inherited_style: ComputedStyle,
    inherited_matrix: Matrix,
) -> list[StyledPath]:
    style = computed_style(element, inherited_style)
    matrix = matmul(parse_transform(element.get("transform")), inherited_matrix)

    if style.display == "none" or style.visibility == "hidden":
        return []

    tag = etree.QName(element).localname
    if tag in {"path", "rect"}:
        if style.fill is None or style.fill_opacity <= 0.0:
            return []

        if tag == "path":
            path = svg_path_to_pathops(element.get("d", ""), matrix, style.fill_rule)
        else:
            path = rect_to_pathops(element, matrix, style.fill_rule)

        if path_is_empty(path):
            return []
        return [StyledPath(path=path, color=style.fill)]

    shapes: list[StyledPath] = []
    for child in element:
        shapes.extend(walk_shapes(child, style, matrix))
    return shapes


def geometry_for(root: etree._Element, grid_cols: int, grid_rows: int) -> SheetGeometry:
    min_x, min_y, width, height = parse_viewbox(root)
    return SheetGeometry(
        min_x=min_x,
        min_y=min_y,
        width=width,
        height=height,
        cell_width=width / grid_cols,
        cell_height=height / grid_rows,
    )


def cell_index_for(path: pathops.Path, geometry: SheetGeometry, grid_cols: int, grid_rows: int) -> int:
    min_x, min_y, max_x, max_y = path.bounds
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    col = int((center_x - geometry.min_x) // geometry.cell_width)
    row = int((center_y - geometry.min_y) // geometry.cell_height)
    col = max(0, min(grid_cols - 1, col))
    row = max(0, min(grid_rows - 1, row))
    return row * grid_cols + col


def collect_layer_cells(
    root: etree._Element,
    layer_name: str,
    geometry: SheetGeometry,
    grid_cols: int,
    grid_rows: int,
    override_color: Color | None,
) -> list[dict[Color, list[pathops.Path]]]:
    layer = find_layer(root, layer_name)
    if layer is None:
        raise ValueError(f"could not find layer {layer_name!r}")

    cells: list[dict[Color, list[pathops.Path]]] = [defaultdict(list) for _ in range(grid_cols * grid_rows)]
    for styled_path in walk_shapes(layer, STYLE_DEFAULT, IDENTITY):
        color = override_color or styled_path.color
        index = cell_index_for(styled_path.path, geometry, grid_cols, grid_rows)
        cells[index][color].append(styled_path.path)
    return cells


def union_paths(paths: list[pathops.Path]) -> pathops.Path:
    nonempty_paths = [path for path in paths if not path_is_empty(path)]
    if not nonempty_paths:
        return pathops.Path()
    if len(nonempty_paths) == 1:
        return simplify_path(nonempty_paths[0])

    builder = pathops.OpBuilder()
    for path in nonempty_paths:
        builder.add(simplify_path(path), pathops.PathOp.UNION)
    return builder.resolve()


def simplify_path(path: pathops.Path) -> pathops.Path:
    if path_is_empty(path):
        return path
    try:
        return pathops.simplify(path)
    except pathops.PathOpsError:
        return path


def union_color_cells(
    cells: list[dict[Color, list[pathops.Path]]],
) -> list[dict[Color, pathops.Path]]:
    output: list[dict[Color, pathops.Path]] = []
    for cell in cells:
        output.append({color: union_paths(paths) for color, paths in cell.items()})
    return output


def union_all(paths_by_color: dict[Color, pathops.Path]) -> pathops.Path:
    return union_paths([path for path in paths_by_color.values() if not path_is_empty(path)])


def rect_path(x0: float, y0: float, x1: float, y1: float) -> pathops.Path:
    path = pathops.Path()
    path.moveTo(x0, y0)
    path.lineTo(x1, y0)
    path.lineTo(x1, y1)
    path.lineTo(x0, y1)
    path.close()
    return path


def intersect_area(path: pathops.Path, clip: pathops.Path) -> float:
    if path_is_empty(path):
        return 0.0
    try:
        result = pathops.op(path, clip, pathops.PathOp.INTERSECTION)
    except pathops.PathOpsError:
        result = pathops.op(simplify_path(path), clip, pathops.PathOp.INTERSECTION)
    return abs(result.area)


def subtract_path(path: pathops.Path, mask: pathops.Path) -> pathops.Path:
    if path_is_empty(path) or path_is_empty(mask):
        return path
    try:
        return pathops.op(path, mask, pathops.PathOp.DIFFERENCE)
    except pathops.PathOpsError:
        return pathops.op(simplify_path(path), simplify_path(mask), pathops.PathOp.DIFFERENCE)


def visible_cell_paths(
    glyph_paths: dict[Color, pathops.Path],
    overlay_paths: dict[Color, pathops.Path],
) -> list[tuple[Color, int, pathops.Path]]:
    overlay_union = union_all(overlay_paths)
    visible: list[tuple[Color, int, pathops.Path]] = []

    for color, path in glyph_paths.items():
        visible.append((color, 1, subtract_path(path, overlay_union)))
    for color, path in overlay_paths.items():
        visible.append((color, 2, path))

    return [(color, priority, path) for color, priority, path in visible if not path_is_empty(path)]


def choose_pixel_color(
    visible_paths: list[tuple[Color, int, pathops.Path]],
    clip: pathops.Path,
    pixel_area: float,
    background: Color,
) -> Color:
    candidates: list[tuple[float, int, Color]] = []
    covered_area = 0.0

    for color, priority, path in visible_paths:
        area = intersect_area(path, clip)
        if area > AREA_EPSILON:
            covered_area += area
            candidates.append((area, priority, color))

    background_area = max(0.0, pixel_area - covered_area)
    candidates.append((background_area, 0, background))

    best_area = max(area for area, _, _ in candidates)
    tied = [candidate for candidate in candidates if abs(candidate[0] - best_area) <= AREA_EPSILON]
    return max(tied, key=lambda candidate: candidate[1])[2]


def clamp_byte(value: float) -> int:
    return max(0, min(255, int(round(value))))


def average_pixel_color(
    visible_paths: list[tuple[Color, int, pathops.Path]],
    clip: pathops.Path,
    pixel_area: float,
    background: Color,
    transparent_background: bool,
) -> RgbaColor | Color:
    area_by_color: dict[Color, float] = defaultdict(float)

    for color, _priority, path in visible_paths:
        area = intersect_area(path, clip)
        if area > AREA_EPSILON:
            area_by_color[color] += area

    visible_area = sum(area_by_color.values())
    background_area = max(0.0, pixel_area - visible_area)

    if transparent_background:
        if visible_area <= AREA_EPSILON:
            return (*background, 0)

        red = sum(color[0] * area for color, area in area_by_color.items()) / visible_area
        green = sum(color[1] * area for color, area in area_by_color.items()) / visible_area
        blue = sum(color[2] * area for color, area in area_by_color.items()) / visible_area
        alpha = 255.0 * min(pixel_area, visible_area) / pixel_area
        return (
            clamp_byte(red),
            clamp_byte(green),
            clamp_byte(blue),
            max(1, clamp_byte(alpha)),
        )

    total_area = visible_area + background_area
    red = (
        sum(color[0] * area for color, area in area_by_color.items())
        + background[0] * background_area
    ) / total_area
    green = (
        sum(color[1] * area for color, area in area_by_color.items())
        + background[1] * background_area
    ) / total_area
    blue = (
        sum(color[2] * area for color, area in area_by_color.items())
        + background[2] * background_area
    ) / total_area
    return (clamp_byte(red), clamp_byte(green), clamp_byte(blue))


def output_pixel_color(
    mode: str,
    visible_paths: list[tuple[Color, int, pathops.Path]],
    clip: pathops.Path,
    pixel_area: float,
    background: Color,
    transparent_background: bool,
) -> RgbaColor | Color:
    if mode == "majority":
        color = choose_pixel_color(
            visible_paths=visible_paths,
            clip=clip,
            pixel_area=pixel_area,
            background=background,
        )
        if transparent_background and color == background:
            return (*background, 0)
        return (*color, 255) if transparent_background else color

    if mode == "average":
        return average_pixel_color(
            visible_paths=visible_paths,
            clip=clip,
            pixel_area=pixel_area,
            background=background,
            transparent_background=transparent_background,
        )

    raise ValueError(f"unsupported rasterization mode: {mode!r}")


def rasterize(
    source_svg: Path,
    output_path: Path,
    glyph_width: int,
    glyph_height: int,
    grid_cols: int,
    grid_rows: int,
    background: Color,
    glyph_color: Color | None,
    overlay_color: Color | None,
    mode: str,
    transparent_background: bool,
) -> None:
    root = etree.parse(str(source_svg)).getroot()
    geometry = geometry_for(root, grid_cols, grid_rows)
    selected_glyph_layer = require_populated_layer(root, STANDARD_GLYPH_LAYER)
    selected_overlay_layer = populated_overlay_layer(root)

    glyph_cells = union_color_cells(
        collect_layer_cells(
            root=root,
            layer_name=selected_glyph_layer,
            geometry=geometry,
            grid_cols=grid_cols,
            grid_rows=grid_rows,
            override_color=glyph_color,
        )
    )
    if selected_overlay_layer is None:
        overlay_cells: list[dict[Color, pathops.Path]] = [{} for _ in range(grid_cols * grid_rows)]
    else:
        overlay_cells = union_color_cells(
            collect_layer_cells(
                root=root,
                layer_name=selected_overlay_layer,
                geometry=geometry,
                grid_cols=grid_cols,
                grid_rows=grid_rows,
                override_color=overlay_color,
            )
        )

    image_mode = "RGBA" if transparent_background else "RGB"
    background_pixel: RgbaColor | Color = (*background, 0) if transparent_background else background
    image = Image.new(image_mode, (grid_cols * glyph_width, grid_rows * glyph_height), background_pixel)
    pixels = image.load()

    pixel_width = geometry.cell_width / glyph_width
    pixel_height = geometry.cell_height / glyph_height
    pixel_area = pixel_width * pixel_height

    for cell_index in range(grid_cols * grid_rows):
        col = cell_index % grid_cols
        row = cell_index // grid_cols
        visible_paths = visible_cell_paths(glyph_cells[cell_index], overlay_cells[cell_index])
        cell_x = geometry.min_x + col * geometry.cell_width
        cell_y = geometry.min_y + row * geometry.cell_height

        for py in range(glyph_height):
            y0 = cell_y + py * pixel_height
            y1 = y0 + pixel_height
            output_y = row * glyph_height + py

            for px in range(glyph_width):
                x0 = cell_x + px * pixel_width
                x1 = x0 + pixel_width
                output_x = col * glyph_width + px
                pixels[output_x, output_y] = output_pixel_color(
                    mode=mode,
                    visible_paths=visible_paths,
                    clip=rect_path(x0, y0, x1, y1),
                    pixel_area=pixel_area,
                    background=background,
                    transparent_background=transparent_background,
                )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    print(f"{source_svg}: layer {selected_glyph_layer!r} -> {output_path}")
    if selected_overlay_layer:
        print(f"overlay layer {selected_overlay_layer!r} overrides glyph coverage where populated")
    print(f"mode: {mode}; transparent background: {'yes' if transparent_background else 'no'}")
    print(f"glyphs: {grid_cols}x{grid_rows}; output glyph: {glyph_width}x{glyph_height}")


def parse_cli_color(value: str) -> Color:
    color = parse_color(value, None)
    if color is None:
        raise argparse.ArgumentTypeError("color must not be none")
    return color


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rasterize an SVG CP437 sheet directly by vector intersection area. "
            "Each output pixel is a rectangle in SVG space. Majority mode picks "
            "the visible layer color with the largest covered area. Average mode "
            "area-averages visible colors. The overlay layer is subtracted from "
            "glyph coverage before pixel colors are calculated."
        )
    )
    parser.add_argument("source", type=Path, help="source SVG sheet")
    parser.add_argument("glyph_width", type=int, help="output width in pixels per glyph")
    parser.add_argument("glyph_height", type=int, help="output height in pixels per glyph")
    parser.add_argument("output", type=Path, help="output BMP/PNG image")
    parser.add_argument("--grid-cols", type=int, default=16, help="glyph columns in the sheet")
    parser.add_argument("--grid-rows", type=int, default=16, help="glyph rows in the sheet")
    parser.add_argument(
        "--mode",
        choices=RASTER_MODES,
        default="majority",
        help="pixel color calculation mode, default majority",
    )
    parser.add_argument(
        "--background-color",
        type=parse_cli_color,
        default=DEFAULT_BACKGROUND,
        help="background color, default #ff00ff",
    )
    parser.add_argument(
        "--transparent-background",
        action="store_true",
        help="write RGBA output with background coverage stored as alpha 0",
    )
    parser.add_argument(
        "--glyph-color",
        type=parse_cli_color,
        help="override glyph layer fill color",
    )
    parser.add_argument(
        "--overlay-color",
        type=parse_cli_color,
        help="override overlay layer fill color",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for name in ("glyph_width", "glyph_height", "grid_cols", "grid_rows"):
        if getattr(args, name) <= 0:
            raise SystemExit(f"{name.replace('_', '-')} must be positive")
    if not args.source.exists():
        raise SystemExit(f"missing source SVG: {args.source}")

    try:
        rasterize(
            source_svg=args.source,
            output_path=args.output,
            glyph_width=args.glyph_width,
            glyph_height=args.glyph_height,
            grid_cols=args.grid_cols,
            grid_rows=args.grid_rows,
            background=args.background_color,
            glyph_color=args.glyph_color,
            overlay_color=args.overlay_color,
            mode=args.mode,
            transparent_background=args.transparent_background,
        )
    except Exception as exc:
        raise SystemExit(f"error: {exc}") from exc


if __name__ == "__main__":
    main()
