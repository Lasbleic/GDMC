from __future__ import division, print_function

import logging

from numpy.random import random, choice
from typing import Dict

from building_seeding.building_encyclopedia import BUILDING_ENCYCLOPEDIA
from generation import CropGenerator, ProcHouseGenerator, WindmillGenerator
from generation.generators import WoodTower, StoneTower
from generation.plaza import PlazaGenerator
from parameters import AVERAGE_PARCEL_SIZE


class BuildingType:
    """
    Just a type of building, defined by a name and a generator
    """

    def __init__(self, name=None, generator=None):
        self.name = name
        self.generator = generator
        if name is not None and isinstance(name, BuildingType):
            self.copy(name)

    def new_instance(self, box):
        if self.generator:
            return self.generator(box)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, BuildingType):
            return self.name == other.name
        return False

    def __str__(self):
        return "Building type {}".format(self.name if self.name is not None else "undefined")

    @property
    def house(self):
        self.name = 'house'
        self.generator = ProcHouseGenerator
        return self

    @property
    def crop(self):
        self.name = 'crop'
        self.generator = CropGenerator
        return self

    @property
    def windmill(self):
        self.name = 'windmill'
        self.generator = WindmillGenerator
        return self

    @property
    def ghost(self):
        self.name = 'ghost'
        self.generator = PlazaGenerator
        return self

    @property
    def wood_tower(self):
        self.name = 'wood_tower'
        self.generator = WoodTower
        return self

    @property
    def stone_tower(self):
        self.name = 'stone_tower'
        self.generator = StoneTower
        return self

    @staticmethod
    def from_name(name):
        if name == 'crop':
            return BuildingType().crop
        if name == 'house':
            return BuildingType().house
        if name == 'ghost':
            return BuildingType().ghost
        if name == 'windmill':
            return BuildingType().windmill
        if name == 'wood_tower':
            return BuildingType().wood_tower
        if name == 'stone_tower':
            return BuildingType().stone_tower

    def copy(self, other):
        assert isinstance(other, BuildingType)
        self.name = other.name
        self.generator = other.generator
        return self


class BuildingPool:
    def __init__(self, exploitable_surface):
        self._building_count = 0  # type: int
        self._settlement_limit = 0  # type: int
        self.__current_type = BuildingType().house
        self.__init_building_count(exploitable_surface)

    def __init_building_count(self, exploitable_surface):
        average_parcel_surface = AVERAGE_PARCEL_SIZE**2  # todo: calibrate this parameter
        min_dens, max_dens = 0.3, 0.6  # portion of built surface of the terrain
        density = min_dens + random() * (max_dens - min_dens)
        self._settlement_limit = int((exploitable_surface / average_parcel_surface) ** 0.7)
        self._settlement_limit = max(self._settlement_limit, 1)
        # self._settlement_limit = min(self._settlement_limit, 50)
        # self.settlement_limit = geometric(1 / average_parcel_count)  # yielded values too high
        logging.info('New BuildingPool will generate {} parcels'.format(self._settlement_limit))

    def __iter__(self):
        return self

    def __next__(self):
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
        if 0 < self._building_count < self._settlement_limit:
            transition_matrix = BUILDING_ENCYCLOPEDIA["Flat_scenario"]["markov"]
            transition_states = transition_matrix[self.__current_type.name]  # type: Dict[str, int]
            types = list(transition_states.keys())
            probs = transition_states.values()
            probs = [p / sum(probs) for p in probs]
            next_type = choice(types, p=probs)
            self.__current_type = BuildingType.from_name(next_type)
        elif self._building_count >= self._settlement_limit:
            raise StopIteration

        self._building_count += 1
        return BuildingType(self.__current_type)

    @property
    def size(self):
        return self._settlement_limit

    @property
    def count(self):
        return self._building_count
