import typing


def listiter(data: list, extra, num: int = 1):
	for item in data:
		yield item
	for n in range(num):
		yield extra


def safe_index(iter, key, ret_iter: bool = False):
	if "__contains__" in dir(iter):
		try:
			if ret_iter:
				if key >= len(iter):
					return listiter(iter, 0, 1 + key - len(iter))
				elif key < 0:
					raise ValueError
				return iter
			return iter[key]
		except IndexError:
			if ret_iter:
				if key >= len(iter):
					return listiter(iter, 0, 1 + key - len(iter))
				elif key < 0:
					raise ValueError
			return type(iter[0])(0)

	elif "fromkeys" in dir(iter):
		try:
			if ret_iter:
				return iter
			return iter[key]
		except KeyError:
			if type(iter) != dict:
				raise TypeError
			iter[key] = type(iter[list(iter.keys())[0]])()
			if ret_iter:
				return iter
			else:
				return iter[key]
	else:
		raise TypeError


class ReadBytes:
	def __init__(self, bytestr: bytes, pointers=("default", )):
		self.original = bytestr
		self.bytestr = bytestr
		self.where = {n: 0 for n in pointers}
		self.default = pointers[0]

	def read(self, amt: typing.Optional[int] = None, point=None, back: typing.Optional[int] = 0, advance: bool = True):
		if type(amt) is str:
			point = amt
			amt = 1
		elif point is None:
			point = self.default
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

	def write(self, byte: bytes, point=None, back: typing.Optional[int] = 0, advance: bool = True, overwrite=True):
		if point is None:
			point = self.default
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

	def seek(self, amt, offset=0, point=None):
		if point is None:
			point = self.default
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

	def tell(self, point=None):
		if point is None:
			point = self.default
		return self.where[point]

	def restore(self, reset_points=()):
		self.bytestr = self.original
		if "__contains__" in dir(reset_points):
			if reset_points == ():
				reset_points = self.default
		else:
			reset_points = list((reset_points,))
		print(reset_points)
		for point in [reset_points]:
			self.where[point] = 0

	def branch(self, *points):
		if "__contains__" not in dir(points):
			points = [points]
		self.where = {**self.where, **{n: 0 for n in points}}

	def show(self):
		return self.bytestr
