from building_pool import BuildingPool, crop_type


class FlatSettlement:
    """
    Intermediate project: generate a realist village on a flat terrain
    """

    def __init__(self, box):
        self.limits = box
        surface = box.width * box.length
        self.building_pool = BuildingPool(surface)

    def generate(self, level):
        # todo: replace this
        crop_town = crop_type.new_instance(self.limits)
        crop_town.generate(level)

