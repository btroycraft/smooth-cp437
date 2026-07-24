# Smooth CP437

Smooth CP437 is a square-aspect, vector-graphics inverse of the IBM VGA 9x14
bitmap font. It is derived from the `Bm437_IBM_VGA_9x14` font in The Ultimate
Oldschool PC Font Pack by VileR / INT10h.org.

The source IBM VGA bitmap uses 9x14 glyph cells. Smooth CP437 adapts those
forms into wider square-cell formats, with changes to utility glyphs where
needed to support that wider format. The DF variants include 12x12 and 14x14
source grids and generated fixed-pitch TrueType fonts for terminal use.

## Font Variants

`smooth-cp437_original.ttf` is the IBM VGA 14x14 variant. It is a pixel-perfect
interpolation of the IBM VGA 9x14 font into a 14x14 pixel cell for each glyph,
with utility glyphs changed to account for the extra width.

`smooth-cp437_14x14_df.ttf` uses the same 14x14 IBM VGA interpretation, but
replaces CP437 glyphs 1 and 2 with the bearded faces from the Dwarf Fortress
font.

`smooth-cp437_12x12_df.ttf` is a custom interpretation of the Dwarf Fortress
font based on a fusion of the IBM VGA font and the default Dwarf Fortress font.
It also includes several small changes to fix glyph spacing for ASCII games such
as Dwarf Fortress, where maps are rendered as ASCII text.

## Build Outputs

The fonts are available as fixed-pitch TrueType fonts and as generated bitmap
pixel-font sheets. Unsmoothed majority-rule rasterizations are available as BMP
files, and smooth averaged rasterizations are available as transparent PNG
files. The unsmoothed majority-rule versions are not recommended for
non-multiple sizes, where the output pixel grid does not align cleanly with the
source pixel grid.

Each bitmap variant is generated at exact source-cell multiples in the main
mode folder:

- IBM VGA 14x14 and DF 14x14: `14, 28, 42, 56, 70` pixels per glyph
- DF 12x12: `12, 24, 36, 48, 60` pixels per glyph

The `nonmultiples/` folders contain every one-pixel size between the 2x and 5x
sizes, excluding exact multiples already written at the main level:

- IBM VGA 14x14 and DF 14x14: `29..41`, `43..55`, and `57..69`
- DF 12x12: `25..35`, `37..47`, and `49..59`

## Screen Fit Reference

These tables list how many square glyph cells fit inside common screen
resolutions for the generated multiple bitmap sizes. Counts are rows x columns,
rounded down to the largest grid that fits inside the screen.

12x12-family outputs:

