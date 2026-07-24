PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
FONTFORGE ?= fontforge
SEVENZ ?= 7z
TAR ?= tar
GZIP ?= gzip

IBM_VGA_SRC := smooth-cp437_ibm-vga-14x14_src.svg
DF12_SRC := smooth-cp437_df-12x12_src.svg
DF14_SRC := smooth-cp437_df-14x14_src.svg

IBM_VGA_TTF := smooth-cp437_ibm-vga-14x14.ttf
DF12_TTF := smooth-cp437_df-12x12.ttf
DF14_TTF := smooth-cp437_df-14x14.ttf
TTFS := $(IBM_VGA_TTF) $(DF12_TTF) $(DF14_TTF)

BUILD_IBM_VGA_TTF := scripts/build_ibm-vga-14x14_ttf.py
BUILD_DF12_TTF := scripts/build_12x12_df_ttf.py
BUILD_DF14_TTF := scripts/build_df_14x14_ttf.py
RASTERIZE_SVG := scripts/rasterize_svg.py

IBM_VGA_BITMAP_PREFIX := smooth-cp437_ibm-vga-14x14
DF12_BITMAP_PREFIX := smooth-cp437_df-12x12
DF14_BITMAP_PREFIX := smooth-cp437_df-14x14

IBM_VGA_BASE_GLYPH_SIZE := 14
DF12_BASE_GLYPH_SIZE := 12
DF14_BASE_GLYPH_SIZE := 14

IBM_VGA_MULTIPLE_SIZES := 14 28 42 56 70
DF12_MULTIPLE_SIZES := 12 24 36 48 60
DF14_MULTIPLE_SIZES := 14 28 42 56 70

IBM_VGA_NONMULTIPLE_SIZES := 29 30 31 32 33 34 35 36 37 38 39 40 41 43 44 45 46 47 48 49 50 51 52 53 54 55 57 58 59 60 61 62 63 64 65 66 67 68 69
DF12_NONMULTIPLE_SIZES := 25 26 27 28 29 30 31 32 33 34 35 37 38 39 40 41 42 43 44 45 46 47 49 50 51 52 53 54 55 56 57 58 59
DF14_NONMULTIPLE_SIZES := 29 30 31 32 33 34 35 36 37 38 39 40 41 43 44 45 46 47 48 49 50 51 52 53 54 55 57 58 59 60 61 62 63 64 65 66 67 68 69

IBM_VGA_MAJORITY_DIR := bmp_ibm-vga-14x14/majority
DF12_MAJORITY_DIR := bmp_df-12x12/majority
DF14_MAJORITY_DIR := bmp_df-14x14/majority
IBM_VGA_AVERAGE_DIR := bmp_ibm-vga-14x14/average
DF12_AVERAGE_DIR := bmp_df-12x12/average
DF14_AVERAGE_DIR := bmp_df-14x14/average

IBM_VGA_MAJORITY_NONMULTIPLES_DIR := $(IBM_VGA_MAJORITY_DIR)/nonmultiples
DF12_MAJORITY_NONMULTIPLES_DIR := $(DF12_MAJORITY_DIR)/nonmultiples
DF14_MAJORITY_NONMULTIPLES_DIR := $(DF14_MAJORITY_DIR)/nonmultiples
IBM_VGA_AVERAGE_NONMULTIPLES_DIR := $(IBM_VGA_AVERAGE_DIR)/nonmultiples
DF12_AVERAGE_NONMULTIPLES_DIR := $(DF12_AVERAGE_DIR)/nonmultiples
DF14_AVERAGE_NONMULTIPLES_DIR := $(DF14_AVERAGE_DIR)/nonmultiples

BITMAP_DIRS := \
	$(IBM_VGA_MAJORITY_DIR) $(DF12_MAJORITY_DIR) $(DF14_MAJORITY_DIR) \
	$(IBM_VGA_AVERAGE_DIR) $(DF12_AVERAGE_DIR) $(DF14_AVERAGE_DIR) \
	$(IBM_VGA_MAJORITY_NONMULTIPLES_DIR) $(DF12_MAJORITY_NONMULTIPLES_DIR) $(DF14_MAJORITY_NONMULTIPLES_DIR) \
	$(IBM_VGA_AVERAGE_NONMULTIPLES_DIR) $(DF12_AVERAGE_NONMULTIPLES_DIR) $(DF14_AVERAGE_NONMULTIPLES_DIR)

