# coding=utf-8
"""
Function used to compute interests
"""

from __future__ import division

import sys
from time import time
from typing import Dict

import numpy as np

from building_seeding import BuildingType, Parcel
from building_seeding.accessibility import accessibility, local_accessibility
from building_seeding.building_encyclopedia import BUILDING_ENCYCLOPEDIA
from building_seeding.extendability import extendability
from building_seeding.math_function import close_distance, obstacle, balance, attraction_repulsion
from building_seeding.sociability import sociability, local_sociability
from map import Maps
from map.road_network import *
from parameters import AVERAGE_PARCEL_SIZE
from utils import Point2D

sys.path.insert(1, '../../visu')


class InterestSeeder:
    """
    Stores an InterestMap for each BuildingType and contains methods relative to seeding building types
    """
    def __init__(self, maps, parcel_list, scenario):
        # type: (Maps, List[Parcel], str) -> None
        self.__terrain_maps = maps
        self.__interest_maps = dict()  # type: Dict[BuildingType, InterestMap]
        self.__parcels = parcel_list
        self.__scenario = scenario

    def __getitem__(self, item):
        if isinstance(item, BuildingType):
            if item not in self.__interest_maps:
                self.__interest_maps[item] = InterestMap(item, self.__scenario, self.__terrain_maps)
            return self.__interest_maps[item]
        elif type(item) == object:
            raise TypeError("Expected BuildingType, found {} of class {}", item, item.__class__)
        raise TypeError("Expected BuildingType, found {} of type {}", item, type(item))

    def get_seed(self, building_type):
        typed_interest_map = self[building_type]
        typed_interest_map.update(self.__parcels)
        return typed_interest_map.get_seed()

    def reuse_existing_parcel(self, new_type):
        for parcel in self.__parcels:
            cur_type = parcel.building_type
            if cur_type.name != 'ghost' and cur_type.name != new_type.name:
                # For every parcel of a different type than the one to be seeded, compute interest in changing type
                seed = parcel.center
                other_parcels = filter(lambda p: p != parcel, self.__parcels)

                if not other_parcels:
                    continue

                # Using sociability computed from the other placed parcels, compute local interest for both
                # building types: the parcel's type and the seeded type
                cur_interest = max(0., self[cur_type].get_interest(seed, other_parcels))
                new_interest = max(0., self[new_type].get_interest(seed, other_parcels))

                if bernouilli(new_interest - cur_interest):
                    # todo: replace with max search ?
                    self.__change_parcel_type(parcel, new_type)
                    return

    def __change_parcel_type(self, parcel, new_type):
        # type: (Parcel, BuildingType) -> None
        """
        Changes the type of a parcel and updates all the interest maps (sociability) accordingly
        """
        old_type = BuildingType(parcel.building_type)  # stores replaced type
        parcel.building_type.copy(new_type)  # effectively changes parcel type
        for typed_interest_map in self.__interest_maps.values():
            # updates pre computed sociability when necessary
            typed_interest_map.notify_type_change(self.__parcels, parcel, old_type)

        # Set the building type to be seeded
        new_type.copy(old_type)