| Resolution | Common name | `12px` | `24px` | `36px` | `48px` | `60px` |
| --- | --- | --- | --- | --- | --- | --- |
| `800x600` | SVGA | 50 x 66 | 25 x 33 | 16 x 22 | 12 x 16 | 10 x 13 |
| `1024x768` | XGA | 64 x 85 | 32 x 42 | 21 x 28 | 16 x 21 | 12 x 17 |
| `1280x720` | HD / 720p | 60 x 106 | 30 x 53 | 20 x 35 | 15 x 26 | 12 x 21 |
| `1280x800` | WXGA | 66 x 106 | 33 x 53 | 22 x 35 | 16 x 26 | 13 x 21 |
| `1366x768` | HD laptop | 64 x 113 | 32 x 56 | 21 x 37 | 16 x 28 | 12 x 22 |
| `1440x900` | WXGA+ | 75 x 120 | 37 x 60 | 25 x 40 | 18 x 30 | 15 x 24 |
| `1600x900` | HD+ | 75 x 133 | 37 x 66 | 25 x 44 | 18 x 33 | 15 x 26 |
| `1680x1050` | WSXGA+ | 87 x 140 | 43 x 70 | 29 x 46 | 21 x 35 | 17 x 28 |
| `1920x1080` | FHD / 1080p | 90 x 160 | 45 x 80 | 30 x 53 | 22 x 40 | 18 x 32 |
| `1920x1200` | WUXGA | 100 x 160 | 50 x 80 | 33 x 53 | 25 x 40 | 20 x 32 |
| `2560x1080` | UW-FHD | 90 x 213 | 45 x 106 | 30 x 71 | 22 x 53 | 18 x 42 |
| `2560x1440` | QHD / 1440p | 120 x 213 | 60 x 106 | 40 x 71 | 30 x 53 | 24 x 42 |
| `2560x1600` | WQXGA | 133 x 213 | 66 x 106 | 44 x 71 | 33 x 53 | 26 x 42 |
| `2880x1800` | Retina 15-inch | 150 x 240 | 75 x 120 | 50 x 80 | 37 x 60 | 30 x 48 |
| `3440x1440` | UWQHD | 120 x 286 | 60 x 143 | 40 x 95 | 30 x 71 | 24 x 57 |
| `3840x2160` | 4K UHD | 180 x 320 | 90 x 160 | 60 x 106 | 45 x 80 | 36 x 64 |
| `3840x2400` | WQUXGA | 200 x 320 | 100 x 160 | 66 x 106 | 50 x 80 | 40 x 64 |
| `5120x1440` | DQHD | 120 x 426 | 60 x 213 | 40 x 142 | 30 x 106 | 24 x 85 |
| `5120x2160` | 5K2K | 180 x 426 | 90 x 213 | 60 x 142 | 45 x 106 | 36 x 85 |
| `5120x2880` | 5K | 240 x 426 | 120 x 213 | 80 x 142 | 60 x 106 | 48 x 85 |
| `7680x4320` | 8K UHD | 360 x 640 | 180 x 320 | 120 x 213 | 90 x 160 | 72 x 128 |

14x14-family outputs:

| Resolution | Common name | `14px` | `28px` | `42px` | `56px` | `70px` |
| --- | --- | --- | --- | --- | --- | --- |
| `800x600` | SVGA | 42 x 57 | 21 x 28 | 14 x 19 | 10 x 14 | 8 x 11 |
| `1024x768` | XGA | 54 x 73 | 27 x 36 | 18 x 24 | 13 x 18 | 10 x 14 |
| `1280x720` | HD / 720p | 51 x 91 | 25 x 45 | 17 x 30 | 12 x 22 | 10 x 18 |
| `1280x800` | WXGA | 57 x 91 | 28 x 45 | 19 x 30 | 14 x 22 | 11 x 18 |
| `1366x768` | HD laptop | 54 x 97 | 27 x 48 | 18 x 32 | 13 x 24 | 10 x 19 |
| `1440x900` | WXGA+ | 64 x 102 | 32 x 51 | 21 x 34 | 16 x 25 | 12 x 20 |
| `1600x900` | HD+ | 64 x 114 | 32 x 57 | 21 x 38 | 16 x 28 | 12 x 22 |
| `1680x1050` | WSXGA+ | 75 x 120 | 37 x 60 | 25 x 40 | 18 x 30 | 15 x 24 |
| `1920x1080` | FHD / 1080p | 77 x 137 | 38 x 68 | 25 x 45 | 19 x 34 | 15 x 27 |
| `1920x1200` | WUXGA | 85 x 137 | 42 x 68 | 28 x 45 | 21 x 34 | 17 x 27 |
| `2560x1080` | UW-FHD | 77 x 182 | 38 x 91 | 25 x 60 | 19 x 45 | 15 x 36 |
| `2560x1440` | QHD / 1440p | 102 x 182 | 51 x 91 | 34 x 60 | 25 x 45 | 20 x 36 |
| `2560x1600` | WQXGA | 114 x 182 | 57 x 91 | 38 x 60 | 28 x 45 | 22 x 36 |
| `2880x1800` | Retina 15-inch | 128 x 205 | 64 x 102 | 42 x 68 | 32 x 51 | 25 x 41 |
| `3440x1440` | UWQHD | 102 x 245 | 51 x 122 | 34 x 81 | 25 x 61 | 20 x 49 |
| `3840x2160` | 4K UHD | 154 x 274 | 77 x 137 | 51 x 91 | 38 x 68 | 30 x 54 |
| `3840x2400` | WQUXGA | 171 x 274 | 85 x 137 | 57 x 91 | 42 x 68 | 34 x 54 |
| `5120x1440` | DQHD | 102 x 365 | 51 x 182 | 34 x 121 | 25 x 91 | 20 x 73 |
| `5120x2160` | 5K2K | 154 x 365 | 77 x 182 | 51 x 121 | 38 x 91 | 30 x 73 |
| `5120x2880` | 5K | 205 x 365 | 102 x 182 | 68 x 121 | 51 x 91 | 41 x 73 |
| `7680x4320` | 8K UHD | 308 x 548 | 154 x 274 | 102 x 182 | 77 x 137 | 61 x 109 |

