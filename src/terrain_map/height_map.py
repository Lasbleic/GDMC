from time import time

from typing import List

from pymclevel import alphaMaterials as Materials
from numpy import array

from utils import Point2D, ground_blocks_ID, fluid_blocks_ID


class HeightMap:
    def __init__(self, level, box):
        # detects highest ground or fluid block
        self.__air_height = None  # type: array
        self.__fluid_height = None  # type: array
        # considers as ground highest ground block
        self.__altitude = None  # type: array

        t0 = time()
        # uses absolute coordinates
        xm, xM, zm, zM = box.minx, box.maxx, box.minz, box.maxz
        self.__origin = Point2D(xm, zm)

        if level is None:
            self.__air_height = array([[0 for _ in range(zm, zM)] for _ in range(xm, xM)])
            self.__fluid_height = self.__altitude = self.__air_height

        else:
            self.__air_height = array([[level.heightMapAt(x, z) for z in range(zm, zM)] for x in range(xm, xM)])

            def drill_down(xa, za, block_list):
                altitude = self.__air_height[xa-xm, za-zm]
                while altitude >= 0 and level.blockAt(xa, altitude, za) not in block_list:
                    altitude -= 1
                return altitude

            self.__fluid_height = array([
                [
                    drill_down(x, z, ground_blocks_ID + fluid_blocks_ID) for z in range(zm, zM)
                ]
                for x in range(xm, xM)])

            self.__altitude = array([
                [
                    drill_down(x, z, ground_blocks_ID) for z in range(zm, zM)
                ]
                for x in range(xm, xM)])

        print('[{}] Computed height map in {}s'.format(self.__class__, time() - t0))

    def altitude(self, xr, zr=None):
        if zr is None:
            return self.altitude(xr.x, xr.z)
        return self.__altitude[xr, zr]

    def fluid_height(self, xr, zr=None):
        if zr is None:
            return self.fluid_height(xr.x, xr.z)
        return self.__fluid_height[xr, zr]

    def air_height(self, xr, zr):
        return self.__air_height[xr, zr]

    def box_height(self, box, use_relative_coords, include_fluids=False):
        x0 = box.minx if use_relative_coords else box.minx - self.__origin.x
        z0 = box.minz if use_relative_coords else box.minz - self.__origin.z
        matrix = self.__fluid_height if include_fluids else self.__altitude
        return matrix[x0: (x0 + box.width), z0:(z0 + box.length)].astype(int)

    def steepness(self, x, z, margin=3):
        value = 0
        for m in range(1, margin + 1):
            local_height = self.__fluid_height[max(0, x - m): min(x + m, self.width),
                                               max(0, z - m): min(z + m, self.length)]
            value += local_height.std()
        return value / margin

    @property
    def width(self):
        return self.__air_height.shape[0]

    @property
    def length(self):
        return self.__air_height.shape[1]

    def update(self, points, heights):
        # type: (List[Point2D], List[int]) -> None
        for p, h in zip(points, heights):
            if self.altitude(p) == self.fluid_height(p):
                self.__fluid_height[p.x, p.z] = h
            self.__altitude[p.x, p.z] = h
