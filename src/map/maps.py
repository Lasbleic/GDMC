from __future__ import division, print_function

from fluid_map import FluidMap
from map.height_map import HeightMap
from obstacle_map import ObstacleMap
from pymclevel import MCLevel
from road_network import RoadNetwork
from utils import TransformBox


class Maps:
    """
    The Map class gather all the maps representing the Minecraft Map selected for the filter
    """

    def __init__(self, level, bounding_box):
        # type: (MCLevel, TransformBox) -> Maps
        self.__width = bounding_box.size.x
        self.__length = bounding_box.size.z
        self.box = bounding_box
        self.obstacle_map = ObstacleMap(self.__width, self.__length, self)  # type: ObstacleMap
        self.height_map = HeightMap(level, bounding_box)  # type: HeightMap
        self.fluid_map = FluidMap(self, level)
        self.road_network = RoadNetwork(self.__width, self.__length, mc_map=self)  # type: RoadNetwork

    @property
    def width(self):
        return self.__width

    @property
    def length(self):
        return self.__length
