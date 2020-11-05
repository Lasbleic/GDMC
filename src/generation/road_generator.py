from __future__ import division, print_function

from math import ceil
from random import randint
from time import sleep
from typing import List

from numpy import full, zeros, uint8, array, mean
from numpy.random.mtrand import choice
from utilityFunctions import setBlock, raytrace

from generation.generators import Generator, Materials
from generation.mining import Point3D
from pymclevel import MCInfdevOldLevel
from pymclevel.block_fill import fillBlocks
from pymclevel.materials import Block
from terrain_map import HeightMap
from utils import TransformBox, Point2D, euclidean, sym_range, product, clear_tree_at, bernouilli, place_torch, \
    Direction, setMaterial, cardinal_directions, manhattan


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
        self.__origin = Point2D(box.minx, box.minz)  # type: Point2D

    def generate(self, level, height_map=None, palette=None):
        # type: (MCInfdevOldLevel, array, dict) -> None

        print("[RoadGenerator] generating road blocks...", end='')
        Generator.generate(self, level, height_map)  # generate bridges

        road_height_map = zeros(height_map.shape, dtype=uint8)
        __network = full((self.width, self.length), Materials.Air)
        x0, z0 = self.__origin.x, self.__origin.z
        sleep(.001)

        for road_block in self.__network.road_blocks.union(self.__network.special_road_blocks):
            road_width = (self.__network.calculate_road_width(road_block.x, road_block.z) - 1) / 2.0
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
                    xa, za = x + x0, z + z0
                    setBlock(level, (b.ID, b.blockData), xa, y, za)
                    if "slab" not in b.stringID and bernouilli(0.1):
                        place_torch(level, xa, y + 1, za)
                    else:
                        fillBlocks(level, TransformBox((xa, y+1, za), (1, 2, 1)), Materials.Air)
                    h = height_map[x, z]
                    if h < y:
                        pole_box = TransformBox((xa, h, za), (1, y-h, 1))
                        fillBlocks(level, pole_box, Materials["Stone Bricks"])
        print("OK")

    def __compute_road_at(self, x, z, height_map, r):
        # type: (int, int, array, Point2D) -> (int, Block)
        material = choice(self.stony_palette.keys(), p=self.stony_palette.values())

        stair_material = choice(["Cobblestone", "Stone Brick"])
        surround_iter = product(sym_range(x, 1, self.width), sym_range(z, 1, self.length))
        surround_alt = {Point2D(x1, z1): height_map[x1, z1] for (x1, z1) in surround_iter if
                        self.__network.is_road(x1, z1) and ((x1 == x) or (z1 == z) or not self.__network.is_road(x, z))}
        if not surround_alt:
            return height_map[x, z], Materials[material]
        y = mean(surround_alt.values())
        h = y - min(surround_alt.values())
        if h < .5:
            return int(y), Materials[material]
        elif h < .84:
            try:
                return int(ceil(y)), Materials["{} Slab (Bottom)".format(material)]
            except KeyError:
                return int(ceil(y)), Materials["Stone Brick Slab (Bottom)"]
        else:
            mx, my, mz = mean([p.x for p in surround_alt.keys()]), y, mean([p.z for p in surround_alt.keys()])
            x_slope = sum((p.x - mx) * (y - my) for p, y in surround_alt.items())
            z_slope = sum((p.z - mz) * (y - my) for p, y in surround_alt.items())
            try:
                direction = Direction(dx=x_slope, dz=z_slope)
                return int(round(y - 0.33)), Materials["{} Stairs (Bottom, {})".format(stair_material, direction)]
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
                        cur_bridge = Bridge(prev_point if prev_point is not None else point, self.__origin)
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
            prev_value = max([abs(h2 - h1) for h2, h1 in
                              zip(path_height[1:], path_height[:-1])])  # max elevation, supposed to decrease

            while any(abs(h2 - h1) > 1 for h2, h1 in zip(path_height[1:], path_height[:-1])):
                changed = True
                for i in range(2, len(path_height) - 2):
                    if not self.__fluids.is_water(path[i]):
                        path_height[i] = sum(path_height[i - 2: i + 3]) / 5
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
                self.children.append(CarvedRoad(path, orig_path_height, self.__origin))
                for updated_point_index in filter(lambda _: path_height[_] != orig_path_height[_], range(len(path))):
                    point = path[updated_point_index]
                    self.__maps.obstacle_map.map[point.x, point.z] += 1
            # todo: public stairs structures (/ ladders ?) in steep streets

        else:
            self.children.append(RampStairs(path[0], path[-1], self.__maps.height_map))


