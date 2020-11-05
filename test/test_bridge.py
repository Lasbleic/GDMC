from __future__ import division

from math import ceil
from random import randint
from typing import List

from numpy.random import choice
from utilityFunctions import raytrace

from generation import Generator
from generation.road_generator import Bridge
from pymclevel import MCLevel, BoundingBox, MCInfdevOldLevel
from pymclevel.block_fill import fillBlocks
from terrain_map import HeightMap
from terrain_map.maps import Maps
from utils import TransformBox, Point2D, Direction, Materials, cardinal_directions, Point3D, manhattan, euclidean, \
    clear_tree_at, bernouilli

displayName = "Bridge generator test filter"

inputs = (("type", ("Bridge", "Stair")), ("Creator: Charlie", "label"))


def perform(level, box, options):
    # type: (MCLevel, BoundingBox, dict) -> None
    box = TransformBox(box)
    print("Selected zone: {}".format(box))
    maps = Maps(level, box)
    assert box.width > 3 and box.length > 3

    if box.width > box.length:
        x1, x2 = 0, box.width - 1
        z1, z2 = randint(1, box.length - 2), randint(1, box.length - 2)
    else:
        x1, x2 = randint(1, box.width - 2), randint(1, box.width - 2)
        z1, z2 = 0, box.length - 1

    p1, p2 = Point2D(x1, z1), Point2D(x2, z2)
    h = maps.height_map.box_height(box, use_relative_coords=False)
    if options["type"] == "Bridge":
        bridge = Bridge(p1, Point2D(box.minx, box.minz))
        bridge += p2
        bridge.generate(level, h)
    else:
        stair = RampStairs(p1, p2, maps.height_map)
        stair.translate(box.minx, 0, box.minz)
        print("Generating ramp stairs: {}".format(stair))
        stair.generate(level, h)


