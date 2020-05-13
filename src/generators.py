from random import randint
from itertools import product
from numpy.random import choice
from numpy import ones

from pymclevel import alphaMaterials
from utilityFunctions import setBlock


class Generator:
    def __init__(self, box):
        self.box = box

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
        pass


class CropGenerator(Generator):
    def generate(self, level, height_map=None):
        # dimensions
        w, l = self.box.width, self.box.length
        x0, y0, z0 = self.box.origin
        # block states
        crop_ids = [141, 142, 59]
        prob = ones(len(crop_ids))/len(crop_ids)

        water_sources = 1 + (w * l) / 81  # each water source irrigates a 9x9 flat zone
        for _ in xrange(water_sources):
            xs, zs = x0 + randint(0, w-1), z0 + randint(0, l-1)
            print(l, w)
            print("new water source @({}, {})".format(xs, zs))
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

