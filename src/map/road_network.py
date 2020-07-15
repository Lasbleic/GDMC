# coding=utf-8
from __future__ import division, print_function

import time
from numpy import zeros, full, empty
from numpy.random import choice
from sys import maxint

from parameters import MAX_LAMBDA, MAX_ROAD_WIDTH, BRIDGE_COST
from pymclevel import MCLevel
from utils import Point2D, bernouilli
from utilityFunctions import setBlock


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
        self.road_blocks = []
        # self.lambda_max = 0
        self.__all_maps = mc_map

    def set_road(self, x, z=None):
        # type: (Point2D or int, None or int) -> None
        if z is None:
            # assert isinstance(x, Point2D) # todo: find why this works when executing this class but not in mcedit
            self.set_road(x.x, x.z)
            self.road_blocks += [x]
        else:
            self.update_distance_map(x, z)
            self.network[x][z] = 1


    def is_road(self, x, z=None):
        # type: (Point2D or int, None or int) -> bool
        if z is None:
            # assert isinstance(x, Point2D)
            return self.is_road(x.x, x.z)
        else:
            return self.network[x][z] == 1

    def create_road(self, path):
        # type: ([Point2D]) -> None
        for point in path:
            self.set_road(point)

    def find_road(self, root_point, ending_point):
        # type: (Point2D, Point2D) -> None
        path, distance = self.dijkstra(root_point, lambda point: point == ending_point)
        self.create_road(path)
        return

    def connect_to_network(self, point_to_connect):
        # type: (Point2D) -> None
        if self.is_accessible(point_to_connect):
            path = self.path_map[point_to_connect.x][point_to_connect.z]
        else:
            path, distance = self.dijkstra(point_to_connect, lambda point: self.is_road(point))
        self.create_road(path)
        return

    def get_distance(self, x, z=None):
        # type: (Point2D or int, None or int) -> (int, [Point2D])
        if z is None:
            # assert isinstance(x, Point2D)
            return self.get_distance(x.x, x.z)
        else:
            return self.distance_map[x][z]

    def update_distance_map(self, x, z):
        self.dijkstra(Point2D(x, z), lambda _: False, self.lambda_max, True)

    def dijkstra(self, root_point, ending_condition, max_distance=maxint, update_distance_map=False):

        def init():
            x, z = root_point.x, root_point.z
            _distance_map = full((self.width, self.length), maxint)
            _distance_map[x][z] = 0
            _neighbours = [root_point]
            _predecessor_map = full((self.width, self.length), None)
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

        def cost(src_point, dest_point):
            _src_height = int(self.__all_maps.height_map[src_point.x, src_point.z])
            _dest_height = int(self.__all_maps.height_map[dest_point.x, dest_point.z])
            std_cost = abs(_src_height - _dest_height) + 1
            if not self.__all_maps.obstacle_map.is_accessible(dest_point) or self.__all_maps.fluid_map.is_lava(dest_point):
                return maxint
            if self.__all_maps.fluid_map.is_water(dest_point):
                return std_cost + BRIDGE_COST
            return std_cost

        def update_distance(updated_point, neighbor, _neighbors):
            c = cost(updated_point, neighbor)
            if c == maxint:
                return
            new_distance = distance_map[updated_point.x][updated_point.z] + c
            previous_distance = distance_map[neighbor.x][neighbor.z]
            if previous_distance >= maxint and new_distance <= max_distance and not self.is_road(neighbor)\
                    and new_distance < self.distance_map[neighbor.x, neighbor.z]:
                _neighbors += [neighbor]
            if previous_distance > new_distance:
                distance_map[neighbor.x][neighbor.z] = new_distance
                predecessor_map[neighbor.x][neighbor.z] = updated_point

        def update_distances(updated_point):
            x, z = updated_point.x, updated_point.z
            if x + 1 < self.width:
                update_distance(updated_point, Point2D(x + 1, z), neighbors)
                """if z + 1 < self.length:
                    update_distance(updated_point, Point2D(x + 1, z + 1), neighbors)
                if z - 1 >= 0:
                    update_distance(updated_point, Point2D(x + 1, z - 1), neighbors)"""
            if x - 1 >= 0:
                update_distance(updated_point, Point2D(x - 1, z), neighbors)
                """if z + 1 < self.length:
                    update_distance(updated_point, Point2D(x - 1, z + 1), neighbors)
                if z - 1 >= 0:
                    update_distance(updated_point, Point2D(x - 1, z - 1), neighbors)"""
            if z + 1 < self.length:
                update_distance(updated_point, Point2D(x, z + 1), neighbors)
            if z - 1 >= 0:
                update_distance(updated_point, Point2D(x, z - 1), neighbors)

        def path_to_dest(dest_point):
            current_point = dest_point
            path = []
            while current_point != root_point:
                path = [current_point] + path
                current_point = predecessor_map[current_point.x][current_point.z]
            return [root_point] + path

        def update_distance_map_at(point):
            if self.get_distance(point) >= distance_map[point.x][point.z]:
                self.distance_map[point.x][point.z] = distance_map[point.x][point.z]
                self.path_map[point.x][point.z] = path_to_dest(point)

        distance_map, neighbors, predecessor_map = init()
        clst_neighbor = root_point
        while len(neighbors) > 0 and not ending_condition(clst_neighbor):
            clst_neighbor = closest_neighbor()
            if update_distance_map:
                update_distance_map_at(clst_neighbor)
            neighbors.remove(clst_neighbor)
            update_distances(clst_neighbor)

        if not ending_condition(clst_neighbor):
            return [], maxint
        else:
            return path_to_dest(clst_neighbor), distance_map[clst_neighbor.x][clst_neighbor.z]

    def is_accessible(self, point):
        return self.get_distance(point) < maxint

    def generate(self, level, origin):
        # type: (MCLevel, (int, int, int)) -> None
        # dimensions
        x0, y0, z0 = origin
        __network = zeros((self.width, self.length), dtype=int)
        # block states
        stony_palette = [4, 13, 1]
        stony_probs = [0.75, 0.20, 0.05]
        grassy_palette = [208]
        grassy_probs = [1]
        sandy_palette = []
        sandy_probs = []

        for road_block in self.road_blocks:
            width = self.__get_road_width(road_block)
            for x in range(max(0, road_block.x - width + 1), min(self.width, road_block.x + width - 1)):
                for z in range(max(0, road_block.z - width + 1), min(self.width, road_block.z + width - 1)):
                    distance = abs(road_block.x - x) + abs(road_block.z - z) #Norme 1
                    prob = 1 - distance/(8*width) #A calibrer
                    if not bernouilli(prob):
                        block = choice(grassy_palette)
                        __network[x][z] = block

        x0, y0, z0 = self.__all_maps.box.origin
        for x in range(self.width):
            for z in range(self.length):
                if __network[x][z] > 0:
                    y = max(63, self.__all_maps.height_map[x][z])
                    setBlock(level, (__network[x][z], 0), x0 + x, y, z0 + z)

    def __get_road_width(self, road_block):
        return 3


