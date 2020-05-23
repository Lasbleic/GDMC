from generation.generators import *


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
        w1, l1 = randint(5, w0), randint(5, l0)
        self._layout_width = w1
        self._layout_length = l1
        main_box = BoundingBox(self.box.origin, (w1, h0, l1))
        self.children.append(_RoomSymbol(main_box))

    def _generate_annex(self):
        pass

    def _center_building(self):
        dx = (self.box.width - self._layout_width) / 2
        dz = (self.box.length - self._layout_length) / 2
        for room in self.children:
            room.box._origin += (dx, 0, dz)


class _RoomSymbol(Generator):

    def generate(self, level, height_map=None):
        room_box = self._get_box()
        fillBlocks(level, room_box, alphaMaterials['Cobblestone'])

        prob = self.box.height / 4 - 1  # probability to build an upper floor
        upper_box = self._get_upper_box()

        if bernouilli(prob):
            self.children.append(_RoomSymbol(upper_box))
        else:
            self.children.append(_RoofSymbol(upper_box))
        # build upper Symbol
        Generator.generate(self, level)

    def _get_box(self):
        return BoundingBox(self.box.origin, (self.box.width, 4, self.box.length))

    def _get_upper_box(self):
        box = self.box
        new_origin = box.origin + (0, 4, 0)
        new_height = max(1, box.height - 4)
        new_size = (box.width, new_height, box.length)
        return BoundingBox(new_origin, new_size)


class _RoofSymbol(Generator):

    def generate(self, level, height_map=None):
        box = self._get_box()
        fillBlocks(level, box, alphaMaterials['Bricks'])

    def _get_box(self):
        box = self.box
        new_size = (box.width, 1, box.length)
        return BoundingBox(box.origin, new_size)
