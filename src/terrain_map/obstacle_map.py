from __future__ import division, print_function

from math import floor

from numpy import full, zeros
from utils import Point2D
from itertools import product


class ObstacleMap:

    def __init__(self, width, length, mc_map=None):
        # type: (int, int, Maps) -> ObstacleMap
        self.__width = width
        self.__length = length
        # self.map = full((self.__width, self.__length), True)
        self.map = zeros((self.__width, self.__length))
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
        # return self.map[x, z]
        return self.map[x, z] == 0

    def __set_obstacle(self, x, z):
        # self.map[x, z] = False
        self.map[x, z] += 1

    def __unset_obstacle(self, x, z):
        # self.map[x, z] = True
        self.map[x, z] -= 1

    # size must be odd
    def add_parcel_to_obstacle_map(self, parcel, margin):
        # type: (generation.Parcel, int) -> None
        parcel = parcel.bounds.expand(margin, 0, margin)
        for x, z in product(range(parcel.minx, parcel.maxx), range(parcel.minz, parcel.maxz)):
            if self.__in_x_limits(x) and self.__in_z_limits(z):
                self.__set_obstacle(x, z)

    def unmark_parcel(self, parcel, margin):
        # type: (generation.Parcel, int) -> None
        parcel = parcel.bounds.expand(margin, 0, margin)
        for x, z in product(range(parcel.minx, parcel.maxx), range(parcel.minz, parcel.maxz)):
            if self.__in_x_limits(x) and self.__in_z_limits(z):
                self.__unset_obstacle(x, z)

    def add_network_to_obstacle_map(self):
        from terrain_map.road_network import RoadNetwork
        if self.__all_maps is not None:
            network = self.__all_maps.road_network  # type: RoadNetwork
            for xo, zo in product(xrange(self.__width), xrange(self.__length)):
                if network.is_road(xo, zo):
                    # build a circular obstacle of designated width around road point
                    margin = network.get_road_width(xo, zo)
                    m0, m1 = int(margin/2.), int(floor(margin/2.)) + 1
                    for dx, dz in product(xrange(-m0, m1), xrange(-m0, m1)):
                        if self.__in_x_limits(xo+dx) and self.__in_z_limits(zo+dz) and abs(dx*dz) < margin**2\
                                and not self.map[xo+dx, zo+dz]:
                            self.__set_obstacle(xo+dx, zo+dz)

    def __getitem__(self, item):
        if len(item) == 2:
            x, z = item
            return self.map[x, z] == 0

    @property
    def width(self):
        return self.map.shape[0]

    @property
    def length(self):
        return self.map.shape[1]
