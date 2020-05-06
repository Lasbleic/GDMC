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
    palette = {'base': alphaMaterials.Cobblestone, 'wall': alphaMaterials.WoodPlanks,
               'roof': alphaMaterials.BrickStairs, 'pillar': alphaMaterials.Wood, 'window': alphaMaterials.GlassPane}
    house = HouseSymbol()
    house.generate(level, box, palette)


class Symbol:
    def __init__(self, name='abstract'):
        self.children = []
        self.name = name
        self.box = None

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

        # make dimensions odd (!= even)
        new_width, new_length = box.width, box.length
        new_width -= 1 - (new_width % 2)
        new_length -= 1 - (new_length % 2)
        box = BoundingBox(box.origin, (new_width, box.height, new_length))
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
        self.children.append(RoomSymbol(self))
        return Symbol.generate(self, level, box2, palette)


class WallSymbol(Symbol):
    def __init__(self, x, z, name='pillar'):
        Symbol.__init__(self, name)
        self.x = x
        self.z = z
        self.is_heavy = True

    def generate(self, level, box, palette):
        x, y, z = self.x, box.miny, self.z
        b1, b2 = x == box.minx, z == box.minz
        if self.is_heavy:
            if b1 ^ b2:
                # wall at constant x
                box2 = BoundingBox((x, box.miny, box.minz+1), (1, box.height, box.length-2))
                print('filling wall in', box2)
                fillBlocks(level, box2, palette['wall'])
                for z in range(box.minz+2, box.maxz-2, 2):
                    fillBlocks(level, BoundingBox((x, y+1, z), (1, 2, 1)), palette['window'])
            else:
                # wall at constant z
                box2 = BoundingBox((box.minx+1, box.miny, z), (box.width-2, box.height, 1))
                print('filling pillar in', box2)
                fillBlocks(level, box2, palette['wall'])
                for x in range(box.minx+2, box.maxx-2, 2):
                    fillBlocks(level, BoundingBox((x, y+1, z), (1, 2, 1)), palette['window'])
        return box


class PillarSymbol(WallSymbol):
    def __init__(self, x, z, name='pillar'):
        WallSymbol.__init__(self, x, z, name)

    def generate(self, level, box, palette):
        box2 = BoundingBox((self.x, box.miny, self.z), (1, box.height, 1))
        material = palette['pillar'] if self.is_heavy else palette['wall']
        print('filling pillar in', box)
        fillBlocks(level, box2, material)
        return box


class RoomSymbol(Symbol):

    def __init__(self, parent, name='room'):
        Symbol.__init__(self, name)
        self.parent = parent  # type: StoreySymbol

    def generate(self, level, box, palette):
        # todo: split test
            # if split, remove self from parent, split self in new RoomSymbols, add each to parent

            # else
        print('filling walls', box)

        for x, z in product([box.minx, box.maxx-1], [box.minz, box.maxz-1]):
            self.children.append(PillarSymbol(x, z))
            self.children.append(WallSymbol(x, z))

        return Symbol.generate(self, level, box, palette)


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

                if box.length % 2:
                    # todo: build arete -> il faut recuperer le materiau du toit en slab, ou block
                    pass

        else:
            for dx in xrange(box.width//2):
                roof_box = BoundingBox((box.minx+dx, box.miny+dx, box.minz), (1, 1, box.length))
                fillBlocks(level, roof_box, alphaMaterials[palette['roof'].ID, 0])

                for z in [box.minz, box.maxz-1]:
                    roof_box = BoundingBox((box.minx+dx+1, box.miny+dx, z), (box.width - 2*(dx+1), 1, 1))
                    fillBlocks(level, roof_box, palette['wall'])

                roof_box = BoundingBox((box.maxx-dx-1, box.miny+dx, box.minz), (1, 1, box.length))
                fillBlocks(level, roof_box, alphaMaterials[palette['roof'].ID, 1])

                if box.width % 2:
                    #todo: same
                    pass

        return Symbol.generate(self, level, box, palette)