class InterestMap:
    """
    Stores precomputed interest matrices for a given building type and contains methods to quickly update these matrices
    """

    def __init__(self, building_type, scenario, terrain_maps):
        # type: (BuildingType, str, Maps) -> None

        # Parameters
        self.__type = building_type  # type: BuildingType
        self.__road_net = terrain_maps.road_network  # type: RoadNetwork
        self.__known_seeds = 0  # type: int
        self.__scenario = scenario
        self.__size = terrain_maps.width, terrain_maps.length

        # Weights
        scenario_dict = BUILDING_ENCYCLOPEDIA[scenario]
        self.__lambdas = {criteria: scenario_dict[criteria][building_type.name]
                          for criteria in scenario_dict if building_type.name in scenario_dict[criteria]}
        self.__acc_w = self.__lambdas["Weighting_factors"][0]
        self.__soc_w = self.__lambdas["Weighting_factors"][1]
        self.__fix_w = sum(self.__lambdas["Weighting_factors"][2:])

        # Interest functions
        self.__access = None
        self.__social = None
        self.__fixed_interest = self.__compute_fixed_interest(terrain_maps)
        self.__interest_value = None

    def update(self, __parcels):
        """
        Updates the interest matrix with the newest road network and parcels added since last update
        """

        n, m = self.__known_seeds, len(__parcels) - self.__known_seeds
        if m > 0:
            self.__access = accessibility(self.type, self.scenario, self.__road_net, self.__size)
            old_soc = self.__social
            new_soc = sociability(self.type, self.scenario, __parcels[n:], self.__size)
            if old_soc is None:
                self.__social = new_soc
            else:
                self.__social = (old_soc * n + new_soc * m) / (n + m)
                self.__social[(old_soc == -1) | (old_soc == -1)] = -1
            self.__known_seeds += m

            self.__compute_interest()

    def get_seed(self, max_iteration=None):
        assert self.__interest_value is not None

        length = self.__interest_value.shape[1]
        size = self.__interest_value.size
        cells = list(range(size))
        cells = filter(lambda pos: self.__interest_value[pos // length, pos % length] > 0, cells)

        if not cells:
            return None  # all positions have a negative interest: impossible to seed

        shuffle(cells)  # shuffles in place
        if max_iteration:
            cells = cells[:max_iteration]  # limit search to first max_iter elements

        for random_index in cells:
            x, z = random_index // length, random_index % length  # convert index to coordinates
            interest_score = self.__interest_value[x, z]
            if bernouilli(interest_score):
                return Point2D(x, z)
        return None

    def __compute_fixed_interest(self, maps):
        """
        Computes interest for fixed functions (relative to the terrain).
        Should be called only once -- at the instance init
        """
        _t = time()

        def river_interest(_x, _z):
            if maps.fluid_map.has_river:
                return close_distance(maps.fluid_map.river_distance[_x, _z], self.__lambdas["RiverDistance"])
            return 0

        def ocean_interest(_x, _z):
            if maps.fluid_map.has_ocean:
                return close_distance(maps.fluid_map.ocean_distance[_x, _z], self.__lambdas["OceanDistance"])
            return 0

        def lava_interest(_x, _z):
            if maps.fluid_map.has_lava:
                return obstacle(maps.fluid_map.lava_distance[_x, _z], self.__lambdas["LavaObstacle"])
            return 0

        def altitude_interest(_x, _z):
            alt = maps.height_map.altitude(_x, _z)
            lm, l0, lM = self.__lambdas["Altitude"]
            return balance(alt, lm, l0, lM)

        def steepness_interest(_x, _z):
            steep = maps.height_map.steepness(_x, _z)
            return close_distance(steep, self.__lambdas["Steepness"])

        size = maps.width, maps.length
        _interest_map = np.zeros(size)

        extendability_map = extendability(size, AVERAGE_PARCEL_SIZE)
        altitude_interest_map = np.array([[altitude_interest(x, z) for z in range(size[1])] for x in range(size[0])])
        steep_interest_map = np.array([[steepness_interest(x, z) for z in range(size[1])] for x in range(size[0])])
        ocean_interest_map = np.array([[ocean_interest(x, z) for z in range(size[1])] for x in range(size[0])])
        river_interest_map = np.array([[river_interest(x, z) for z in range(size[1])] for x in range(size[0])])
        lava_interest_map = np.array([[lava_interest(x, z) for z in range(size[1])] for x in range(size[0])])

        for x, z, in product(range(size[0]), range(size[1])):
            interest_functions = np.array([
                altitude_interest_map[x, z],
                river_interest_map[x, z],
                ocean_interest_map[x, z],
                lava_interest_map[x, z],
                steep_interest_map[x, z]
            ])

            if min(interest_functions) == -1 or extendability_map[x][z] == -1:
                interest_score = 0
            else:
                weights = np.array(self.__lambdas["Weighting_factors"][2:])
                weighted_score = interest_functions.dot(weights) / sum(weights)
                interest_score = max(0, weighted_score)

            _interest_map[x][z] = interest_score

        print("[{}] Computed fixed interest functions in {:0.2} s".format(self.__class__, time() - _t))
        return _interest_map

    def __compute_interest(self):
        """
        Must be called when any of the interest matrices are modified to update the main interest matrix
        """
        a, s, f = self.__acc_w, self.__soc_w, self.__fix_w
        mask = (self.__access == -1) | (self.__social == -1) | (self.__fixed_interest == -1)
        self.__interest_value = (self.__access * a + self.__social * s + self.__fixed_interest * f) / (a + s + f)
        self.__interest_value[mask] = -1

    def get_interest(self, seed, parcels=None):
        # type: (Point2D, List[Parcel]) -> float
        """
        Returns interest value at a given seed. If a list of parcels is passed, will recompute local accessibility
        and sociability from this parcel list
        """
        if parcels is None:
            return self.__interest_value[seed.x, seed.z]

        local_acc = local_accessibility(seed.x, seed.z, self.type, self.scenario, self.__road_net)
        local_soc = local_sociability(seed.x, seed.z, self.type, self.scenario, parcels)
        local_fix = self.__fixed_interest[seed.x, seed.z]

        if local_acc == -1 or local_soc == -1 or local_fix == -1:
            return -1

        a, s, f = self.__acc_w, self.__soc_w, self.__fix_w
        return (local_acc * a + local_soc * s + local_fix * f) / (a + s + f)

    def notify_type_change(self, parcels, parcel, old_type):
        """
        When an existing parcel changes type, recomputing in sociability (and interest) matrices may be necessary
        """
        if parcel not in parcels[:self.__known_seeds]:
            # parcel with old type has no effect on self.__access -> nothing to do
            return

        # Update sociability matrix
        def soc_interest(value, other_type):
            # type: (float, BuildingType) -> float
            lm, l0, lM = self.__lambdas["Sociability"]["-".join([self.type.name, other_type.name])]
            return attraction_repulsion(value, lm, l0, lM)

        for x, z in product(range(self.__size[0], self.__size[1])):
            distance = euclidean(parcel.center, Point2D(x, z))
            old_score = soc_interest(distance, old_type)
            new_score = soc_interest(distance, parcel.building_type)

            if new_score == -1:
                self.__social[x, z] = -1
            elif old_score == -1:
                # Cannot trace back influence of parcel -> must compute influence of all the other parcels as well
                self.__social[x, z] = local_sociability(x, z, self.type, self.scenario, parcels[:self.__known_seeds])
            else:
                # Add a differential term in the mean value
                self.__social[x, z] += (new_score - old_score) / self.__known_seeds

        # Compute interest with the updated sociability matrix
        self.__compute_interest()

    @property
    def type(self):
        return BuildingType(self.__type)

    @property
    def scenario(self):
        return str(self.__scenario)


# def local_interest(x, z, building_type, scenario, road_network, settlement_seeds):
#     """DEPRECATED"""
#     weighting_factors = BUILDING_ENCYCLOPEDIA[scenario]["Weighting_factors"][building_type.name]
#
#     local_access = local_accessibility(x, z, building_type, scenario, road_network)
#     local_social = local_sociability(x, z, building_type, scenario, settlement_seeds)
#
#     if local_access == -1 or local_social == -1:
#         interest_score = 0
#     else:
#         interest_score = max(0, weighting_factors[0] * local_access + weighting_factors[1] *
#                              local_social)
#     return interest_score


# def interest(building_type, scenario, maps, settlement_seeds, size, parcel_size):
#     # type: (BuildingType, str, Maps, object, tuple, object) -> object
#
#     def river_interest(_x, _z):
#         if maps.fluid_map.has_river:
#             return close_distance(maps.fluid_map.river_distance[_x, _z], lambdas["RiverDistance"])
#         return 0
#
#     def ocean_interest(_x, _z):
#         if maps.fluid_map.has_ocean:
#             return close_distance(maps.fluid_map.ocean_distance[_x, _z], lambdas["OceanDistance"])
#         return 0
#
#     def lava_interest(_x, _z):
#         if maps.fluid_map.has_lava:
#             return obstacle(maps.fluid_map.lava_distance[_x, _z], lambdas["LavaObstacle"])
#         return 0
#
#     def altitude_interest(_x, _z):
#         alt = maps.height_map.altitude(_x, _z)
#         lm, l0, lM = lambdas["Altitude"]
#         return balance(alt, lm, l0, lM)
#
#     def steepness_interest(_x, _z):
#         steep = maps.height_map.steepness(_x, _z)
#         return close_distance(steep, lambdas["Steepness"])
#
#     _interest_map = np.zeros(size)
#
#     print("Compute accessibility map")
#     accessibility_map = accessibility(building_type, scenario, maps.road_network, size)
#     print("Compute sociability map")
#     sociability_map = sociability(building_type, scenario, settlement_seeds, size)
#     extendability_map = extendability(size, parcel_size)
#
#     scenario_dict = BUILDING_ENCYCLOPEDIA[scenario]
#     lambdas = {criteria: scenario_dict[criteria][building_type.name]
#                for criteria in scenario_dict if building_type.name in scenario_dict[criteria]}
#
#     altitude_interest_map = np.array([[altitude_interest(x, z) for z in range(size[1])] for x in range(size[0])])
#     steep_interest_map = np.array([[steepness_interest(x, z) for z in range(size[1])] for x in range(size[0])])
#     ocean_interest_map = np.array([[ocean_interest(x, z) for z in range(size[1])] for x in range(size[0])])
#     river_interest_map = np.array([[river_interest(x, z) for z in range(size[1])] for x in range(size[0])])
#     lava_interest_map = np.array([[lava_interest(x, z) for z in range(size[1])] for x in range(size[0])])
#
#     for x, z, in product(range(size[0]), range(size[1])):
#         interest_functions = np.array([
#             accessibility_map[x][z],
#             sociability_map[x][z],
#             altitude_interest_map[x, z],
#             river_interest_map[x, z],
#             ocean_interest_map[x, z],
#             lava_interest_map[x, z],
#             steep_interest_map[x, z]
#         ])
#
#         if min(interest_functions) == -1 or extendability_map[x][z] == -1:
#             interest_score = 0
#         else:
#             weights = np.array(lambdas["Weighting_factors"])
#             weighted_score = interest_functions.dot(weights) / sum(weights)
#             interest_score = max(0, weighted_score)
#
#         _interest_map[x][z] = interest_score
#
#     return _interest_map, accessibility_map, sociability_map
#
#
# def max_interest(_interest_map):
#     width, length = _interest_map.shape[0], _interest_map.shape[1]
#     argmax = np.argmax(_interest_map)
#     return Point2D(argmax // width, argmax % length)
#
#
# def random_interest(_interest_map, max_iteration=100):
#     raise DeprecationWarning("Use InterestMap.get_seed() instead")
#     length = _interest_map.shape[1]
#     # opportunity = width
#     size = _interest_map.size
#     cells = list(range(size))
#     cells = filter(lambda pos: _interest_map[pos // length, pos % length] > 0, cells)
#     if not cells:
#         return None
#     while cells and max_iteration:
#         random_cell = choice(cells)
#         x, z = random_cell // length, random_cell % length
#         interest_score = _interest_map[x, z]
#         if np.random.binomial(1, interest_score):
#             return Point2D(x, z)
#         cells.remove(random_cell)
#         max_iteration -= 1
#     return None
#     # return max_interest(_interest_map)
#
#
# def fast_random_interest(building_type, scenario, road_network, settlement_seeds, sizes):
#     """DEPRECATED"""
#     width = sizes[1]
#     size = sizes[0] * sizes[1]
#     cells = list(range(size))
#     max_local_interest = 0
#     argmax_coord = (0, 0)
#     while cells:
#         random_cell = choice(cells)
#         x, z = random_cell // width, random_cell % width
#         local_interest_score = local_interest(x, z, building_type, scenario, road_network, settlement_seeds)
#         if np.random.binomial(1, local_interest_score):
#             return x, z
#         if local_interest_score > max_local_interest:
#             max_local_interest = local_interest
#             argmax_coord = (x, z)
#         cells.remove(random_cell)
#     return
