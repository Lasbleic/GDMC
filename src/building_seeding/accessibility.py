# coding=utf-8
"""
Function used to compute accessibility
"""

from __future__ import division

from itertools import product
from math_function import balance
import numpy as np
from map.road_network import RoadNetwork
from building_encyclopedia import BUILDING_ENCYCLOPEDIA
from utils import Point2D

import sys


def local_accessibility(x, z, building_type, scenario, road_network):
    lambda_min, lambda_0, lambda_max = BUILDING_ENCYCLOPEDIA[scenario]["Accessibility"][building_type.name]
    distance = road_network.distance_map[x, z]
    return balance(distance, lambda_min, lambda_0, lambda_max)


def accessibility(building_type, scenario, road_network, size):
    accessibility_map = np.zeros(size)

    for x, z, in product(range(size[0]), range(size[1])):
        # point_to_connect = Point2D(x, z)
        # path, distance = road_network.dijkstra(point_to_connect, lambda point: road_network.is_road(point))
        accessibility_map[x, z] = local_accessibility(x, z, building_type, scenario, road_network)

    return accessibility_map


if __name__ == '__main__':
    sys.path.insert(1, '../../visu')

    # Accessibility test

    N = 10
    import time

    p1, p2, p3 = Point2D(0, 8), Point2D(6, 1), Point2D(99, 23)
    road_net = RoadNetwork(N, N)
    road_net.find_road(p1, p2)

    print(road_net.network)
    print(road_net.distance_map)

    # road_net.find_road(p2, p3)
    #
    # road_cmap = colors.ListedColormap(['forestgreen', 'beige'])
    # road_map = Map("road_network", N, road_net.network, road_cmap, (0, 1), ['Grass', 'Road'])
    # start_time = time.time()
    # print("Compute accessibility...")
    # access_net = accessibility(BuildingType().house, "Flat_scenario", road_net, (N, N))
    # print("--- %s seconds ---" % (time.time() - start_time))
    # access_cmap = "jet"
    # access_map = Map("accessibility_map", N, access_net, access_cmap, (-1, 1))
    #
    # the_stock = MapStock("interest_test", N, clean_dir=True)
    # the_stock.add_map(road_map)
    # the_stock.add_map(access_map)
