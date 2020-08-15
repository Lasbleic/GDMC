from __future__ import division
from generation.generators import Generator
from utils import TransformBox, Point2D, euclidean
from utilityFunctions import setBlock, raytrace


class Bridge(Generator):

    def __init__(self, edge, origin):
        # type: (Point2D, Point2D) -> None
        assert isinstance(edge, Point2D) and isinstance(origin, Point2D)
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
        self.__straighten_bridge_points()
        o1, o2 = self.__points[0], self.__points[-1]  # type: Point2D, Point2D
        om = self.__points[len(self.__points)//2]
        length = euclidean(o1, o2) + 1
        try:
            y1, y2 = height_map[o1.x, o1.z] + 1, height_map[o2.x, o2.z] + 1
        except IndexError:
            return

        def base_height(_d):
            # y1 when d = 0, y2 when d = length
            return y1 + _d/length * (y2 - y1)

        def curv_height(_d):
            # 0 in d = 0 & d = length, 0.5 derivative in 0
            cst1 = 1 / length  # steepness constraint
            cst2 = (4/length**2) * (67 - base_height(length/2))  # bridge height constraint
            cst = max(0, min(cst1, cst2))
            return cst * _d * (length - _d)

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

    def __straighten_bridge_points(self):
        def my_round(v):
            return int(round(v))
        o1, o2 = self.__points[0], self.__points[-1]
        if o1.x == o2.x:
            self.__points = [Point2D(o1.x, _) for _ in range(o1.z, o2.z)] + [o2]
        elif o1.z == o2.z:
            self.__points = [Point2D(_, o1.z) for _ in range(o1.x, o2.x)] + [o2]
        else:
            self.__points = [Point2D(p[0], p[2]) for p in raytrace((o1.x, 0, o1.z), (o2.x, 0, o2.z))]
        # elif self.width > self.length:
        #     # bridge z = int(f(x))
        #     a = (o2.z - o1.z) / (o2.x - o1.x)
        #     b = (o1.z * o2.x - o2.z * o1.x) / (o2.x - o1.x)
        #     self.__points = [Point2D(x, my_round(a*x + b)) for x in range(o1.x, o2.x)]
        # else:
        #     # bridge x = int(f(z))
        #     a = (o2.x - o1.x) / (o2.z - o1.z)
        #     b = (o1.x * o2.z - o2.x * o1.z) / (o2.z - o1.z)
        #     self.__points = [Point2D(my_round(a*z + b), z) for z in range(o1.z, o2.z)]
        # self.__points.append(o2)  # o2 is excluded from the ranges
