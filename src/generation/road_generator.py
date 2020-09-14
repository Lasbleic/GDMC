from __future__ import division, print_function

from math import ceil
from time import sleep

from numpy.random.mtrand import choice
from typing import List

from generation.generators import Generator, Materials
from pymclevel import MCInfdevOldLevel
from pymclevel.block_fill import fillBlocks
from pymclevel.materials import Block
from utils import TransformBox, Point2D, euclidean, sym_range, product, clear_tree_at, bernouilli, place_torch, \
    Direction
from utilityFunctions import setBlock, raytrace
from numpy import full, zeros, uint8, array, mean


class RoadGenerator(Generator):

    # stony_palette_str = ["Cobblestone", "Gravel", "Stone"]
    # stony_probs = [0.75, 0.20, 0.05]
    stony_palette = {"Cobblestone": 0.7, "Gravel": 0.2, "Stone": 0.1}

    def __init__(self, network, box, maps):
        # type: (RoadNetwork, TransformBox, map.Maps) -> None
        Generator.__init__(self, box)
        self.__network = network  # type: RoadNetwork
        self.__fluids = maps.fluid_map
        self.__maps = maps
        self.__origin = Point2D(box.minx, box.minz)

    def generate(self, level, height_map=None, palette=None):
        # type: (MCInfdevOldLevel, array, dict) -> None

        print("[RoadGenerator] generating road blocks...", end='')
        Generator.generate(self, level, height_map)  # generate bridges

        road_height_map = zeros(height_map.shape, dtype=uint8)
        __network = full((self.width, self.length), Materials.Air)
        x0, y0, z0 = self._box.origin
        sleep(.001)

        for road_block in self.__network.road_blocks.union(self.__network.special_road_blocks):
            road_width = (self.__network.calculate_road_width(road_block.x, road_block.z) - 1) / 2.0
            # road_width = 0
            # todo: flatten roads & use stairs/slabs + richer block palette
            for x in sym_range(road_block.x, road_width, self.width):
                for z in sym_range(road_block.z, road_width, self.length):
                    if road_height_map[x, z] or road_height_map[x, z] > 0:
                        # if x, z is a road point or has already been computed, no need to do it now
                        continue
                    clear_tree_at(level, self._box, Point2D(x + x0, z + z0))
                    if not self.__fluids.is_water(x, z):
                        distance = abs(road_block.x - x) + abs(road_block.z - z)
                        prob = distance / (8 * road_width)
                        # if not bernouilli(prob):
                        if True:
                            y, b = self.__compute_road_at(x, z, height_map, road_block)
                            __network[x, z] = b
                            road_height_map[x, z] = y

        for x in range(self.width):
            for z in range(self.length):
                if road_height_map[x, z]:
                    y, b = road_height_map[x, z], __network[x, z]
                    setBlock(level, (b.ID, b.blockData), x0 + x, y, z0 + z)
                    if bernouilli(0.08):
                        place_torch(level, x + x0, y + 1, z + z0)
                    else:
                        fillBlocks(level, TransformBox((x0+x, y+1, z0+z), (1, 2, 1)), Materials.Air)
                    h = height_map[x, z]
                    if y > h:
                        pole_box = TransformBox((x, h, z), (1, y-h, 1))
                        fillBlocks(level, pole_box, Materials["Stone Bricks"])
        print("OK")

    def __compute_road_at(self, x, z, height_map, r):
        # type: (int, int, array, Point2D) -> (int, Block)
        material = choice(self.stony_palette.keys(), p=self.stony_palette.values())

        def inc(l):
            # return all(l[i+1] > l[i] for i in range(len(l)-1))
            return l[0] <= l[1] < l[2] or l[0] < l[1] <= l[2]

        def dec(l):
            # return all(l[i+1] < l[i] for i in range(len(l)-1))
            return l[0] > l[1] >= l[2] or l[0] >= l[1] > l[2]
        # if abs(r.x-x) <= 1 and abs(r.z-z) <= 1:
        #     r = Point2D(x, z)
        # surrnd_road_xh = [height_map[_, r.z] for _ in sym_range(r.x, 1, self.width) if self.__network.is_road(_, r.z)]
        # surrnd_road_zh = [height_map[r.x, _] for _ in sym_range(r.z, 1, self.length) if self.__network.is_road(r.x, _)]

        # surrnd_road_xh = [height_map[_, z] for _ in sym_range(x, 1, self.width) if self.__network.is_road(_, z)]
        # surrnd_road_zh = [height_map[x, _] for _ in sym_range(z, 1, self.length) if self.__network.is_road(x, _)]

        # y = height_map[r.x, r.z]
        stair_material = choice(["Cobblestone", "Stone Brick"])
        # lx, lz, sx, sz = len(surrnd_road_xh), len(surrnd_road_zh), std(surrnd_road_xh), std(surrnd_road_zh)
        # if (lx >= 3) and ((lx > lz) or sx > sz or (sx == sz and bernouilli())):
        #     y = max(surrnd_road_xh) - 1
        #     if inc(surrnd_road_xh):
        #         return y, Materials["{} Stairs (Bottom, East)".format(stair_material)]
        #     elif dec(surrnd_road_xh):
        #         return y, Materials["{} Stairs (Bottom, West)".format(stair_material)]
        # elif lz >= 3:
        #     y = max(surrnd_road_zh) - 1
        #     if inc(surrnd_road_zh):
        #         return y, Materials["{} Stairs (Bottom, South)".format(stair_material)]
        #     elif dec(surrnd_road_zh):
        #         return y, Materials["{} Stairs (Bottom, North)".format(stair_material)]
        #
        # surround_iter = product(sym_range(x, 1, self.width), sym_range(z, 1, self.length))
        # surround_alt = [height_map[x1, z1] for (x1, z1) in surround_iter if self.__network.is_road(x1, z1) and ((x1 == x) ^ (z1 == z))]
        # y = mean(surround_alt) if surround_alt else height_map[x, z]
        # try:
        #     if 0.25 < (y % 1) < 0.75:  # slab interval
        #         b = Materials["{} Slab (Bottom)".format(material)]
        #         y = int(ceil(y))
        #     else:
        #         b = Materials[material]
        #         y = int(round(y))
        # except KeyError:
        #     b = Materials["Stone Brick Slab (Bottom)"]
        #     y = int(ceil(y))
        # return y, b
        surround_iter = product(sym_range(x, 1, self.width), sym_range(z, 1, self.length))
        surround_alt = [height_map[x1, z1] for (x1, z1) in surround_iter if self.__network.is_road(x1, z1) and ((x1 == x) or (z1 == z) or not self.__network.is_road(x, z))]
        if not surround_alt:
            return height_map[x, z], Materials[material]
        y = mean(surround_alt)
        h = y - min(surround_alt)
        if h < .5:
            return int(y), Materials[material]
        elif h < .84:
            try:
                return int(ceil(y)), Materials["{} Slab (Bottom)".format(material)]
            except KeyError:
                return int(ceil(y)), Materials["Stone Brick Slab (Bottom)"]
        else:
            x, z = r.x, r.z
            xm, xM = x-1 if x > 0 else x, x+1 if x+1 < self.width else x
            zm, zM = z-1 if z > 0 else z, z+1 if z+1 < self.length else z
            p = [(_x, _z) if self.__network.is_road(_x, _z) else (x, z) for _x, _z in [(xM, z), (xm, z), (x, zM), (x, zm)]]
            # if p[0] == p[1] and p[2] == p[3]:
            #     p = [(xM, z), (xm, z), (x, zM), (x, zm)]
            try:
                direction = Direction(dx=height_map[p[0]] - height_map[p[1]], dz=height_map[p[2]] - height_map[p[3]])
                return int(round(y-0.33)), Materials["{} Stairs (Bottom, {})".format(stair_material, direction)]
            except AssertionError:
                return int(y), Materials[material]

    def handle_new_road(self, path):
        """
        Builds necessary bridges and stairs for every new path
        Assumes that it is called before the path is marked as a road in the RoadNetwork
        """
        if len(path) < 2:
            return
        prev_point = None
        cur_bridge = None
        if any(self.__fluids.is_water(_) for _ in path):
            for point in path:
                if not self.__network.is_road(point) and self.__fluids.is_water(point):
                    if cur_bridge is None:
                        cur_bridge = Bridge(prev_point if prev_point is not None else point, self.origin)
                    cur_bridge += point
                elif cur_bridge is not None:
                    cur_bridge += point
                    self.children.append(cur_bridge)
                    cur_bridge = None
                prev_point = point

        # carves the new path if possible and necessary to avoid steep slopes
        path_height = [self.__maps.height_map.fluid_height(_) for _ in path]
        orig_path_height = [_ for _ in path_height]
        if len(path_height) > max(path_height) - min(path_height):
            # while there is a 2 block elevation in the path, smooth path heights
            changed = False
            prev_value = max([abs(h2 - h1) for h2, h1 in zip(path_height[1:], path_height[:-1])])  # max elevation, supposed to decrease

            while any(abs(h2 - h1) > 1 for h2, h1 in zip(path_height[1:], path_height[:-1])):
                changed = True
                for i in range(2, len(path_height)-2):
                    if not self.__fluids.is_water(path[i]):
                        path_height[i] = sum(path_height[i-2: i+3]) / 5
                path_height[1] = sum(path_height[:3]) / 3
                path_height[-2] = sum(path_height[-3:]) / 3
                new_value = max([abs(h2 - h1) for h2, h1 in zip(path_height[1:], path_height[:-1])])

                if new_value >= prev_value:
                    break
                else:
                    prev_value = new_value
            if changed:
                path_height = [int(round(_)) for _ in path_height]
                self.__maps.height_map.update(path, path_height)
                self.children.append(CarvedRoad(path, orig_path_height, self.origin))
            # todo: public stairs structures (/ ladders ?) in steep streets


