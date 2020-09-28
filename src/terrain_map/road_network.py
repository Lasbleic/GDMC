# coding=utf-8
from __future__ import division, print_function

from sys import maxint

from numpy import empty, argmin

from utils import *
import terrain_map
from generation.generators import *
from generation.road_generator import RoadGenerator
from parameters import *

MAX_FLOAT = 100000.0
MAX_DISTANCE_CYCLE = 32
MIN_DISTANCE_CYCLE = 24
DIST_BETWEEN_NODES = 12


class RoadNetwork:

    def __init__(self, width, length, mc_map=None):
        # type: (int, int, terrain_map.Maps) -> RoadNetwork
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
        self.special_road_blocks = set()  # type: Set[Point2D]
        self.network_extremities = []
        self.__generator = RoadGenerator(self, mc_map.box, mc_map) if mc_map else None
        self.__all_maps = mc_map
        self.cycle_creation_condition = self.__natural_path_cycle_creation  # self.__distance_based_cycle_creation

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
            # return self.network[x, z]
            return 1

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
            # steep roads are not marked as road points
            maps = self.__all_maps
            if maps and (maps.height_map.steepness(xp.x, xp.z, margin=1) >= 0.35 or maps.fluid_map.is_water(xp)
                         or not maps.obstacle_map.is_accessible(xp)):
                self.special_road_blocks.add(xp)
            else:
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
            p = path[-1]
            refresh_perimeter = product(sym_range(p.x, len(path), self.width), sym_range(p.z, len(path), self.length))
            refresh_sources = []
            for x, z in refresh_perimeter:
                if self.is_road(x, z):
                    refresh_sources.append(Point2D(x, z))
                else:
                    self.distance_map[x, z] = maxint
                    self.cost_map[x, z] = maxint
                    self.path_map[x, z] = []
            self.__update_distance_map(refresh_sources)
            path = self.path_map[p.x, p.z]
            # path = self.a_star(path[0], path[-1])
        # else:
        if self.__generator:
            self.__generator.handle_new_road(path)
        for point in path:
            self.__set_road_block(point)
        self.__update_distance_map(path, force_update)

    def is_accessible(self, point):
        return type(self.path_map[point.x][point.z]) == list

    # endregion

    def calculate_road_width(self, x, z):
        """
        todo: algorithme simulationniste ? dépendance au centre ?
        """
        # return self.network[x, z]
        return 3

    # region PUBLIC INTERFACE

    def create_road(self, root_point, ending_point):
        # type: (Point2D, Point2D) -> List[Point2D]
        path = self.a_star(root_point, ending_point, RoadNetwork.road_build_cost)
        self.__set_road([root_point] + path)
        self.network_extremities += [root_point, ending_point]
        return path

    def connect_to_network(self, point_to_connect):
        # type: (Point2D) -> List[Set[Point2D]]
        from time import time

        # if self.is_road(point_to_connect):
        if self.get_distance(point_to_connect) < MAX_ROAD_WIDTH:
            return []

        if self.is_accessible(point_to_connect):
            path = self.path_map[point_to_connect.x][point_to_connect.z]
            print("[RoadNetwork] Found existing road")
        else:
            _t0 = time()
            path = self.a_star(self.__get_closest_node(point_to_connect), point_to_connect, RoadNetwork.road_build_cost)
            print("[RoadNetwork] Computed road path in {:0.2f}s".format(time()-_t0))
        self.network_extremities += [point_to_connect]
        if path:
            self.__set_road(path)

        _t1, cycles = None, []
        for node in self.network_node_list + self.network_extremities:
            if self.cycle_creation_condition(node, point_to_connect):
                old_path = set(self.a_star(node, point_to_connect, RoadNetwork.road_only_cost))
                new_path = set(self.create_road(point_to_connect, node)).difference(old_path)
                if len(new_path) > DIST_BETWEEN_NODES:
                    # worth building this path
                    if _t1 is None:
                        _t1 = time()
                    cycles.append(set(old_path).union(set(new_path)))
        if _t1 is not None:
            print("[RoadNetwork] Computed road cycles in {:0.2f}s".format(time()-_t1))

        if path and all(euclidean(path[0], node) > DIST_BETWEEN_NODES for node in self.network_node_list):
            self.network_node_list.append(path[0])

        return cycles

    # endregion

    def generate(self, level):
        # type: (MCInfdevOldLevel) -> None
        hm = self.__all_maps.height_map  # type: terrain_map.HeightMap
        self.__generator.generate(level, hm.box_height(self.__all_maps.box, False))

    def __update_distance_map(self, road, force_update=False):
        self.dijkstra(road, self.lambda_max, force_update)

    def road_build_cost(self, src_point, dest_point):
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

    def road_only_cost(self, src_point, dest_point):
        return 1 if self.is_road(dest_point) else maxint

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
            if self.__all_maps is None:
                return euclidean(orig_point, dest_point)

            fluids = self.__all_maps.fluid_map
            if fluids.is_lava(dest_point):
                return maxint
            elif fluids.is_water(dest_point):
                return BRIDGE_UNIT_COST
            else:
                orig_height = self.__all_maps.height_map.fluid_height(orig_point)
                dest_height = self.__all_maps.height_map.fluid_height(dest_point)
                if abs(orig_height - dest_height) > 1:
                    return maxint
            return euclidean(orig_point, dest_point)

        def update_distance(updated_point, neighbor, _neighbors):
            edge_cost = self.road_build_cost(updated_point, neighbor)
            edge_dist = distance(updated_point, neighbor)
            if edge_cost == maxint or edge_dist == maxint:
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
            path = path_to_dest(updated_point)
            is_straight_road = (len(path) < 3) or (path[-1].x == path[-3].x) or (path[-1].z == path[-3].z)
            if (x + 1 < self.width) and (is_straight_road or path[-2].z == z):
                update_distance(updated_point, Point2D(x + 1, z), neighbors)
            if (x - 1 >= 0) and (is_straight_road or path[-2].z == z):
                update_distance(updated_point, Point2D(x - 1, z), neighbors)
            if (z + 1 < self.length) and (is_straight_road or path[-2].x == x):
                update_distance(updated_point, Point2D(x, z + 1), neighbors)
            if (z - 1 >= 0) and (is_straight_road or path[-2].x == x):
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
            if self.cost_map[x, z] > cost_map[x, z]:
                self.cost_map[point.x][point.z] = cost_map[point.x][point.z]
                self.distance_map[point.x][point.z] = distance_map[point.x][point.z]
                self.path_map[point.x][point.z] = path_to_dest(point)

        cost_map, distance_map, neighbors, predecessor_map = init()
        while len(neighbors) > 0:
            clst_neighbor = closest_neighbor()
            neighbors.remove(clst_neighbor)
            update_maps_info_at(clst_neighbor)
            update_distances(clst_neighbor)

    def a_star(self, root_point, ending_point, cost_function):
        # type: (Point2D, Point2D, Callable[[RoadNetwork, Point2D, Point2D], int]) -> List[Point2D]
        """
        Parameters
        ----------
        root_point path origin
        ending_point path destination
        cost_function (RoadNetwork, Point2D, Point2D) -> int

        Returns
        -------
        best first path from root_point to ending_point if any exists
        """

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
            return 1.3 * euclidean(point, ending_point)

        def update_distance(updated_point, neighbor, _neighbors):
            edge_cost = cost_function(self, updated_point, neighbor)
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
            path = path_to_dest(updated_point)
            is_straight_road = (len(path) < 3) or (path[-1].x == path[-3].x) or (path[-1].z == path[-3].z)
            if (x + 1 < self.width) and (is_straight_road or path[-2].z == z):
                update_distance(updated_point, Point2D(x + 1, z), neighbors)
            if (x - 1 >= 0) and (is_straight_road or path[-2].z == z):
                update_distance(updated_point, Point2D(x - 1, z), neighbors)
            if (z + 1 < self.length) and (is_straight_road or path[-2].x == x):
                update_distance(updated_point, Point2D(x, z + 1), neighbors)
            if (z - 1 >= 0) and (is_straight_road or path[-2].x == x):
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

    def __distance_based_cycle_creation(self, node1, node2):
        return MIN_DISTANCE_CYCLE < euclidean(node1, node2) < MAX_DISTANCE_CYCLE

    def __natural_path_cycle_creation(self, node1, node2):
        straight_dist = euclidean(node1, node2)
        if straight_dist > MAX_DISTANCE_CYCLE or straight_dist == 0:
            # todo: cette condition pourrait varier selon la distance au(x) centre-ville(s), pour modéliser des patés
            #  de maison plus petits/denses en centre qu'en périphérie
            return False

        existing_path = self.a_star(node1, node2, RoadNetwork.road_only_cost)
        current_dist = len(existing_path)
        if current_dist / straight_dist >= 2.5:
            return True
        return False

