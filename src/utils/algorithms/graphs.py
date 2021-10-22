from typing import Dict, List

from utils import Point


class Graph:
    def __init__(self, directed, wtype=float):
        self.__adjacency_lists: Dict[Point, Dict[Point, wtype]] = {}
        self.__directed = directed

    def addEdge(self, node, neighbour, weight=None):
        self.__addNode(node)
        self.__addNode(neighbour)
        self.__adjacency_lists[node][neighbour] = weight
        if not self.__directed:
            self.__adjacency_lists[neighbour][node] = weight

    def removeEdge(self, node, neighbour):
        self.__adjacency_lists[node].pop(neighbour)
        if not self.__directed:
            self.__adjacency_lists[neighbour].pop(node)

    def __addNode(self, node):
        if node not in self.nodes:
            self.__adjacency_lists[node] = {}

    @property
    def nodes(self):
        return self.__adjacency_lists.keys()

    def getNeighbours(self, node):
        return set(self.__adjacency_lists[node].keys())

    def __getitem__(self, item):
        node, neigh = item
        return self.__adjacency_lists[node][neigh]


class Tree(Graph):
    def __init__(self):
        super().__init__(True)
        self.__parent_node: Dict[Point, Point] = {}

    def addEdge(self, node, neighbour, weight=None):
        if neighbour in self.__parent_node:
            self.removeEdge(self.__parent_node[neighbour], neighbour)
        super().addEdge(node, neighbour, weight)
        self.__parent_node[neighbour] = node

    def getParent(self, node):
        if node in self.__parent_node:
            return self.__parent_node[node]
        return None

    def getPath(self, target: Point) -> List[Point]:
        node = target
        path: List[Point] = []
        while node != self.getParent(node):
            path.append(node)
            node = self.getParent(node)
        path.append(node)
        return [_ for _ in reversed(path)]


class CostFunctionGraph(Graph):
    def __init__(self, directed, cost_function):
        super().__init__(directed)
        self.__cost = cost_function

    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError:
            node, neigh = item
            cost = self.__cost(node, neigh)
            self.addEdge(node, neigh, cost)
            return cost

