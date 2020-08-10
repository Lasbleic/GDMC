from time import time

from pymclevel import alphaMaterials as Materials
from numpy import array

from utils import Point2D


class HeightMap:
    ground_blocks = [
        Materials.Grass.ID,
        Materials.Dirt.ID,
        Materials.Stone.ID,
        Materials.Bedrock.ID,
        Materials.Sand.ID,
        Materials.Gravel.ID,
        Materials.GoldOre.ID,
        Materials.IronOre.ID,
        Materials.CoalOre.ID,
        Materials.LapisLazuliOre.ID,
        Materials.DiamondOre.ID,
        Materials.RedstoneOre.ID,
        Materials.RedstoneOreGlowing.ID,
        Materials.Netherrack.ID,
        Materials.SoulSand.ID,
        Materials.Clay.ID,
        Materials.Glowstone.ID
    ]

    fluid_blocks = [Materials.Water.ID, Materials.WaterActive.ID,
                    Materials.Lava.ID, Materials.LavaActive.ID,
                    Materials.Ice.ID, Materials.PackedIce.ID, Materials.FrostedIce.ID]

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
                    drill_down(x, z, self.ground_blocks + self.fluid_blocks) for z in range(zm, zM)
                ]
                for x in range(xm, xM)])

            self.__altitude = array([
                [
                    drill_down(x, z, self.ground_blocks) for z in range(zm, zM)
                ]
                for x in range(xm, xM)])

        print('[{}] Computed height map in {}s'.format(self.__class__, time() - t0))

    def altitude(self, xr, zr):
        return self.__altitude[xr, zr]

    def fluid_height(self, xr, zr):
        return self.__fluid_height[xr, zr]

    def air_height(self, xr, zr):
        return self.__air_height[xr, zr]

    def box_height(self, box, use_relative_coords):
        x0 = box.minx if use_relative_coords else box.minx + self.__origin.x
        z0 = box.minz if use_relative_coords else box.minz + self.__origin.z
        return self.__altitude[x0: (x0 + box.width), z0:(z0 + box.length)]

    def steepness(self, x, z):
        value = 0
        for m in range(1, 4):
            local_height = self.__fluid_height[max(0, x - m): min(x + m, self.width),
                                               max(0, z - m): min(z + m, self.length)]
            value += local_height.std()
        return value / 3

    @property
    def width(self):
        return self.__air_height.shape[0]

    @property
    def length(self):
        return self.__air_height.shape[1]
