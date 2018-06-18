"""
>                             Indexed Palette Image format spec                            <
>------------------------------------------------------------------------------------------<
> Designed for pixel art
> File is encoded as a palette number and index
> there are a few encodings
>     |
>     | 8 bit:  | PP-PP-PP-II         | palettes:   64 indices:   4 | mode nibble: 0001
>     | 8 bit:  | PP-PP-PI-II         | palettes:   32 indices:   8 | mode nibble: 0010
>     | 8 bit:  | PP-PP-II-II         | palettes:   16 indices:  16 | mode nibble: 0011
>     | 8 bit:  | PP-PI-II-II         | palettes:    8 indices:  32 | mode nibble: 0100
>     |         |                     |                             |
>     | 16 bit: | PPPP-PPPP-PPPP-PIII | palettes: 8192 indices:   8 | mode nibble: 1000
>     | 16 bit: | PPPP-PPPP-PPPP-IIII | palettes: 4096 indices:  16 | mode nibble: 1001
>     | 16 bit: | PPPP-PPPP-PPPI-IIII | palettes: 2048 indices:  32 | mode nibble: 1010
>     | 16 bit: | PPPP-PPPP-PPII-IIII | palettes: 1024 indices:  64 | mode nibble: 1011
>     | 16 bit: | PPPP-PPPP-PIII-IIII | palettes:  512 indices: 128 | mode nibble: 1100
>     | 16 bit: | PPPP-PPPP-IIII-IIII | palettes:  256 indices: 256 | mode nibble: 1101
>     |
> the 0th index of every palette is transparent black
> all colors are fully opaque
> it is 16 bit color, so two bytes per channel per palette index in the palette table
> separate layers, if implemented, may have their own set of palettes as well as a percent opacity
> Sample header:
>     | 01101001 01110000 01101001 00110001 ( ipi1 in ascii binary )
>     -----------------------------------------
>     | version byte
>     --- LYT --- per layer (16 total) --------
>     | index nibble
>     | tile mode nibble (normal is 0000, tiled is 1111)
>     | zeros nibble
>     | color mode nibble
>     | opacity byte
>     | vertical position byte, later layers are put on top of earlier layers in the event of a shared position
>     | if normal mode: layer height, represented in 3 nibbles, for a maximum of 4096 pixels on edge
>     | if normal mode: layer width, represented in 3 nibbles, for a maximum of 4096 pixels on edge
>     | if tiled mode: tile height byte
>     | if tiled mode: tile width byte
>     | if tiled mode: tiles are stored left-to-right top-to-bottom for each tile and left-to-right top-to-bottom for each pixel with 256 tiles on each edge
>     | start position of that layer's image data "IMD", represented in 8 bytes, 8 byte pointer allows for a maximum file size of approx 4.25 gigabytes
>     | PLT
>     | name of layer
>     | 4 bytes of 0101-0101
> CLI Flags
>     | -m -8b  -8     8bit mode, allocates 12,288 bytes for palettes
>     | -M -16b -16    16bit mode, allocates 3,145,728 bytes for palettes
>     | -h -H   -help  prints help text
>     | -L             prealloc maximum image dimensions possible 4096x4096, original is top left if supplied, this will take up over 0.25 gigabytes in 16bit mode
>     | -u -U  -up     upgrades 8bit ipi to 16bit, refactors image (or layers), takes input on what mode to switch to
>     | -d -D -down    downgrades 16bit ipi to 8bit, refactors image (or layers), takes input on what mode to switch to
>     | -smart         if passed with -d scans image (or layers) for palette usage to decide which to remove, refactors image (or layers)
>     | -r -R          refactor palettes, takes input on what mode to switch to
>     | -o -O          output to image
>     | -i -I          input from image
>     | -c -C          compress input image or compresses output ipi if passed with -i
"""

import sys
import os
import numpy

inputs = [f.lower() if f.startswith("-") and ("m" not in f.lower()) else f for f in list(set(sys.argv[1:]))]

file_in = [
			bool(
				len(
					str(flag)
					.split(".")
					) - 1)
			for flag in inputs]

file_in_condensed = list(set(file_in))
has_file = file_in_condensed[0] or file_in_condensed[1]

if has_file:
	file = [inputs[i] for i, f in enumerate(file_in) if f is True]
else:
	file = None

if has_file and ("-o" in inputs):
	pass

if has_file and ("-i" in inputs):
	pass


def header2bytes():
	pass


def bytes2header(bytes):
	version = 0
	LYT = [
		{
			"tile_mode": 0,
			"opacity": 0,
			"vertical_pos": 0,
			"height": 0,
			"width": 0,
			"color_mode": 0,
			"IMD_pos": 0,
			"PLT": [],
			"name": 0
		}
	]
	IMD = [
		{
			"tile_mode": 0,
			"tiles": [],
			"img": 0
		}
	]
	return version, LYT, IMD
