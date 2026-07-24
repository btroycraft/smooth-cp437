#!/usr/bin/env python3
"""Reduce a high-resolution CP437 sheet with area-weighted majority voting."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class AxisWindow:
    start: int
    stop: int
    weights: np.ndarray

    @property
    def exact(self) -> bool:
        return self.stop > self.start and np.all(self.weights == 1.0)


def floor_fraction(value: Fraction) -> int:
    return value.numerator // value.denominator


def ceil_fraction(value: Fraction) -> int:
    return -(-value.numerator // value.denominator)


def build_axis_windows(
    source_size: int,
    glyph_count: int,
    output_glyph_size: int,
) -> list[AxisWindow]:
    windows: list[AxisWindow] = []

    for glyph in range(glyph_count):
        glyph_start = Fraction(glyph * source_size, glyph_count)
        glyph_stop = Fraction((glyph + 1) * source_size, glyph_count)
        glyph_span = glyph_stop - glyph_start

        for pixel in range(output_glyph_size):
            window_start = glyph_start + glyph_span * pixel / output_glyph_size
            window_stop = glyph_start + glyph_span * (pixel + 1) / output_glyph_size
            start = max(0, floor_fraction(window_start))
            stop = min(source_size, ceil_fraction(window_stop))
            weights: list[float] = []

            for source_pixel in range(start, stop):
                overlap_start = max(window_start, Fraction(source_pixel, 1))
                overlap_stop = min(window_stop, Fraction(source_pixel + 1, 1))
                overlap = overlap_stop - overlap_start
                if overlap > 0:
                    weights.append(float(overlap))

            if not weights:
                raise ValueError("output pixel maps to an empty source area")

            windows.append(AxisWindow(start, stop, np.asarray(weights, dtype=np.float64)))

    return windows


def regular_exact_scale(windows: list[AxisWindow]) -> int | None:
    if not windows:
        return None

    scale = windows[0].stop - windows[0].start
    if scale <= 0:
        return None

    for index, window in enumerate(windows):
        if window.start != index * scale or window.stop != (index + 1) * scale:
            return None
        if not window.exact:
            return None

    return scale


def normalize_image_mode(image: Image.Image) -> Image.Image:
    if image.mode in {"L", "RGB", "RGBA"}:
        return image
    return image.convert("RGBA")


def pack_pixels(array: np.ndarray) -> np.ndarray:
    if array.ndim == 2:
        return array.astype(np.uint32)

    channels = array.shape[2]
    values = array.astype(np.uint32)

    if channels == 4:
        return (
            (values[:, :, 0] << 24)
            | (values[:, :, 1] << 16)
            | (values[:, :, 2] << 8)
            | values[:, :, 3]
        )
    if channels == 3:
        return (values[:, :, 0] << 16) | (values[:, :, 1] << 8) | values[:, :, 2]
    if channels == 1:
        return values[:, :, 0]

    raise ValueError(f"unsupported channel count: {channels}")


def unpack_pixels(packed: np.ndarray, mode: str) -> np.ndarray:
    values = packed.astype(np.uint32)

    if mode == "RGBA":
        output = np.empty((*values.shape, 4), dtype=np.uint8)
        output[:, :, 0] = (values >> 24) & 0xFF
        output[:, :, 1] = (values >> 16) & 0xFF
        output[:, :, 2] = (values >> 8) & 0xFF
        output[:, :, 3] = values & 0xFF
        return output

    if mode == "RGB":
        output = np.empty((*values.shape, 3), dtype=np.uint8)
        output[:, :, 0] = (values >> 16) & 0xFF
        output[:, :, 1] = (values >> 8) & 0xFF
        output[:, :, 2] = values & 0xFF
        return output

    if mode == "L":
        return values.astype(np.uint8)

    raise ValueError(f"unsupported output mode: {mode}")


def first_source_order_tie_winner(rectangle: np.ndarray, winners: np.ndarray) -> np.uint32:
    winner_set = set(int(value) for value in winners)
    for value in rectangle.reshape(-1):
        if int(value) in winner_set:
            return value
    raise RuntimeError("tie winner set did not contain any source pixels")


def choose_unweighted(rectangle: np.ndarray) -> np.uint32:
    values, counts = np.unique(rectangle, return_counts=True)
    maximum = counts.max()
    winners = values[counts == maximum]
    if len(winners) == 1:
        return winners[0]
    return first_source_order_tie_winner(rectangle, winners)


def choose_weighted(
    rectangle: np.ndarray,
    x_weights: np.ndarray,
    y_weights: np.ndarray,
) -> np.uint32:
    values, inverse = np.unique(rectangle.reshape(-1), return_inverse=True)
    weights = np.outer(y_weights, x_weights).reshape(-1)
    totals = np.bincount(inverse, weights=weights)
    maximum = totals.max()
    winners = values[np.isclose(totals, maximum, rtol=0.0, atol=1e-12)]
    if len(winners) == 1:
        return winners[0]
    return first_source_order_tie_winner(rectangle, winners)


def reduce_regular_exact(
    image: Image.Image,
    output_width: int,
    output_height: int,
    x_scale: int,
    y_scale: int,
) -> np.ndarray:
    output = np.empty((output_height, output_width), dtype=np.uint32)

    for output_y in range(output_height):
        y0 = output_y * y_scale
        y1 = y0 + y_scale
        block = np.asarray(image.crop((0, y0, image.width, y1)))
        packed = pack_pixels(block)
        cells = packed.reshape(y_scale, output_width, x_scale)
        colors = np.unique(packed)

        counts = np.empty((len(colors), output_width), dtype=np.uint32)
        for color_index, color in enumerate(colors):
            counts[color_index] = (cells == color).sum(axis=(0, 2))

        best = counts.argmax(axis=0)
        output[output_y] = colors[best]

        ties = (counts == counts.max(axis=0)).sum(axis=0) > 1
        for output_x in np.flatnonzero(ties):
            rectangle = cells[:, output_x, :]
            winner_colors = colors[counts[:, output_x] == counts[:, output_x].max()]
            output[output_y, output_x] = first_source_order_tie_winner(
                rectangle,
                winner_colors,
            )

    return output


def reduce_general(
    image: Image.Image,
    x_windows: list[AxisWindow],
    y_windows: list[AxisWindow],
) -> np.ndarray:
    output = np.empty((len(y_windows), len(x_windows)), dtype=np.uint32)

    for output_y, y_window in enumerate(y_windows):
        block = np.asarray(image.crop((0, y_window.start, image.width, y_window.stop)))
        packed = pack_pixels(block)

        for output_x, x_window in enumerate(x_windows):
            rectangle = packed[:, x_window.start : x_window.stop]
            if x_window.exact and y_window.exact:
                output[output_y, output_x] = choose_unweighted(rectangle)
            else:
                output[output_y, output_x] = choose_weighted(
                    rectangle,
                    x_window.weights,
                    y_window.weights,
                )

    return output


def reduce_sheet(
    source: Path,
    output: Path,
    grid_cols: int,
    grid_rows: int,
    glyph_width: int,
    glyph_height: int,
) -> None:
    Image.MAX_IMAGE_PIXELS = None

    with Image.open(source) as opened:
        image = normalize_image_mode(opened)
        image.load()

        x_windows = build_axis_windows(image.width, grid_cols, glyph_width)
        y_windows = build_axis_windows(image.height, grid_rows, glyph_height)
        output_width = grid_cols * glyph_width
        output_height = grid_rows * glyph_height

        x_scale = regular_exact_scale(x_windows)
        y_scale = regular_exact_scale(y_windows)

        if x_scale is not None and y_scale is not None:
            reduced = reduce_regular_exact(image, output_width, output_height, x_scale, y_scale)
        else:
            reduced = reduce_general(image, x_windows, y_windows)

        output_image = Image.fromarray(unpack_pixels(reduced, image.mode), mode=image.mode)
        output.parent.mkdir(parents=True, exist_ok=True)
        output_image.save(output)

        print(
            f"{source}: {image.width}x{image.height} -> "
            f"{output}: {output_width}x{output_height}"
        )
        print(f"glyphs: {grid_cols}x{grid_rows}; output glyph: {glyph_width}x{glyph_height}")
        if x_scale is not None and y_scale is not None:
            print(f"exact source blocks: {x_scale}x{y_scale} pixels per output pixel")
        else:
            print("used fractional boundary areas for at least one output pixel")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reduce a high-resolution CP437 sheet by exact area-weighted "
            "winner-takes-all color selection. For each output pixel, the script "
            "maps the pixel back into the corresponding source glyph area, gives "
            "fractional boundary source pixels only their overlapping area, and "
            "uses the color with the largest total area. Exact ties are broken by "
            "the first tied color encountered in source row-major order."
        )
    )
    parser.add_argument(
        "source",
        type=Path,
        help="source image to reduce",
    )
    parser.add_argument(
        "glyph_width",
        type=int,
        help="output width in pixels per glyph",
    )
    parser.add_argument(
        "glyph_height",
        type=int,
        help="output height in pixels per glyph",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="output reduced image",
    )
    parser.add_argument("--grid-cols", type=int, default=16, help="glyph columns in the sheet")
    parser.add_argument("--grid-rows", type=int, default=16, help="glyph rows in the sheet")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    for name in ("grid_cols", "grid_rows", "glyph_width", "glyph_height"):
        if getattr(args, name) <= 0:
            raise SystemExit(f"{name.replace('_', '-')} must be positive")

    reduce_sheet(
        source=args.source,
        output=args.output,
        grid_cols=args.grid_cols,
        grid_rows=args.grid_rows,
        glyph_width=args.glyph_width,
        glyph_height=args.glyph_height,
    )


if __name__ == "__main__":
    main()
