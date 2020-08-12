from __future__ import division
from generation.generators import Generator
from utils import TransformBox, Point2D, euclidean
from utilityFunctions import setBlock


class Bridge(Generator):

    def __init__(self, edge, origin):
        # type: (Point2D, Point2D) -> None
        init_box = TransformBox((edge.x, 0, edge.z), (1, 1, 1))
        Generator.__init__(self, init_box, edge)
        self.__points = [edge]
        self.__origin = origin

    def __iadd__(self, other):
        assert isinstance(other, Point2D)
        self.__points.append(other)
        self._box = self._box.union(TransformBox((other.x, 0, other.z), (1, 1, 1)))
        return self

    def generate(self, level, height_map=None, palette=None):
        # todo: draw a cleaner curve / line
        self._box = TransformBox(self._box)
        self.translate(dx=self.__origin.x, dz=self.__origin.z)
        o1, o2 = self.__points[0], self.__points[-1]  # type: Point2D, Point2D
        length = euclidean(o1, o2) + 1
        y1, y2 = height_map[o1.x, o1.z] + 1, height_map[o2.x, o2.z] + 1

        def base_height(_d):
            # y1 when d = 0, y2 when d = length
            return y1 + _d/length * (y2 - y1)

        def curv_height(_d):
            # 0 in d = 0 & d = length, 0.5 derivative in 0
            cst = -1 / length
            return cst * _d * (_d - length)

        for p in self.__points:
            d = euclidean(p, o1)
            interpol1 = base_height(d) + curv_height(d)
            interpol2 = base_height(d+1) + curv_height(d+1)
            ap = p + self.__origin
            self.place_block(level, ap.x, interpol1, interpol2, ap.z)

    @property
    def width(self):
        return abs(self.__points[-1].x - self.__points[0].x)

    @property
    def length(self):
        return abs(self.__points[-1].z - self.__points[0].z)

    def place_block(self, level, x, y1, y2, z):
        if y1 > y2:
            y1, y2 = y2, y1

        def get_stair_orientation(xs, zs):
            if self.width > self.length:
                return 0 if xs < (self._box.minx + self.width / 2) else 1
            else:
                return 2 if zs < (self._box.minz + self.length / 2) else 3

        def my_round(v):
            d, r = v // 1, v % 1
            rounded = 0 if r < 1/3 else 0.5 if r < 2/3 else 1
            return d + rounded

        r1, r2 = my_round(2*y1)/2, my_round(2*y2)/2
        print(r1, r2)
        y = int(r1)
        if r2 - r1 <= 1/2 and y2 - y1 <= 2/3:
            if r1 - int(r1) == 0:
                b_id, b_data = 44, 5
            else:
                b_id, b_data = 44, 13
        else:
            if r1 - int(r1) == 0:
                b_id, b_data = 109, get_stair_orientation(x, z)
            else:
                b_id, b_data = 44, 5
                y += 1

        if self.width > self.length:
            for dz in range(-1, 2):
                setBlock(level, (b_id, b_data), x, y, z + dz)
        else:

            for dx in range(-1, 2):
                setBlock(level, (b_id, b_data), x + dx, y, z)
