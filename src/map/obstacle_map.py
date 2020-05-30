from __future__ import division, print_function
from pymclevel import BoundingBox
from numpy import full
from utils import Point2D
from itertools import product
from parcel import Parcel


class ObstacleMap:

    def __init__(self, bounding_box):
        # type: (BoundingBox) -> ObstacleMap
        self.__width = bounding_box.size.x
        self.__height = bounding_box.size.z
        self.__map = full((self.__width, self.__height), True)
        self.__init_map_with_environment(bounding_box)

    def __in_z_limits(self, z):
        return 0 <= z < self.__height

    def __in_x_limits(self, x):
        return 0 <= x < self.__width

    def __init_map_with_environment(self, bounding_box):
        # TODO: For every water/tree bloc, set bloc to un-accessible
        pass

    def is_accessible(self, point):
        # type: (Point2D) -> bool
        return self.__is_accessible(point.x, point.z)

    def __is_accessible(self, x, z):
        return self.__map[z][x]

    def __set_obstacle(self, x, z):
        self.__map[z][x] = False

    # size must be odd
    def add_parcel_to_obstacle_map(self, parcel):
        # type: (Parcel, int) -> void
        for i, j in product(range(parcel.width), range(parcel.height)):
            if self.__in_x_limits(i) and self.__in_z_limits(j):
                self.__set_obstacle(parcel.origin.x + i, parcel.origin.z + j)


