from __future__ import division, print_function

from pymclevel import MCLevel
from generation import TransformBox, compute_height_map
from obstacle_map import ObstacleMap
from road_network import RoadNetwork


class Maps:
    """
    The Map class gather all the maps representing the Minecraft Map selected for the filter
    """

    def __init__(self, level, bounding_box):
        # type: (MCLevel, TransformBox) -> Maps
        self.width = bounding_box.size.x
        self.height = bounding_box.size.z
        self.box = bounding_box
        self.obstacle_map = ObstacleMap(self.width, self.height, self)
        self.height_map = compute_height_map(level, bounding_box, False)
        self.road_network = RoadNetwork(self.width, self.height, self)
