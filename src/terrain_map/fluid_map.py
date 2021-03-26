from __future__ import print_function

from itertools import product
from random import choice
from time import time

from statistics import mean
from typing import List

from numpy import full
from numpy.core.multiarray import ndarray
from numpy.ma import array
from sklearn.semi_supervised import LabelPropagation, LabelSpreading

from parameters import MAX_WATER_EXPLORATION, MAX_LAVA_EXPLORATION, MIN_DIST_TO_OCEAN, MIN_DIST_TO_RIVER, \
    MIN_DIST_TO_LAVA, MAX_POND_EXPLORATION
from pymclevel import MCLevel, alphaMaterials as Materials
from pymclevel import MCLevel, alphaMaterials as Materials
from pymclevel.biome_types import biome_types
from utils import Point2D, cardinal_directions, water_blocks_id, lava_blocks_id
from pymclevel.block_fill import fillBlocks
from utils import Point2D, cardinal_directions, connected_component, setBlock, BoundingBox


class FluidMap:

    def __init__(self, mc_maps, level, water_limit=MAX_WATER_EXPLORATION, lava_limit=MAX_LAVA_EXPLORATION):
        self.__width = mc_maps.width
        self.__length = mc_maps.length
        self.__water_map = full((mc_maps.width, mc_maps.length), 0)
        self.__lava_map = full((mc_maps.width, mc_maps.length), False)
        self.__other_maps = mc_maps
        self.__water_limit = water_limit
        self.__lava_limit = lava_limit

        self.__borderpts = []  # type: List[Point2D]
        self.__coastline = []  # type: List[Point2D]

        self.has_lava = self.has_river = self.has_ocean = False
        self.detect_ponds_remove_ponds(level)
        self.detect_sources(level)

    def detect_sources(self, level, algorithm='spread', kernel='knn', param=256):
        # type: (MCLevel, str, str, int) -> None
        water_points = []
        t0 = time()
        for x, z in product(range(self.__width), range(self.__length)):
            xs, zs = x + self.__other_maps.box.minx, z + self.__other_maps.box.minz
            y = self.__other_maps.height_map.fluid_height(x, z)
            if level.blockAt(xs, y, zs) in water_blocks_id:
                cx, cz = xs // 16, zs // 16
                biome = level.getChunk(cx, cz).Biomes[zs & 15, xs & 15]
                if 'Ocean' in biome_types[biome] or 'Beach' in biome_types[biome]:
                    label = 1
                elif 'River' in biome_types[biome]:
                    label = 2
                elif 'Swamp' in biome_types[biome]:
                    label = 3
                else:
                    label = -1  # yet unlabeled
                water_points.append((x, z, label))

            elif level.blockAt(xs, y, zs) in lava_blocks_id:
                self.__lava_map[x, z] = True
                self.has_lava = True

        if water_points:
            data = [entry[:2] for entry in water_points]
            lbls = [entry[2] for entry in water_points]

            if algorithm in ['prop', 'spread']:
                algo = LabelPropagation if algorithm == 'prop' else LabelSpreading
                model = algo(kernel, gamma=param, n_neighbors=min(len(lbls), param), tol=0, max_iter=200)
                try:
                    model.fit(data, lbls)
                    lbls = model.predict(data)
                except ValueError:
                    # no water or no labeled water point (ponds only)
                    lbls = [3 for _ in data]

            for (x, z), water_type in zip(data, lbls):
                self.__water_map[x, z] = water_type
                if water_type == 1:
                    self.has_ocean = True
                elif water_type in [2, 3]:
                    self.has_river = True

        t1 = time()
        print('Computed water map in {} seconds'.format(t1 - t0))
        self.__build_distance_maps()
        print('Computed distance maps in {} seconds'.format(time() - t1))

    def detect_ponds_remove_ponds(self, level):
        maps = self.__other_maps
        explored_points = set()
        for x, z in product(range(self.__width), range(self.__length)):
            xs, zs = x + maps.box.minx, z + maps.box.minz
            y = maps.height_map.fluid_height(x, z)
            if level.blockAt(xs, y, zs) in [Materials.Water.ID, Materials.WaterActive.ID, Materials.Ice.ID]:
                cx, cz = xs // 16, zs // 16
                biome = level.getChunk(cx, cz).Biomes[xs & 15, zs & 15]
                # if all(_ not in biome_types[biome] for _ in ['Ocean', 'Beach', 'River', 'Swamp']):
                if all(_ not in biome_types[biome] for _ in ['Ocean', 'River', 'Swamp']):
                    if Point2D(xs, zs) in explored_points:
                        continue

                    condition = lambda p1, p2, _maps: _maps.level.blockAt(p2.x, y, p2.z) in [Materials.Water.ID, Materials.WaterActive.ID, Materials.Ice.ID] and _maps.in_limits(p2, True)
                    early_stop = lambda s: len(s) >= MAX_POND_EXPLORATION
                    pond_origin, mask = connected_component(maps, Point2D(xs, zs), condition, early_stop, False)
                    if mask.all():
                        pond_origin -= Point2D(1, 1)
                        tmp_mask = full((mask.shape[0]+2, mask.shape[1]+2), False)
                        tmp_mask[1:-1, 1:-1] = mask
                        mask = tmp_mask
                    matrix_pos = product(range(mask.shape[0]), range(mask.shape[1]))
                    out_pond_points = {pond_origin + Point2D(i, j) for i, j in matrix_pos if not mask[i, j]}
                    out_pond_points = {_ for _ in out_pond_points if maps.in_limits(_, True)}
                    x0, z0 = maps.minx, maps.minz

                    if mask.sum() < MAX_POND_EXPLORATION:
                        h = maps.height_map.altitude
                        ground_y = mean(h(p.x - x0, p.z - z0) for p in out_pond_points)
                        for i, j in product(range(mask.shape[0]), range(mask.shape[1])):
                            abs_coords = pond_origin + Point2D(i, j)
                            rel_coords = abs_coords - Point2D(x0, z0)
                            try:
                                cur_height = h(rel_coords)
                            except IndexError:
                                break  # pond at the border of the settlement

                            if cur_height < ground_y - 1 or mask[i, j]:
                                # sample material in surroundings to fill the hole
                                random_point = choice(list(out_pond_points))
                                mat = level.blockAt(random_point.x, h(random_point - Point2D(x0, z0)), random_point.z)
                                fillBlocks(level, BoundingBox((abs_coords.x, cur_height, abs_coords.z),
                                                              (1, 1 + ground_y - cur_height, 1)), Materials[mat])
                                maps.height_map.update([rel_coords], [ground_y])

                    explored_points.update(out_pond_points)

    def __build_distance_maps(self):
        self.river_distance = full(self.__water_map.shape, self.__water_limit)
        self.ocean_distance = full(self.__water_map.shape, self.__water_limit)
        self.lava_distance = full(self.__lava_map.shape, self.__lava_limit)

        for x, z in product(xrange(self.__width), xrange(self.__length)):
            if self.__water_map[x, z] in [2, 3]:
                self.river_distance[x, z] = 0
            elif self.__water_map[x, z] == 1:
                self.ocean_distance[x, z] = 0
            elif self.__lava_map[x, z]:
                self.lava_distance[x, z] = 0
            elif (x == 0) or (z == 0) or (x == (self.__width - 1)) or (z == (self.__length - 1)):
                self.__borderpts.append(Point2D(x, z))

        def is_init_neigh(distance_map, _x, _z):
            # Context: find border water points in a water surface.
            # Surrounded water points are useless in exploration
            if distance_map[_x, _z] != 0:
                return False
            else:
                for direction in cardinal_directions():
                    x0, z0 = _x + direction.x, _z + direction.z
                    try:
                        if distance_map[x0, z0] != 0:
                            return True  # (x, z) is a water (or lava) point with a non water neighbour
                    except IndexError:
                        continue
                return False

        self.__coastline = [Point2D(_x, _z) for _x, _z in product(xrange(self.__width), xrange(self.__length))
                            if is_init_neigh(self.ocean_distance, _x, _z)]

        def __pseudo_dijkstra(distance_map):
            # type: (array) -> None
            max_distance = distance_map.max()

            def cost(src_point, dst_point):
                x_cost = abs(src_point.x - dst_point.x)
                z_cost = abs(src_point.z - dst_point.z)
                src_y = int(self.__other_maps.height_map.fluid_height(src_point.x, src_point.z))
                dst_y = int(self.__other_maps.height_map.fluid_height(dst_point.x, dst_point.z))
                y_cost = 2 * max(dst_y - src_y, 0)  # null cost for water to go downhill
                return x_cost + y_cost + z_cost

            def update_distance(updated_point, neighbour):
                new_distance = distance_map[updated_point.x][updated_point.z] + cost(updated_point, neighbour)
                previous_distance = distance_map[neighbour.x][neighbour.z]
                if previous_distance >= max_distance > new_distance:
                    # assert neighbour not in neighbours
                    neighbours.append(neighbour)
                distance_map[neighbour.x, neighbour.z] = min(previous_distance, new_distance)

            def update_distances(updated_point):
                x0, z0 = updated_point.x, updated_point.z
                for xn, zn in product(xrange(x0 - 1, x0 + 2), xrange(z0 - 1, z0 + 2)):
                    if (xn != x0 or zn != z0) and 0 <= xn < _w and 0 <= zn < _l and distance_map[xn, zn] > 0:
                        update_distance(updated_point, Point2D(xn, zn))

            # Function core
            _w, _l = distance_map.shape
            neighbours = [Point2D(x1, z1) for x1, z1 in product(xrange(_w), xrange(_l))
                          if is_init_neigh(distance_map, x1, z1)]

            while len(neighbours) > 0:
                clst_neighbor = neighbours[0]
                update_distances(clst_neighbor)
                del neighbours[0]

        __pseudo_dijkstra(self.river_distance)
        __pseudo_dijkstra(self.ocean_distance)
        __pseudo_dijkstra(self.lava_distance)

    def is_lava(self, x_or_point, z=None, margin=0):
        # type: (Point2D or int, None or int, float) -> object
        if isinstance(x_or_point, Point2D):
            p = x_or_point
            return self.lava_distance[p.x, p.z] <= margin
        else:
            x = x_or_point
            return self.lava_distance[x, z] <= margin

    def is_close_to_fluid(self, x_or_point, z=None):
        # type: (Point2D or int, None or int) -> object
        if isinstance(x_or_point, Point2D):
            p = x_or_point
            return self.is_close_to_fluid(p.x, p.z)
        else:
            x = x_or_point
            return ((self.ocean_distance[x][z] <= MIN_DIST_TO_OCEAN)
                    | (self.river_distance[x][z] <= MIN_DIST_TO_RIVER)
                    | (self.lava_distance[x][z] <= MIN_DIST_TO_LAVA))

    def is_water(self, x_or_point, z=None, margin=0):
        # type: (int or Point2D, int or None, float) -> bool
        if isinstance(x_or_point, Point2D):
            return self.is_water(x_or_point.x, x_or_point.z)
        else:
            x = x_or_point
            return (self.ocean_distance[x, z] <= margin) | (self.river_distance[x, z] <= margin)

    @property
    def as_obstacle_array(self):
        # if one of the conditions is valid, fluids are an obstacle
        obs = ((self.ocean_distance <= MIN_DIST_TO_OCEAN)
               | (self.river_distance <= MIN_DIST_TO_RIVER)
               | (self.lava_distance <= MIN_DIST_TO_LAVA))  # type: ndarray
        return obs.astype(int)

    @property
    def water(self):
        return self.__water_map

    @property
    def external_connections(self):
        return self.__borderpts + self.__coastline