if __name__ == "__main__":

    """
    mapTest = zeros((5, 8), dtype=int)
    print(mapTest)
    mapTest[0][1] = 5
    print(mapTest)
    
    print(BUILDING_ENCYCLOPEDIA["Flat_scenario"]["Accessibility"]["windmill"][2])
    net = RoadNetwork(100, 10)
    p1, p2 = Point2D(0, 0), Point2D(99, 9)
    print(map(str, net.dijkstra(p1, lambda point: point == p2)))
    net.find_road(p1, p2)"""

    N = 10
    start = time.time()
    p1, p2, p3 = Point2D(0, 6), Point2D(9, 1), Point2D(0, 0)
    net2 = RoadNetwork(N, N)
    net2.find_road(p1, p2)
    print("============ {ROAD FROM (0,6) to (9, 1)}===============")
    print(net2.network)
    print(net2.get_distance(p3))
    net2.connect_to_network(p3)
    print(net2.get_distance(p3))
    print("============ {ROAD FROM (0,0) to Network}===============")
    print(net2.network)

    end = time.time()
    print(end - start)

    # Save vizus in visu/stock folder

    # Import vizu classes
    # -> "from pre_processing import Map, MapStock" is sufficient if folder visu is a Source Root
    import sys
    sys.path.insert(1, '../../visu')
    from pre_processing import Map, MapStock
    import numpy as np
    from matplotlib import colors

    net2 = RoadNetwork(N, N)
    net2.find_road(p1, p2)
    print("============ {ROAD FROM (0,6) to (9, 1)}===============")
    print(net2.network)

    road_cmap = colors.ListedColormap(['forestgreen', 'beige'])
    road_map = Map("road_network", N, np.copy(net2.network), road_cmap, (0, 1), ['Grass', 'Road'])

    net2.connect_to_network(p3)
    print("============ {ROAD FROM (0,0) to Network}===============")
    print(net2.network)

    road_cmap = colors.ListedColormap(['forestgreen', 'beige'])
    road_map2 = Map("road_network_2", N, np.copy(net2.network), road_cmap, (0, 1), ['Grass', 'Road'])

    the_stock = MapStock("road_network_test", N, clean_dir=True)
    the_stock.add_map(road_map)
    the_stock.add_map(road_map2)
