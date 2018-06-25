"""
>                             Indexed Palette Image format spec                            <
>------------------------------------------------------------------------------------------<
> Designed for pixel art
> File is encoded as a palette number and index
> All data is big-endian encoded
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
>     | layer in use byte (all 0s or all 1s to enable or disable respectively, if disabled, layer must have no following bytes)
>     | index byte  (end nibble is used)
>     | tile mode byte (normal is all zeros, tiled is all ones)
>     | color mode byte (end nibble is used)
>     | opacity byte
>     | vertical position byte, later layers are put on top of earlier layers in the event of a shared position
>     | if normal mode: layer height, represented in two bytes with the leftmost nibble ignored, for a maximum of 4096 pixels on edge
>     | if normal mode: layer width, represented in two bytes with the leftmost nibble ignored, for a maximum of 4096 pixels on edge
>     | if tiled mode: tile height byte, with a maximum of 256 pixels on edge
>     | if tiled mode: tile width byte, with a maximum of 256 pixels on edge
>     | if tiled mode: tiles are stored left-to-right top-to-bottom for each tile and left-to-right top-to-bottom for each pixel with 256 tiles on each edge
>     | start position of that layer's image data "IMD", represented in 8 bytes, 8 byte pointer allows for a maximum file size of approx 4.25 gigabytes
>     | PLT
>     | name of layer
>     | twice of 00000001 10010111, 00000000 11100111 11010000 00000000 (01 97 00 e7 d0 00 - 0 LYT 00 END 000)
> CLI Flags
>     | -m -8b  -8     8bit mode, allocates 1,536 bytes for palettes
>     | -M -16b -16    16bit mode, allocates 393,216 bytes for palettes
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
import numpy as np
import typing
import bitstring
import codecs
import math


class FileTypeError(Exception):
	__slots__ = ["message"]

	def __init__(self, message):
		self.message = message

	def __repr__(self):
		return "FileTypeError: " + self.message


class HeaderByteError(Exception):
	__slots__ = ["message"]

	def __init__(self, message):
		self.message = message

	def __repr__(self):
		return "HeaderByteError: " + self.message


class UnfinishedCodeError(Exception):
	__slots__ = ["message"]

	def __init__(self, message):
		self.message = message

	def __repr__(self):
		return "UnfinishedCodeError: " + self.message


def inis(x, y):
	try:
		return x in y
	except TypeError:
		return x == y


def in_ranges(value, *ranges):
	if any([inis(value, v) for v in ranges]):
		return True
	return False


def delist(list):
	if len(list) == 1:
		return list[0]
	return list


def only_zo(bits: str):
	return "".join([n if n in ("0", "1") else "" for n in bits])


"""
def b(bits, splitchar=" "):
	return str.encode("".join([chr(int(bit, 2)) for bit in bits.split(splitchar)]))
# """


def b(bits: str):
	n = int(only_zo(bits), 2)
	L = len(hex(n)) - 2
	s = f'{n:0>{L + L % 2}X}'
	return codecs.decode(s, "hex-codec")


sb = b


def ib(num: int):
	L = len(hex(num)) - 2
	s = f'{num:0>{L + L % 2}X}'
	return codecs.decode(s, "hex-codec")


def hexsb(num: str):
	L = len(num) - 2
	s = f'{num:0>{L + L % 2}}'
	return codecs.decode(s, "hex-codec")


def byte_sum(bits: bytes):
	L = list(bits)
	return sum([n * m for n, m in zip(L, [2 ** (n * 8) for n in range(len(list(L)))][::-1])])


"""
def sb(bits, splitchar=" "):
	return str.encode(chr(int(bits.replace(splitchar, ""), 2)))
# """


def bytecolor_to_rgb(bits: bytes):
	print(bits, list(bits))
	r1, r2, g1, g2, b1, b2 = list(bits)
	return 256 * r1 + r2, 256 * g1 + g2, 256 * b1 + b2


def erange(min, max, sep):
	current = min
	its = 0
	while current <= max:
		yield min + its * sep
		current += sep
		its += 1
		if current >= max:
			yield max


def itersplit(data, size, with_remainder=True):
	if with_remainder:
		first = range(0, len(data) + 1, size)
		last = erange(size - 1, len(data) + 1, size)
	else:
		first = range(0, len(data) + 1, size)[:-1]
		last = range(size - 1, len(data) + 1, size)
	return [data[n[0]:n[1] + 1] for n in zip(first, last)]


