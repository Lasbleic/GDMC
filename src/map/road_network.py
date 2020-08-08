# coding=utf-8
from __future__ import division, print_function

from math import sqrt
from sys import maxint

from numpy import zeros, full, empty
from numpy.random import choice

from parameters import MAX_LAMBDA, BRIDGE_COST
from pymclevel import MCLevel
from utilityFunctions import setBlock
from utils import Point2D, bernouilli, euclidean, clear_tree_at, place_torch

MAX_FLOAT = 100000.0
MAX_DISTANCE_CYCLE = 24
MIN_DISTANCE_CYCLE = 16


class RoadNetwork:

    def __init__(self, width, length, mc_map=None):
        # type: (int, int, Maps) -> RoadNetwork
        self.width = width
        self.length = length
        self.network = zeros((width, length), dtype=int)
        # Representing the distance from the network + the path to the network
        self.distance_map = full((width, length), maxint)
        self.path_map = empty((width, length), dtype=object)
        self.lambda_max = MAX_LAMBDA
        # self.lambda_max = 0
        self.network_node_list = []
        self.road_blocks = []
        self.network_extremities = []
        self.__all_maps = mc_map

    # region GETTER AND SETTER

    def __is_point_obstacle(self, point):
        if self.__all_maps is not None:
            return not self.__all_maps.obstacle_map.is_accessible(point)
        else:
            return False

    def __get_road_width(self, x, z=None):
        # type: (Point2D or int, None or int) -> (int, [Point2D])
        if z is None:
            # assert isinstance(x, Point2D)
            return self.__get_road_width(x.x, x.z)
        else:
            return self.network[x][z]

    def __get_closest_node(self, point):

        closest_node = None
        min_distance = MAX_FLOAT
        if len(self.network_node_list) == 0:
            closest_node = choice(self.road_blocks)
        for node in self.network_node_list:
            if euclidean(node, point) < min_distance:
                closest_node = node
                min_distance = euclidean(node, point)
        return closest_node

    def get_distance(self, x, z=None):
        # type: (Point2D or int, None or int) -> (int, [Point2D])
        if z is None:
            # assert isinstance(x, Point2D)
            return maxint if self.__is_point_obstacle(x) else self.get_distance(x.x, x.z)
        else:
            if self.distance_map[x][z] == maxint:
                return maxint
            return max(0, self.distance_map[x][z] - self.__get_road_width(self.__get_closest_road_point(Point2D(x, z))))

    def __set_road_block(self, x, z=None):
        # type: (Point2D or int, None or int) -> None
        if z is None:
            # assert isinstance(x, Point2D) # todo: find why this works when executing this class but not in mcedit
            self.__set_road_block(x.x, x.z)
            self.road_blocks += [x]
        else:
            self.network[x][z] = self.calculate_road_width(x, z)

    def is_road(self, x, z=None):
        # type: (Point2D or int, None or int) -> bool
        if z is None:
            # assert isinstance(x, Point2D)
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

        if any(self.__is_point_obstacle(point) for point in path):
            self.__invalidate(path[-1])
            self.__set_road_block(path[0])
            self.__update_distance_map([path[0]])
            self.__set_road(path[1:])
        else:
            for point in path:
                self.__set_road_block(point)
            self.__update_distance_map(path)

    def is_accessible(self, point):
        return self.distance_map[point.x][point.z] < maxint

    # endregion

    def calculate_road_width(self, x, z):
        return 1

    # region PUBLIC INTERFACE

    def create_road(self, root_point, ending_point):
        # type: (Point2D, Point2D) -> None
        path = self.a_star(root_point, ending_point)
        self.__set_road([root_point] + path)
        self.network_extremities += [root_point, ending_point]
        return

    def connect_to_network(self, point_to_connect):
        # type: (Point2D) -> None

        if self.is_accessible(point_to_connect):
            path = self.path_map[point_to_connect.x][point_to_connect.z]
        else:
            path = self.a_star(self.__get_closest_node(point_to_connect), point_to_connect)
        self.network_extremities += [point_to_connect]
        if path:
            self.__set_road(path)

        for node in self.network_node_list:
            if MIN_DISTANCE_CYCLE < euclidean(node, point_to_connect) < MAX_DISTANCE_CYCLE:
                self.create_road(point_to_connect, node)

        if path:
            self.network_node_list.append(path[0])

        return

    # endregion

    def generate(self, level):
        # type: (MCLevel) -> None
        # dimensions
        __network = zeros((self.width, self.length), dtype=int)
        # block states
        stony_palette = [4, 13, 1]
        stony_probs = [0.75, 0.20, 0.05]
        # grassy_palette = [208]
        # grassy_probs = [1]
        # sandy_palette = []
        # sandy_probs = []

        x0, y0, z0 = self.__all_maps.box.origin

        for road_block in self.road_blocks:
            road_width = self.__get_road_width(road_block)
            for x in range(max(0, road_block.x - road_width), min(self.width, road_block.x + road_width + 1)):
                for z in range(max(0, road_block.z - road_width), min(self.length, road_block.z + road_width + 1)):
                    clear_tree_at(level, Point2D(x + x0, z + z0))
                    if self.__all_maps.fluid_map.is_water(x, z):
                        __network[x, z] = 98
                    else:
                        distance = abs(road_block.x - x) + abs(road_block.z - z)  # Norme 1
                        prob = distance / (8 * road_width)  # A calibrer
                        if not bernouilli(prob):
                            block = choice(stony_palette, p=stony_probs)
                            __network[x][z] = block

        for x in range(self.width):
            for z in range(self.length):
                if __network[x][z] > 0:
                    y = max(self.__all_maps.water_height, self.__all_maps.height_map[x][z])
                    setBlock(level, (__network[x][z], 0), x0 + x, y, z0 + z)
                    if bernouilli(0.05):
                        place_torch(level, x + x0, y + 1, z + z0)

    def __update_distance_map(self, road, force_update=False):
        self.dijkstra(road, self.lambda_max, force_update)

    # return the path from the point satisfying the ending_condition to the root_point, excluded
    def dijkstra(self, root_points, max_distance, force_update):

        def init():
            _distance_map = full((self.width, self.length), maxint)
            for root_point in root_points:
                _distance_map[root_point.x][root_point.z] = 0
            _neighbours = root_points
            _predecessor_map = empty((self.width, self.length), dtype=object)
            return _distance_map, _neighbours, _predecessor_map

        def closest_neighbor():
            _closest_neighbors = []
            _min_distance = maxint
            for neighbor in neighbors:
                _current_distance = distance_map[neighbor.x][neighbor.z]
                if _current_distance < _min_distance:
                    _closest_neighbors = [neighbor]
                    _min_distance = _current_distance
                elif _current_distance == _min_distance:
                    _closest_neighbors += [neighbor]
            return choice(_closest_neighbors)

        def cost(orig_point, dest_point):
            fluids = self.__all_maps.fluid_map
            if fluids.is_water(dest_point) or fluids.is_lava(dest_point):
                return maxint
            return euclidean(orig_point, dest_point)

        def update_distance(updated_point, neighbor, _neighbors):
            edge_cost = cost(updated_point, neighbor)
            if edge_cost == maxint:
                return

            new_distance = distance_map[updated_point.x][updated_point.z] + edge_cost
            previous_distance = distance_map[neighbor.x][neighbor.z]
            if previous_distance >= maxint and new_distance <= max_distance and not self.is_road(neighbor) \
                    and new_distance < self.distance_map[neighbor.x][neighbor.z]:
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
            while not self.is_road(current_point):
                path = [current_point] + path
                current_point = predecessor_map[current_point.x][current_point.z]
            return path

        def update_maps_info_at(point):
            if self.distance_map[point.x][point.z] >= distance_map[point.x][point.z]:
                self.distance_map[point.x][point.z] = distance_map[point.x][point.z]
                self.path_map[point.x][point.z] = path_to_dest(point)

        distance_map, neighbors, predecessor_map = init()
        while len(neighbors) > 0:
            clst_neighbor = closest_neighbor()
            neighbors.remove(clst_neighbor)
            update_maps_info_at(clst_neighbor)
            update_distances(clst_neighbor)

    def a_star(self, root_point, ending_point):

        height_map = self.__all_maps.height_map

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

        def cost(src_point, dest_point):
            value = 1
            # if we don't have access to terrain info
            if self.__all_maps is None:
                return value

            # if dest is road, no additional cost
            if self.is_road(dest_point):
                return 1

            # if dest_point is an obstacle, return inf
            is_dest_obstacle = not self.__all_maps.obstacle_map.is_accessible(dest_point)
            is_dest_obstacle |= self.__all_maps.fluid_map.is_lava(dest_point, margin=8)
            if is_dest_obstacle:
                return maxint

            # if height gap from src to dest is too high, return inf
            _src_height = height_map[src_point.x, src_point.z]
            _dest_height = height_map[dest_point.x, dest_point.z]
            elevation = abs(int(_src_height) - int(_dest_height))
            if elevation > 1:
                value += elevation

            # finally, local cost depends on local steepness, measured as maximal elevation in a small radius
            m = 2
            local_height = height_map[max(0, dest_point.x - m): min(dest_point.x + m, self.width),
                                      max(0, dest_point.z - m): min(dest_point.z + m, self.length)]
            # value += (local_height.max() - local_height.min()) / m ** 2
            value += local_height.std()

            # additional cost to build on water
            if self.__all_maps.fluid_map.is_water(dest_point, margin=4):
                value += BRIDGE_COST
            return value

        def update_distance(updated_point, neighbor, _neighbors):
            edge_cost = cost(updated_point, neighbor)
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
