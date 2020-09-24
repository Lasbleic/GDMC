from numpy.core.multiarray import ndarray

from pymclevel.block_fill import fillBlocks
from utils import *

from numpy import array, zeros

from generation.generators import MaskedGenerator, Generator
from pymclevel import MCLevel


class PlazaGenerator(MaskedGenerator):

    def __terraform(self, level, height_map):
        # type: (MCLevel, array) -> ndarray
        mean_y = int(round(height_map.mean()))
        terraform_map = zeros(height_map.shape)
        for x, y, z in self.surface_pos(height_map):
            if y > mean_y:
                vbox = BoundingBox((x, mean_y + 1, z), (1, y - mean_y, 1))
                fillBlocks(level, vbox, Materials['Air'])
            elif y < mean_y:
                vbox = BoundingBox((x, y + 1, z), (1, mean_y - y, 1))
                material = Materials["Stone Bricks"] if self.is_lateral(x, z) else Materials["Dirt"]
                fillBlocks(level, vbox, material)
        terraform_map[:] = mean_y
        return terraform_map

    def generate(self, level, height_map=None, palette=None):
        generator_function = self.__choose_generator(level, height_map)
        terraform_map = self.__terraform(level, height_map)
        generator_function(self, level, height_map, terraform_map, palette)
        Generator.generate(self, level, height_map, palette)

    def __choose_generator(self, level, height_map):
        return PlazaGenerator.__city_park

    def __city_plaza(self, level, ground_height, build_height, palette):
        for x, y, z in self.surface_pos(build_height):
            b = Materials['Prismarine Bricks']
            if bernouilli(0.75):
                setBlock(level, b, x, y, z)

    def __city_park(self, level, ground_height, build_height, palette):
        has_door = False
        for x, y, z in self.surface_pos(build_height):
            if self.is_lateral(x, z):
                material = Materials["Cobblestone"] if (self.is_corner(Point2D(x, z)) or (x+z) % 3 == 0) else Materials["Cobblestone Wall"]
                setBlock(level, material, x, y+1, z)
                setBlock(level, Materials["Cobblestone Slab (Bottom)"], x, y+2, z)
            else:
                setBlock(level, Materials["Grass Block"], x, y, z)
        pass

    def __abs_coords(self, x, z):
        pass
