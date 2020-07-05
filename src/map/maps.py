from __future__ import division, print_function

from pymclevel import MCLevel
from obstacle_map import ObstacleMap
from road_network import RoadNetwork
from fluid_map import FluidMap
from utils import TransformBox, compute_height_map
from numpy import array


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
        if level is not None:
            self.height_map = compute_height_map(level, bounding_box)
        else:
            xmin, xmax = bounding_box.minx, bounding_box.maxx
            zmin, zmax = bounding_box.minz, bounding_box.maxz
            self.height_map = array([[0 for _ in range(zmin, zmax)] for _ in range(xmin, xmax)])
        self.road_network = RoadNetwork(self.__width, self.__length, mc_map=self)
        self.fluid_map = FluidMap(self, level)

    @property
    def width(self):
        return self.__width

    @property
    def length(self):
        return self.__length
