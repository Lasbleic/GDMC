from graphs.graph import Graph
from graphs.edge import Edge
from graphs.node import Node
import RoadNode
import RoadSegment
from numpy import zeros, ones
from math import sqrt

def find_path(point1, point2, height_map):
    return []

def euclidean_distance(point1, point2):
    return sqrt( (point1.x - point2.x)**2 + (point1.z - point2.z)**2 )

MAX_LENGTH_EDGE = 20

class RoadNetwork(Graph):

    def __init__(self, width, length, height_map = None):
        super().__init__()
        self.width = width
        self.length = length
        self.distance_map = zeros((width, length), dtype=(int, object))
        if height_map is None:
            self.height_map = ones((width, length), dtype=int)
        else:
            self.height_map = height_map
        

    # region PUBLIC INTERFACE

    def create_road(self, root_point, ending_point):
        # type: (Point2D, Point2D) -> List[Point2D]
        node1 = RoadNode(root_point)
        node2 = RoadNode(ending_point)
        self.add_connex_component(node1)
        self.add_connex_component(node2)
        self._connect(node2, node1)
        pass

    def connect_to_network(self, point_to_connect):
        # type: (Point2D) -> List[Set[Point2D]]
        node_to_connect = RoadNode(point_to_connect)
        self.add_connex_component(node_to_connect)
        node2 = self._get_closest_node(node_to_connect, euclidean_distance)
        self._connect(node2, node_to_connect)
        pass

    def generate(self, level):
        # type: (MCInfdevOldLevel) -> None
        pass

    # endregion

    def _connect(self, node1, node2, edge = None):
        path = find_path(node1, node2, self.height_map)
        counter = 0
        road_blocks = []
        previous_node = node1
        for i in range(len(path)):
            counter += 1
            road_blocks += path[i]
            if counter == MAX_LENGTH_EDGE:
                
                new_node = RoadNode(path[i])
                self.add_connex_component(new_node) 
                super()._connect(new_node, previous_node, RoadSegment(new_node, previous_node, road_blocks))
                previous_node = new_node
                counter = 0
                road_blocks = []

        if counter != 0:
            super()._connect(previous_node, node2, RoadSegment(previous_node, node2, road_blocks))

    def _get_closest_node(self, reference_node, heuristic):
        nodes = self.get_nodes()
        closest_node = nodes[0]
        minimal_distance = 10000000000

        for node in nodes:
            if node != reference_node:
                if heuristic(node, reference_node) < minimal_distance:
                    minimal_distance = heuristic(node, reference_node)
                    closest_node = node