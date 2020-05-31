# coding=utf-8
from __future__ import division, print_function

from random import choice
import time
from numpy import zeros, full, empty
from sys import maxint
from building_seeding import BUILDING_ENCYCLOPEDIA
from utils import Point2D


class RoadNetwork:

    def __init__(self, width, length, mc_map=None):
        # type: (int, int, Maps) -> RoadNetwork
        self.width = width
        self.length = length
        self.network = zeros((length, width), dtype=int)
        # Representing the distance from the network + the path to the network
        self.distance_map = full((self.length, self.width), maxint)
        self.path_map = empty((self.length, self.width), dtype=object)
        self.lambda_max = BUILDING_ENCYCLOPEDIA["Flat_scenario"]["Accessibility"]["windmill"][2]
        # self.lambda_max = 0
        self.__all_maps = mc_map

    def set_road(self, x, z=None):
        # type: (Point2D or int, None or int) -> None
        if z is None:
            # assert isinstance(x, Point2D) # todo: find why this works when executing this class but not in mcedit
            self.set_road(x.x, x.z)
        else:
            self.update_distance_map(x, z)
            self.network[z][x] = 1

    def is_road(self, x, z=None):
        # type: (Point2D or int, None or int) -> bool
        if z is None:
            # assert isinstance(x, Point2D)
            return self.is_road(x.x, x.z)
        else:
            return self.network[z][x] == 1

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
            path = self.path_map[point_to_connect.z][point_to_connect.x]
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
            return self.distance_map[z][x]

    def update_distance_map(self, x, z):
        self.dijkstra(Point2D(x, z), lambda _: False, self.lambda_max, True)

    def dijkstra(self, root_point, ending_condition, max_distance=maxint, update_distance_map=False):

        def init():
            x, z = root_point.x, root_point.z
            _distance_map = full((self.length, self.width), maxint)
            _distance_map[z][x] = 0
            _neighbours = [root_point]
            _predecessor_map = full((self.length, self.width), None)
            return _distance_map, _neighbours, _predecessor_map

        def closest_neighbor():
            neighbors_distance = map(lambda neighbor: distance_map[neighbor.z][neighbor.x], neighbors)
            min_distance = min(neighbors_distance)
            closest_neighbors = [neighbors[i] for i, dist in enumerate(neighbors_distance) if dist == min_distance]
            return choice(closest_neighbors)

        def cost(src_point, dest_point):
            return 1

        def update_distance(updated_point, neighbor, _neighbors):
            new_distance = distance_map[updated_point.z][updated_point.x] + cost(updated_point, neighbor)
            previous_distance = distance_map[neighbor.z][neighbor.x]
            if previous_distance >= maxint and new_distance <= max_distance and not self.is_road(neighbor):
                _neighbors += [neighbor]
            if previous_distance > new_distance:
                distance_map[neighbor.z][neighbor.x] = new_distance
                predecessor_map[neighbor.z][neighbor.x] = updated_point

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
                current_point = predecessor_map[current_point.z][current_point.x]
            return [root_point] + path

        def update_distance_map_at(point):
            if self.get_distance(point) >= distance_map[point.z][point.x]:
                self.distance_map[point.z][point.x] = distance_map[point.z][point.x]
                self.path_map[point.z][point.x] = path_to_dest(point)

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
            return path_to_dest(clst_neighbor), distance_map[clst_neighbor.z][clst_neighbor.x]

    def is_accessible(self, point):
        return self.get_distance(point) < maxint


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
