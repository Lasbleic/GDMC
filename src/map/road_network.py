# coding=utf-8
from __future__ import division, print_function

from sys import maxint
from typing import Set

from numpy import full, empty, mean, uint8, zeros, std, argmin

import map
from generation.bridge import Bridge
from generation.generators import *
from parameters import *
from pymclevel import alphaMaterials as Materials
from utilityFunctions import setBlock
from utils import Point2D, bernouilli, euclidean, clear_tree_at, place_torch, TransformBox

MAX_FLOAT = 100000.0
MAX_DISTANCE_CYCLE = 32
MIN_DISTANCE_CYCLE = 24
DIST_BETWEEN_NODES = 12


class RoadNetwork:

    def __init__(self, width, length, mc_map=None):
        # type: (int, int, map.Maps) -> RoadNetwork
        self.width = width
        self.length = length
        self.network = zeros((width, length), dtype=int)
        # Representing the distance from the network + the path to the network
        self.cost_map = full((width, length), maxint)
        self.distance_map = full((width, length), maxint)
        self.path_map = empty((width, length), dtype=object)
        self.lambda_max = MAX_LAMBDA
        self.network_node_list = []
        self.road_blocks = set()  # type: Set[Point2D]
        self.network_extremities = []
        self.__generator = RoadGenerator(self, mc_map.box, mc_map.fluid_map)
        self.__all_maps = mc_map

    # region GETTER AND SETTER

    def __is_point_obstacle(self, point):
        if self.__all_maps is not None:
            return not self.__all_maps.obstacle_map.is_accessible(point)
        else:
            return False

    def get_road_width(self, x, z=None):
        # type: (Point2D or int, None or int) -> (int, [Point2D])
        if z is None:
            # assert isinstance(x, Point2D)
            return self.get_road_width(x.x, x.z)
        else:
            return self.network[x, z]

    def __get_closest_node(self, point):

        closest_node = None
        min_distance = MAX_FLOAT
        if len(self.network_node_list) == 0:
            closest_node = choice(list(self.road_blocks))
        for node in self.network_node_list:
            if euclidean(node, point) < min_distance:
                closest_node = node
                min_distance = euclidean(node, point)

        # try to promote an extremity to node
        alt_edge = [_ for _ in self.road_blocks if _ not in self.network_node_list]
        alt_dist = [euclidean(_, point) for _ in alt_edge]
        i = int(argmin(alt_dist))
        edge, dist = alt_edge[i], alt_dist[i]
        # i = int(argmin([euclidean(_, point) for _ in self.road_blocks if _ not in self.network_node_list]))
        # edge = self.network_extremities[i]
        # dist = euclidean(edge, point)
        if dist < min_distance:
            if euclidean(edge, closest_node) >= DIST_BETWEEN_NODES:
                self.network_node_list.append(edge)
            closest_node = edge
        return closest_node

    def get_distance(self, x, z=None):
        # type: (Point2D or int, None or int) -> (int, [Point2D])
        if z is None:
            # assert isinstance(x, Point2D)
            return maxint if self.__is_point_obstacle(x) else self.get_distance(x.x, x.z)
        else:
            if self.distance_map[x][z] == maxint:
                return maxint
            return max(0, self.distance_map[x][z] - self.get_road_width(self.__get_closest_road_point(Point2D(x, z))))

    def __set_road_block(self, xp, z=None):
        # type: (Point2D or int, None or int) -> None
        if z is None:
            self.road_blocks.add(xp)
            x, z = xp.x, xp.z
            if self.network[x, z] == 0:
                self.network[x, z] = MIN_ROAD_WIDTH
            elif self.network[x, z] < MAX_ROAD_WIDTH:
                self.network[x, z] += 1
        else:
            self.__set_road_block(Point2D(xp, z))

    def is_road(self, x, z=None):
        # type: (Point2D or int, None or int) -> bool
        if z is None:
            return self.is_road(x.x, x.z)
        else:
            return self.network[x][z] > 0

    def __get_closest_road_point(self, point):
        # type: (Point2D) -> Point2D
        if self.is_road(point):
            return point
        if self.is_accessible(point):
            return self.path_map[point.x][point.z][0]
        else:
            return self.__get_closest_node(point)

    def __invalidate(self, point):
        self.distance_map[point.x][point.z] = maxint
        self.path_map[point.x][point.z] = None

    def __set_road(self, path):
        # type: ([Point2D]) -> None
        force_update = False
        if any(self.__is_point_obstacle(point) for point in path):
            force_update = True
            # todo: qu'est-ce qu'on fait ici ?
            # self.__invalidate(path[-1])
            # self.__set_road_block(path[0])
            # self.__update_distance_map([path[0]])
            # self.__set_road(path[1:])
            path = self.a_star(path[0], path[-1])
        # else:
        self.__generator.handle_new_road(path)
        for point in path:
            self.__set_road_block(point)
        self.__update_distance_map(path, force_update)

    def is_accessible(self, point):
        return type(self.path_map[point.x][point.z]) == list

    # endregion

    # def calculate_road_width(self, x, z):
    #     """
    #     Takes relative coordinates. Return local road width based on the number of surrounding roads.
    #     The denser the network, the wider the road
    #     """
    #     # mx, mz = int(sqrt(self.width)), int(sqrt(self.length))
    #     # surroundings = product(range(max(0, x-mx), min(self.width, x+mx)),
    #     #                        range(max(0, z-mz), min(self.length, z+mz))
    #     #                        )
    #     # road_count = sum(int(self.is_road(x, z)) for x, z in surroundings)
    #     # return min(MAX_ROAD_WIDTH, 1 + road_count // max(mx, mz))
    #     return 1

    # region PUBLIC INTERFACE

    def create_road(self, root_point, ending_point):
        # type: (Point2D, Point2D) -> None
        path = self.a_star(root_point, ending_point)
        self.__set_road([root_point] + path)
        self.network_extremities += [root_point, ending_point]
        return

    def connect_to_network(self, point_to_connect):
        # type: (Point2D) -> None
        from time import time

        if self.is_accessible(point_to_connect):
            path = self.path_map[point_to_connect.x][point_to_connect.z]
            print("[RoadNetwork] Found existing road")
        else:
            _t0 = time()
            path = self.a_star(self.__get_closest_node(point_to_connect), point_to_connect)
            print("[RoadNetwork] Computed road path in {:0.2f}s".format(time()-_t0))
        self.network_extremities += [point_to_connect]
        if path:
            self.__set_road(path)

        _t1 = None
        for node in self.network_node_list:
            if MIN_DISTANCE_CYCLE < euclidean(node, point_to_connect) < MAX_DISTANCE_CYCLE:
                if _t1 is None:
                    _t1 = time()
                self.create_road(point_to_connect, node)
                # todo: add plazas / city blocks in the middle of road cycles
                # todo: ajouter une condition du genre "si c'est 4x plus long d'aller par la route que tout droit, créer chemin"
        if _t1 is not None:
            print("[RoadNetwork] Computed road cycles in {:0.2f}s".format(time()-_t1))

        if path and all(euclidean(path[0], node) > DIST_BETWEEN_NODES for node in self.network_node_list):
            self.network_node_list.append(path[0])

        return

    # endregion

    def generate(self, level):
        # type: (MCInfdevOldLevel) -> None
        hm = self.__all_maps.height_map  # type: map.HeightMap
        self.__generator.generate(level, hm.box_height(self.__all_maps.box, False))

    def __update_distance_map(self, road, force_update=False):
        self.dijkstra(road, self.lambda_max, force_update)

    def cost(self, src_point, dest_point):
        value = 1
        # if we don't have access to terrain info
        if self.__all_maps is None:
            return value

        # if dest is road, no additional cost
        if self.is_road(dest_point):
            return 0.2

        # if dest_point is an obstacle, return inf
        is_dest_obstacle = not self.__all_maps.obstacle_map.is_accessible(dest_point)
        is_dest_obstacle |= self.__all_maps.fluid_map.is_lava(dest_point, margin=8)
        if is_dest_obstacle:
            return maxint

        # specific cost to build on water
        if self.__all_maps.fluid_map.is_water(dest_point, margin=4):
            if not self.__all_maps.fluid_map.is_water(src_point):
                return BRIDGE_COST
            return BRIDGE_UNIT_COST

        # additional cost for slopes
        _src_height = self.__all_maps.height_map.fluid_height(src_point.x, src_point.z)
        _dest_height = self.__all_maps.height_map.fluid_height(dest_point.x, dest_point.z)
        elevation = abs(int(_src_height) - int(_dest_height))
        value += elevation * 0.5

        # finally, local cost depends on local steepness, measured as stdev in a small radius
        value += self.__all_maps.height_map.steepness(dest_point.x, dest_point.z) * 0.3

        return value

    # return the path from the point satisfying the ending_condition to the root_point, excluded
    def dijkstra(self, root_points, max_distance, force_update):
        # type: (List[Point2D], int, bool) -> None
        """
        Accelerated Dijkstra algorithm to compute distance & shortest paths from root points to all others.
        The cost function is the euclidean distance
        Parameters
        ----------
        root_points null distance points to start the exploration
        max_distance todo
        force_update todo

        Returns
        -------
        Nothing. Result is stored in self.distance_map and self.path_map
        """
        def init():
            _distance_map = full((self.width, self.length), maxint)  # on foot distance walking from road points
            _cost_map = full((self.width, self.length), maxint)  # cost distance building from road points
            for root_point in root_points:
                _distance_map[root_point.x, root_point.z] = 0
                _cost_map[root_point.x, root_point.z] = 0
            _neighbours = root_points
            _predecessor_map = empty((self.width, self.length), dtype=object)
            return _cost_map, _distance_map, _neighbours, _predecessor_map

        def closest_neighbor():
            _closest_neighbors = []
            min_cost = maxint
            for neighbor in neighbors:
                _current_cost = cost_map[neighbor.x, neighbor.z]
                if _current_cost < min_cost:
                    _closest_neighbors = [neighbor]
                    min_cost = _current_cost
                elif _current_cost == min_cost:
                    _closest_neighbors += [neighbor]
            return choice(_closest_neighbors)
            # old_neighbours = neighbors if len(neighbors) < 16 else neighbors[:16]
            # distances = map(lambda n: distance_map[n.x, n.z], old_neighbours)
            # return old_neighbours[argmin(distances)]
            # return neighbors[0]

        def distance(orig_point, dest_point):
            fluids = self.__all_maps.fluid_map
            if fluids.is_lava(dest_point):
                return maxint
            elif fluids.is_water(dest_point):
                return BRIDGE_UNIT_COST
            return euclidean(orig_point, dest_point)

        def update_distance(updated_point, neighbor, _neighbors):
            edge_cost = self.cost(updated_point, neighbor)
            edge_dist = distance(updated_point, neighbor)
            if edge_cost == maxint:
                return

            new_cost = cost_map[updated_point.x][updated_point.z] + edge_cost
            new_dist = distance_map[updated_point.x][updated_point.z] + edge_dist
            previous_cost = cost_map[neighbor.x][neighbor.z]
            if previous_cost >= maxint and new_dist <= max_distance and not self.is_road(neighbor) \
                    and (new_cost < self.cost_map[neighbor.x][neighbor.z] or force_update):
                _neighbors += [neighbor]
            if previous_cost > new_cost:
                cost_map[neighbor.x][neighbor.z] = new_cost
                distance_map[neighbor.x][neighbor.z] = new_dist
                predecessor_map[neighbor.x][neighbor.z] = updated_point

        def update_distances(updated_point):
            x, z = updated_point.x, updated_point.z
            if x + 1 < self.width:
                update_distance(updated_point, Point2D(x + 1, z), neighbors)
            if x - 1 >= 0:
                update_distance(updated_point, Point2D(x - 1, z), neighbors)
            if z + 1 < self.length:
                update_distance(updated_point, Point2D(x, z + 1), neighbors)
            if z - 1 >= 0:
                update_distance(updated_point, Point2D(x, z - 1), neighbors)

        def path_to_dest(dest_point):
            current_point = dest_point
            path = []
            while not self.is_road(current_point):
                path = [current_point] + path
                current_point = predecessor_map[current_point.x][current_point.z]
            return path

        def update_maps_info_at(point):
            x, z = point.x, point.z
            if self.cost_map[x, z] > cost_map[x, z]\
               or (self.is_accessible(point) and any(self.__is_point_obstacle(p) for p in self.path_map[x, z])):
                cost_map[point.x][point.z] = cost_map[point.x][point.z]
                self.distance_map[point.x][point.z] = distance_map[point.x][point.z]
                self.path_map[point.x][point.z] = path_to_dest(point)

        cost_map, distance_map, neighbors, predecessor_map = init()
        while len(neighbors) > 0:
            clst_neighbor = closest_neighbor()
            neighbors.remove(clst_neighbor)
            update_maps_info_at(clst_neighbor)
            update_distances(clst_neighbor)

    def a_star(self, root_point, ending_point):

        def init():
            x, z = root_point.x, root_point.z
            _distance_map = full((self.width, self.length), MAX_FLOAT)
            _distance_map[x][z] = 0
            _neighbours = [root_point]
            _predecessor_map = empty((self.width, self.length), dtype=object)
            return _distance_map, _neighbours, _predecessor_map

        def closest_neighbor():
            _closest_neighbors = []
            _min_heuristic = MAX_FLOAT
            for neighbor in neighbors:
                _heuristic = heuristic(neighbor)
                _current_heuristic = distance_map[neighbor.x][neighbor.z] + _heuristic
                if _current_heuristic < _min_heuristic:
                    _closest_neighbors = [neighbor]
                    _min_heuristic = _current_heuristic
                elif _current_heuristic == _min_heuristic:
                    _closest_neighbors += [neighbor]
            return choice(_closest_neighbors)

        def heuristic(point):
            return sqrt((point.x - ending_point.x) ** 2 + (point.z - ending_point.z) ** 2)

        def update_distance(updated_point, neighbor, _neighbors):
            edge_cost = self.cost(updated_point, neighbor)
            if edge_cost == maxint:
                return

            new_distance = distance_map[updated_point.x][updated_point.z] + edge_cost
            previous_distance = distance_map[neighbor.x][neighbor.z]
            if previous_distance >= MAX_FLOAT:
                _neighbors += [neighbor]
            if previous_distance > new_distance:
                distance_map[neighbor.x][neighbor.z] = new_distance
                predecessor_map[neighbor.x][neighbor.z] = updated_point

        def update_distances(updated_point):
            x, z = updated_point.x, updated_point.z
            if x + 1 < self.width:
                update_distance(updated_point, Point2D(x + 1, z), neighbors)
            if x - 1 >= 0:
                update_distance(updated_point, Point2D(x - 1, z), neighbors)
            if z + 1 < self.length:
                update_distance(updated_point, Point2D(x, z + 1), neighbors)
            if z - 1 >= 0:
                update_distance(updated_point, Point2D(x, z - 1), neighbors)

        def path_to_dest(dest_point):
            current_point = dest_point
            path = []
            while current_point.z != root_point.z or current_point.x != root_point.x:
                path = [current_point] + path
                current_point = predecessor_map[current_point.x][current_point.z]
            return path

        distance_map, neighbors, predecessor_map = init()
        clst_neighbor = root_point
        while len(neighbors) > 0 and (clst_neighbor.z != ending_point.z or clst_neighbor.x != ending_point.x):
            clst_neighbor = closest_neighbor()
            neighbors.remove(clst_neighbor)
            update_distances(clst_neighbor)

        if clst_neighbor.z != ending_point.z or clst_neighbor.x != ending_point.x:
            return []
        else:
            return path_to_dest(clst_neighbor)


