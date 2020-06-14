from numpy import zeros, full
from itertools import product
from sklearn.semi_supervised import LabelPropagation

from pymclevel import MCLevel, alphaMaterials as Blocks
from pymclevel.biome_types import biome_types
from utils import Point2D


class FluidMap:

    def __init__(self, mc_maps, level):
        self.__width = mc_maps.width
        self.__length = mc_maps.length
        self.__water_map = full((mc_maps.width, mc_maps.length), -1)
        self.__lava_map = full((mc_maps.width, mc_maps.length), False)
        self.__other_maps = mc_maps

        self.__build_water_map(level)
        self.__build_lava_map(level)

    def __build_water_map(self, level):
        # type: (MCLevel) -> None
        water_points = []
        for x, z in product(range(self.__width), range(self.__length)):
            xs, zs = x + self.__other_maps.box.minx, z + self.__other_maps.box.minz
            y = self.__other_maps.height_map[x, z] + 1
            if level.blockAt(xs, y, zs) == Blocks.Water.ID:
                cx, cz = xs // 16, zs // 16
                biome = level.getChunk(cx, cz).Biomes[xs & 15, zs & 15]
                if 'Ocean' in biome_types[biome] or 'Beach' in biome_types[biome]:
                    label = 1
                elif 'River' in biome_types[biome]:
                    label = 2
                elif 'Swamp' in biome_types[biome]:
                    label = 3
                else:
                    label = -1  # yet unlabeled
                water_points.append((x, z, label))

        if water_points:
            data = [entry[:2] for entry in water_points]
            lbls = [entry[2] for entry in water_points]

            model = LabelPropagation('knn', n_neighbors=4)
            model.fit(data, lbls)
            lbls = model.predict(data)

            for (x, z), water_type in zip(data, lbls):
                self.__water_map[x, z] = water_type

    def __build_lava_map(self, level):
        pass

    def is_lava(self, x_or_point, z=None):
        # type: (Point2D or int, None or int) -> object
        if isinstance(x_or_point, Point2D):
            p = x_or_point
            return self.__lava_map[p.x, p.z]
        else:
            x = x_or_point
            return self.__lava_map[x, z]

    @property
    def water(self):
        return self.__water_map
