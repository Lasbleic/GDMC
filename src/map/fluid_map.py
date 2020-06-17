from __future__ import print_function

from itertools import product
from time import time

from numpy import full
from numpy.ma import array
from sklearn.semi_supervised import LabelPropagation, LabelSpreading

from parameters import MAX_WATER_EXPLORATION, MAX_LAVA_EXPLORATION
from pymclevel import MCLevel, alphaMaterials as Blocks
from pymclevel.biome_types import biome_types
from utils import Point2D, cardinal_directions


class FluidMap:

    def __init__(self, mc_maps, level, water_limit=MAX_WATER_EXPLORATION, lava_limit=MAX_LAVA_EXPLORATION):
        self.__width = mc_maps.width
        self.__length = mc_maps.length
        self.__water_map = full((mc_maps.width, mc_maps.length), 0)
        self.__lava_map = full((mc_maps.width, mc_maps.length), False)
        self.__other_maps = mc_maps
        self.__water_limit = water_limit
        self.__lava_limit = lava_limit
        self.detect_sources(level)

    def detect_sources(self, level, algorithm='spread', kernel='knn', param=256):
        # type: (MCLevel, str, str, int) -> None
        water_points = []
        t0 = time()
        for x, z in product(range(self.__width), range(self.__length)):
            xs, zs = x + self.__other_maps.box.minx, z + self.__other_maps.box.minz
            y = self.__other_maps.height_map[x, z] + 1
            if level.blockAt(xs, y, zs) in [Blocks.Water.ID, Blocks.WaterActive.ID, Blocks.Ice.ID]:
                cx, cz = xs // 16, zs // 16
                biome = level.getChunk(cx, cz).Biomes[xs & 15, zs & 15]
                if 'Ocean' in biome_types[biome] or 'Beach' in biome_types[biome]:
                    label = 1
                elif 'River' in biome_types[biome]:
                    label = 2
                elif 'Swamp' in biome_types[biome]:
                    label = 3
                else:
                    label = -1  # yet unlabeled
                water_points.append((x, z, label))

            elif level.blockAt(xs, y, zs) in [Blocks.Lava.ID, Blocks.LavaActive.ID]:
                self.__lava_map[x, z] = True

        if water_points:
            data = [entry[:2] for entry in water_points]
            lbls = [entry[2] for entry in water_points]

            if algorithm in ['prop', 'spread']:
                algo = LabelPropagation if algorithm == 'prop' else LabelSpreading
                model = algo(kernel, gamma=param, n_neighbors=min(len(lbls), param), tol=0, max_iter=200)
                model.fit(data, lbls)
                lbls = model.predict(data)

            for (x, z), water_type in zip(data, lbls):
                self.__water_map[x, z] = water_type

        t1 = time()
        print('Computed water map in {} seconds'.format(t1 - t0))
        self.__build_distance_maps()
        print('Computed distance maps in {} seconds'.format(time() - t1))

    def __build_distance_maps(self):
        self.fresh_water_distance = full(self.__water_map.shape, self.__water_limit)
        self.sea_water_distance = full(self.__water_map.shape, self.__water_limit)
        self.lava_distance = full(self.__lava_map.shape, self.__lava_limit)

        for x, z in product(xrange(self.__width), xrange(self.__length)):
            if self.__water_map[x, z] in [2, 3]:
                self.fresh_water_distance[x, z] = 0
            elif self.__water_map[x, z] == 1:
                self.sea_water_distance[x, z] = 0
            elif self.__lava_map[x, z]:
                self.lava_distance[x, z] = 0

        def __pseudo_dijkstra(distance_map):
            # type: (array) -> None
            max_distance = distance_map.max()

            def is_init_neigh(_x, _z):
                # Context: find border water points in a water surface.
                # Surrounded water points are useless in exploration
                if distance_map[_x, _z] != 0:
                    return False
                else:
                    for dir in cardinal_directions():
                        x0, z0 = _x + dir.x, _z + dir.z
                        try:
                            if distance_map[x0, z0] != 0:
                                return True  # (x, z) is a water (or lava) point with a non water neighbour
                        except IndexError:
                            continue
                    return False

            def cost(src_point, dst_point):
                x_cost = abs(src_point.x - dst_point.x)
                z_cost = abs(src_point.z - dst_point.z)
                # todo: create HeightMap class, __getitem__(Point2D)
                src_y = int(self.__other_maps.height_map[src_point.x, src_point.z])
                dst_y = int(self.__other_maps.height_map[dst_point.x, dst_point.z])
                y_cost = 2 * max(dst_y - src_y, 0)  # null cost for water to go downhill
                return x_cost + y_cost + z_cost

            def update_distance(updated_point, neighbour):
                new_distance = distance_map[updated_point.x][updated_point.z] + cost(updated_point, neighbour)
                previous_distance = distance_map[neighbour.x][neighbour.z]
                if previous_distance >= max_distance > new_distance:
                    assert neighbour not in neighbours
                    neighbours.append(neighbour)
                distance_map[neighbour.x, neighbour.z] = min(previous_distance, new_distance)

            def update_distances(updated_point):
                x0, z0 = updated_point.x, updated_point.z
                for xn, zn in product(xrange(x0-1, x0+2), xrange(z0-1, z0+2)):
                    if (xn != x0 or zn != z0) and 0 <= xn < W and 0 <= zn < L and distance_map[xn, zn] > 0:
                        update_distance(updated_point, Point2D(xn, zn))

            # Function core
            W, L = distance_map.shape
            neighbours = [Point2D(_x, _z) for _x, _z in product(xrange(W), xrange(L)) if is_init_neigh(_x, _z)]

            while len(neighbours) > 0:
                clst_neighbor = neighbours[0]
                update_distances(clst_neighbor)
                del neighbours[0]

        __pseudo_dijkstra(self.fresh_water_distance)
        __pseudo_dijkstra(self.sea_water_distance)
        __pseudo_dijkstra(self.lava_distance)

    def is_lava(self, x_or_point, z=None):
        # type: (Point2D or int, None or int) -> object
        if isinstance(x_or_point, Point2D):
            p = x_or_point
            return self.__lava_map[p.x, p.z]
        else:
            x = x_or_point
            return self.__lava_map[x, z]

    @property
    def water(self):
        return self.__water_map
