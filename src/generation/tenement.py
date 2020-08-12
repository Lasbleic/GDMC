from generation.generators import Generator


class TenementGenerator(Generator):
    def __init__(self, box, entry_point=None):
        Generator.__init__(self, box, entry_point)

    def generate(self, level, height_map=None, palette=None):
        Generator.generate(self, level, height_map, palette)
        # todo: split & build lots