majority_bitmap_paths = \
	$(foreach size,$($(1)_MULTIPLE_SIZES),$($(1)_MAJORITY_DIR)/$($(1)_BITMAP_PREFIX)_majority_$(size)x$(size).bmp) \
	$(foreach size,$($(1)_NONMULTIPLE_SIZES),$($(1)_MAJORITY_NONMULTIPLES_DIR)/$($(1)_BITMAP_PREFIX)_majority_$(size)x$(size).bmp)

average_bitmap_paths = \
	$(foreach size,$($(1)_MULTIPLE_SIZES),$($(1)_AVERAGE_DIR)/$($(1)_BITMAP_PREFIX)_average_$(size)x$(size).png) \
	$(foreach size,$($(1)_NONMULTIPLE_SIZES),$($(1)_AVERAGE_NONMULTIPLES_DIR)/$($(1)_BITMAP_PREFIX)_average_$(size)x$(size).png)

IBM_VGA_MAJORITY_BITMAPS := $(call majority_bitmap_paths,IBM_VGA)
DF12_MAJORITY_BITMAPS := $(call majority_bitmap_paths,DF12)
DF14_MAJORITY_BITMAPS := $(call majority_bitmap_paths,DF14)
MAJORITY_BITMAPS := $(IBM_VGA_MAJORITY_BITMAPS) $(DF12_MAJORITY_BITMAPS) $(DF14_MAJORITY_BITMAPS)

IBM_VGA_AVERAGE_BITMAPS := $(call average_bitmap_paths,IBM_VGA)
DF12_AVERAGE_BITMAPS := $(call average_bitmap_paths,DF12)
DF14_AVERAGE_BITMAPS := $(call average_bitmap_paths,DF14)
AVERAGE_BITMAPS := $(IBM_VGA_AVERAGE_BITMAPS) $(DF12_AVERAGE_BITMAPS) $(DF14_AVERAGE_BITMAPS)
BITMAPS := $(MAJORITY_BITMAPS) $(AVERAGE_BITMAPS)
ARCHIVE_BASENAME := smooth-cp437-fonts
PACKAGE_7Z := $(ARCHIVE_BASENAME).7z
PACKAGE_TAR_GZ := $(ARCHIVE_BASENAME).tar.gz
PACKAGES := $(PACKAGE_7Z) $(PACKAGE_TAR_GZ)
PACKAGE_INPUTS := $(TTFS) $(BITMAPS)

.PHONY: build package fonts bitmaps majority-bitmaps average-bitmaps bitmap-dirs check-tools clean-generated

build: package

package: check-tools $(PACKAGES)

fonts: $(TTFS)

bitmaps: majority-bitmaps average-bitmaps

majority-bitmaps: $(MAJORITY_BITMAPS)

average-bitmaps: $(AVERAGE_BITMAPS)

bitmap-dirs: $(BITMAP_DIRS)

check-tools:
	@command -v $(PYTHON) >/dev/null
	@command -v $(FONTFORGE) >/dev/null
	@command -v $(SEVENZ) >/dev/null
	@command -v $(TAR) >/dev/null
	@command -v $(GZIP) >/dev/null

$(IBM_VGA_TTF): $(IBM_VGA_SRC) $(BUILD_IBM_VGA_TTF) $(BUILD_DF12_TTF)
	$(PYTHON) $(BUILD_IBM_VGA_TTF)

$(DF12_TTF): $(DF12_SRC) $(BUILD_DF12_TTF)
	$(PYTHON) $(BUILD_DF12_TTF)

$(DF14_TTF): $(DF14_SRC) $(BUILD_DF14_TTF) $(BUILD_DF12_TTF)
	$(PYTHON) $(BUILD_DF14_TTF)

$(PACKAGE_7Z): $(PACKAGE_INPUTS)
	$(RM) "$@"
	$(SEVENZ) a -t7z "$@" $(PACKAGE_INPUTS)

$(PACKAGE_TAR_GZ): $(PACKAGE_INPUTS)
	$(RM) "$@"
	$(TAR) -czf "$@" $(PACKAGE_INPUTS)

define DEFINE_BITMAP_RULE
$(1): $(2) $(RASTERIZE_SVG) | $(3)
	$$(PYTHON) $$(RASTERIZE_SVG) "$$<" $(4) $(4) "$$@" $(strip --mode $(5) $(6))
endef

