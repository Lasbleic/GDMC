# coding=utf-8
"""
Function used to compute accessibility
"""

from __future__ import division

from itertools import product

import numpy as np

from building_seeding.building_encyclopedia import BUILDING_ENCYCLOPEDIA
from building_seeding.interest.math_function import balance


def local_accessibility(x, z, building_type, scenario, road_network):
    lambda_min, lambda_0, lambda_max = BUILDING_ENCYCLOPEDIA[scenario]["Accessibility"][building_type.name]
    distance = road_network.distance_map[x, z]
    return balance(distance, lambda_min, lambda_0, lambda_max)


def accessibility(building_type, scenario, road_network, size):
    accessibility_map = np.zeros(size)

    for x, z, in product(range(size[0]), range(size[1])):
        accessibility_map[x, z] = local_accessibility(x, z, building_type, scenario, road_network)

    return accessibility_map
