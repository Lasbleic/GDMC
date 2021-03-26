from itertools import product

from numpy import argmin

from generation import Generator
from pymclevel import alphaMaterials as Materials
from pymclevel.block_fill import fillBlocks
from utils import TransformBox


class DefenseTower(Generator):

    def generate(self, level, height_map=None, palette=None):
        self._clear_trees(level)
        tower_size = min(self.width-1, self.length-1, 8)
        tower_x, ground_y, tower_y, tower_z = self.__find_tower_position(tower_size, height_map)
        base_box = TransformBox((tower_x, ground_y, tower_z), (tower_size, tower_y-ground_y, tower_size))
        tower_box = TransformBox((tower_x, tower_y, tower_z), (tower_size, 5, tower_size))
        fillBlocks(level, base_box.expand(1, 0, 1), Materials["Cobblestone"])
        fillBlocks(level, tower_box, Materials["Stone Bricks"])
        fillBlocks(level, tower_box.expand(-1, 0, -1), Materials["Air"])

    def __find_tower_position(self, size, height_map):
        positions = list(product(range(self.width-size), range(self.length-size)))
        steepness = list(map(lambda (x, z): height_map[x:(x+size), z:(z+size)].std(), positions))
        tower_x, tower_z = positions[int(argmin(steepness))]
        ground_y = height_map[tower_x:(tower_x+size), tower_z:(tower_z+size)].min()
        tower_y = height_map[tower_x:(tower_x+size), tower_z:(tower_z+size)].max() + 2
        tower_x += self._box.minx
        tower_z += self._box.minz
        return tower_x, ground_y, tower_y, tower_z
