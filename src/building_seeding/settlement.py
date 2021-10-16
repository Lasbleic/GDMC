from collections import Counter
from typing import Set

from terrain import TerrainMaps
from utils import Position


class DistrictCluster:

    def __init__(self, id):
        self.id = id
        self.reps: Set[Position] = set()
        self.score: float = 0.
        self.isTown: bool = False
        self.center: Position = Position(0, 0)
        self.size: int = 0


class Town:
    def __init__(self, center: Position, name: str, palette):
        self.__name: str = name
        self.__center: Position = center
        self.__palette = palette

    @classmethod
    def fromCluster(cls, dc: DistrictCluster, terrain: TerrainMaps):
        from generation.building_palette import get_biome_palette
        center = dc.center
        name = cls.genName()

        biome_occurrence = Counter(map(lambda pos: terrain.biome[pos], dc.reps))
        town_biome: int = biome_occurrence.most_common()[0][0]
        biome_name: str = terrain.biome.getBiome(town_biome)
        palette = get_biome_palette(biome_name)

        return cls(center, name, palette)

    @property
    def center(self) -> Position:
        return self.__center

    @property
    def palette(self):
        return self.__palette

    @property
    def name(self):
        return self.__name

    @staticmethod
    def genName() -> str:
        from building_seeding.districts import CityNameGenerator
        return CityNameGenerator().generate()

    @staticmethod
    def genPalette(terrain, districtMap) -> str:
        pass
