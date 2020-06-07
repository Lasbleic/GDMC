from __future__ import division, print_function
from pymclevel import BoundingBox
from numpy import full
from utils import Point2D
from itertools import product
import generation


class ObstacleMap:

    def __init__(self, width, length, mc_map=None):
        # type: (int, int, Maps) -> ObstacleMap
        self.__width = width
        self.__length = length
        self.map = full((self.__width, self.__length), True)
        self.__all_maps = mc_map
        self.__init_map_with_environment(mc_map.box)

    def __in_z_limits(self, z):
        return 0 <= z < self.__length

    def __in_x_limits(self, x):
        return 0 <= x < self.__width

    def __init_map_with_environment(self, bounding_box):
        # TODO: For every water/tree bloc, set bloc to un-accessible
        pass

    def is_accessible(self, point):
        # type: (Point2D) -> bool
        return self.__is_accessible(point.x, point.z)

    def __is_accessible(self, x, z):
        return self.map[x, z]

    def __set_obstacle(self, x, z):
        self.map[x, z] = False

    # size must be odd
    def add_parcel_to_obstacle_map(self, parcel):
        # type: (generation.Parcel) -> None
        for x, z in product(range(parcel.minx, parcel.maxx), range(parcel.minz, parcel.maxz)):
            if self.__in_x_limits(x) and self.__in_z_limits(z):
                self.__set_obstacle(x, z)

    def __getitem__(self, item):
        if len(item) == 2:
            x, z = item
            return self.map[x, z]
