# coding=utf-8
"""
Function used to compute interests
"""

from __future__ import division

from itertools import product

from accessibility import accessibility, local_accessibility
from building_encyclopedia import BUILDING_ENCYCLOPEDIA
from building_seeding import BuildingType
from building_seeding.math_function import close_distance, obstacle, balance
from map import Maps
from map.road_network import *
from sociability import sociability, local_sociability
from extendability import extendability
import numpy as np
import sys

from utils import Point2D

sys.path.insert(1, '../../visu')


def local_interest(x, z, building_type, scenario, road_network, settlement_seeds):
    weighting_factors = BUILDING_ENCYCLOPEDIA[scenario]["Weighting_factors"][building_type.name]

    local_access = local_accessibility(x, z, building_type, scenario, road_network)
    local_social = local_sociability(x, z, building_type, scenario, settlement_seeds)

    if local_access == -1 or local_social == -1:
        interest_score = 0
    else:
        interest_score = max(0, weighting_factors[0] * local_access + weighting_factors[1] *
                             local_social)
    return interest_score


def interest(building_type, scenario, maps, settlement_seeds, size, parcel_size):
    # type: (BuildingType, str, Maps, object, object, object) -> object

    def river_interest():
        if maps.fluid_map.has_river:
            return close_distance(maps.fluid_map.river_distance[x, z], lambdas["RiverDistance"])
        return 0

    def ocean_interest():
        if maps.fluid_map.has_ocean:
            return close_distance(maps.fluid_map.ocean_distance[x, z], lambdas["OceanDistance"])
        return 0

    def lava_interest():
        if maps.fluid_map.has_lava:
            return obstacle(maps.fluid_map.lava_distance[x, z], lambdas["LavaObstacle"])
        return 0

    def altitude_interest():
        alt = maps.height_map[x, z]
        lm, l0, lM = lambdas["Altitude"]
        return balance(alt, lm, l0, lM)

    _interest_map = np.zeros(size)

    print("Compute accessibility map")
    accessibility_map = accessibility(building_type, scenario, maps.road_network, size)
    print("Compute sociability map")
    sociability_map = sociability(building_type, scenario, settlement_seeds, size)
    extendability_map = extendability(size, parcel_size)

    scenario_dict = BUILDING_ENCYCLOPEDIA[scenario]
    lambdas = {criteria: scenario_dict[criteria][building_type.name]
               for criteria in scenario_dict if building_type.name in scenario_dict[criteria]}

    for x, z, in product(range(size[0]), range(size[1])):
        interest_functions = np.array([
            accessibility_map[x][z],
            sociability_map[x][z],
            altitude_interest(),
            river_interest(),
            ocean_interest(),
            lava_interest()
        ])

        if min(interest_functions) == -1 or extendability_map[x][z] == -1:
            interest_score = 0
        else:
            weights = np.array(lambdas["Weighting_factors"])
            weighted_score = interest_functions.dot(weights) / sum(weights)
            interest_score = max(0, weighted_score)

        _interest_map[x][z] = interest_score

    return _interest_map, accessibility_map, sociability_map


def max_interest(_interest_map):
    width, length = _interest_map.shape[0], _interest_map.shape[1]
    argmax = np.argmax(_interest_map)
    return Point2D(argmax // width, argmax % length)


def random_interest(_interest_map, max_iteration=100):
    length = _interest_map.shape[1]
    # opportunity = width
    size = _interest_map.size
    cells = list(range(size))
    cells = filter(lambda pos: _interest_map[pos//length, pos % length] > 0, cells)
    if not cells:
        return None
    while cells and max_iteration:
        random_cell = choice(cells)
        x, z = random_cell // length, random_cell % length
        interest_score = _interest_map[x, z]
        if np.random.binomial(1, interest_score):
            return Point2D(x, z)
        cells.remove(random_cell)
        max_iteration -= 1
    return max_interest(_interest_map)


def fast_random_interest(building_type, scenario, road_network, settlement_seeds, sizes):
    width = sizes[1]
    size = sizes[0] * sizes[1]
    cells = list(range(size))
    max_local_interest = 0
    argmax_coord = (0, 0)
    while cells:
        random_cell = choice(cells)
        x, z = random_cell // width, random_cell % width
        local_interest_score = local_interest(x, z, building_type, scenario, road_network, settlement_seeds)
        if np.random.binomial(1, local_interest_score):
            return x, z
        if local_interest_score > max_local_interest:
            max_local_interest = local_interest
            argmax_coord = (x, z)
        cells.remove(random_cell)
    return argmax_coord