class Bridge(Generator):

    def __init__(self, edge, origin):
        # type: (Point2D, Point2D) -> None
        assert isinstance(edge, Point2D) and isinstance(origin, Point2D)
        init_box = TransformBox((edge.x, 0, edge.z), (1, 1, 1))
        Generator.__init__(self, init_box, edge)
        self.__points = [edge]
        self.__origin = origin  # type: Point2D

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
        length = euclidean(o1, o2) + 1
        try:
            y1, y2 = height_map[o1.x, o1.z] + 1, height_map[o2.x, o2.z] + 1
        except IndexError:
            return

        def base_height(_d):
            # y1 when d = 0, y2 when d = length
            return y1 + _d / length * (y2 - y1)

        def curv_height(_d):
            # 0 in d = 0 & d = length, 0.5 derivative in 0
            cst1 = 1 / length  # steepness constraint
            cst2 = (4 / length ** 2) * (67 - base_height(length / 2))  # bridge height constraint
            cst = max(0, min(cst1, cst2))
            return cst * _d * (length - _d)

        for p in self.__points:
            d = euclidean(p, o1)
            interpol1 = base_height(d) + curv_height(d)
            interpol2 = base_height(d + 1) + curv_height(d + 1)
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
            rounded = 0 if r < 1 / 3 else 0.5 if r < 2 / 3 else 1
            return d + rounded

        r1, r2 = my_round(y1), my_round(y2)
        y = int(r1)
        if r2 - r1 <= 1 / 2:
            if r1 - int(r1) == 0:
                b = Materials["Stone Brick Slab (Bottom)"]
            else:
                b = Materials["Stone Bricks"]
            b_id, b_data = b.ID, b.blockData
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
        init_box = TransformBox((x_min, y_min, z_min), (x_max + 1 - x_min, y_max + 1 - y_min, z_max + 1 - z_min))
        Generator.__init__(self, init_box, points[0])
        self.__points = [_ for _ in points]  # type: List[Point2D]
        self.__heights = [_ for _ in heights]  # type: List[int]
        self.__origin = origin

    def generate(self, level, height_map=None, palette=None):
        for i in range(len(self.__points)):
            relative_road, ground_height = self.__points[i], self.__heights[i]  # type: Point2D, int
            absolute_road = relative_road + self.__origin  # rp with absolute coordinates
            road_height = height_map[relative_road.x, relative_road.z]
            height = road_height + 2 - ground_height
            if height < 2:
                road_box = TransformBox((absolute_road.x - 1, road_height + 1, absolute_road.z - 1), (3, 3, 3))
                fillBlocks(level, road_box, Materials['Air'])


