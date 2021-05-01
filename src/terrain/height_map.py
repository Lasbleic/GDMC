from typing import List

import numpy as np
import cv2

from utils import WorldSlice, BuildArea
from terrain.map import Map
from utils import Point


class HeightMap(Map):
    def __init__(self, level: WorldSlice, area: BuildArea):
        # highest non air block
        super().__init__(self.__calcGoodHeightmap(level))
        self.area = area
        self.__air_height: Map = Map(level.heightmaps["WORLD_SURFACE"][:] - 1)

        # highest solid block (below oceans)
        self.__ocean_floor: Map = Map(np.minimum(self[:], level.heightmaps["OCEAN_FLOOR"]))

        # uses absolute coordinates
        self.__origin = Point(area.x, area.z)

        self.__steepness_x = cv2.Scharr(np.array(self[:], dtype=np.uint8), -1, 1, 0) / 32
        self.__steepness_z = cv2.Scharr(np.array(self[:], dtype=np.uint8), -1, 0, 1) / 32

        self.__steepness_x = cv2.GaussianBlur(self.__steepness_x, (5, 5), 0)
        self.__steepness_z = cv2.GaussianBlur(self.__steepness_z, (5, 5), 0)

    def upper_height(self, xr: Point or int, zr=None):
        """
        :param xr: X coordinate or Point instance
        :param zr: Z coordinate or None
        :return: Y coordinate of the highest non air block
        """
        if zr is None:
            return self.__air_height[xr]
        return self.__air_height[xr, zr]

    def lower_height(self, xr, zr=None):
        """
        :param xr: X coordinate or Point instance
        :param zr: Z coordinate or None
        :return: Y coordinate of the highest ground block (below oceans, and trees)
        """
        if zr is None:
            return self.__ocean_floor[xr]
        return self.__ocean_floor[xr, zr]

    def box_height(self, box, use_relative_coords, include_fluids=False):
        x0 = box.minx if use_relative_coords else box.minx - self.__origin.x
        z0 = box.minz if use_relative_coords else box.minz - self.__origin.z
        matrix = self._values if include_fluids else self.__ocean_floor
        return matrix[x0: (x0 + box.width), z0:(z0 + box.length)].astype(int)

    def steepness(self, x, z=None, norm=True):
        if isinstance(x, Point):
            return self.steepness(x.x, x.z, norm)
        steepness_vector = Point(self.__steepness_x[x, z], self.__steepness_z[x, z])
        return steepness_vector.norm if norm else steepness_vector

    def update(self, points, heights):
        # type: (List[Point], List[int]) -> None
        for p, h in zip(points, heights):
            if self.upper_height(p) == self[p]:
                self.__air_height._values[p.x, p.z] = h
            self._values[p.x, p.z] = h
            # self.__ocean_floor.__values[p.x, p.z] = h

    @staticmethod
    def __calcGoodHeightmap(world_slice):
        """Calculates a heightmap that is well suited for building.
        It ignores any logs and leaves and treats water as ground.

        Args:
            world_slice (WorldSlice): an instance of the WorldSlice class containing the raw heightmaps and block data

        Returns:
            any: numpy array containing the calculated heightmap
        """
        hm_mbnl = world_slice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
        heightmapNoTrees = hm_mbnl[:]
        area = world_slice.rect

        from itertools import product
        for x, z in product(range(area[2]), range(area[3])):
            while True:
                y = heightmapNoTrees[x, z]
                block = world_slice.getBlockAt((area[0] + x, y - 1, area[1] + z))
                if block[-4:] == '_log' or block.split(':')[-1] == 'bamboo':
                    heightmapNoTrees[x, z] -= 1
                else:
                    break

        return np.array(np.minimum(hm_mbnl, heightmapNoTrees)) - 1
