from pymclevel.block_fill import fillBlocks
from utils import *

from numpy import array

from generation.generators import MaskedGenerator, Generator
from pymclevel import MCLevel


class PlazaGenerator(MaskedGenerator):

    def __terraform(self, level, height_map):
        # type: (MCLevel, array) -> None
        mean_y = int(round(height_map.mean()))
        for x, y, z in self.surface_pos(height_map):
            if y > mean_y:
                vbox = BoundingBox((x, mean_y + 1, z), (1, y - mean_y, 1))
                fillBlocks(level, vbox, Materials['Air'])
            elif y < mean_y:
                vbox = BoundingBox((x, y + 1, z), (1, mean_y - y, 1))
                fillBlocks(level, vbox, Materials['Dirt'])
        height_map[:] = mean_y

    def generate(self, level, height_map=None, palette=None):
        generator_function = self.__choose_generator(level, height_map)
        self.__terraform(level, height_map)
        generator_function(self, level, height_map, palette)
        Generator.generate(self, level, height_map, palette)

    def __choose_generator(self, level, height_map):
        return PlazaGenerator.__city_plaza

    def __city_plaza(self, level, height_map, palette):
        for x, y, z in self.surface_pos(height_map):
            b = Materials['Prismarine Bricks']
            if bernouilli(0.75):
                setBlock(level, (b.ID, b.blockData), x, y, z)

    def __abs_coords(self, x, z):
        pass