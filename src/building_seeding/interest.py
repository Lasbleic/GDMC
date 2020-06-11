# coding=utf-8
"""
Function used to compute interests
"""

from __future__ import division

from itertools import product

from accessibility import accessibility, local_accessibility
from building_encyclopedia import BUILDING_ENCYCLOPEDIA
from building_pool import house_type, windmill_type
from map.road_network import *
from sociability import sociability, local_sociability
from extendability import extendability
import numpy as np
import sys
sys.path.insert(1, '../../visu')
from pre_processing import Map, MapStock


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


def interest(building_type, scenario, road_network, settlement_seeds, size, parcel_size):
    weighting_factors = BUILDING_ENCYCLOPEDIA[scenario]["Weighting_factors"][building_type.name]
    _interest_map = np.zeros(size)

    print("Compute accessibility map")
    accessibility_map = accessibility(building_type, scenario, road_network, size)
    print("Compute sociability map")
    sociability_map = sociability(building_type, scenario, settlement_seeds, size)
    extendability_map = extendability(size, parcel_size)

    for x, z, in product(range(size[0]), range(size[1])):

        if accessibility_map[x][z] == -1 or sociability_map[x][z] == -1 or extendability_map[x][z] == -1:
            interest_score = 0
        else:
            interest_score = max(0, weighting_factors[0] * accessibility_map[x][z] + weighting_factors[1] *
                                 sociability_map[x][z])

        _interest_map[x][z] = interest_score

    return _interest_map, accessibility_map, sociability_map


def max_interest(_interest_map):
    width, length = _interest_map.shape[0], _interest_map.shape[1]
    argmax = np.argmax(_interest_map)
    return Point2D(argmax // width, argmax % length)


def random_interest(_interest_map, max_iteration=10):
    width = _interest_map.shape[1]
    # opportunity = width
    size = _interest_map.size
    cells = list(range(size))
    while cells and max_iteration:
        random_cell = choice(cells)
        x, z = random_cell // width, random_cell % width
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


if __name__ == '__main__':
    # note Charlie: commented this because the import of Parcel causes a circular import
    #
    # # Interest test
    print("Initialize test")
    #
    # N = 100
    #
    # p1, p2, p3 = Point2D(0, 28), Point2D(27, 17), Point2D(99, 23)
    # road_net = RoadNetwork(N, N)
    # road_net.find_road(p1, p2)
    # road_net.find_road(p2, p3)
    # lvl_net = np.copy(road_net.network)
    #
    # set_seeds = []
    #
    # house_1 = Parcel((5, 31), house_type)
    # lvl_net[5, 31] = 2
    # set_seeds.append(house_1)
    #
    # house_2 = Parcel((16, 6), house_type)
    # lvl_net[16, 6] = 2
    # set_seeds.append(house_2)
    #
    # mill_1 = Parcel((37, 18), windmill_type)
    # lvl_net[37, 18] = 3
    # set_seeds.append(mill_1)
    #
    # lvl_cmap = colors.ListedColormap(["forestgreen", "beige", "darkorange", "yellow"])
    # lvl_map = Map("level", N, lvl_net, lvl_cmap, (0, 3), ["Grass", "Road", "House", "Windmill"])
    #
    # print("Compute interest map")
    # interest_net = interest(house_type, "Flat_scenario", road_net, set_seeds, (N, N))
    # print("Interest map : Done")
    # interest_cmap = "jet"
    # interest_map = Map("interest_map", N, interest_net, interest_cmap, (0, 1))
    #
    # the_stock = MapStock("interest_test", N, clean_dir=True)
    # the_stock.add_map(lvl_map)
    # the_stock.add_map(interest_map)

    # Show selected position

    # max_lvl_net = np.copy(lvl_net)
    # max_coord = max_interest(interest_net)
    # print(max_coord)
    # max_lvl_net[max_coord[0], max_coord[1]] = 4
    # max_lvl_cmap = matplotlib.colors.ListedColormap(["forestgreen", "beige", "darkorange", "yellow",  "red"])
    # max_lvl_map = Map("choice (max)", N, max_lvl_net, max_lvl_cmap, (0, 4),
    #                   ["Grass", "Road", "House", "Windmill", "max choice"])
    # the_stock.add_map(max_lvl_map)

    # for i in range(3):
    #     rand_lvl_net = np.copy(lvl_net)
    #     rand_coord = random_interest(interest_net)
    #     rand_lvl_net[rand_coord[0], rand_coord[1]] = 4
    #     rand_lvl_cmap = matplotlib.colors.ListedColormap(["forestgreen", "beige", "darkorange", "yellow", "red"])
    #     rand_lvl_map = Map("choice (random_{})".format(i), N, rand_lvl_net, rand_lvl_cmap, (0, 4),
    #                       ["Grass", "Road", "House", "Windmill", "random choice"])
    #     the_stock.add_map(rand_lvl_map)

    # Update test

    # house_3 = (house_type, (13, 12))
    # lvl_net[13, 12] = 2
    # set_seeds.append(house_3)
    #
    # updated_lvl_map = Map("updated_level", N, lvl_net, lvl_cmap, (0, 3), ["Grass", "Road", "House", "Windmill"])
    #
    # updated_interest_net = interest(house_type, "Flat_scenario", road_net, set_seeds, (N, N))
    # updated_interest_map = Map("updated_interest_map", N, updated_interest_net, interest_cmap, (0, 1))
    #
    # the_stock.add_map(updated_lvl_map)
    # the_stock.add_map(updated_interest_map)

    # Execution time test of decision function

    # import time
    #
    # print("Time test")
    #
    # start_time = time.time()
    # for i in range(1000):
    #     random_interest(interest_net, 10)
    # print("--- %s seconds ---" % (time.time() - start_time))
    #
    # start_time = time.time()
    # for i in range(1000):
    #     interest_net = fast_random_interest(house_type, "Flat_scenario", road_net, set_seeds, (N, N))
    # print("--- %s seconds ---" % (time.time() - start_time))

    # WTF il nous faut un getter !

    # p1, p2 = Point2D(0, 25), Point2D(29, 16)
    # road_net = RoadNetwork(30, 30)
    # road_net.find_road(p1, p2)
    # print(road_net.network[0, 25])
    # print(road_net.network[25, 0])
