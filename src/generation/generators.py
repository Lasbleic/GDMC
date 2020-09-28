from math import floor
from os import sep
from random import randint

from numpy import percentile
from numpy.random import choice

from generation.building_palette import HousePalette
from pymclevel import MCLevel, Entity, TAG_Compound, TAG_Int, TAG_String
from pymclevel.block_copy import copyBlocksFrom
from pymclevel.block_fill import fillBlocks
from utils import *
from utils.structure_void_handle import VoidStructureNBT, all_but_void

SURFACE_PER_ANIMAL = 16


def copyBlocksWrap(level, sch, box, origin, blocksToCopy=all_but_void):
    try:
        copyBlocksFrom(level, sch, box, origin, blocksToCopy=blocksToCopy)
    except IndexError:
        level.removeEntitiesInBox(box)
        copyBlocksFrom(level, sch, box, origin, blocksToCopy=blocksToCopy)


class Generator:
    _box = None  # type: TransformBox

    def __init__(self, box, entry_point=None, mask=None):
        # type: (TransformBox, Point2D, ndarray) -> Generator
        self._box = box
        self._entry_point = entry_point if entry_point is not None else Point2D(0, 0)
        self.children = []  # type: List[Generator]
        self._sub_generator_function = None

    def _clear_trees(self, level):
        for x, z in product(range(self._box.minx, self._box.maxx), range(self._box.minz, self._box.maxz)):
            clear_tree_at(level, self._box, Point2D(x, z))

    def surface_pos(self, height_map):
        for x, z in product(xrange(self.width), xrange(self.length)):
            yield x+self.origin.x, height_map[x, z], z+self.origin.z

    def choose_sub_generator(self, parcels):
        pass

    def generate(self, level, height_map=None, palette=None):
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
            sub_generator.generate(level, height_map, palette)

    def is_corner(self, pos):
        return Generator.is_lateral(self, pos.x) and Generator.is_lateral(self, None, pos.z)

    def is_lateral(self, x=None, z=None):
        assert x is not None or z is not None
        z_lateral = (z == self._box.minz or z == self._box.maxz - 1)
        x_lateral = (x == self._box.minx or x == self._box.maxx - 1)
        if x is None:
            return z_lateral
        if z is None:
            return x_lateral
        else:
            return x_lateral or z_lateral

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

    @property
    def mean(self):
        return Point2D(self._box.minx + self.width // 2, self._box.minz + self.length // 2)

    def translate(self, dx=0, dy=0, dz=0):
        self._box.translate(dx, dy, dz, True)
        for gen in self.children:
            gen.translate(dx, dy, dz)

    @property
    def entry_direction(self):
        door_x, door_z = self._entry_point.x, self._entry_point.z
        mean_x, mean_z = self._box.minx + self.width // 2, self._box.minz + self.length // 2
        try:
            return Direction(dx=door_x-mean_x, dz=door_z-mean_z)
        except AssertionError:
            return list(cardinal_directions())[0]

    def absolute_coords(self, x, z):
        return x + self._box.minx, z + self._box.minz


class MaskedGenerator(Generator):
    def __init__(self, box, entry_point=None, mask=None):
        Generator.__init__(self, box, entry_point)
        if mask is None:
            mask = full((box.width, box.length), True)
        self.__mask = mask

    def _terraform(self, level, height_map):
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

    def is_masked(self, px, z=None, absolute_coords=False):
        if z is None:
            return self.is_masked(px.x, px.z, absolute_coords)
        else:
            if absolute_coords:
                return self.is_masked(px - self.origin.x, z - self.origin.z, False)
            else:
                return self.__mask[px, z]

    def surface_pos(self, height_map):
        for x, y, z in Generator.surface_pos(self, height_map):
            if self.is_masked(x, z, True):
                yield x, y, z

    def is_corner(self, pos):
        if Generator.is_corner(self, pos):
            return self.is_masked(pos, absolute_coords=True)  # box corner in mask
        elif not self.is_masked(pos, absolute_coords=True):
            return False
        else:
            # internal point to the box, could still be a corner
            try:
                x_lateral = not (self.is_masked(pos + East.asPoint2D, absolute_coords=True)
                                 and self.is_masked(pos + West.asPoint2D, absolute_coords=True)
                                 )
            except IndexError:
                x_lateral = False

            try:
                z_lateral = not (self.is_masked(pos + South.asPoint2D, absolute_coords=True)
                                 and self.is_masked(pos + North.asPoint2D, absolute_coords=True)
                                 )
            except IndexError:
                z_lateral = False
            return x_lateral and z_lateral

    def is_lateral(self, x=None, z=None):
        if not (0 <= x < self.width and 0 <= z < self.length):
            return False
        elif Generator.is_lateral(self, x, z):
            return self.is_masked(x, z, True)
        elif not self.is_masked(x, z, True):
            return False
        else:
            assert x is not None and z is not None
            pos = Point2D(x, z)
            return any(not self.is_masked(pos + dir.asPoint2D, absolute_coords=True) for dir in cardinal_directions())

    def _clear_trees(self, level):
        x0, z0 = self.origin.x, self.origin.z
        for x, z in product(range(self._box.minx, self._box.maxx), range(self._box.minz, self._box.maxz)):
            if self.__mask[x-x0, z-z0]:
                clear_tree_at(level, self._box, Point2D(x, z))

    def add_mask(self, height_mask):
        assert self.__mask.shape == height_mask.shape
        self.__mask = self.__mask & height_mask


class CropGenerator(MaskedGenerator):

    def choose_sub_generator(self, parcels):
        # type: (List[Parcel]) -> None
        if any(_.building_type.name == 'windmill' for _ in parcels):
            d = min(euclidean(self.mean, _.absolute_mean) for _ in parcels if _.building_type.name == 'windmill')
            if d <= 24:
                self._sub_generator_function = self._gen_harvested_crop
            elif d <= 35:
                self._sub_generator_function = self._gen_crop_v1
            else:
                self._sub_generator_function = self._gen_animal_farm
        else:
            self._sub_generator_function = choice([self._gen_harvested_crop, self._gen_crop_v1, self._gen_animal_farm])

    def generate(self, level, height_map=None, palette=None):
        # height_map = self._terraform(level, height_map)
        self.__terraform(level, height_map)
        self._clear_trees(level)
        self._sub_generator_function(level, height_map, palette)

    def _gen_animal_farm(self, level, height_map, palette, animal=None):
        # type: (MCLevel, array, HousePalette, str) -> None
        # todo: abreuvoir + herbe + abri + terrain adaptability
        if not animal:
            animal = choice(["Cow", "Pig", "Chicken", "Sheep"])
        fence_box = TransformBox(self.origin, (self.width, 1, self.length)).expand(-1, 0, -1)
        fence_block = Materials['{} Fence'.format(palette['door'])]
        gate_pos, gate_dist, gate_block = None, 0, None

        max_height = percentile(height_map.flatten(), 85)
        # place fences
        for x, y, z in self.surface_pos(height_map):
            if not self.is_masked(x, z, True):
                continue
            if self.is_lateral(x, z) and y <= max_height:
                setBlock(level, fence_block, x, y + 1, z)
                new_gate_pos = Point2D(x, z)
                new_gate_dist = euclidean(new_gate_pos, self._entry_point)
                if (gate_pos is None or new_gate_dist < gate_dist) and not self.is_corner(new_gate_pos):
                    gate_pos, gate_dist = new_gate_pos, new_gate_dist
                    door_dir_vec = self._entry_point - gate_pos
                    door_dir = Direction(dx=door_dir_vec.x, dz=door_dir_vec.z)
                    gate_block = Materials['{} Fence Gate (Closed, {})'.format(palette['door'], door_dir)]

        # place gate
        if gate_pos:
            x, z = gate_pos.x, gate_pos.z
            y = height_map[x-self.origin.x, z-self.origin.z] + 1
            setBlock(level, gate_block, x, y, z)

        # place animals
        animal_count = fence_box.surface // SURFACE_PER_ANIMAL
        for _ in xrange(animal_count):
            entity = Entity.Create(animal)  # type: Entity
            x = randint(fence_box.minx, fence_box.maxx-1)
            z = randint(fence_box.minz, fence_box.maxz-1)
            y = height_map[x-self.origin.x, z-self.origin.z] + 1
            Entity.setpos(entity, (x, y, z))
            level.addEntity(entity)

    def _gen_crop_v1(self, level, height=None, palette=None):
        # dimensions
        x0, y0, z0 = self.origin
        min_height = int(percentile(height.flatten(), 15))
        max_height = int(percentile(height.flatten(), 85))
        # block states
        crop_ids = [141, 142, 59]
        prob = ones(len(crop_ids)) / len(crop_ids)  # uniform across the crops

        # each water source irrigates a 9x9 flat zone
        water_sources = (1 + (self.width - 1) // 9) * (1 + (self.length - 1) // 9)
        for _ in xrange(water_sources):
            xs, zs = x0 + randint(0, self.width - 1), z0 + randint(0, self.length - 1)
            for xd, zd in product(xrange(max(x0, xs - 4), min(x0 + self.width, xs + 5)),
                                  xrange(max(z0, zs - 4), min(z0 + self.length, zs + 5))):
                if height is not None:
                    y0 = height[xd-x0, zd-z0]
                    if y0 < min_height:
                        fillBlocks(level, BoundingBox((xd-x0, y0, zd-z0), (1, min_height-y0, 1)), Materials["Coarse"])
                        y0 = min_height
                    elif y0 > max_height:
                        continue
                if not self.is_masked(xd, zd, True):
                    continue
                if (xd, zd) == (xs, zs):
                    # water source
                    setBlock(level, Materials["Water (Still, Level 7 (Source))"], xd, y0, zd)
                elif level.blockAt(xd, y0, zd) != 9:
                    setBlock(level, Materials["Farmland (Wet, Moisture 7)"], xd, y0, zd)  # farmland
                    bid = choice(crop_ids, p=prob)
                    age = randint(0, 7)
                    level.setBlockAt(xd, y0+1, zd, bid)
                    level.setBlockDataAt(xd, y0+1, zd, age)

    def _gen_harvested_crop(self, level, height_map, palette=None):
        # TODO: fix water sources
        mx, mz = randint(0, 1), randint(0, 2)
        for x, y, z in self.surface_pos(height_map):
            if (x % 2 == mx and (z+x//2) % 3 == mz) and bernouilli(0.35):
                setBlock(level, Materials["Dirt"], x, y, z)  # dirt under hay bales
                b = Materials["Hay Bale (East/West)"]
                y += 1
            else:
                b = Materials["Farmland (Dry, Moisture 6)"]
            setBlock(level, b, x, y, z)
        h = height_map
        irrigation_height = min(h[h.shape[0]//2, h.shape[1]//2], h.max()) + 1 - self._box.miny
        irrigation_box = TransformBox((self.mean.x, self._box.miny, self.mean.z), (1, irrigation_height, 1))
        fillBlocks(level, irrigation_box, Materials["Water (Still, Level 7 (Source))"])

    def __terraform(self, level, height_map):
        # type: (MCLevel, ndarray) -> ndarray
        road_dir_x, road_dir_z = self.entry_direction.x, self.entry_direction.z
        if road_dir_x == 1:
            road_side_height = height_map[-1, :]
        elif road_dir_x == -1:
            road_side_height = height_map[0, :]
        elif road_dir_z == -1:
            road_side_height = height_map[:, 0]
        else:
            road_side_height = height_map[:, -1]
        ref_height = int(round(road_side_height.mean()))
        height_mask = (height_map >= ref_height - 1) & (height_map <= ref_height + 1)
        self.add_mask(height_mask)
        for x, _, z in self.surface_pos(height_map):
            h = height_map[x-self.origin.x, z-self.origin.z]
            if h == (ref_height - 1):
                setBlock(level, Materials["Dirt"], x, ref_height, z)
            elif h == (ref_height + 1):
                setBlock(level, Materials["Air"], x, h, z)
        height_map[height_mask] = ref_height
        return height_map

    def is_lateral(self, x=None, z=None):
        if MaskedGenerator.is_lateral(self, x, z):
            return True
        p = Point2D(x, z)
        if not self.is_masked(p, absolute_coords=True):
            return False
        b1 = sum(MaskedGenerator.is_lateral(self, x + _.asPoint2D.x, z + _.asPoint2D.z) for _ in cardinal_directions()) >= 2
        return b1


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

    def generate(self, level, height_map=None, palette=None):
        for x, y, z in self._box.positions:
            setBlock(level, self._resource(x, y, z, palette), x, y, z)
        fillBlocks(level, self._box.translate(self._direction).split(dy=2)[0], Materials['Air'], ground_blocks)

    def _resource(self, x, y, z, palette):
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
            block_name = palette['wall']
        return Materials[block_name]


class WindmillGenerator(Generator):
    def generate(self, level, height_map=None, palette=None):
        # type: (MCLevel, array, dict) -> None
        box = self._box
        x, z = box.minx + box.width // 2, box.minz + box.length // 2
        y = height_map[box.width//2, box.length//2] if height_map is not None else 15
        box = TransformBox((x-5, y-32, z-4), (11, 11, 8))
        fillBlocks(level, box.expand(1), Materials['Bedrock'])  # protective shell around windmill frames
        mech_nbt = VoidStructureNBT(sep.join([get_project_path(), 'structures', 'gdmc_windmill_mech.nbt']))
        mech_sch = mech_nbt.toSchematic()
        copyBlocksWrap(level, mech_sch, mech_sch.bounds, box.origin)

        box.translate(dy=31, inplace=True)
        windmill_nbt = VoidStructureNBT(sep.join([get_project_path(), 'structures', 'gdmc_windmill.nbt']))
        windmill_sch = windmill_nbt.toSchematic()
        copyBlocksWrap(level, windmill_sch, windmill_sch.bounds, box.origin)
        ground_box = TransformBox((x-2, y, z-2), (5, 1, 5))

        self.__activate_one_repeater(level, ground_box)

    @staticmethod
    def __activate_one_repeater(level, box):
        # type: (MCLevel, TransformBox) -> None
        repeatr_pos = []
        repeatr_id = Materials['unpowered_repeater'].ID
        for x, y, z in box.positions:
            block_id = level.blockAt(x, y, z)
            if block_id == repeatr_id:
                repeatr_pos.append((x, y, z))

        x, y, z = box.minx + 1, box.miny, box.maxz-1
        repeater = Materials[repeatr_id, level.blockDataAt(x, y, z)]
        dir_str = str(repeater.Blockstate[1]['facing'])
        dir_com = Direction.from_string(dir_str)

        # activate a repeater and preparing its tile tick
        block = Materials['Redstone Repeater (Powered, Delay 4, {})'.format(str(-dir_com))]
        WindmillGenerator.__repeater_tile_tick(level, x, y, z, True)
        setBlock(level, block, x, y, z)

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


class WoodTower(Generator):
    def generate(self, level, height_map=None, palette=None):
        self._clear_trees(level)
        origin_x = self._box.minx + randint(0, self.width - 4)
        origin_z = self._box.minz + randint(0, self.length - 4)
        origin_y = height_map[origin_x + 2 - self._box.minx, origin_z + 2 - self._box.minz] + 1
        nbt = VoidStructureNBT(sep.join([get_project_path(), 'structures', 'wooden_watch_tower.nbt']))
        schem = nbt.toSchematic()
        # todo: rotate schematic to face door to entry point
        copyBlocksWrap(level, schem, schem.bounds, (origin_x, origin_y, origin_z))


class StoneTower(Generator):
    def generate(self, level, height_map=None, palette=None):
        self._clear_trees(level)
        # relative coords
        origin_x = randint(0, self.width - 8) if self.width > 8 else 0
        origin_z = randint(0, self.length - 8) if self.length > 8 else 0
        try:
            origin_y = height_map[origin_x + 4, origin_z + 4] + 1
        except IndexError:
            origin_y = int(round(height_map.mean()))
        # absolute coords
        origin_x += self._box.minx
        origin_z += self._box.minz
        nbt = VoidStructureNBT(sep.join([get_project_path(), 'structures', 'stone_watch_tower.nbt']))
        schem = nbt.toSchematic()
        # todo: rotate schematic to face door to entry point
        copyBlocksWrap(level, schem, schem.bounds, (origin_x, origin_y, origin_z))


class Plaza(Generator):
    def generate(self, level, height_map=None, palette=None):
        self._clear_trees(level)
        # if self.length >= 7 and self.width >= 7 and bernouilli(0.7):
        #     file_name = 'romantic_booth.nbt'
        #     origin_x = self._box.minx + randint(0, self.width - 7)
        #     origin_z = self._box.minz + randint(0, self.length - 7)
        #     origin_y = height_map[origin_x + 3 - self._box.minx, origin_z + 3 - self._box.minz] + 1
        # else:
        #     file_name = 'fountain.nbt'
        #     origin_x = self._box.minx + randint(0, self.width - 5)
        #     origin_z = self._box.minz + randint(0, self.length - 5)
        #     origin_y = height_map[origin_x + 2 - self._box.minx, origin_z + 2 - self._box.minz] + 1
        # nbt = VoidStructureNBT(sep.join([get_project_path(), 'structures', file_name]))
        # schem = nbt.toSchematic()
        # # todo: rotate schematic to face door to entry point
        # copyBlocksFrom(level, schem, schem.bounds, (origin_x, origin_y, origin_z), blocksToCopy=all_but_void)


def place_street_lamp(level, x, y, z, material):
    fillBlocks(level, BoundingBox((x, y+1, z), (1, 3, 1)), Materials[material+" Fence"])
    setBlock(level, Materials["Redstone Lamp (Off)"], x, y+4, z)
    setBlock(level, Materials["Daylight Sensor Inverted (Power 0)"], x, y+5, z)
