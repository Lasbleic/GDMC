from building_pool import BuildingPool


class FlatSettlement:
    """
    Intermediate project: generate a realist village on a flat terrain
    """

    def __init__(self, box):
        self.limits = box
        surface = box.width * box.length
        self.building_pool = BuildingPool(surface)

    def generate(self, level):
        pass
