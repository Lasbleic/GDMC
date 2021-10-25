from typing import Dict, List, Tuple, Set

from sortedcontainers import SortedList

from parameters import MAX_INT
from utils import Point, BuildArea, manhattan


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

    def getPathTowards(self, target: Point) -> List[Point]:
        """
        Gets the path in the tree
        :param target: Node in the tree
        :return: path from tree source to target
        """
        node = target  # starts in the target
        path: List[Point] = []
        while node != self.getParent(node):
            path.insert(0, node)  # adds in first Point, keeps the order
            node = self.getParent(node)  # go up in the tree
        path.insert(0, node)  # finally, add the tree source
        return path


class GridGraph(Graph):
    def __init__(self, directed, **kwargs):
        """
        :param directed: is the graph directed
        :keyword step: granularity of the graph, def = 1
        :keyword width: width of the graph, def: terrain width
        :keyword length: length of the graph, def: terrain length
        :keyword cost: cost function to apply on edges (pair of nodes), def = road build cost
        """
        super().__init__(directed)
        self.step = kwargs.get("step", 1)
        self.width = kwargs.get("width", BuildArea().width)
        self.length = kwargs.get("length", BuildArea().length)
        self.__cost = kwargs.get("cost", manhattan)

    def getNeighbours(self, node):
        from utils import cardinal_directions
        res = set()
        for _dir in cardinal_directions():
            neigh = node + (_dir * self.step)
            if 0 <= neigh.x < self.width and 0 <= neigh.z < self.length:
                res.add(neigh)

        return res

    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError:
            node, neigh = item
            cost = self.__cost(node, neigh)
            self.addEdge(node, neigh, cost)
            return cost


def dijkstra(graph: Graph, source: Point or Set[Point], end_condition=(lambda _: False)) -> Tuple[Tree, Point]:
    """
    Dijkstra algorithm
    :param graph: graph to explore
    :param source: starting point of the exploration
    :param end_condition: ending condition on the explored node
    :return: (tree starting in source, last node explored)
    """

    if isinstance(source, Point):
        source = {source}
    tree = Tree()
    explored: Set[Point] = set()
    for source_pos in source:
        tree.addEdge(source_pos, source_pos, 0)
    neighbours: SortedList = SortedList(source, lambda pos: tree[tree.getParent(pos), pos])

    node: Point = source.pop()
    while neighbours:
        node = neighbours.pop(0)
        if end_condition(node):
            break

        elif node in explored:
            continue

        node_value = tree[tree.getParent(node), node]
        for neighbour in filter(lambda n: n not in explored, graph.getNeighbours(node)):
            cost = graph[node, neighbour]
            if cost < MAX_INT:
                tree.addEdge(node, neighbour, node_value + cost)
                neighbours.add(neighbour)
        explored.add(node)

    return tree, node