class Bridge(Generator):

    def __init__(self, edge, origin):
        # type: (Point2D, object) -> None
        assert isinstance(edge, Point2D)
        init_box = TransformBox((edge.x, 0, edge.z), (1, 1, 1))
        Generator.__init__(self, init_box, edge)
        self.__points = [edge]
        self.__origin = Point2D(origin.x, origin.z)

    def __iadd__(self, other):
        assert isinstance(other, Point2D)
        self.__points.append(other)
        self._box = self._box.union(TransformBox((other.x, 0, other.z), (1, 1, 1)))
        return self

    def generate(self, level, height_map=None, palette=None):
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


class CarvedRoad(Generator):
    def __init__(self, points, heights, origin):
        # type: (List[Point2D], List[int], Point2D) -> None
        x_min, x_max = min([_.x for _ in points]), max([_.x for _ in points])
        y_min, y_max = min(heights), max(heights)
        z_min, z_max = min([_.z for _ in points]), max([_.z for _ in points])
        init_box = TransformBox((x_min, y_min, z_min), (x_max+1-x_min, y_max+1-y_min, z_max+1-z_min))
        Generator.__init__(self, init_box, points[0])
        self.__points = [_ for _ in points]  # type: List[Point2D]
        self.__heights = [_ for _ in heights]  # type: List[int]
        self.__origin = Point2D(origin.x, origin.z)

    def generate(self, level, height_map=None, palette=None):
        for i in range(len(self.__points)):
            relative_road, ground_height = self.__points[i], self.__heights[i]  # type: Point2D, int
            absolute_road = relative_road + self.__origin  # rp with absolute coordinates
            road_height = height_map[relative_road.x, relative_road.z]
            height = road_height + 2 - ground_height
            if height < 2:
                road_box = TransformBox((absolute_road.x - 1, road_height+1, absolute_road.z - 1), (3, 3, 3))
                fillBlocks(level, road_box, Materials['Air'])
