from generation.gen_utils import North, South, West, East
from generation.generators import *
from pymclevel import MCLevel, MCSchematic
from pymclevel.block_copy import copyBlocksFrom
from pymclevel.block_fill import fillBlocks
from utils import bernouilli


class ProcHouseGenerator(Generator):

    def __init__(self, box):
        Generator.__init__(self, box)

    def generate(self, level, height_map=None):
        self._generate_main_building()
        self._generate_annex()
        self._center_building()
        Generator.generate(self, level, height_map)
        self._generate_door(level)
        self._generate_stairs(level)

    def _generate_main_building(self):
        w0, h0, l0 = self._box.width, self._box.height, self._box.length
        # generate main building
        w1, l1 = randint(max(5, w0//2), w0 - 2), randint(max(5, l0/2), l0 - 2)
        self._layout_width = w1
        self._layout_length = l1
        main_box = TransformBox(self._box.origin + (0, 1, 0), (w1, h0, l1))
        self.children.append(_RoomSymbol(main_box, has_base=True))

    def _generate_annex(self):
        height = self.children[0].height - 2  # note: -2 makes annexes on average 2 blocks lower than the main build
        w0, w1, l0, l1 = self.width, self.children[0].width, self.length, self.children[0].length
        # extension in x
        try:
            max_width = w0 - w1  # available width
            width = randint(-max_width, max_width)  # annex width, west or east of main room
            width = 2 * width if (abs(width) == 1) and max_width >= 2 else width
            length = randint(5, l1 - 2)  # annex length, limited by main room's dimension
            delta = randint(0, l1 - length)  # position relative to main room

            if width:
                if width > 0:
                    annex_box = TransformBox(self.children[0].origin + (w1, 0, delta), (width, height, length))
                else:
                    annex_box = TransformBox(self.children[0].origin + (0, 0, delta), (-width, height, length))
                    self.children[0].translate(dx=-width)
                direction = Direction(dx=width)
                self.children[0][direction] = _RoomSymbol(annex_box, has_base=True)
                self._layout_width += abs(width) - 1

        except ValueError:
            # if excepted, should have been raised from randint
            print('not enough space to build an annex in x')

        # extension in z
        try:
            max_length = l0 - l1  # available width
            length = randint(-max_length, max_length)  # annex length, north or south of main room
            length = 2 * length if (abs(length) == 1) and max_length >= 2 else length
            width = randint(5, w1 - 2)  # annex length, limited by main room's dimension
            delta = randint(0, w1 - width)  # position relative to main room

            if length:
                if length > 0:
                    annex_box = TransformBox(self.children[0].origin + (delta, 0, l1), (width, height, length))
                else:
                    annex_box = TransformBox(self.children[0].origin + (delta, 0, 0), (width, height, -length))
                    self.children[0].translate(dz=-length)
                direction = Direction(dz=length)
                self.children[0][direction] = _RoomSymbol(annex_box, has_base=True)
                self._layout_length += abs(length) - 1

        except ValueError:
            # if excepted, should have been raised from randint
            print('not enough space to build an annex in z')

    def _center_building(self):
        dx = (self._box.width - self._layout_width) / 2
        dz = (self._box.length - self._layout_length) / 2
        self.children[0].translate(dx, 0, dz)

    def _generate_door(self, level):
        door_x, door_z = self._box.maxx, self._box.maxz  # todo: use parcel entrance instead
        mean_x, mean_z = self._box.minx + self.width // 2, self._box.minz + self.length // 2
        door_direction = Direction(dx=door_x-mean_x, dz=door_z-mean_z)
        self.children[0].generate_door(door_direction, door_x, door_z, level)

    def _generate_stairs(self, level):
        pass


class _RoomSymbol(CardinalGenerator):

    def __init__(self, box, has_base=False):
        CardinalGenerator.__init__(self, box)
        self._has_base = has_base

    def generate(self, level, height_map=None):
        print("Generating Room at", self._get_box().origin, self._get_box().size)
        if self._has_base:
            self.children.append(_BaseSymbol(TransformBox(self.origin - (0, 1, 0), (self.width, 1, self.length))))
        self._generate_pillars(level)
        self._create_walls(level)

        prob = self._box.height / 4 - 1  # probability to build an upper floor
        upper_box = self._get_upper_box()

        if bernouilli(prob):
            upper_room = _RoomSymbol(upper_box)
        else:
            upper_room = _RoofSymbol(upper_box, roof_type='gable')
        self[Top] = upper_room
        # build upper Symbol
        Generator.generate(self, level, height_map)

    def _get_box(self):
        return TransformBox(self._box.origin, (self._box.width, 4, self._box.length))

    def _get_upper_box(self):
        box = self._box
        new_origin = box.origin + (0, 4, 0)
        new_height = max(1, box.height - 4)
        new_size = (box.width, new_height, box.length)
        return TransformBox(new_origin, new_size)

    def _generate_pillars(self, level):
        b = self._get_box()
        for col_box in [TransformBox(b.origin, (1, b.height, 1)),
                        TransformBox(b.origin + (0, 0, b.length - 1), (1, b.height, 1)),
                        TransformBox(b.origin + (b.width - 1, 0, 0), (1, b.height, 1)),
                        TransformBox(b.origin + (b.width - 1, 0, b.length - 1), (1, b.height, 1))]:
            fillBlocks(level, col_box, Block['Oak Wood (Upright)'])

    def _create_walls(self, level):
        for direction in cardinal_directions():
            wall_box = self.get_wall_box(direction)
            if self[direction] is not None:
                if isinstance(self[direction], _RoofSymbol):
                    fillBlocks(level, wall_box, Block['Oak Wood Planks'])
                    continue
                elif wall_box.volume < self[direction].get_wall_box(-direction).volume:
                    wall_box.expand(direction, inplace=True)
                    wider_box = wall_box.enlarge(direction)
                    fillBlocks(level, wider_box, Block['Oak Wood Planks'])
                    fillBlocks(level, wall_box, Block['Air'])
                    continue

            # some annexes are only one block wide or long, could generate negative dimensions
            if abs(wall_box.width) * abs(wall_box.length) >= 1:
                self.children.insert(0, _WallSymbol(wall_box))

    def get_wall_box(self, direction):
        # type: (Direction) -> TransformBox
        b = self._get_box()
        if direction == North:
            return TransformBox(b.origin + (1, 0, 0), (b.width - 2, b.height, 1))
        elif direction == South:
            return TransformBox(b.origin + (1, 0, b.length - 1), (b.width - 2, b.height, 1))
        elif direction == West:
            return TransformBox(b.origin + (0, 0, 1), (1, b.height, b.length - 2))
        elif direction == East:
            return TransformBox(b.origin + (b.width - 1, 0, 1), (1, b.height, b.length - 2))
        else:
            raise ValueError("Not implemented yet, or unexpected direction")

    def generate_door(self, parcel_door_dir, door_x, door_z, level):
        # type: (Direction, int, int, MCLevel) -> None
        """
            Generate a door in self room
            Parameters
            ----------
            parcel_door_dir Direction of the door relative to the parcel
            door_x X coordinate of the door on the parcel border
            door_z Z coordinate of the door on the parcel border
        """
        mean_x, mean_z = self._box.minx + self.width // 2, self._box.minz + self.length // 2  # center of the room
        local_door_dir = Direction(dx=door_x-mean_x, dz=door_z-mean_z)  # direction of the door relative to this room
        if self[local_door_dir] is not None and isinstance(self[local_door_dir], _RoomSymbol):
            # passes the door to an annex room
            self[local_door_dir].generate_door(local_door_dir, door_x, door_z, level)
        else:
            # passes the door to the most suited wall of the room (no annex, close to entrance & large enough)
            door_dir = local_door_dir if self.get_wall_box(local_door_dir).surface > 1 else parcel_door_dir
            door_wall_box = self.get_wall_box(door_dir)
            self[door_wall_box].generate_door(door_dir, door_x, door_z, level)


class _RoofSymbol(CardinalGenerator):

    def __init__(self, box, direction=None, roof_type='flat'):
        # type: (TransformBox, Direction, str) -> _RoofSymbol
        CardinalGenerator.__init__(self, box)
        self._direction = direction
        self._roof_type = roof_type

        if self._direction is None:
            # sets roof direction randomly, lower roofs are preferred
            width, length = self._box.width, self._box.length
            if width < 5:
                self._direction = East
            elif length < 5:
                self._direction = South
            else:
                prob = (1. * width ** 2) / (width ** 2 + length ** 2)
                self._direction = South if (bernouilli(prob)) else East

    def generate(self, level, height_map=None):
        material = 'Stone Brick'
        box = self._get_box()
        if self._roof_type == 'flat':
            fillBlocks(level, box, Block['Bricks'])
        elif self._roof_type == 'gable':
            box.expand(1, 1, 1, inplace=True)
            stair_format = '{} Stairs (Bottom, {})'
            stair_revers = '{} Stairs (Top, {})'
            if self._direction in [West, East]:
                for index in xrange(box.length / 2):
                    north_box = TransformBox((box.minx, box.miny + index, box.maxz - index - 1), (box.width, 1, 1))
                    fillBlocks(level, north_box, Block[stair_format.format(material, 'North')], [Block['Air']])
                    south_box = TransformBox((box.minx, box.miny + index, box.minz + index), (box.width, 1, 1))
                    fillBlocks(level, south_box, Block[stair_format.format(material, 'South')], [Block['Air']])
                    if index != 0:
                        for x, z in product([self._box.minx, self._box.maxx-1], [north_box.minz, south_box.maxz]):
                            col_box = TransformBox((x, box.miny+1, z), (1, index, 1))
                            fillBlocks(level, col_box, Block['Bone Block (Upright)'], [Block['Air']])
                        fillBlocks(level, north_box.translate(dy=-1), Block[stair_revers.format(material, 'South')], [Block['Air']])
                        fillBlocks(level, south_box.translate(dy=-1), Block[stair_revers.format(material, 'North')], [Block['Air']])
                # build roof ridge
                if box.length % 2 == 1:
                    index = box.length / 2
                    ridge_box = TransformBox((box.minx, box.miny + index, box.minz + index), (box.width, 1, 1))
                    fillBlocks(level, ridge_box, Block['{} Slab (Bottom)'.format(material)], [Block['Air']])
                    fillBlocks(level, ridge_box.translate(dy=-1), Block['Oak Wood (East/West)'], [Block['Air']])
            elif self._direction in [North, South]:
                for index in xrange(box.width / 2):
                    east_box = TransformBox((box.minx + index, box.miny + index, box.minz), (1, 1, box.length))
                    fillBlocks(level, east_box, Block[stair_format.format(material, 'East')], [Block['Air']])
                    west_box = TransformBox((box.maxx - index - 1, box.miny + index, box.minz), (1, 1, box.length))
                    fillBlocks(level, west_box, Block[stair_format.format(material, 'West')], [Block['Air']])
                    if index != 0:
                        for x, z in product([east_box.minx, west_box.minx], [self._box.minz, self._box.maxz-1]):
                            col_box = TransformBox((x, box.miny+1, z), (1, index, 1))
                            fillBlocks(level, col_box, Block['Bone Block (Upright)'], [Block['Air']])
                        fillBlocks(level, east_box.translate(dy=-1), Block[stair_revers.format(material, 'West')], [Block['Air']])
                        fillBlocks(level, west_box.translate(dy=-1), Block[stair_revers.format(material, 'East')], [Block['Air']])
                # build roof ridge
                if box.width % 2 == 1:
                    index = box.width / 2
                    ridge_box = TransformBox((box.minx + index, box.miny + index, box.minz), (1, 1, box.length))
                    fillBlocks(level, ridge_box, Block['{} Slab (Bottom)'.format(material)], [Block['Air']])
                    fillBlocks(level, ridge_box.translate(dy=-1), Block['Oak Wood (North/South)'], [Block['Air']])
            else:
                raise ValueError('Expected direction str, found {}'.format(self._direction))
            self.__gen_gable_cross(level)

    def _get_box(self):
        box = self._box
        height = 1 if self._direction is None else (box.width + 1) // 2 if self._direction in [North, South] else (box.length + 1) // 2
        new_size = (box.width, height, box.length)
        return TransformBox(box.origin, new_size)

    def __gen_gable_cross(self, level):
        for direction in cardinal_directions():
            if self[direction] is not None and isinstance(self[direction], _RoofSymbol):
                neighbour = self[direction]  # type: _RoofSymbol
                if abs(self._direction) == abs(direction) and abs(neighbour._direction.rotate()) == abs(direction):
                    box0 = self._box
                    box1 = neighbour._box
                    if direction in [North, South]:
                        box2 = TransformBox((box0.minx, box0.miny, box1.minz), (box0.width, box0.height, box1.length))
                    else:
                        box2 = TransformBox((box1.minx, box1.miny, box0.minz), (box1.width, box1.height, box0.length))
                    _RoofSymbol(box2, self._direction, self._roof_type).generate(level)


class _WallSymbol(Generator):
    def generate(self, level, height_map=None):
        assert (self.width == 1 or self.length == 1)
        assert (self.width * self.length >= 1)
        if self.length == 1:
            self._generate_xwall(level)
        else:
            self._generate_zwall(level, height_map)
        Generator.generate(self, level, height_map)

    def _generate_xwall(self, level):
        if self.width % 2 == 0:
            # even wall: split in two
            if self.width == 2:
                fillBlocks(level, self._box, Block['Oak Wood Planks'])
                if bernouilli(0.5):
                    fillBlocks(level, self._box.expand(0, -1, 0), Block['White Stained Glass Pane'])
            elif self.width == 4:
                fillBlocks(level, self._box, Block['Oak Wood Planks'])
                box_win = TransformBox(self._box.origin + (1, 0, 0), (2, self.height, 1))
                self.children.append(_WallSymbol(box_win))
            else:
                for half_wall_box in self._box.split(dx=randint(3, self.width - 3)):
                    self.children.append(_WallSymbol(half_wall_box))
        else:
            # uneven wall: derive in column | window | wall
            if self.width == 1:
                fillBlocks(level, self._box, Block['Oak Wood Planks'])
            else:
                box_col, box_wal = self._box.split(dx=2)
                box_win = TransformBox((self._box.origin + (1, 1, 0)), (1, self.height - 2, 1))
                fillBlocks(level, box_col, Block['Oak Wood Planks'])
                fillBlocks(level, box_win, Block['White Stained Glass Pane'])
                self.children.append(_WallSymbol(box_wal))

    def _generate_zwall(self, level, height_map):
        """
        Generates a flipped x_wall in a virtual level and pastes it to level.
        Kept the version without flip underneath cause I'm too much of a coward to delete it lol
        Parameters
        ----------
        level MCLevel level to generate in
        height_map

        Returns
        -------
        None
        """
        tmp_box = TransformBox((0, 0, 0), (self.length, self.height, self.width))  # flip wall box
        wall_level = MCSchematic(tmp_box.size)  # prepare virtual level to generate rotated wall
        _WallSymbol(tmp_box).generate(wall_level, height_map)  # generate rotated wall
        wall_level.rotateLeft()  # flip generated wall
        tmp_box = TransformBox(tmp_box.origin, self.size)  # flip generation box
        copyBlocksFrom(level, wall_level, tmp_box, self.origin)  # retrieve wall to real level

        # if self.length % 2 == 0:
        #     # even wall: split in two
        #     if self.length == 2:
        #         block = Block['Oak Wood Planks']
        #         fillBlocks(level, self._box, block)
        #         if bernouilli(0.5):
        #             fillBlocks(level, self._box.expand(0, -1, 0), Block['White Stained Glass Pane'])
        #     elif self.length == 4:
        #         fillBlocks(level, self._box, Block['Oak Wood Planks'])
        #         box_win = TransformBox(self._box.origin + (0, 0, 1), (1, self.height, 2))
        #         self.children.append(_WallSymbol(box_win))
        #     else:
        #         for half_wall_box in self._box.split(dz=randint(3, self.length - 3)):
        #             self.children.append(_WallSymbol(half_wall_box))
        # else:
        #     # uneven wall: derive in column | window | wall
        #     if self.length == 1:
        #         fillBlocks(level, self._box, Block['Oak Wood Planks'])
        #     else:
        #         box_col, box_wal = self._box.split(dz=2)
        #         box_win = TransformBox((self._box.origin + (0, 1, 1)), (1, self.height - 2, 1))
        #         fillBlocks(level, box_col, Block['Oak Wood Planks'])
        #         fillBlocks(level, box_win, Block['White Stained Glass Pane'])
        #         self.children.append(_WallSymbol(box_wal))

    def generate_door(self, door_dir, door_x, door_z, level):
        if not self.children:
            if self._box.surface <= 2:
                DoorGenerator(self._box, door_dir).generate(level)
            elif self.width > 2:
                DoorGenerator(self._box.expand(-((self.width-1)/2), 0, 0), door_dir).generate(level)
            else:
                DoorGenerator(self._box.expand(0, 0, -((self.length-1)/2)), door_dir).generate(level)
        elif len(self.children) == 1:
            if self.surface == 4 or self.surface > 3 and bernouilli(1. * self.surface / self.children[0].surface):
                self.children[0].generate_door(door_dir, door_x, door_z, level)
            else:
                # see wall structure, this is a part of an uneven wall -> replace window with door
                door_box = TransformBox(self.origin, (1, self.height, 1))
                door_box.translate(dx=1) if self.width > 2 else door_box.translate(dz=1)
                DoorGenerator(door_box, door_dir).generate(level)
        else:
            choice(self.children).generate_door(door_dir, door_x, door_z, level)


class _BaseSymbol(Generator):
    def generate(self, level, height_map=None):
        fillBlocks(level, self._box, Block['Cobblestone'])
