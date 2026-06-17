# Smooth CP437

Smooth CP437 is a square-aspect, vector-graphics inverse of the IBM VGA 9x14
bitmap font. It is derived from the `Bm437_IBM_VGA_9x14` font in The Ultimate
Oldschool PC Font Pack by VileR / INT10h.org.

The source IBM VGA bitmap uses 9x14 glyph cells. Smooth CP437 adapts those
forms into a wider square-cell format based on a 14x14 grid per glyph, with
changes to utility glyphs where needed to support that wider format.

## Files

- `smooth-cp437_original_src.svg`: source vector SVG sheet for the original variant
- `smooth-cp437_original.svg`: generated SVG font for the original variant
- `smooth-cp437_original.ttf`: generated TrueType font for the original variant
- `smooth-cp437_df_src.svg`: source vector SVG sheet for the DF variant
- `smooth-cp437_df.svg`: generated SVG font for the DF variant
- `smooth-cp437_df.ttf`: generated TrueType font for the DF variant
- `bitmap_df/`: generated DF BMP raster outputs at multiple block sizes

The bitmap outputs are grouped by reduction method:

- `bitmap_df/average/`: averaged-area outputs
- `bitmap_df/majority/`: winner-takes-all area outputs
- `non_14_multiples/`: block sizes that are not multiples of 14

## License

This repository is distributed under the Creative Commons
Attribution-ShareAlike 4.0 International License.

Attribution:

Based on The Ultimate Oldschool PC Font Pack by VileR / INT10h.org,
licensed under CC BY-SA 4.0.

Upstream:

- https://int10h.org/oldschool-pc-fonts/
- https://int10h.org/oldschool-pc-fonts/readme/
- https://creativecommons.org/licenses/by-sa/4.0/

Changes:

The original bitmap font was transformed into a square-aspect vector-graphics
inverse based on a 14x14 grid per glyph. Utility glyphs were adjusted where
needed for the wider format, and the result was exported as SVG, TrueType, and
condensed BMP raster outputs.
