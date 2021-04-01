from terrain import ObstacleMap, RoadNetwork
from terrain.tree_map import TreesMap
from utils import BuildArea, WorldSlice, BoundingBox
from terrain.biomes import BiomeMap
from terrain.fluid_map import FluidMap
from terrain.height_map import HeightMap
# from terrain.obstacle_map import Obstacle  # todo: rewrite ObstacleMap


class TerrainMaps:
    """
    The Map class gather all the maps representing the Minecraft Map selected for the filter
    """

    def __init__(self, level: WorldSlice, area: BuildArea):
        self.level = level
        self.area: BuildArea = area
        self.height_map = HeightMap(level, area)
        self.biome = BiomeMap(level, area)
        self.fluid_map = FluidMap(level, area, self)
        self.obstacle_map = ObstacleMap(self.width, self.length, self)
        self.road_network = RoadNetwork(self.width, self.length, self)  # type: RoadNetwork
        self.trees = TreesMap(level, self.height_map)

    @property
    def width(self):
        return self.area.width

    @property
    def length(self):
        return self.area.length

    @property
    def shape(self):
        return self.width, self.length

    @property
    def box(self):
        return BoundingBox((self.area.x, 0, self.area.z), (self.width, 256, self.length))

    def in_limits(self, point, absolute_coords):
        if absolute_coords:
            return point in self.area
        else:
            return point + self.area.origin in self.area

    @staticmethod
    def request():
        from utils.gdmc_http_client_python.interfaceUtils import requestBuildArea
        build_area = BuildArea(requestBuildArea())
        level = WorldSlice((build_area.x, build_area.z, build_area.width, build_area.length))
        return TerrainMaps(level, build_area)
