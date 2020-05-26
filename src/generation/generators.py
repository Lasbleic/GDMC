from random import randint
from itertools import product
from numpy.random import choice
from numpy import ones

from utilityFunctions import setBlock

from generation.gen_utils import TransformBox
from pymclevel.schematic import StructureNBT

from utils import get_project_path


def paste_NBT(level, box, nbt_file_name):
    _structure = StructureNBT(get_project_path() + '/structures/' + nbt_file_name)
    _width, _height, _length = _structure.Size

    x0, y0, z0 = box.minx, box.miny, box.minz
    # iterates over coordinates in the structure, copy to level
    for xs, ys, zs in product(xrange(_width), xrange(_height), xrange(_length)):
        xd, yd, zd = x0 + xs, y0 + ys, z0 + zs  # coordinates in the level: translation of the structure
        block = _structure.Blocks[xs, ys, zs]  # (id, data) tuple
        print(xs, ys, zs, block)
        setBlock(level, block, xd, yd, zd)


class Generator:
    _box = None  # type: TransformBox

    def __init__(self, box):
        self._box = box
        self.children = []

    def generate(self, level, height_map=None):
        """
        Generates this building on the level
        Parameters
        ----------
        level MC world
        height_map optional height_map

        Returns nothing
        -------

        """
        for sub_generator in self.children:
            sub_generator.generate(level, height_map)

    @property
    def width(self):
        return self._box.width

    @property
    def length(self):
        return self._box.length

    @property
    def height(self):
        return self._box.height


class CropGenerator(Generator):
    def generate(self, level, height_map=None):
        # dimensions
        w, l = self._box.width, self._box.length
        x0, y0, z0 = self._box.origin
        # block states
        crop_ids = [141, 142, 59]
        prob = ones(len(crop_ids))/len(crop_ids)  # uniform across the crops

        water_sources = (1 + (w-1)//9) * (1 + (l-1)//9)  # each water source irrigates a 9x9 flat zone
        for _ in xrange(water_sources):
            xs, zs = x0 + randint(0, w-1), z0 + randint(0, l-1)
            for xd, zd in product(xrange(max(x0, xs-4), min(x0+w, xs+5)),
                                  xrange(max(z0, zs-4), min(z0+l, zs+5))):
                if (xd, zd) == (xs, zs):
                    # water source
                    setBlock(level, (9, 15), xd, y0, zd)
                elif level.blockAt(xd, y0, zd) != 9:
                    setBlock(level, (60, 7), xd, y0, zd)  # farmland
                    bid = choice(crop_ids, p=prob)
                    age = randint(0, 7)
                    setBlock(level, (bid, age), xd, y0+1, zd)  # crop


class HouseGenerator(Generator):
    def generate(self, level, height_map=None):
        if self._box.width >= 7 and self._box.length >= 9:
            # warning: structure NBT here must have been generated in Minecraft 1.11 or below, must be tested
            paste_NBT(level, self._box, 'house_7x9.nbt')