## Building

The generated materials are built with the Makefile:

- `make build`: build TrueType fonts and bitmap sheets, then bundle them into release archives
- `make package`: bundle the generated TrueType fonts and bitmap sheets into `smooth-cp437-fonts.7z` and `smooth-cp437-fonts.tar.gz`
- `make fonts`: build the three TrueType fonts
- `make bitmaps`: build majority BMP sheets and averaged transparent PNG sheets
- `make majority-bitmaps`: build only winner-takes-all BMP sheets
- `make average-bitmaps`: build only averaged transparent PNG sheets

Build dependencies are GNU Make, Python 3, FontForge with Python scripting,
GNU tar, `gzip`, and 7-Zip's `7z` command. The Python packages listed in
`requirements.txt` are `lxml`, `numpy`, `Pillow`, `skia-pathops`, and
`svgpathtools`.

## Files

- `smooth-cp437_ibm-vga_src.svg`: source vector SVG sheet for the IBM VGA variant
- `smooth-cp437_original.ttf`: generated TrueType font for the original variant
- `smooth-cp437_df-12x12_src.svg`: source vector SVG sheet for the 12x12 DF variant
- `smooth-cp437_df.ttf`: generated TrueType font for the DF variant
- `smooth-cp437_12x12_df.ttf`: generated fixed-pitch TrueType font for the 12x12 DF variant
- `smooth-cp437_df-14x14_src.svg`: source vector SVG sheet for the 14x14 DF variant
- `smooth-cp437_14x14_df.ttf`: generated fixed-pitch TrueType font for the 14x14 DF variant
- `bmp_ibm-vga/`: ignored generated bitmap sheets for the IBM VGA variant
- `bmp_df_12x12/`: ignored generated bitmap sheets for the 12x12 DF variant
- `bmp_df_14x14/`: ignored generated bitmap sheets for the 14x14 DF variant
- `smooth-cp437-fonts.7z`: generated 7-Zip distribution archive containing the three TrueType fonts and generated bitmap sheets
- `smooth-cp437-fonts.tar.gz`: generated gzip-compressed tar distribution archive
- `scripts/build_ibm_vga_ttf.py`: builds `smooth-cp437_original.ttf`
- `scripts/build_12x12_df_ttf.py`: builds `smooth-cp437_12x12_df.ttf`
- `scripts/build_df_14x14_ttf.py`: builds `smooth-cp437_14x14_df.ttf`
- `scripts/rasterize_svg.py`: direct SVG rasterizer with majority and averaged transparent modes

The bitmap outputs are grouped by reduction method:

- `majority/`: winner-takes-all BMP outputs at 1x through 5x source glyph-size multiples
- `average/`: averaged-area transparent PNG outputs at 1x through 5x source glyph-size multiples
- `majority/nonmultiples/` and `average/nonmultiples/`: every one-pixel size from 2x through 5x, excluding exact source glyph-size multiples

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

The original bitmap font was transformed into square-aspect vector-graphics
inverses based on 12x12 and 14x14 grids per glyph. Utility glyphs were adjusted
where needed for the wider format, and the result was exported as SVG,
fixed-pitch TrueType, and condensed BMP raster outputs.
