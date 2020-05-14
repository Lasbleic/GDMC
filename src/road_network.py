from __future__ import division, print_function

from math import sqrt
from numpy import zeros, full
from sys import maxint


class Point2D:

    def __init__(self, x, z):
        self.x = x
        self.z = z

    def __str__(self):
        return "(x:" + str(self.x) + "; z:" + str(self.z) + ")"

    def __eq__(self, other):
        return other.x == self.x and other.z == self.z


class RoadNetwork:

    def __init__(self, width, length):
        self.width = width
        self.length = length
        self.network = zeros((length, width), dtype=int)

    def set_road(self, point):
        self.set_road(point.x, point.z)

    def set_road(self, x, z):
        self.network[z][x] = 1

    def is_road(self, point):
        return self.is_road(point.x, point.z)

    def is_road(self, x, z):
        return self.network[z][x] == 1

    def create_road(self, path):
        for point in path:
            self.set_road(point)

    def find_road(self, root_point, ending_point):
        path, distance = self.dijkstra(root_point, lambda point: point == ending_point)
        self.create_road(path)
        return

    def connect_to_network(self, point_to_connect):
        path, distance = self.dijkstra(point_to_connect, lambda point: self.is_road(point))
        self.create_road(path)
        return

    def dijkstra(self, root_point, ending_condition):

        def init():
            x, z = root_point.x, root_point.z
            distance_map = full((self.length, self.width), maxint)
            distance_map[z][x] = 0
            neighbours = [root_point]
            predecessor_map = full((self.length, self.width), None)
            return distance_map, neighbours, predecessor_map

        def closest_neighbor():
            neighbors_distance = map(lambda neighbor: distance_map[neighbor.z][neighbor.x], neighbors)
            min_distance = min(neighbors_distance)
            return neighbors[neighbors_distance.index(min_distance)]

        def cost(src_point, dest_point):
            if src_point.x == dest_point.x or src_point.z == dest_point.z:
                return 1
            else:
                return sqrt(2)
            return 1

        def update_distance(updated_point, neighbor, neighbors):
            new_distance = distance_map[updated_point.z][updated_point.x] + cost(updated_point, neighbor)
            previous_distance = distance_map[neighbor.z][neighbor.x]
            if previous_distance >= maxint:
                neighbors += [neighbor]
            if previous_distance > new_distance:
                distance_map[neighbor.z][neighbor.x] = new_distance
                predecessor_map[neighbor.z][neighbor.x] = updated_point

        def update_distances(updated_point, neighbors):
            x, z = updated_point.x, updated_point.z
            if x + 1 < self.width:
                update_distance(updated_point, Point2D(x + 1, z), neighbors)
                if z + 1 < self.length:
                    update_distance(updated_point, Point2D(x + 1, z + 1), neighbors)
                if z - 1 >= 0:
                    update_distance(updated_point, Point2D(x + 1, z - 1), neighbors)
            if x - 1 >= 0:
                update_distance(updated_point, Point2D(x - 1, z), neighbors)
                if z + 1 < self.length:
                    update_distance(updated_point, Point2D(x - 1, z + 1), neighbors)
                if z - 1 >= 0:
                    update_distance(updated_point, Point2D(x - 1, z - 1), neighbors)
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

        distance_map, neighbors, predecessor_map = init()
        clst_neighbor = root_point
        while len(neighbors) > 0 and not ending_condition(clst_neighbor):
            clst_neighbor = closest_neighbor()
            neighbors.remove(clst_neighbor)
            update_distances(clst_neighbor, neighbors)

        if not ending_condition(clst_neighbor):
            return [], maxint
        else:
            return path_to_dest(clst_neighbor), distance_map[clst_neighbor.z][clst_neighbor.x]


if __name__ == "__main__":
    """
    mapTest = zeros((5, 8), dtype=int)
    print(mapTest)
    mapTest[0][1] = 5
    print(mapTest)
    """
    net = RoadNetwork(100, 10)
    print(map(str, net.dijkstra(Point2D(0, 0), lambda point: point == Point2D(99, 9))))

