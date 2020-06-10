# coding=utf-8
"""
Function used to compute sociability
"""

from __future__ import division

from matplotlib import colors
import numpy as np
from itertools import product
from math_function import attraction_repulsion
from math import sqrt
from building_seeding.building_pool import house_type, windmill_type
from pre_processing import Map, MapStock
from building_encyclopedia import BUILDING_ENCYCLOPEDIA
from parcel import Parcel
from utils import Point2D

def local_sociability(x, z, building_type, scenario, settlement_seeds):

    _sociability = 0
    social_score = -1

    for settlement_seed in settlement_seeds:

        neighbor_type, neighbor_position = settlement_seed.building_type, settlement_seed.center
        distance_to_building = sqrt((neighbor_position.x - x) ** 2 + (neighbor_position.z - z) ** 2)
        lambda_min, lambda_0, lambda_max = BUILDING_ENCYCLOPEDIA[scenario]["Sociability"][
            building_type.name + "-" + neighbor_type.name]

        social_score = attraction_repulsion(distance_to_building, lambda_min, lambda_0, lambda_max)

        if social_score == -1:
            _sociability = -1
            break

        _sociability += social_score

    if social_score != -1:
        _sociability /= len(settlement_seeds)

    return _sociability


def sociability(building_type, scenario, settlement_seeds, size):

    sociability_map = np.zeros(size)

    for x, z, in product(range(size[0]), range(size[1])):

        sociability_map[x, z] = local_sociability(x, z, building_type, scenario, settlement_seeds)

    return sociability_map


if __name__ == '__main__':

    # Sociability test

    N = 50

    building_net = np.zeros((N, N))
    set_seeds = []

    house_1 = Parcel(Point2D(15, 31), house_type)
    building_net[15, 31] = 1
    set_seeds.append(house_1)

    house_2 = Parcel(Point2D(26, 6), house_type)
    building_net[26, 6] = 1
    set_seeds.append(house_2)

    mill_1 = Parcel(Point2D(37, 18), windmill_type)
    building_net[37, 18] = 2
    set_seeds.append(mill_1)

    building_cmap = colors.ListedColormap(['forestgreen', 'darkorange', "yellow"])
    building_map = Map("building_map", N, building_net, building_cmap, (0, 2), ['Grass', 'House', "Windmill"])

    social_net = sociability(house_type, "Flat_scenario", set_seeds, (N, N))
    social_cmap = "jet"
    social_map = Map("accessibility_map", N, social_net, social_cmap, (-1, 1))

    the_stock = MapStock("interest_test", N, clean_dir=True)
    the_stock.add_map(building_map)
    the_stock.add_map(social_map)