$(foreach size,$(IBM_VGA_MULTIPLE_SIZES),$(eval $(call DEFINE_BITMAP_RULE,$(IBM_VGA_MAJORITY_DIR)/$(IBM_VGA_BITMAP_PREFIX)_majority_$(size)x$(size).bmp,$(IBM_VGA_SRC),$(IBM_VGA_MAJORITY_DIR),$(size),majority,)))
$(foreach size,$(IBM_VGA_NONMULTIPLE_SIZES),$(eval $(call DEFINE_BITMAP_RULE,$(IBM_VGA_MAJORITY_NONMULTIPLES_DIR)/$(IBM_VGA_BITMAP_PREFIX)_majority_$(size)x$(size).bmp,$(IBM_VGA_SRC),$(IBM_VGA_MAJORITY_NONMULTIPLES_DIR),$(size),majority,)))
$(foreach size,$(IBM_VGA_MULTIPLE_SIZES),$(eval $(call DEFINE_BITMAP_RULE,$(IBM_VGA_AVERAGE_DIR)/$(IBM_VGA_BITMAP_PREFIX)_average_$(size)x$(size).png,$(IBM_VGA_SRC),$(IBM_VGA_AVERAGE_DIR),$(size),average,--transparent-background)))
$(foreach size,$(IBM_VGA_NONMULTIPLE_SIZES),$(eval $(call DEFINE_BITMAP_RULE,$(IBM_VGA_AVERAGE_NONMULTIPLES_DIR)/$(IBM_VGA_BITMAP_PREFIX)_average_$(size)x$(size).png,$(IBM_VGA_SRC),$(IBM_VGA_AVERAGE_NONMULTIPLES_DIR),$(size),average,--transparent-background)))

$(foreach size,$(DF12_MULTIPLE_SIZES),$(eval $(call DEFINE_BITMAP_RULE,$(DF12_MAJORITY_DIR)/$(DF12_BITMAP_PREFIX)_majority_$(size)x$(size).bmp,$(DF12_SRC),$(DF12_MAJORITY_DIR),$(size),majority,)))
$(foreach size,$(DF12_NONMULTIPLE_SIZES),$(eval $(call DEFINE_BITMAP_RULE,$(DF12_MAJORITY_NONMULTIPLES_DIR)/$(DF12_BITMAP_PREFIX)_majority_$(size)x$(size).bmp,$(DF12_SRC),$(DF12_MAJORITY_NONMULTIPLES_DIR),$(size),majority,)))
$(foreach size,$(DF12_MULTIPLE_SIZES),$(eval $(call DEFINE_BITMAP_RULE,$(DF12_AVERAGE_DIR)/$(DF12_BITMAP_PREFIX)_average_$(size)x$(size).png,$(DF12_SRC),$(DF12_AVERAGE_DIR),$(size),average,--transparent-background)))
$(foreach size,$(DF12_NONMULTIPLE_SIZES),$(eval $(call DEFINE_BITMAP_RULE,$(DF12_AVERAGE_NONMULTIPLES_DIR)/$(DF12_BITMAP_PREFIX)_average_$(size)x$(size).png,$(DF12_SRC),$(DF12_AVERAGE_NONMULTIPLES_DIR),$(size),average,--transparent-background)))

$(foreach size,$(DF14_MULTIPLE_SIZES),$(eval $(call DEFINE_BITMAP_RULE,$(DF14_MAJORITY_DIR)/$(DF14_BITMAP_PREFIX)_majority_$(size)x$(size).bmp,$(DF14_SRC),$(DF14_MAJORITY_DIR),$(size),majority,)))
$(foreach size,$(DF14_NONMULTIPLE_SIZES),$(eval $(call DEFINE_BITMAP_RULE,$(DF14_MAJORITY_NONMULTIPLES_DIR)/$(DF14_BITMAP_PREFIX)_majority_$(size)x$(size).bmp,$(DF14_SRC),$(DF14_MAJORITY_NONMULTIPLES_DIR),$(size),majority,)))
$(foreach size,$(DF14_MULTIPLE_SIZES),$(eval $(call DEFINE_BITMAP_RULE,$(DF14_AVERAGE_DIR)/$(DF14_BITMAP_PREFIX)_average_$(size)x$(size).png,$(DF14_SRC),$(DF14_AVERAGE_DIR),$(size),average,--transparent-background)))
$(foreach size,$(DF14_NONMULTIPLE_SIZES),$(eval $(call DEFINE_BITMAP_RULE,$(DF14_AVERAGE_NONMULTIPLES_DIR)/$(DF14_BITMAP_PREFIX)_average_$(size)x$(size).png,$(DF14_SRC),$(DF14_AVERAGE_NONMULTIPLES_DIR),$(size),average,--transparent-background)))

$(BITMAP_DIRS):
	mkdir -p "$@"

clean-generated:
	rm -rf bmp_ibm-vga-14x14 bmp_df-12x12 bmp_df-14x14 $(PACKAGES)
