import typing

class ReadBytes:
	def __init__(self, bytestr: bytes, pointers=1):
		self.bytestr = bytestr
		self.where = [0] * pointers

	def read(self, amt: typing.Optional[int] = None, point=0, back: typing.Optional[int] = 0, advance: bool = True):
		if (amt is None) or (amt < 1):
			return self.bytestr
		where = self.where[point]
		f = where - back
		if f < 0:
			f = 0
		l = where + amt
		if l > len(self.bytestr):
			l = len(self.bytestr)
		if advance:
			self.where[point] += l - f
		return self.bytestr[f:l]

	def write(self, byte: bytes, point=0, back: typing.Optional[int] = 0, advance: bool = True, overwrite=True):
		where = self.where[point]
		f = where - back
		if f < 0:
			f = 0
		l = f + len(byte)
		if l > len(self.bytestr):
			l = len(self.bytestr)
		if overwrite:
			self.bytestr = self.bytestr[:f] + byte + self.bytestr[l:]
			if advance:
				self.where[point] += l - f
		else:
			self.bytestr = self.bytestr[:f+1] + byte + self.bytestr[f+1:]
			if advance:
				for p in self.where:
					if p >= self.where[point]:
						self.where[p] += len(byte)
		return self.where[point]

	def seek(self, amt, offset=0, point=0):
		if offset == 0:
			self.where[point] = amt
		elif offset == 1:
			self.where[point] += amt
		elif offset == 2:
			self.where[point] = len(self.bytestr) - amt
		else:
			self.where[point] = amt
		if self.where[point] > len(self.bytestr):
			self.where[point] = len(self.bytestr)
		elif self.where[point] < 0:
			self.where[point] = 0
		return self.where[point]

	def tell(self, point=0):
		return self.where[point]