class RampStairs(Generator):
    RAMP_WIDTH = 2  # ramp stair width
    RAMP_LENGTH = 4  # ramp stair min length

    def __init__(self, p1, p2, height_map):
        # type: (Point2D, Point2D, HeightMap) -> None
        y1, y2 = height_map.fluid_height(p1), height_map.fluid_height(p2)
        if y2 < y1:
            p1, p2, y1, y2 = p2, p1, y2, y1
        self.__entry3d = Point3D(p1.x, y1, p1.z)
        self.__exit3d = Point3D(p2.x, y2, p2.z)
        self.__direction = Direction(dx=p2.x - p1.x, dz=p2.z - p1.z)
        dy = abs(height_map.fluid_height(p2) - height_map.fluid_height(p1))
        width = abs(p1.x - p2.x) + 1
        length = abs(p1.z - p2.z) + 1
        size = max(width, length)
        self.__ramp_length = max(self.RAMP_LENGTH, int(ceil(dy * (self.RAMP_WIDTH + 1) / size)))
        self.__ramp_count = int(ceil(dy / self.__ramp_length)) + 1
        extended_ramp_length = self.__ramp_length + 2 * self.RAMP_WIDTH

        x0 = min(p1.x, p2.x)
        z0 = min(p1.z, p2.z)
        if width > length:
            z0 = min(z0, (p1.z + p2.z - extended_ramp_length) // 2)
            length = max(length, extended_ramp_length)
        else:
            x0 = min(x0, (p1.x + p2.x - extended_ramp_length) // 2)
            width = max(width, extended_ramp_length)
        box = TransformBox((x0, y1, z0), (width, 256 - y1, length))

        Generator.__init__(self, box, p1)

    def __generate_stairs(self, level, p1, p2):
        # type: (MCInfdevOldLevel, Point3D, Point3D) -> None
        assert p1.x == p2.x or p1.z == p2.z
        if p2.y < p1.y:
            p2, p1 = p1, p2
        stair_dir = Direction(dx=p2.x - p1.x, dz=p2.z - p1.z)
        if p1.x == p2.x:
            if p1.z < p2.z:
                z_list = range(p1.z + 1, p2.z - 1)
            else:
                z_list = range(p1.z - 2, p2.z, -1)
            print(str(stair_dir.asPoint2D), z_list[0], z_list[-1])
            l = len(z_list)
            x_list = [p1.x - self.RAMP_WIDTH // 2] * l
            width, length = self.RAMP_WIDTH, 1
        else:
            if p1.x < p2.x:
                x_list = range(p1.x + 1, p2.x - 1)
            else:
                x_list = range(p1.x - 2, p2.x, -1)
            print(str(stair_dir.asPoint2D), x_list[0], x_list[-1])
            l = len(x_list)
            z_list = [p1.z - self.RAMP_WIDTH // 2] * l
            width, length = 1, self.RAMP_WIDTH
        y_list = [p1.y * (1 - _ / l) + p2.y * (_ / l) for _ in range(l)] + [p2.y]
        for _ in range(l):
            x, z = x_list[_], z_list[_]
            y, y1 = int(round(y_list[_])), int(round(y_list[_ + 1]))
            if y < y1:
                material = Materials["Stone Brick Stairs (Bottom, {})".format(stair_dir)]
            else:
                material = Materials["Stone Bricks"]
            box = TransformBox((x, y1, z), (width, 1, length))
            clear_tree_at(level, box=BoundingBox((x - 5, 0, z - 5), (11, 256, 11)), point=Point2D(x, z))
            fillBlocks(level, box, material)
            fillBlocks(level, box.translate(dy=2).expand(0, 1, 0), Materials[0])
        box = TransformBox((p1.x - 1, p1.y, p1.z - 1), (2, 1, 2))
        fillBlocks(level, box, Materials["Stone Bricks"])
        fillBlocks(level, box.translate(dy=2).expand(0, 1, 0), Materials[0])
        clear_tree_at(level, box, Point2D(box.minx, box.minz))
        box = TransformBox((p2.x - 1, p2.y, p2.z - 1), (2, 1, 2))
        fillBlocks(level, box, Materials["Stone Bricks"])
        fillBlocks(level, box.translate(dy=2).expand(0, 1, 0), Materials[0])
        clear_tree_at(level, box, Point2D(box.minx, box.minz))

    def generate(self, level, height_map=None, palette=None):
        from time import time

        def terminate():
            return 0 <= best_cost < 1 or (time() - t0) > 15

        def cost():
            res = sum(edge_cost(edge[0], edge[1]) for edge in zip(ramp_points[:-1], ramp_points[1:]))
            res2 = sum(euclidean(edge[0], edge[1]) for edge in zip(ramp_points[:-1], ramp_points[1:]))
            if ramp_points[-1] != self.__exit3d:
                res += edge_cost(ramp_points[-1], self.__exit3d) + manhattan(ramp_points[-1], self.__exit3d)
                res2 += euclidean(ramp_points[-1], Point2D(self.__exit3d.x, self.__exit3d.z))
            return res / res2

        stored_edge_cost = {}

        def edge_cost(_p1, _p2):
            _sp1, _sp2 = str(_p1), str(_p2)
            if _sp1 in stored_edge_cost and _sp2 in stored_edge_cost[_sp1]:
                return stored_edge_cost[_sp1][_sp2]
            else:
                edge_points = raytrace(_p1.coords, _p2.coords)[1:]
                v = sum((1 + abs(heightMapAt(Point2D(x, z)) - y)) ** 2 for x, y, z in edge_points)
                if _sp1 not in stored_edge_cost:
                    stored_edge_cost[_sp1] = {}
                stored_edge_cost[_sp1][_sp2] = v
                return v
            # return (v / len(edge_points)) * manhattan(_p1, _p2)

        def heightMapAt(pos):
            return height_map[pos.x - self.origin.x, pos.z - self.origin.z]

        def buildRandomSolution():
            _ramp_points = [self.__entry3d]  # type: List[Point3D]
            while _ramp_points[-1] != self.__exit3d:
                cur_p = _ramp_points[-1]

                # Compute direction to extend to
                if len(_ramp_points) == 1:
                    valid_directions = [self.__direction, self.__direction.rotate(), -self.__direction.rotate()]
                    # valid_directions = [self.__direction]
                else:
                    prev_p = _ramp_points[-2]  # previous point
                    prev_d = Direction(dx=cur_p.x - prev_p.x, dz=cur_p.z - prev_p.z)  # previous direction
                    valid_directions = set(cardinal_directions())
                    for d in {-self.__direction, -prev_d}:
                        valid_directions.remove(d)  # cannot walk twice in the same direction, or go back

                next_p, next_cost = None, None
                while valid_directions:
                    cur_d = choice(list(valid_directions))  # type: Direction
                    # Compute random extensions in that direction
                    next_possible_point = [cur_p + cur_d.asPoint2D * (
                        self.RAMP_WIDTH + 1 if cur_d == self.__direction else self.RAMP_LENGTH + 2)]
                    while next_possible_point[-1].coords in self._box and len(
                            next_possible_point) <= self.__ramp_length:
                        p = next_possible_point[-1] + cur_d.asPoint2D
                        if p.x == self.__exit3d.x and p.z == self.__exit3d.z and abs(
                                self.__exit3d.y - cur_p.y) <= manhattan(cur_p, self.__exit3d) - 2:
                            point2 = self.__exit3d
                        else:
                            max_elevation = abs((p - cur_p).dot(cur_d.asPoint2D)) - 2
                            point2 = Point3D(p.x, cur_p.y + randint(-max_elevation // 2, max_elevation), p.z)
                        next_possible_point.append(point2)
                    next_possible_point.pop()  # remove last point as it is not in the box

                    valid_directions.remove(cur_d)
                    if self.__exit3d in next_possible_point and bernouilli():
                        next_p = self.__exit3d
                        break
                    elif next_possible_point:
                        weights = [1 / (edge_cost(cur_p, _) + manhattan(_, self.__exit3d)) for _ in
                                   next_possible_point]  # the higher the cost, the lower the probability
                        index = choice(range(len(weights)), p=map(lambda _: _ / sum(weights), weights))
                        # next_p = choice(next_possible_point, p=map(lambda _: _ / sum(weights), weights))
                        if next_p is None or weights[index] < next_cost:
                            next_p, next_cost = next_possible_point[index], weights[index]
                if next_p is not None:
                    _ramp_points.append(next_p)
                else:
                    break

            return _ramp_points

        # function init
        lt = euclidean(self.__entry3d, self.__exit3d)
        t0 = time()
        time_list, score_list = [], []
        ramp_points = best_ramp = []
        best_cost = -1
        explored_solutions = 0
        while not terminate():
            ramp_points = buildRandomSolution()
            explored_solutions += 1
            c = cost()
            if len(ramp_points) >= 2 and (not best_ramp or c < best_cost):
                print("Cost decreased to {}".format(c))
                best_cost = c
                best_ramp = ramp_points
                time_list.append(time() - t0)
                score_list.append(c)

        print("Explored {} solutions".format(explored_solutions))
        for p1, p2 in zip(best_ramp[:-1], best_ramp[1:]):
            print("Building stairs from {} to {}".format(p1, p2))
            self.__generate_stairs(level, p1, p2)

        # from matplotlib import pyplot as plt
        # plt.plot(time_list, score_list)
        # plt.show()

    def translate(self, dx=0, dy=0, dz=0):
        Generator.translate(self, dx, dy, dz)
        self.__entry3d += Point3D(dx, dy, dz)
        self.__exit3d += Point3D(dx, dy, dz)

    def __str__(self):
        return "stairs from {} to {}, oriented {}".format(self.__entry3d, self.__exit3d, self.__direction)
