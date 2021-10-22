from math import ceil
from typing import List, Set

from numpy import full
from sortedcontainers import SortedList

from parameters import MAX_INT
from utils import Singleton, BuildArea, Point, argmin, euclidean
from .graphs import Graph, Tree, CostFunctionGraph
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
        self.__cost_graph: Graph = CostFunctionGraph(True, road_build_cost)

    def getRoughPath(self, source: Position, target: Position):
        step = self.__granularity
        rough_source = source - source % step
        rough_target = target - target % step
        target_tree: Tree = self.__dijkstra(rough_target, rough_source)
        rough_path = list(reversed(target_tree.getPath(rough_source)))
        if len(rough_path) < 3:
            rough_path = [source, target]
        else:
            rough_path = [source] + rough_path[1: -1] + [target]
        return rough_path

    def getPath(self, source: Position, target: Position):
        if source == target:
            return [source]
        rough_path = self.getRoughPath(source, target)
        return self.__astar(source, target, rough_path)

    def registerRoad(self, road: List[Position]):
        pass  # mark road points & update cost graph

    def __dijkstra(self, source: Position, target: Position) -> Tree:
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

        while neighbours:
            node = neighbours.pop()
            if node == target:
                break

            elif node in explored:
                continue

            for neighbour in filter(lambda n: n not in explored, self.__neighbourhood(node, self.__granularity)):
                cost = self.__cost_graph[node, neighbour]
                if cost < MAX_INT and (neighbour not in tree.getNeighbours(node) or tree[tree.getParent(neighbour), neighbour] > cost):
                    tree.addEdge(node, neighbour, cost)
                    neighbours.add(neighbour)
            explored.add(node)

        return tree

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
