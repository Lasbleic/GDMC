from __future__ import division, print_function

from pymclevel import BoundingBox
from obstacle_map import ObstacleMap
from road_network import *


class Maps:
    """
    The Map class gather all the maps representing the Minecraft Map selected for the filter
    """

    def __init__(self, bounding_box):
        # type: (BoundingBox) -> Map
        self.width = bounding_box.size.x
        self.height = bounding_box.size.z
        self.bounding_box = bounding_box
        self.obstacle_map = ObstacleMap(self.width, self.height, self)
        self.height_map = None
        self.road_network = RoadNetwork(self.width, self.height, self)

