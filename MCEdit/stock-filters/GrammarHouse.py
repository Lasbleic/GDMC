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
    palette = {'base': alphaMaterials.Cobblestone, 'wall': alphaMaterials.WoodPlanks, 'roof': alphaMaterials.BrickStairs}
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
        print(h, np.mean(h) + 1)
        box = BoundingBox((box.minx, np.min(h), box.minz), (box.width, np.mean(h) + 2 - np.min(h), box.length))
        print('filling base', box)
        fillBlocks(level, box, palette['base'])
        return Symbol.generate(self, level, box, palette)


class StoreySymbol(Symbol):

    def generate(self, level, box, palette):
        box2 = BoundingBox((box.minx, box.maxy, box.minz), (box.width, 4, box.length))
        print('filling walls', box2)
        fillBlocks(level, box2, palette['wall'])
        fillBlocks(level, box2.expand(-1, 0, -1), alphaMaterials.Air)
        return Symbol.generate(self, level, box2, palette)


class RoofSymbol(Symbol):
    def generate(self, level, box, palette):
        box = BoundingBox((box.minx, box.maxy, box.minz), (box.width, 1, box.length))
        print('filling roof', box)
        r = random()
        t = float(box.length**2) / (box.width**2 + box.length**2)
        print(r, t)
        roof_in_width = r > t  # higher probability to have a lower & longer triangular roof

        if roof_in_width:
            for dz in xrange(box.length//2):
                # north line
                roof_box = BoundingBox((box.minx, box.miny+dz, box.minz+dz), (box.width, 1, 1))
                fillBlocks(level, roof_box, alphaMaterials[palette['roof'].ID, 2])  # this way to access oriented blocks is ugly

                # wood fill
                for x in [box.minx, box.maxx-1]:
                    roof_box = BoundingBox((x, box.miny+dz, box.minz+dz+1), (1, 1, box.length - 2*(dz+1)))
                    fillBlocks(level, roof_box, palette['wall'])

                # south line
                roof_box = BoundingBox((box.minx, box.miny+dz, box.maxz-dz-1), (box.width, 1, 1))
                fillBlocks(level, roof_box, alphaMaterials[palette['roof'].ID, 3])

        else:
            for dx in xrange(box.width//2):
                roof_box = BoundingBox((box.minx+dx, box.miny+dx, box.minz), (1, 1, box.length))
                fillBlocks(level, roof_box, alphaMaterials[palette['roof'].ID, 0])

                for z in [box.minz, box.maxz-1]:
                    roof_box = BoundingBox((box.minx+dx+1, box.miny+dx, z), (box.width - 2*(dx+1), 1, 1))
                    fillBlocks(level, roof_box, palette['wall'])

                roof_box = BoundingBox((box.maxx-dx-1, box.miny+dx, box.minz), (1, 1, box.length))
                fillBlocks(level, roof_box, alphaMaterials[palette['roof'].ID, 1])
        return Symbol.generate(self, level, box, palette)






