from math import floor
from os import sep
from random import randint
from itertools import product

from numpy.random import choice
from numpy import ones, array

from pymclevel.block_copy import copyBlocksFrom
from pymclevel.block_fill import fillBlocks
from utilityFunctions import setBlock

from utils import TransformBox, Direction, cardinal_directions, Bottom, Top
from pymclevel import alphaMaterials as Block, MCLevel, Entity, TAG_Compound, TAG_Int, TAG_String
from pymclevel.schematic import StructureNBT

from utils import get_project_path, Point2D

SURFACE_PER_ANIMAL = 16


def paste_nbt(level, box, nbt_file_name):
    _structure = StructureNBT(get_project_path() + '/structures/' + nbt_file_name)
    _width, _height, _length = _structure.Size

    x0, y0, z0 = box.minx, box.miny, box.minz
    # iterates over coordinates in the structure, copy to level
    for xs, ys, zs in product(xrange(_width), xrange(_height), xrange(_length)):
        block = _structure.Blocks[xs, ys, zs]  # (id, data) tuple
        if ys == 14:
            print(xs, ys, zs, block)
        if block != Block['Structure Void'].ID:
            xd, yd, zd = x0 + xs, y0 + ys, z0 + zs  # coordinates in the level: translation of the structure
            setBlock(level, block, xd, yd, zd)


class Generator:
    _box = None  # type: TransformBox

    def __init__(self, box, entry_point=None):
        # type: (TransformBox, Point2D) -> Generator
        self._box = box
        self._entry_point = entry_point if entry_point is not None else Point2D(0, 0)
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
        self._gen_animal_farm(level, height_map)

    def _gen_animal_farm(self, level, height_map, animal='Cow'):
        # type: (MCLevel, numpy.array, str) -> None
        # todo: abreuvoir + herbe + abri
        x, z = self._box.minx, self._box.minz
        y = height_map[x - self._box.minx, z - self._box.minz]
        fence_box = TransformBox((x, y, z), (self.width, 1, self.length))
        fillBlocks(level, fence_box, Block['Oak Fence'])
        fence_box.expand(-1, 0, -1, True)
        fillBlocks(level, fence_box, Block['Air'])
        animal_count = fence_box.surface // SURFACE_PER_ANIMAL
        for _ in xrange(animal_count):
            entity = Entity.Create(animal)  # type: Entity
            x = randint(fence_box.minx, fence_box.maxx-1)
            z = randint(fence_box.minz, fence_box.maxz-1)
            Entity.setpos(entity, (x, y, z))
            level.addEntity(entity)

    def _gen_crop_v1(self, level):
        # dimensions
        x0, y0, z0 = self.origin
        # block states
        crop_ids = [141, 142, 59]
        prob = ones(len(crop_ids)) / len(crop_ids)  # uniform across the crops

        water_sources = (1 + (self.width - 1) // 9) * (1 + (self.length - 1) // 9)  # each water source irrigates a 9x9 flat zone
        for _ in xrange(water_sources):
            xs, zs = x0 + randint(0, self.width - 1), z0 + randint(0, self.length - 1)
            for xd, zd in product(xrange(max(x0, xs - 4), min(x0 + self.width, xs + 5)),
                                  xrange(max(z0, zs - 4), min(z0 + self.length, zs + 5))):
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


class WindmillGenerator(Generator):
    def generate(self, level, height_map=None):
        # type: (MCLevel, array) -> None
        box = self._box
        x, z = box.minx + box.width // 2, box.minz + box.length // 2
        y = height_map[box.width//2, box.length//2] if height_map is not None else 15
        box = TransformBox((x-5, y-14, z-4), (11, 11, 8))
        fillBlocks(level, box.expand(1), Block['Bedrock'])  # protective shell around windmill frames

        windmill_nbt = StructureNBT(sep.join([get_project_path(), 'structures', 'gdmc_windmill.nbt']))
        windmill_sch = windmill_nbt.toSchematic()
        copyBlocksFrom(level, windmill_sch, windmill_sch.bounds, box.origin)
        ground_box = TransformBox((x-2, y, z-2), (5, 1, 5))

        self.__activate_one_repeater(level, ground_box)

    @staticmethod
    def __activate_one_repeater(level, box):
        # type: (MCLevel, TransformBox) -> None
        repeatr_pos = []
        repeatr_id = Block['unpowered_repeater'].ID
        for x, y, z in box.positions:
            block_id = level.blockAt(x, y, z)
            if block_id == repeatr_id:
                repeatr_pos.append((x, y, z))

        x, y, z = box.minx + 1, box.miny, box.maxz-1
        repeater = Block[repeatr_id, level.blockDataAt(x, y, z)]
        dir_str = str(repeater.Blockstate[1]['facing'])
        dir_com = Direction.from_string(dir_str)

        # activate a repeater and preparing its tile tick
        block = Block['Redstone Repeater (Powered, Delay 4, {})'.format(str(-dir_com))]
        WindmillGenerator.__repeater_tile_tick(level, x, y, z, True)
        setBlock(level, (block.ID, block.blockData), x, y, z)

        # activate the command block following the previous repeater
        x += 1
        command_block_entity = level.getTileEntitiesInBox(TransformBox((x, y, z), (1, 1, 1)))[0]
        command_block_entity['powered'].value = True  # power command block

        # prepare tile tick for the repeater following the command block
        x += 1
        WindmillGenerator.__repeater_tile_tick(level, x, y, z, False)

    @staticmethod
    def __repeater_tile_tick(level, x, y, z, powered):
        string_id = '{}powered_repeater'.format('' if powered else 'un')
        tile_tick = TAG_Compound()
        tile_tick.add(TAG_Int(-1, 'p'))
        tile_tick.add(TAG_Int(10, 't'))
        tile_tick.add(TAG_Int(x, 'x'))
        tile_tick.add(TAG_Int(y, 'y'))
        tile_tick.add(TAG_Int(z, 'z'))
        tile_tick.add(TAG_String(string_id, 'i'))
        level.addTileTick(tile_tick)