class RoadGenerator(Generator):

    # stony_palette_str = ["Cobblestone", "Gravel", "Stone"]
    # stony_probs = [0.75, 0.20, 0.05]
    stony_palette = {"Cobblestone": 0.7, "Gravel": 0.2, "Stone": 0.1}

    def __init__(self, network, box, fluid_map):
        # type: (RoadNetwork, TransformBox, map.FluidMap) -> None
        Generator.__init__(self, box)
        self.__network = network  # type: RoadNetwork
        self.__fluids = fluid_map
        self.__origin = Point2D(box.minx, box.minz)

    def generate(self, level, height_map=None, palette=None):
        # type: (MCInfdevOldLevel, array, dict) -> None

        road_height_map = zeros(height_map.shape, dtype=uint8)
        # dimensions
        __network = full((self.width, self.length), Materials.Air)
        # block states
        # stony_palette = [4, 13, 1]

        x0, y0, z0 = self._box.origin

        print("[RoadGenerator] generating road blocks...", end='')
        for road_block in self.__network.road_blocks:
            road_width = self.__network.get_road_width(road_block) / 2.0
            # todo: flatten roads & use stairs/slabs + richer block palette
            for x in sym_range(road_block.x, road_width, self.width):
                for z in sym_range(road_block.z, road_width, self.length):
                    if road_height_map[x, z]:
                        continue
                    clear_tree_at(level, self._box, Point2D(x + x0, z + z0))
                    if not self.__fluids.is_water(x, z):
                        distance = abs(road_block.x - x) + abs(road_block.z - z)  # Norme 1
                        prob = distance / (8 * road_width)  # A calibrer
                        if not bernouilli(prob):
                            y, b = self.__compute_road_at(x, z, height_map, road_block)
                            __network[x, z] = b
                            road_height_map[x, z] = y

        for x in range(self.width):
            for z in range(self.length):
                if road_height_map[x, z]:
                    y, b = road_height_map[x, z], __network[x, z]
                    setBlock(level, (b.ID, b.blockData), x0 + x, y, z0 + z)
                    if bernouilli(0.05):
                        place_torch(level, x + x0, y + 1, z + z0)
                    elif bernouilli(0.8) or "slab" in b.stringID:
                        fillBlocks(level, TransformBox((x0+x, y+1, z0+z), (1, 3, 1)), Materials.Air)
                        setBlock(level, (0, 0), x0 + x, y + 1, z0 + z)
                    h = height_map[x, z]
                    if y > h+1 and bernouilli(1/3):
                        pole_box = TransformBox((x, h+1, z), (1, y-1-h, 1))
                        fillBlocks(level, pole_box, Materials["Oak Fence"])
        print("OK")

        Generator.generate(self, level, height_map)  # generate bridges

    def __compute_road_at(self, x, z, height_map, r):
        # type: (int, int, array, Point2D) -> (int, Block)
        material = choice(self.stony_palette.keys(), p=self.stony_palette.values())

        def inc(l):
            return all(l[i+1] > l[i] for i in range(len(l)-1))

        def dec(l):
            return all(l[i+1] < l[i] for i in range(len(l)-1))

        surrnd_road_xh = [height_map[_, r.z] for _ in sym_range(r.x, 1, self.width) if self.__network.is_road(_, r.z)]
        surrnd_road_zh = [height_map[r.x, _] for _ in sym_range(r.z, 1, self.length) if self.__network.is_road(r.x, _)]

        y = height_map[x, z]
        stair_material = choice(["Cobblestone", "Stone Brick"])
        lx, lz, sx, sz = len(surrnd_road_xh), len(surrnd_road_zh), std(surrnd_road_xh), std(surrnd_road_zh)
        if (lx >= 3) and ((lx > lz) or (lx == lz and sx > sz) or (lx == lz and sx == sz and bernouilli())):
            if inc(surrnd_road_xh):
                return y, Materials["{} Stairs (Bottom, East)".format(stair_material)]
            elif dec(surrnd_road_xh):
                return y, Materials["{} Stairs (Bottom, West)".format(stair_material)]
        elif lz >= 3:
            if inc(surrnd_road_zh):
                return y, Materials["{} Stairs (Bottom, South)".format(stair_material)]
            elif dec(surrnd_road_zh):
                return y, Materials["{} Stairs (Bottom, North)".format(stair_material)]

        surround_iter = product(sym_range(x, 1, self.width), sym_range(z, 1, self.length))
        surround_alt = [height_map[x, z] for (x, z) in surround_iter if self.__network.is_road(x, z)]
        y = mean(surround_alt) if surround_alt else 0
        try:
            b = Materials["{} Slab (Bottom)".format(material)] if (0.4 < (y % 1) < 0.8) else Materials[material]
        except KeyError:
            b = Materials["Stone Brick Slab (Bottom)"]
        y = int(y) if (y % 1) < 0.4 else int(y) + 1
        return y, b

    def handle_new_road(self, path):
        """
        Builds necessary bridges and stairs for every new path
        Assumes that it is called before the path is marked as a road in the RoadNetwork
        """
        prev_point = None
        cur_bridge = None
        for point in path:
            if self.__network.is_road(point):
                cur_bridge = None
            elif self.__fluids.is_water(point):
                if cur_bridge is None:
                    cur_bridge = Bridge(prev_point if prev_point is not None else point, self.__origin)
                cur_bridge += point
            elif cur_bridge is not None:
                cur_bridge += point
                self.children.append(cur_bridge)
                cur_bridge = None
            prev_point = point

        # todo: public stairs structures (/ ladders ?) in steep streets
