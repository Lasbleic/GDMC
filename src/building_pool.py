from __future__ import division, print_function
from numpy.random import geometric, random, choice


class BuildingType:
    def __init__(self, name, generator=None):
        self.name = name
        self.generator = generator

    def new_instance(self, x, z):
        return self.generator(x, z)

    def __hash__(self):
        return hash(self.name)


# All building types available for generation, with a weight. The normalized weight = frequency of each type
all_types = dict()
all_types[BuildingType('house')] = 10
all_types[BuildingType('crop')] = 6
all_types[BuildingType('windmill')] = 2


class BuildingPool:
    def __init__(self, exploitable_surface, type_weight=None):
        if type_weight is None:
            type_weight = all_types
        self.settlement_size = 0  # type: int
        self.settlement_limit = 0  # type: int
        self.building_types = type_weight  # type: dict
        self.__init_settlement_size(exploitable_surface)

    def __init_settlement_size(self, exploitable_surface):
        average_parcel_surface = 100  # todo: calibrate this parameter
        min_dens, max_dens = 0.25, 0.75  # portion of built surface of the terrain
        density = min_dens + random() * (max_dens - min_dens)
        self.settlement_limit = int((density * exploitable_surface) / average_parcel_surface)
        # self.settlement_limit = geometric(1 / average_parcel_count)  # yielded values too high

    def __iter__(self):
        return self

    def next(self):
        """
        Pick randomly a building type in the pool
        Returns a BuildingType to build next
        -------

        """
        if self.settlement_size < self.settlement_limit:
            self.settlement_size += 1
            norm = sum([v for v in self.building_types.values()])
            prob = [v / norm for v in self.building_types.values()]
            btype = choice(self.building_types.keys(), p=prob)
            return btype
        raise StopIteration


if __name__ == '__main__':
    size = 64
    pool = BuildingPool(size**2)
    print('settlement size: {}'.format(pool.settlement_limit))
    for build_type in pool:
        print(build_type.name)
