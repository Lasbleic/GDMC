from math import floor
from os import sep
from random import randint, random

from numpy import percentile
from numpy.random import choice

from generation.building_palette import HousePalette
from interfaceUtils import sendBlocks, runCommand
from utils import *

from utils.nbt_structures import StructureNBT

SURFACE_PER_ANIMAL = 16


class Generator:
    _box = None  # type: TransformBox

    def __init__(self, box: TransformBox, entry_point: Point = None, mask: ndarray = None):
        self._box = box
        self._entry_point = entry_point if entry_point is not None else Point(0, 0)
        self.children = []  # type: List[Generator]
        self._sub_generator_function = None

    def _clear_trees(self, level):
        for x, z in product(range(self._box.minx, self._box.maxx), range(self._box.minz, self._box.maxz)):
            clear_tree_at(level, Point(x, z))

    def surface_pos(self, height_map):
        for x, z in product(range(self.width), range(self.length)):
            yield x + self.origin.x, height_map[x, z], z + self.origin.z

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
        return Point(self._box.minx + self.width // 2, self._box.minz + self.length // 2)

    def translate(self, dx=0, dy=0, dz=0):
        self._box.translate(dx, dy, dz, True)
        for gen in self.children:
            gen.translate(dx, dy, dz)

    @property
    def entry_direction(self):
        door_x, door_z = self._entry_point.x, self._entry_point.z
        mean_x, mean_z = self._box.minx + self.width // 2, self._box.minz + self.length // 2
        try:
            return Direction.of(dx=door_x - mean_x, dz=door_z - mean_z)
        except AssertionError:
            return list(cardinal_directions())[0]

    def absolute_coords(self, x, z):
        return x + self._box.minx, z + self._box.minz


class MaskedGenerator(Generator):
    def __init__(self, box, entry_point=None, mask=None):
        Generator.__init__(self, box, entry_point)
        if mask is None:
            mask = full((box.width, box.length), True)
        self._mask = mask

    def _terraform(self, level, height_map):
        # type: (MCLevel, array) -> ndarray
        mean_y = int(round(height_map.mean()))
        terraform_map = zeros(height_map.shape)
        for x, y, z in self.surface_pos(height_map):
            if y > mean_y:
                vbox = BoundingBox((x, mean_y + 1, z), (1, y - mean_y + 1, 1))
                fillBlocks(vbox, BlockAPI.blocks.Air)
            elif y < mean_y:
                vbox = BoundingBox((x, y + 1, z), (1, mean_y - y, 1))
                material = BlockAPI.blocks.StoneBricks if self.is_lateral(x, z) else BlockAPI.blocks.Dirt
                fillBlocks(vbox, material)
        terraform_map[:] = mean_y
        return terraform_map

    def is_masked(self, px, z=None, absolute_coords=False):
        if z is None:
            return self.is_masked(px.x, px.z, absolute_coords)
        else:
            if absolute_coords:
                return self.is_masked(px - self.origin.x, z - self.origin.z, False)
            else:
                if 0 <= px < self.width and 0 <= z < self.length:
                    return self._mask[px, z]
                return False

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
                x_lateral = not (self.is_masked(pos + utils.Direction.East.value, absolute_coords=True)
                                 and self.is_masked(pos + utils.Direction.West.value, absolute_coords=True)
                                 )
            except IndexError:
                x_lateral = False

            try:
                z_lateral = not (self.is_masked(pos + utils.Direction.South.value, absolute_coords=True)
                                 and self.is_masked(pos + utils.Direction.North.value, absolute_coords=True)
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
            pos = Point(x, z)
            return any(not self.is_masked(pos + dir.asPoint, absolute_coords=True) for dir in cardinal_directions())

    def _clear_trees(self, level):
        x0, z0 = self.origin.x, self.origin.z
        for x, z in product(range(self._box.minx, self._box.maxx), range(self._box.minz, self._box.maxz)):
            if self._mask[x - x0, z - z0]:
                clear_tree_at(level, Point(x, z))

    def add_mask(self, height_mask):
        assert self._mask.shape == height_mask.shape
        self._mask = self._mask & height_mask

    def refine_mask(self):
        """
        Removes narrow positions from the mask
        """
        def surrounding(x, z):
            return filter(lambda xz: xz != (x, z) and self.is_masked(xz[0], xz[1], True), product(range(x-1, x+2), range(z-1, z+2)))

        def is_corner(xz):
            return self.is_corner(Point(*xz))

        def in_inner_mask(xz):
            return self.is_masked(*xz, True) and not self.is_lateral(*xz)

        mask_corners = {(x, z) for (x, y, z) in self.surface_pos(zeros((self.width, self.length))) if self.is_corner(Point(x, z))}
        while mask_corners:
            corner = mask_corners.pop()
            if all(not in_inner_mask(xz) for xz in surrounding(*corner)):
                self._mask[corner[0] - self.origin[0], corner[1] - self.origin[2]] = False
                mask_corners.update(filter(is_corner, surrounding(*corner)))


class CropGenerator(MaskedGenerator):

    animal_distribution = {"cow": 3, "pig": 2, "chicken": 3, "sheep": 2, "donkey": 1, "horse": 1, "rabbit": 1}

    def _pick_animal(self):
        samples = list(self.animal_distribution.keys())
        probs = array(list(self.animal_distribution.values()))
        probs = probs / sum(probs)
        return choice(samples, p=probs)

    def choose_sub_generator(self, parcels):
        # type: (List[Parcel]) -> None
        self._sub_generator_function = self._gen_animal_farm
        if any(_.building_type.name == 'windmill' for _ in parcels) and bernouilli():
            d = min(euclidean(self.mean, _.absolute_mean) for _ in parcels if _.building_type.name == 'windmill')
            if d <= 16:
                self._sub_generator_function = self._gen_harvested_crop
            elif d <= 28:
                self._sub_generator_function = self._gen_crop_v1
            else:
                self._sub_generator_function = self._gen_animal_farm
        else:
            self._sub_generator_function = choice([self._gen_harvested_crop, self._gen_crop_v1, self._gen_animal_farm])

    def generate(self, level, height_map=None, palette=None):
        self.__terraform(height_map)
        self._clear_trees(level)
        self._sub_generator_function(level, height_map, palette)

    def _gen_animal_farm(self, level, height_map, palette, animal=None):
        # type: (TerrainMaps, array, HousePalette, str) -> None
        # todo: surround water with trapdoors to avoid leaks
        self.refine_mask()
        if not animal:
            animal = self._pick_animal()
        fence_box = TransformBox(self.origin, (self.width, 1, self.length)).expand(-1, 0, -1)
        fence_block = BlockAPI.getFence(palette['door'])
        gate_pos, gate_dist, gate_block = None, 0, None

        # place fences
        for x, y, z in self.surface_pos(height_map):
            if not self.is_masked(x, z, True):
                continue
            if self.is_lateral(x, z):
                setBlock(Point(x, z, y + 1), fence_block)
                new_gate_pos = Point(x, z)
                new_gate_dist = euclidean(new_gate_pos, self._entry_point)
                if (gate_pos is None or new_gate_dist < gate_dist) and not self.is_corner(new_gate_pos):
                    gate_pos, gate_dist = new_gate_pos, new_gate_dist
                    door_dir_vec = self._entry_point - self.mean
                    door_dir = Direction.of(dx=door_dir_vec.x, dz=door_dir_vec.z)
                    for direction in cardinal_directions(False):
                        if not self.is_masked(gate_pos + direction.value, absolute_coords=True):
                            door_dir = direction
                            break
                    gate_block = BlockAPI.getFence(palette['door'], facing=str(door_dir).lower())

        print(gate_pos, gate_block)
        # place gate
        if gate_pos:
            x, z = gate_pos.x, gate_pos.z
            y = height_map[x - self.origin.x, z - self.origin.z] + 1
            setBlock(Point(x, z, y), gate_block)

        # place animals
        animal_count = sum(self._mask.flat) // SURFACE_PER_ANIMAL
        while animal_count > 0:
            x = randint(fence_box.minx, fence_box.maxx - 1)
            z = randint(fence_box.minz, fence_box.maxz - 1)
            y = height_map[x - self.origin.x, z - self.origin.z] + 1
            if self.is_masked(x, z, True) and not self.is_lateral(x, z):
                command = f"summon {animal} {x} {y} {z}"
                if bernouilli(.3):
                    command += "{" + f"Age:{randint(-25000, -5000)}" + "}"
                interfaceUtils.runCommand(command)
                animal_count -= 1
            else:
                animal_count -= .1

    def _gen_crop_v1(self, level, height=None, palette=None):
        from numpy import ones
        # todo: store max age somewhere (beetroots grow up to age 3)
        # todo: deter water sources from leaking everywhere
        # dimensions
        x0, y0, z0 = self.origin
        min_height = int(percentile(height.flatten(), 15))
        max_height = int(percentile(height.flatten(), 85))
        # block states
        b = BlockAPI.blocks
        crop_type = choice([b.Carrots, b.Beetroots, b.Potatoes, b.Wheat])
        crop_age = randint(2, 5)

        # each water source irrigates a 9x9 flat zone
        water_source_count = (1 + (self.width - 1) // 9) * (1 + (self.length - 1) // 9)
        if self.width <= 3 or self.length <= 3:
            water_source_count = 0
        water_sources = set()
        for _ in range(water_source_count):
            xs, zs = x0 + randint(1, self.width - 2), z0 + randint(1, self.length - 2)
            for xd, zd in product(range(max(x0, xs - 4), min(x0 + self.width, xs + 5)),
                                  range(max(z0, zs - 4), min(z0 + self.length, zs + 5))):
                if height is not None:
                    y0 = height[xd - x0, zd - z0]
                    if y0 < min_height:
                        fillBlocks(BoundingBox((xd, y0, zd), (1, min_height - y0, 1)), BlockAPI.blocks.CoarseDirt)
                        y0 = min_height
                    elif y0 > max_height:
                        continue
                if not self.is_masked(xd, zd, True):
                    continue
                if (xd, zd) == (xs, zs):
                    # water source
                    setBlock(Point(xd, zd, y0), BlockAPI.blocks.Water)
                    water_sources.add((xd, zd))
                elif (xd, zd) not in water_sources:
                    # farmland
                    setBlock(Point(xd, zd, y0), f"farmland[moisture=7]")

                    # crop
                    crop_age = crop_age + random() - .5
                    int_crop_age = pos_bound(int(round(crop_age)), 7)
                    crop_block = f"{crop_type}[age={int_crop_age}]"
                    setBlock(Point(xd, zd, y0+1), crop_block)

    def _gen_harvested_crop(self, level, height_map, palette=None):
        # TODO: fix water sources
        mx, mz = randint(0, 1), randint(0, 2)
        for x, y, z in self.surface_pos(height_map):
            if x % 9 in [5, (self.width - 4) % 9] and z % 9 in [5, (self.length - 4) % 9]:
                b = BlockAPI.blocks.Water
            if (x % 2 == mx and (z + x // 2) % 3 == mz) and bernouilli(0.35):
                setBlock(Point(x, z, y), BlockAPI.blocks.Dirt)  # dirt under hay bales
                b = BlockAPI.blocks.HayBlock
                y += 1
            else:
                b = BlockAPI.blocks.Farmland
            setBlock(Point(x, z, y), b)
        h = height_map
        irrigation_height = min(h[h.shape[0] // 2, h.shape[1] // 2], h.max()) + 1 - self._box.miny
        irrigation_box = TransformBox((self.mean.x, self._box.miny, self.mean.z), (1, 1, 1))
        fillBlocks(irrigation_box, BlockAPI.blocks.Water)

    def __terraform(self, height_map):
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
            h = height_map[x - self.origin.x, z - self.origin.z]
            if h == (ref_height - 1):
                setBlock(Point(x, z, ref_height), BlockAPI.blocks.Dirt)
            elif h == (ref_height + 1):
                setBlock(Point(x, z, h), BlockAPI.blocks.Air)
        height_map[height_mask] = ref_height
        return height_map

    def is_lateral(self, x=None, z=None):
        p = Point(x, z)
        if Generator.is_lateral(self, x, z):
            return True
        if not self.is_masked(p, absolute_coords=True):
            return False
        x0, z0 = x - self.origin.x, z - self.origin.z
        for x1, z1 in product(sym_range(x0, 1, self.width), sym_range(z0, 1, self.length)):
            if not self.is_masked(x1, z1):
                return True
        return False


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
            if neighbour[Direction.Bottom] is None:
                self.children.insert(0, neighbour)
            neighbour._neighbors[-direction] = self
            if direction == Direction.Top:
                for direction2 in cardinal_directions():
                    if self[direction2] is not None and self[direction2][Direction.Top] is not None:
                        neighbour[direction2] = self[direction2][Direction.Top]
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
            setBlock(Point(x, z, y), self._resource(x, y, z, palette))
        fillBlocks(self._box.translate(self._direction).split(dy=2)[0], BlockAPI.blocks.Air, ground_blocks)

    def _resource(self, x, y, z, palette):
        if self._box.miny <= y <= self._box.miny + 1:
            half = "lower" if y == self._box.miny else "upper"
            if self._box.surface == 1:
                hinge = 'left'
            else:
                mean_x = self._box.minx + 0.5 * self._box.width
                mean_z = self._box.minz + 0.5 * self._box.length
                norm_dir = self._direction.rotate()
                left_x = int(floor(mean_x + 0.5 * norm_dir.x))  # floored because int(negative float) rounds up
                left_z = int(floor(mean_z + 0.5 * norm_dir.z))
                hinge = 'left' if (x == left_x and z == left_z) else 'right'
            block_name = BlockAPI.getDoor(palette['door'], half=half, hinge=hinge, facing=(-self._direction).name.lower())
        else:
            block_name = palette['wall']
        return block_name


class WindmillGenerator(Generator):
    def generate(self, level, height_map=None, palette=None):
        # todo: reactivate windmills

        # Compute windmill position
        box = self._box
        x, z = box.minx + box.width // 2, box.minz + box.length // 2
        y = height_map[box.width//2, box.length//2]


        # Build floor
        ground_box = TransformBox((x-2, y, z-2), (5, 1, 5))
        fillBlocks(ground_box, BlockAPI.blocks.CoarseDirt)

        # Build windmill frames
        box = TransformBox((x-5, y-31, z-4), (11, 11, 8))
        fillBlocks(box.expand(1), BlockAPI.blocks.Bedrock)  # protective shell around windmill frames
        mech_nbt = StructureNBT('gdmc_windmill_mech.nbt')
        mech_nbt.build(*box.origin)

        # Build windmill
        box.translate(dy=31, inplace=True)
        windmill_nbt = StructureNBT('gdmc_windmill.nbt')
        windmill_nbt.build(*box.origin)
        sendBlocks()
        # print(runCommand(f'setblock {x} {y+4} {z-1} minecraft:redstone_wall_torch[facing=north, lit=true]'))
        runCommand(f'setblock {x} {y+4} {z-1} minecraft:redstone_wall_torch[facing=north, lit=true]')


class WoodTower(Generator): pass


#     def generate(self, level, height_map=None, palette=None):
#         self._clear_trees(level)
#         origin_x = self._box.minx + randint(0, self.width - 4)
#         origin_z = self._box.minz + randint(0, self.length - 4)
#         origin_y = height_map[origin_x + 2 - self._box.minx, origin_z + 2 - self._box.minz] + 1
#         nbt = VoidStructureNBT(sep.join([get_project_path(), 'structures', 'wooden_watch_tower.nbt']))
#         schem = nbt.toSchematic()
#         # todo: rotate schematic to face door to entry point
#         copyBlocksWrap(level, schem, schem.bounds, (origin_x, origin_y, origin_z))


class StoneTower(Generator): pass


#     def generate(self, level, height_map=None, palette=None):
#         self._clear_trees(level)
#         # relative coords
#         origin_x = randint(0, self.width - 8) if self.width > 8 else 0
#         origin_z = randint(0, self.length - 8) if self.length > 8 else 0
#         try:
#             origin_y = height_map[origin_x + 4, origin_z + 4] + 1
#         except IndexError:
#             origin_y = int(round(height_map.mean()))
#         # absolute coords
#         origin_x += self._box.minx
#         origin_z += self._box.minz
#         nbt = VoidStructureNBT(sep.join([get_project_path(), 'structures', 'stone_watch_tower.nbt']))
#         schem = nbt.toSchematic()
#         # todo: rotate schematic to face door to entry point
#         copyBlocksWrap(level, schem, schem.bounds, (origin_x, origin_y, origin_z))


def place_street_lamp(level, x, y, z, material):
    fillBlocks(BoundingBox((x, y + 1, z), (1, 3, 1)), BlockAPI.getFence(material))
    setBlock(Point(x, z, y + 4), BlockAPI.blocks.RedstoneLamp)
    setBlock(Point(x, z, y + 5), f"daylight_detector[inverted=true]")


if __name__ == '__main__':
    gen = CropGenerator(TransformBox((0, 0, 0), (1, 1, 1)))
    print(gen.animal_distribution)
    print(gen._pick_animal())