""" rewrite
def split_bytes(bits: bytes, split_to=None, more_than_byte=False):
	if split_to is None:
		return [str.encode(chr(bit)) for bit in bits]
	elif split_to < 2:
		return bits
	elif split_to == len(bits):
		return [str.encode(chr(n)) for n in list(bits)]
	else:
		if more_than_byte:
			bit_list = bitstring.BitArray(bits).bin
			len_new = len(bit_list) // split_to
			chopped = [r for r in itersplit(bit_list, len_new) if r != ""]
			return [str.encode(chr(int(n, 2))) for n in chopped]
		else:
			bit_list = bitstring.BitArray(bits).bin
			len_new = len(bit_list) // split_to
			chopped = [itersplit(r, 8) for r in itersplit(bit_list, len_new) if r != ""]
			return [[str.encode(chr(int(m, 2))) for m in n] for n in chopped]
# """


zeros = b("00000000")
ones = b("11111111")
one = b("00000001")

oooooooo = zeros
llllllll = ones

oooollll = b("00001111")
lllloooo = b("11110000")

oollooll = b("00110011")
lloolloo = b("11001100")

olololol = b("01010101")
lolololo = b("10101010")


class IPI:
	def __init__(self, filename: typing.Optional[str] = None):
		self.LYT = [
			{
				"enable":       0,
				"tile_mode":    "",
				"color_mode":   "",
				"opacity":      0,
				"vertical_pos": 0,
				"height":       0,
				"width":        0,
				"IMD_pos":      0,
				"PLT":          [],
				"name&info":    ""
			}
		] * 16
		self.IMD = [
			{
				"enable":       0,
				"height":       0,
				"width":        0,
				"tile_mode":    "",
				"tiles":        [],
				"img":          np.zeros((1, 1, 1), dtype=np.int32)
			}
		] * 16
		self.colormode_dict = {1: [6, 2], 2: [5, 3], 3: [4, 4], 4: [3, 5], 8: [13, 3], 9: [12, 4], 10: [11, 5], 11: [10, 6], 12: [9, 7], 13: [8, 8]}
		if filename:
			self.open(filename)

	def open(self, filename):
		with open(filename, mode='rb') as input_file:
			magic_number = input_file.read(4)
			if magic_number != b"ipi1":
				raise FileTypeError("not an ipi file or header is damaged")
			version = input_file.read(1)
			print(version)
			if version in [b'\x00', b'\x01', b'\x80', b'\x81']:
				if version >= b"\x80":
					self.decode_v1(filename, True)
				else:
					self.decode_v1(filename, False)

	def decode_v1(self, filename, compressed=False):
		with open(filename, mode='rb') as input_file:
			_ = input_file.read(5)
			enabled_written = []

			for n in range(16):
				layer_in_use = input_file.read(1)
				index = int(input_file.read(1)[4:], 2)

				if index in enabled_written:  # this avoids overwriting layers
					continue
				if layer_in_use == zeros:
					self.LYT[index]["enable"] = 0
					self.IMD[index]["enable"] = 0
					continue
				elif (layer_in_use == ones) or (layer_in_use == one):
					self.LYT[index]["enable"] = 1
					self.IMD[index]["enable"] = 1
					enabled_written += [index]
				else:
					raise HeaderByteError("enable byte toggle is not a valid option, header may be damaged")

				tilemode = input_file.read(1)
				colormode = int(input_file.read(1)[4:], 2)

				if tilemode == zeros:
					self.LYT[index]["tile_mode"] = "normal"
					self.IMD[index]["tile_mode"] = "normal"
				elif tilemode == ones:
					self.LYT[index]["tile_mode"] = "tiles"
					self.IMD[index]["tile_mode"] = "tiles"
				elif tilemode == one:
					self.LYT[index]["tile_mode"] = "tiles"
					self.IMD[index]["tile_mode"] = "tiles"
				else:
					raise HeaderByteError("tilemode byte toggle is not a valid option, header may be damaged")

				if not in_ranges(colormode, range(1, 5), range(8, 14)):
					raise HeaderByteError("colormode byte is not a valid option, header may be damaged")
				self.LYT[index]["color_mode"] = colormode

				self.LYT[index]["opacity"] = int(input_file.read(1), 2) % 16
				self.LYT[index]["vertical_pos"] = int(input_file.read(1), 2) % 256

				if tilemode == "normal":
					self.IMD[index]["height"] = self.LYT[index]["height"] = int(input_file.read(2), 2) % 4096
					self.IMD[index]["width"] = self.LYT[index]["width"] = int(input_file.read(2), 2) % 4096
				elif tilemode == "tiles":
					self.IMD[index]["height"] = self.LYT[index]["height"] = int(input_file.read(1), 2)
					self.IMD[index]["width"] = self.LYT[index]["width"] = int(input_file.read(1), 2)

				pal_num = self.colormode_dict[colormode][0]
				clr_num = self.colormode_dict[colormode][1]
				imd_pos = list(input_file.read(8))

				self.LYT[index]["IMD_pos"] = sum([n * m for n, m in zip(imd_pos, [2 ** (n * 8) for n in range(len(imd_pos))][::-1])])
				self.LYT[index]["PLT"] = []
				for n in range(pal_num):
					self.LYT[index]["PLT"][n] = [bytecolor_to_rgb(input_file.read(6)) for _ in range(clr_num)]

				textbyte = b""
				textstr = b""
				while textbyte != b"00000001 10010111, 00000000 11100111 11010000 00000000" * 2:  # (01 97 00 e7 d0 00 - 0 LYT 00 END 000)
					textbyte = input_file.read(2)
					if textbyte != b"00000001 10010111, 00000000 11100111 11010000 00000000" * 2:
						textstr = textstr + textbyte

		if not compressed:
			with open(filename, mode='rb') as input_file:
				for i, file in enumerate(self.LYT):

					if not self.LYT[i]["enable"]:
						continue

					pos = self.LYT[i]["IMD_pos"]
					cmode = self.LYT[i]["color_mode"]
					tmode = self.LYT[i]["tile_mode"]
					width = self.LYT[i]["width"]
					height = self.LYT[i]["height"]

					input_file.seek(pos)

					if tmode == "tiles":
						for z in range(256 * 256):
							img_array = np.zeros((height, width, 2), dtype=np.int32)

							for y in range(height):
								for x in range(width):

									if cmode >= 8:
										clr_raw = input_file.read(2)
									else:
										clr_raw = input_file.read(1)

									pal_n = self.colormode_dict[cmode][0]
									pal_data = byte_sum(b(bitstring.BitArray(clr_raw[:pal_n]).bin))
									clr_data = byte_sum(b(bitstring.BitArray(clr_raw[pal_n:]).bin))
									img_array[y][x][0] = pal_data
									img_array[y][x][1] = clr_data

							self.IMD[i]["tiles"][z] = img_array

					elif tmode == "normal":
						img_array = np.zeros((height, width, 2), dtype=np.int32)

						for y in range(height):
							for x in range(width):

								if cmode >= 8:
									clr_raw = input_file.read(2)
								else:
									clr_raw = input_file.read(1)

								pal_n = self.colormode_dict[cmode][0]
								pal_data = byte_sum(b(bitstring.BitArray(clr_raw[:pal_n]).bin))
								clr_data = byte_sum(b(bitstring.BitArray(clr_raw[pal_n:]).bin))
								img_array[y][x][0] = pal_data
								img_array[y][x][1] = clr_data

						self.IMD[i]["img"] = img_array

					input_file.seek(0)

		else:
			"""a
			with open(filename, mode='rb') as input_file:
				for i, file in enumerate(self.LYT):

					if not self.LYT[i]["enable"]:
						continue

					pos = self.LYT[i]["IMD_pos"]
					cmode = self.LYT[i]["color_mode"]
					tmode = self.LYT[i]["tile_mode"]
					width = self.LYT[i]["width"]
					height = self.LYT[i]["height"]

					input_file.seek(pos)

					if tmode == "tiles":
						for z in range(256 * 256):
							img_array = np.zeros((height, width, 2), dtype=np.int32)

							for y in range(height):
								for x in range(width):

									if cmode >= 8:
										clr_raw = input_file.read(2)
									else:
										clr_raw = input_file.read(1)

									pal_n = self.colormode_dict[cmode][0]
									pal_data = byte_sum(b(bitstring.BitArray(clr_raw[:pal_n]).bin))
									clr_data = byte_sum(b(bitstring.BitArray(clr_raw[pal_n:]).bin))
									img_array[y][x][0] = pal_data
									img_array[y][x][1] = clr_data

							self.IMD[i]["tiles"][z] = img_array

					elif tmode == "normal":
						img_array = np.zeros((height, width, 2), dtype=np.int32)

						for y in range(height):
							for x in range(width):

								if cmode >= 8:
									clr_raw = input_file.read(2)
								else:
									clr_raw = input_file.read(1)

								pal_n = self.colormode_dict[cmode][0]
								pal_data = byte_sum(b(bitstring.BitArray(clr_raw[:pal_n]).bin))
								clr_data = byte_sum(b(bitstring.BitArray(clr_raw[pal_n:]).bin))
								img_array[y][x][0] = pal_data
								img_array[y][x][1] = clr_data

						self.IMD[i]["img"] = img_array

					input_file.seek(0)
			# """
			raise UnfinishedCodeError("compressed files not supported")

	def write(self, filename):
		pass


if len(sys.argv) > 1:
	inputs = [f.lower() if f.startswith("-") and ("m" not in f.lower()) else f for f in list(set(sys.argv[1:]))]

	file_in = [bool(len(str(flag).split(".")) - 1) for flag in inputs]

	file_in_condensed = list(set(file_in))
	has_file = file_in_condensed[0] or file_in_condensed[1]

	if has_file:
		file = [inputs[i] for i, f in enumerate(file_in) if f is True][0]
	else:
		file = None

	if has_file and ("-o" in inputs):
		pass
	elif has_file and ("-i" in inputs):
		pass
	elif has_file:
		created_file = IPI(file)
	else:
		pass