class RampStairs(Generator):
    RAMP_WIDTH = 2  # ramp stair width
    RAMP_LENGTH = 4  # ramp stair min length

    def __init__(self, p1, p2, height_map):
        # type: (Point2D, Point2D, HeightMap) -> None
        entry = p1 if height_map.fluid_height(p1) < height_map.fluid_height(p2) else p2
        self.__exit = exitt = p2 if entry == p1 else p1
        self.__direction = Direction(dx=exitt.x - entry.x, dz=exitt.z - entry.z)
        dy = abs(height_map.fluid_height(p1) - height_map.fluid_height(p1))
        width = abs(p1.x - p2.x)
        length = abs(p1.z - p2.z)
        size = max(width, length)
        self.__ramp_length = max(self.RAMP_LENGTH, int(ceil(dy * (self.RAMP_WIDTH + 1) / size)))
        self.__ramp_count = int(ceil(dy / self.__ramp_length)) + 1
        extended_ramp_length = self.__ramp_length + 2 * self.RAMP_WIDTH

        x0 = min(p1.x, p2.x)
        y0 = min(height_map.fluid_height(p1), height_map.fluid_height(p1))
        z0 = min(p1.z, p2.z)
        if width > length:
            z0 = min(z0, (p1.z + p2.z - extended_ramp_length) // 2)
            length = max(length, extended_ramp_length)
        else:
            x0 = min(x0, (p1.x + p2.x - extended_ramp_length) // 2)
            width = max(width, extended_ramp_length)
        box = TransformBox((x0, y0, z0), (width, abs(dy), length))

        Generator.__init__(self, box, entry)

    @staticmethod
    def __generate_stairs(level, p1, p2):
        # type: (MCInfdevOldLevel, Point3D, Point3D) -> None
        assert p1.x == p2.x or p1.z == p2.z
        stair_dir = Direction(dx=p2.x - p1.x, dz=p2.z - p1.z)
        if p1.x == p2.x:
            z_list = range(p1.z + 1, p2.z) if p1.z < p2.z else range(p2.z + 1, p1.z)
            l = len(z_list)
            x_list = [p1.x] * l
            y_list = [p1.y * _ / l + p2.y * (1 - _ / l) for _ in range(l + 1)]
        else:
            x_list = range(p1.x + 1, p2.x) if p1.x < p2.x else range(p2.x + 1, p1.x)
            l = len(x_list)
            z_list = [p1.z] * l
            y_list = [p1.y * _ / l + p2.y * (1 - _ / l) for _ in range(l + 1)]
        for _ in range(l):
            x, z = x_list[_], z_list[_]
            y, y1 = int(round(y_list[_])), int(round(y_list[_ + 1]))
            if y < y1:
                setMaterial(level, x, y, z, Materials["Stone Brick Stairs (Bottom, {})".format(-stair_dir)])
            else:
                setMaterial(level, x, y, z, Materials["Stone Bricks"])
        fillBlocks(level, TransformBox((p1.x - 1, p1.y, p1.z - 1), (2, 1, 2)), Materials["Stone Bricks"])
        fillBlocks(level, TransformBox((p2.x - 1, p2.y, p2.z - 1), (2, 1, 2)), Materials["Stone Bricks"])

    def generate(self, level, height_map=None, palette=None):
        ramp_points = []
        print("Hi")

        def found_valid_stairs():
            return True

        def bound_point_in_box(point):
            # type: (Point2D) -> Point2D
            if (point.x, self._box.miny, point.z) not in self._box:
                x = min(max(point.x, self._box.minx), self._box.maxx)
                z = min(max(point.z, self._box.minz), self._box.maxz)
                return Point2D(x, z)
            return point

        while not found_valid_stairs():
            ramp_points = [self._entry_point]  # type: List[Point3D]
            while ramp_points[-1] != self.__exit:
                if len(ramp_points) == 1:
                    valid_directions = [self.__direction, self.__direction.rotate(), -self.__direction.rotate()]
                else:
                    cur_p, prev_p = ramp_points[-1], ramp_points[-2]
                    prev_dir = Direction(dx=cur_p.x - prev_p.x, dz=cur_p.z - prev_p.z)
                    valid_directions = set(cardinal_directions())
                    for d in [-self.__direction, prev_dir, -prev_dir]:
                        valid_directions.remove(d)
                    cur_d = choice(valid_directions)  # type: Direction
                    ramp_length = randint(self.RAMP_LENGTH, self.__ramp_length)
                    next_p = bound_point_in_box(cur_p + (cur_d.asPoint2D * ramp_length))
                    ramp_points.append(Point3D(next_p.x, cur_p.y + manhattan(cur_p, next_p) - 2, next_p.z))
