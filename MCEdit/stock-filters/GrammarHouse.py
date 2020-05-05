from random import random
from pymclevel import BoundingBox, alphaMaterials
from pymclevel.block_fill import fillBlocks
from itertools import product
import numpy as np
from CharliesDataExtraction import compute_height_map


displayName = "Grammar House"

inputs = (
    ('Grammatically generated simple house', 'label'),
    ('(hope it works)', 'label'),
    ('by Charlie <3', 'label')
)


def perform(level, box, options):
    print('building house in box', box)
    palette = {'base': alphaMaterials.Cobblestone, 'walls': alphaMaterials.WoodPlanks, 'roof': alphaMaterials.Brick}
    house = HouseSymbol()
    house.generate(level, box, palette)


class Symbol:
    def __init__(self, name='abstract'):
        self.children = []
        self.name = name

    def generate(self, level, box, palette):
        for child in self.children:
            box = child.generate(level, box, palette)
        return box


class HouseSymbol(Symbol):
    def __init__(self, name='house'):
        Symbol.__init__(self, name)

    def generate(self, level, box, palette):
        self.children.append(BaseSymbol())
        self.children.append(StoreySymbol())
        self.children.append(RoofSymbol())
        Symbol.generate(self, level, box, palette)


class BaseSymbol(Symbol):
    def __init__(self, name='basement'):
        Symbol.__init__(self, name)

    def generate(self, level, box, palette):
        h = compute_height_map(level, box)
        box = BoundingBox((box.minx, np.min(h), box.minz), (box.width, np.mean(h) + 1 - np.min(h), box.length))
        print('filling base', box)
        fillBlocks(level, box, palette['base'])
        return Symbol.generate(self, level, box, palette)


class StoreySymbol(Symbol):

    def generate(self, level, box, palette):
        box2 = BoundingBox((box.minx, box.maxy, box.minz), (box.width, 4, box.length))
        print('filling walls', box2)
        fillBlocks(level, box2, palette['walls'])
        fillBlocks(level, box2.expand(-1, 0, -1), alphaMaterials.Air)
        return Symbol.generate(self, level, box2, palette)


class RoofSymbol(Symbol):
    def generate(self, level, box, palette):
        box2 = BoundingBox((box.minx, box.maxy, box.minz), (box.width, 1, box.length))
        print('filling roof', box2)
        fillBlocks(level, box2, palette['roof'])
        return Symbol.generate(self, level, box2, palette)






