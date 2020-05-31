from math import floor
from random import randint
from itertools import product
from numpy.random import choice
from numpy import ones

from utilityFunctions import setBlock

from gen_utils import TransformBox, Direction, cardinal_directions, Bottom, Top
from pymclevel import alphaMaterials as Block
from pymclevel.schematic import StructureNBT

from utils import get_project_path


def paste_nbt(level, box, nbt_file_name):
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
        # type: (TransformBox) -> Generator
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

    @property
    def origin(self):
        return self._box.origin

    @property
    def size(self):
        return self._box.size

    @property
    def surface(self):
        return self._box.surface

    def translate(self, dx=0, dy=0, dz=0):
        self._box.translate(dx, dy, dz)
        for gen in self.children:
            gen.translate(dx, dy, dz)


class CropGenerator(Generator):
    def generate(self, level, height_map=None):
        # dimensions
        width, length = self._box.width, self._box.length
        x0, y0, z0 = self._box.origin
        # block states
        crop_ids = [141, 142, 59]
        prob = ones(len(crop_ids)) / len(crop_ids)  # uniform across the crops

        water_sources = (1 + (width - 1) // 9) * (1 + (length - 1) // 9)  # each water source irrigates a 9x9 flat zone
        for _ in xrange(water_sources):
            xs, zs = x0 + randint(0, width - 1), z0 + randint(0, length - 1)
            for xd, zd in product(xrange(max(x0, xs - 4), min(x0 + width, xs + 5)),
                                  xrange(max(z0, zs - 4), min(z0 + length, zs + 5))):
                if (xd, zd) == (xs, zs):
                    # water source
                    setBlock(level, (9, 15), xd, y0, zd)
                elif level.blockAt(xd, y0, zd) != 9:
                    setBlock(level, (60, 7), xd, y0, zd)  # farmland
                    bid = choice(crop_ids, p=prob)
                    age = randint(0, 7)
                    setBlock(level, (bid, age), xd, y0 + 1, zd)  # crop


class HouseGenerator(Generator):
    def generate(self, level, height_map=None):
        if self._box.width >= 7 and self._box.length >= 9:
            # warning: structure NBT here must have been generated in Minecraft 1.11 or below, must be tested
            paste_nbt(level, self._box, 'house_7x9.nbt')


class CardinalGenerator(Generator):
    """
    Generator linked to its direct neighbors in each direction (N, E, S, W, top, bottom)
    """

    def __init__(self, box):
        Generator.__init__(self, box)
        self._neighbors = dict()

    def __getitem__(self, item):
        # type: (object) -> CardinalGenerator
        if isinstance(item, Direction) and item in self._neighbors:
            # find a sub generator by its direction
            return self._neighbors[item]
        elif isinstance(item, TransformBox):
            # find a sub generator by its box
            for sub_item in self.children:
                if sub_item.origin == item.origin and item.size == sub_item.size:
                    return sub_item
        return None

    def __setitem__(self, direction, neighbour):
        # type: (Direction, CardinalGenerator) -> None
        """
        Marks neighbouring relationship between two generators
        """
        if isinstance(direction, Direction) and isinstance(neighbour, CardinalGenerator):
            self._neighbors[direction] = neighbour
            # Upper floor neighbours are descendants of lower floors. If this method is called with rooms from the upper
            # floors, then <neighbour> already has a parent: the room underneath -> no new parenting link
            if neighbour[Bottom] is None:
                self.children.insert(0, neighbour)
            neighbour._neighbors[-direction] = self
            if direction == Top:
                for direction2 in cardinal_directions():
                    if self[direction2] is not None and self[direction2][Top] is not None:
                        neighbour[direction2] = self[direction2][Top]
        else:
            raise TypeError


class DoorGenerator(Generator):
    def __init__(self, box, direction, material='Oak'):
        # type: (TransformBox, Direction, str) -> DoorGenerator
        Generator.__init__(self, box)
        assert 1 <= box.surface <= 2
        self._direction = direction
        self._material = material

    def generate(self, level, height_map=None):
        for x, y, z in self._box.positions:
            setBlock(level, (self._resource(x, y, z)), x, y, z)

    def _resource(self, x, y, z):
        if y == self._box.miny:
            block_name = '{} Door (Lower, Unopened, {})'.format(self._material, -self._direction)
        elif y == self._box.miny + 1:
            if self._box.surface == 1:
                hinge = 'Left'
            else:
                mean_x = self._box.minx + 0.5 * self._box.width
                mean_z = self._box.minz + 0.5 * self._box.length
                norm_dir = self._direction.rotate()
                left_x = int(floor(mean_x + 0.5 * norm_dir.x))  # floored because int(negative float) rounds up
                left_z = int(floor(mean_z + 0.5 * norm_dir.z))
                hinge = 'Left' if (x == left_x and z == left_z) else 'Right'
            block_name = '{} Door (Upper, {} Hinge, Unpowered)'.format(self._material, hinge)
        else:
            block_name = 'Oak Wood Planks'
        block = Block[block_name]
        return block.ID, block.blockData
