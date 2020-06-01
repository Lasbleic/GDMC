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
        self.__width = bounding_box.size.x
        self.__length = bounding_box.size.z
        self.box = bounding_box
        self.obstacle_map = ObstacleMap(self.__width, self.__length, self)
        self.height_map = compute_height_map(level, bounding_box, False)
        self.road_network = RoadNetwork(self.__width, self.__length, self)

    @property
    def width(self):
        return self.__width

    @property
    def length(self):
        return self.__length
