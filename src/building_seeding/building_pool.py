from __future__ import division, print_function
from numpy.random import random, choice
from typing import Dict

from building_encyclopedia import BUILDING_ENCYCLOPEDIA
from generation import CropGenerator, ProcHouseGenerator, WindmillGenerator

import logging


class BuildingType:
    """
    Just a type of building, defined by a name and a generator
    """

    def __init__(self, name, generator=None):
        self.name = name
        self.generator = generator

    def new_instance(self, box):
        return self.generator(box)

    def __hash__(self):
        return hash(self.name)

    @staticmethod
    def from_name(name):
        if name == 'crop':
            return BuildingType(name, CropGenerator)
        if name == 'house':
            return BuildingType(name, ProcHouseGenerator)
        if name == 'ghost':
            return BuildingType(name)
        if name == 'windmill':
            return BuildingType(name, WindmillGenerator)


house_type = BuildingType.from_name('house')
crop_type = BuildingType.from_name('crop')
windmill_type = BuildingType.from_name('windmill')
# dict to associate weights to types. The normalized weight = frequency of each type
type_weights = {house_type: 10, crop_type: 6, windmill_type: 2}


class BuildingPool:
    def __init__(self, exploitable_surface, type_weight=None):
        if type_weight is None:
            type_weight = type_weights
        self._building_count = 0  # type: int
        self._settlement_limit = 0  # type: int
        self.building_types = type_weight  # type: Dict[BuildingType, int]
        self.__current_type = house_type
        self.__init_building_count(exploitable_surface)

    def __init_building_count(self, exploitable_surface):
        average_parcel_surface = 15**2  # todo: calibrate this parameter
        min_dens, max_dens = 0.3, 0.6  # portion of built surface of the terrain
        density = min_dens + random() * (max_dens - min_dens)
        self._settlement_limit = int((density * exploitable_surface) / average_parcel_surface)
        # self.settlement_limit = geometric(1 / average_parcel_count)  # yielded values too high
        logging.info('New BuildingPool will generate {} parcels'.format(self._settlement_limit))

    def __iter__(self):
        return self

    def next(self):
        """
        Pick randomly a building type in the pool
        Returns a BuildingType to build next
        -------

        """
        # first version, distribution based
        # if self.building_count < self.settlement_limit:
        #     self.building_count += 1
        #     norm = sum([v for v in self.building_types.values()])
        #     prob = [v / norm for v in self.building_types.values()]
        #     btype = choice(self.building_types.keys(), p=prob)
        #     return btype

        # second version, markov chain based:
        if self._building_count == 0:
            self.__current_type = house_type
        elif self._building_count < self._settlement_limit:
            transition_matrix = BUILDING_ENCYCLOPEDIA["Flat_scenario"]["markov"]
            transition_states = transition_matrix[self.__current_type.name]  # type: Dict[str, int]
            types = transition_states.keys()
            probs = transition_states.values()
            probs = [p / sum(probs) for p in probs]
            next_type = choice(types, p=probs)
            self.__current_type = BuildingType.from_name(next_type)
        else:
            raise StopIteration

        self._building_count += 1
        return self.__current_type


if __name__ == '__main__':
    size = 64
    pool = BuildingPool(size**2)
    print('settlement size: {}'.format(pool._settlement_limit))
    for build_type in pool:
        print(build_type.name)
