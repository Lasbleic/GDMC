from generation.generators import *
from generation.gen_utils import TransformBox
from pymclevel import alphaMaterials
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
        w0, h0, l0 = self.box.width, self.box.height, self.box.length
        # generate main building
        w1, l1 = randint(5, w0-2), randint(5, l0-2)
        self._layout_width = w1
        self._layout_length = l1
        main_box = TransformBox(self.box.origin, (w1, h0, l1))
        self.children.append(_RoomSymbol(main_box))

    def _generate_annex(self):
        height = self.children[0].box.height - 2  # note: -2 makes annexes on average 2 blocks lower than the main build
        w0, w1, l0, l1 = self.box.width, self.children[0].box.width, self.box.length, self.children[0].box.length
        # extension in x
        try:
            max_width = w0 - w1  # available width
            width = randint(-max_width, max_width)  # annex width, west or east of main room
            length = randint(5, l1 - 2)  # annex length, limited by main room's dimension
            delta = randint(0, l1 - length)  # position relative to main room

            if width > 0:
                annex_box = TransformBox(self.box.origin + (w1, 0, delta), (width, height, length))
            elif width < 0:
                width = -width
                annex_box = TransformBox(self.box.origin + (0, 0, delta), (width, height, length))
                self.children[0].box.transpose(dx=width)

            self.children.append(_RoomSymbol(annex_box))  # possible Error caught
            self._layout_width += width - 1
        except ValueError:
            print('not enough space to build an annex in x')
        except NameError:
            print('no extension in x')

        # extension in z
        try:
            max_length = l0 - l1  # available width
            length = randint(-max_length, max_length)  # annex length, north or south of main room
            width = randint(5, w1 - 2)  # annex length, limited by main room's dimension
            delta = randint(0, w1 - width)  # position relative to main room

            if length > 0:
                annex_box = TransformBox(self.box.origin + (delta, 0, l1), (width, height, length))
            elif length < 0:
                length = -length
                annex_box = TransformBox(self.box.origin + (delta, 0, 0), (width, height, length))
                map(lambda room: room.box.transpose(dz=length), self.children)

            self.children.append(_RoomSymbol(annex_box))  # possible Error caught
            self._layout_length += length - 1
        except ValueError:
            print('not enough space to build an annex in z')
        except NameError:
            print('no extension in z')

    def _center_building(self):
        dx = (self.box.width - self._layout_width) / 2
        dz = (self.box.length - self._layout_length) / 2
        for room in self.children:
            room.box.transpose(dx=dx, dz=dz)


class _RoomSymbol(Generator):

    def generate(self, level, height_map=None):
        room_box = self._get_box()
        fillBlocks(level, room_box, alphaMaterials['Cobblestone'])

        prob = self.box.height / 4 - 1  # probability to build an upper floor
        upper_box = self._get_upper_box()

        if bernouilli(prob):
            self.children.append(_RoomSymbol(upper_box))
        else:
            self.children.append(_RoofSymbol(upper_box, roof_type='gable'))
        # build upper Symbol
        Generator.generate(self, level)

    def _get_box(self):
        return TransformBox(self.box.origin, (self.box.width, 4, self.box.length))

    def _get_upper_box(self):
        box = self.box
        new_origin = box.origin + (0, 4, 0)
        new_height = max(1, box.height - 4)
        new_size = (box.width, new_height, box.length)
        return TransformBox(new_origin, new_size)


class _RoofSymbol(Generator):

    def __init__(self, box, direction=None, roof_type='flat'):
        Generator.__init__(self, box)
        self._direction = direction
        self._roof_type = roof_type

        if self._direction is None:
            # sets roof direction randomly, lower roofs are preferred
            w, l = self.box.width, self.box.length
            if w < 5:
                self._direction = 'East'
            elif l < 5:
                self._direction = 'South'
            else:
                prob = (1. * w**2) / (w**2 + l**2)
                self._direction = 'South' if (bernouilli(prob)) else 'East'

    def generate(self, level, height_map=None):
        box = self._get_box()
        if self._roof_type == 'flat':
            fillBlocks(level, box, alphaMaterials['Bricks'])
        elif self._roof_type == 'gable':
            stair_format = '{} Stairs (Bottom, {})'
            if self._direction in ['West', 'East']:
                for index in xrange(box.length / 2):
                    north_box = TransformBox((box.minx, box.miny+index, box.maxz-index-1), (box.width, 1, 1))
                    fillBlocks(level, north_box, alphaMaterials[stair_format.format('Oak Wood', 'North')])
                    south_box = TransformBox((box.minx, box.miny+index, box.minz+index), (box.width, 1, 1))
                    fillBlocks(level, south_box, alphaMaterials[stair_format.format('Oak Wood', 'South')])
                # build roof ridge
                if box.length % 2 == 1:
                    index = box.length / 2
                    ridge_box = TransformBox((box.minx, box.miny+index, box.minz+index), (box.width, 1, 1))
                    fillBlocks(level, ridge_box, alphaMaterials['Oak Wood Slab (Bottom)'])
            elif self._direction in ['North', 'South']:
                for index in xrange(box.width / 2):
                    east_box = TransformBox((box.minx+index, box.miny+index, box.minz), (1, 1, box.length))
                    fillBlocks(level, east_box, alphaMaterials[stair_format.format('Oak Wood', 'East')])
                    west_box = TransformBox((box.maxx-index-1, box.miny+index, box.minz), (1, 1, box.length))
                    fillBlocks(level, west_box, alphaMaterials[stair_format.format('Oak Wood', 'West')])
                # build roof ridge
                if box.width % 2 == 1:
                    index = box.width / 2
                    ridge_box = TransformBox((box.minx+index, box.miny+index, box.minz), (1, 1, box.length))
                    fillBlocks(level, ridge_box, alphaMaterials['Oak Wood Slab (Bottom)'])
            else:
                raise ValueError('Expected direction str, found {}'.format(self._direction))

    def _get_box(self):
        box = self.box
        new_size = (box.width, 1, box.length)
        return TransformBox(box.origin, new_size)
