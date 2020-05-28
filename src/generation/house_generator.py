from generation.generators import *
from generation.gen_utils import TransformBox, Direction, South, North, West, Top, Bottom, East, cardinal_directions
from pymclevel import alphaMaterials as Block
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

    def _generate_main_building(self):
        w0, h0, l0 = self._box.width, self._box.height, self._box.length
        # generate main building
        w1, l1 = randint(max(5, w0//2), w0 - 2), randint(max(5, l0/2), l0 - 2)
        self._layout_width = w1
        self._layout_length = l1
        main_box = TransformBox(self._box.origin, (w1, h0, l1))
        self.children.append(_RoomSymbol(main_box))

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
                    annex_box = TransformBox(self._box.origin + (w1, 0, delta), (width, height, length))
                else:
                    annex_box = TransformBox(self._box.origin + (0, 0, delta), (-width, height, length))
                    self.children[0].translate(dx=-width)
                direction = Direction(dx=width)
                self.children[0][direction] = _RoomSymbol(annex_box)
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
                    annex_box = TransformBox(self.children[0]._box.origin + (delta, 0, l1), (width, height, length))
                else:
                    annex_box = TransformBox(self.children[0]._box.origin + (delta, 0, 0), (width, height, -length))
                    self.children[0].translate(dz=-length)
                direction = Direction(dz=length)
                self.children[0][direction] = _RoomSymbol(annex_box)
                self._layout_length += abs(length) - 1

        except ValueError:
            # if excepted, should have been raised from randint
            print('not enough space to build an annex in z')

    def _center_building(self):
        dx = (self._box.width - self._layout_width) / 2
        dz = (self._box.length - self._layout_length) / 2
        self.children[0].translate(dx, 0, dz)


class _RoomSymbol(CardinalGenerator):

    def generate(self, level, height_map=None):
        print("Generating Room at", self._get_box().origin, self._get_box().size)
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
                _WallSymbol(wall_box).generate(level, height_map=None)

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


class _RoofSymbol(CardinalGenerator):

    def __init__(self, box, direction=None, roof_type='flat'):
        # type: (TransformBox, Direction, str) -> _RoofSymbol
        CardinalGenerator.__init__(self, box)
        self._direction = direction
        self._roof_type = roof_type

        if self._direction is None:
            # sets roof direction randomly, lower roofs are preferred
            w, l = self._box.width, self._box.length
            if w < 5:
                self._direction = East
            elif l < 5:
                self._direction = South
            else:
                prob = (1. * w ** 2) / (w ** 2 + l ** 2)
                self._direction = South if (bernouilli(prob)) else East

    def generate(self, level, height_map=None):
        material = 'Stone Brick'
        box = self._get_box()
        if self._roof_type == 'flat':
            fillBlocks(level, box, Block['Bricks'])
        elif self._roof_type == 'gable':
            stair_format = '{} Stairs (Bottom, {})'
            if self._direction in [West, East]:
                for index in xrange(box.length / 2):
                    north_box = TransformBox((box.minx, box.miny + index, box.maxz - index - 1), (box.width, 1, 1))
                    fillBlocks(level, north_box, Block[stair_format.format(material, 'North')])
                    south_box = TransformBox((box.minx, box.miny + index, box.minz + index), (box.width, 1, 1))
                    fillBlocks(level, south_box, Block[stair_format.format(material, 'South')])
                # build roof ridge
                if box.length % 2 == 1:
                    index = box.length / 2
                    ridge_box = TransformBox((box.minx, box.miny + index, box.minz + index), (box.width, 1, 1))
                    fillBlocks(level, ridge_box, Block['{} Slab (Bottom)'.format(material)])
            elif self._direction in [North, South]:
                for index in xrange(box.width / 2):
                    east_box = TransformBox((box.minx + index, box.miny + index, box.minz), (1, 1, box.length))
                    fillBlocks(level, east_box, Block[stair_format.format(material, 'East')])
                    west_box = TransformBox((box.maxx - index - 1, box.miny + index, box.minz), (1, 1, box.length))
                    fillBlocks(level, west_box, Block[stair_format.format(material, 'West')])
                # build roof ridge
                if box.width % 2 == 1:
                    index = box.width / 2
                    ridge_box = TransformBox((box.minx + index, box.miny + index, box.minz), (1, 1, box.length))
                    fillBlocks(level, ridge_box, Block['{} Slab (Bottom)'.format(material)])
            else:
                raise ValueError('Expected direction str, found {}'.format(self._direction))

    def _get_box(self):
        box = self._box
        new_size = (box.width, 1, box.length)
        return TransformBox(box.origin, new_size)


class _WallSymbol(Generator):
    def generate(self, level, height_map=None):
        assert (self.width == 1 or self.length == 1)
        assert (self.width * self.length >= 1)
        if self.width > 1:
            self._generate_xwall(level, height_map)
        else:
            self._generate_zwall(level, height_map)
        Generator.generate(self, level, height_map)

    def _generate_xwall(self, level, height_map):
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
        if self.length % 2 == 0:
            # even wall: split in two
            if self.length == 2:
                block = Block['Oak Wood Planks']
                fillBlocks(level, self._box, block)
                if bernouilli(0.5):
                    fillBlocks(level, self._box.expand(0, -1, 0), Block['White Stained Glass Pane'])
            elif self.length == 4:
                fillBlocks(level, self._box, Block['Oak Wood Planks'])
                box_win = TransformBox(self._box.origin + (0, 0, 1), (1, self.height, 2))
                self.children.append(_WallSymbol(box_win))
            else:
                for half_wall_box in self._box.split(dz=randint(3, self.length - 3)):
                    self.children.append(_WallSymbol(half_wall_box))
        else:
            # uneven wall: derive in column | window | wall
            if self.length == 1:
                fillBlocks(level, self._box, Block['Oak Wood Planks'])
            else:
                box_col, box_wal = self._box.split(dz=2)
                box_win = TransformBox((self._box.origin + (0, 1, 1)), (1, self.height - 2, 1))
                fillBlocks(level, box_col, Block['Oak Wood Planks'])
                fillBlocks(level, box_win, Block['White Stained Glass Pane'])
                self.children.append(_WallSymbol(box_wal))
