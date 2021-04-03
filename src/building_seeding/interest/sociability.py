# coding=utf-8
"""
Function used to compute sociability
"""

from __future__ import division

from itertools import product
from typing import List

import numpy as np

from building_seeding import Parcel
from building_seeding.building_encyclopedia import BUILDING_ENCYCLOPEDIA
from building_seeding.interest.math_function import attraction_repulsion
from utils import Point, euclidean


def local_sociability(x, z, building_type, scenario, settlement_seeds: List[Parcel]):
    if not settlement_seeds:
        return 0

    _sociability = 0
    social_score = -1

    for settlement_seed in settlement_seeds:

        neighbor_type, neighbor_position = settlement_seed.building_type, settlement_seed.center
        distance_to_building = euclidean(Point(x, z), neighbor_position)
        lambda_min, lambda_0, lambda_max = BUILDING_ENCYCLOPEDIA[scenario]["Sociability"][
            building_type.name + "-" + neighbor_type.name]

        social_score = attraction_repulsion(distance_to_building, lambda_min, lambda_0, lambda_max)

        if social_score == -1:
            return -1

        _sociability += social_score

    return _sociability / len(settlement_seeds)


def sociability(building_type, scenario, settlement_seeds, size):

    sociability_map = np.zeros(size)

    for x, z, in product(range(size[0]), range(size[1])):

        sociability_map[x, z] = local_sociability(x, z, building_type, scenario, settlement_seeds)

    return sociability_map
