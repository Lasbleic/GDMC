from math import ceil
from typing import List, Set, Tuple

from numpy import full
from sortedcontainers import SortedList

from parameters import MAX_INT
from terrain.road_network import road_recording_cost, RoadNetwork
from utils import Singleton, BuildArea, Point, argmin, euclidean
from .graphs import Graph, Tree, GridGraph, dijkstra
from .. import Position


class PathFinder(metaclass=Singleton):
    """
    Path finder. Combines Dijkstra for optimal medium step path, and A* to follow this rough path from origin to destination
    """
    def __init__(self, granularity: int):
        self.__area: BuildArea = BuildArea()
        self.__granularity: int = granularity

        self.__has_road = full((self.gwidth, self.glength), False, dtype=bool)

        from terrain.road_network import road_build_cost
        self.__cost_graph: Graph = GridGraph(True, step=granularity, cost=road_build_cost)
        self.__local_cost_graph: Graph = GridGraph(True, step=1, cost=road_recording_cost)

    def getRoughPath(self, target: Position, source: Position = None):
        """
        Finds rough path (with a step > 1) from source to target. Assumes that source is already connected to the road net
        :param target: point to connect, dijkstra will start in this position, and try to walk up to the source, or the road net
        :param source: optional target point
        :return: path, ie list of points, from source (or possible source) to target
        """
        step = self.__granularity
        rough_target = (target - target % step)
        if source is None:
            # If target is None, Dijkstra explores until finding a road point
            end_condition = (lambda _: self.__hasRoad(_))
            target_tree, rough_source = dijkstra(self.__cost_graph, rough_target, end_condition)  # type: Tree, Position
            source = rough_source
        else:
            rough_source = source - source % step
            # Otherwise, explores until joining both positions
            end_condition = (lambda _: _ == rough_source)  # ends in rough source
            target_tree, _ = dijkstra(self.__cost_graph, rough_target, end_condition)  # type: Tree, Position  # starts in target

        # In both cases, target_tree starts in rough_target
        targetSourcePath = target_tree.getPathTowards(rough_source)
        sourceTargetPath = list(reversed(targetSourcePath))  # path from source to target
        if len(sourceTargetPath) < 3:
            rough_path = [source, target]
        else:
            rough_path = [source] + sourceTargetPath[1: -1] + [target]
        return rough_path

    def getPath(self, source: Position, target: Position):
        """
        Gets a suboptimal path from source to target
        :param source: source point
        :param target: target point
        :return:
        """
        if source == target:
            return [source]
        rough_path = self.getRoughPath(target, source)
        return self.__astar(source, target, rough_path)

    def getPathTowards(self, target: Position):
        """
        Gets a suboptimal path towards unconnected point. Finds the most suitable road point to connect from
        :param target: point to connect
        :return: path from existing road point toward target
        """
        roughPathTowardsTarget = self.getRoughPath(target)
        roughSource = roughPathTowardsTarget[0]
        _, source = dijkstra(self.__local_cost_graph, roughSource, end_condition=(lambda _: RoadNetwork().is_road(_)))
        return self.__astar(source, target, roughPathTowardsTarget)

    def registerRoad(self, road: List[Position]):
        for p in road:
            self.__setRoad(p)
        pass  # mark road points & update cost graph

    def __setRoad(self, p: Position):
        q = p // self.__granularity
        self.__has_road[q.x, q.z] = True

    def __hasRoad(self, p: Position):
        q = p // self.__granularity
        return self.__has_road[q.x, q.z]

    def __dijkstra(self, source: Position, target: Position = None) -> Tuple[Tree, Position]:
        """
        Dijkstra algorithm
        """

        if isinstance(source, Point):
            source = {source}
        tree = Tree()
        explored: Set[Position] = set()
        for source_pos in source:
            tree.addEdge(source_pos, source_pos, 0)
        neighbours: SortedList = SortedList(source, lambda pos: -tree[tree.getParent(pos), pos])

        node: Position = target
        while neighbours:
            node = neighbours.pop()
            if node == target or self.__hasRoad(node):
                break

            elif node in explored:
                continue

            for neighbour in filter(lambda n: n not in explored, self.__neighbourhood(node, self.__granularity)):
                cost = self.__cost_graph[node, neighbour]
                if cost < MAX_INT and (neighbour not in tree.getNeighbours(node) or tree[tree.getParent(neighbour), neighbour] > cost):
                    tree.addEdge(node, neighbour, cost)
                    neighbours.add(neighbour)
            explored.add(node)

        return tree, node

    def __neighbourhood(self, node: Point, step: int) -> Set[Point]:
        from utils import cardinal_directions
        res = set()
        for _dir in cardinal_directions():
            neigh = node + (_dir * step)
            if 0 <= neigh.x < self.__area.width and 0 <= neigh.z < self.__area.length:
                res.add(neigh)

        return res

    def __astar(self, source: Position, target: Position, rough_path):
        """
        Custom A* algorithm - computes path with decreasing steps
        :param source: source point (x, z)
        :param target: target point (x, z)
        """
        from terrain.road_network import road_build_cost as cost_function

        def build_cumsum() -> List:
            """
            Computes target heuristic for each point in the rough path
            :return:
            """
            l = [0]
            for i in range(len(rough_path) - 1, 0, -1):
                l.append(l[-1] + euclidean(rough_path[i], rough_path[i - 1]))
            return list(reversed(l))

        def init():
            dims = self.__area.width, self.__area.length
            _distance_map = full(dims, MAX_INT, dtype=float)
            _distance_map[source.x, source.z] = 0
            _predecessor_map = full(dims, None)
            _heuristic_map = full(dims, MAX_INT, dtype=float)
            return _distance_map, _predecessor_map, _heuristic_map

        def heuristic(_pos):
            if heuristic_map[_pos.x, _pos.z] == MAX_INT:
                _id = argmin(map(lambda p: euclidean(_pos, p), rough_path))  # index of the closest reference point
                # heuristic = distance towards this point + heuristic starting in this point
                if _id >= len(rough_path) - 2:
                    heuristic_map[_pos.x, _pos.z] = euclidean(_pos, target)
                else:
                    heuristic_map[_pos.x, _pos.z] = euclidean(_pos, rough_path[_id + 2]) + cumsum[_id + 2]
            return heuristic_map[_pos.x, _pos.z]

        def update_distance(_node, _neigh):
            cost = cost_function(_node, _neigh)
            if cost == MAX_INT:
                return
            old_dist = distance_map[_neigh.x, _neigh.z]
            new_dist = distance_map[_node.x, _node.z] + cost
            if new_dist < old_dist:
                neighbours.add(_neigh)
                distance_map[_neigh.x, _neigh.z] = new_dist
                predecessor_map[_neigh.x, _neigh.z] = _node

        def path_to_dest():
            _node = target
            _path = [_node]
            while _node != source:
                _node = predecessor_map[_node.x, _node.z]
                _path.append(_node)
            return list(reversed(_path))

        cumsum = build_cumsum()
        distance_map, predecessor_map, heuristic_map = init()
        neighbours = SortedList([source], lambda pos: distance_map[pos.x, pos.z] + heuristic(pos))

        node = source

        while node != target and neighbours:

            # pick new exploration point -> point closer to target
            node = neighbours.pop(0)

            # explore neighbours to this point
            for neighbour in self.__neighbourhood(node, 1):
                update_distance(node, neighbour)

        if predecessor_map[target.x, target.z]:
            return path_to_dest()
        return []

    @property
    def gwidth(self):
        return int(ceil(self.__area.width / self.__granularity))

    @property
    def glength(self):
        return int(ceil(self.__area.length / self.__granularity))
