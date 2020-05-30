# coding=utf-8
"""
Function used to compute accessibility
"""

from __future__ import division

import matplotlib
import numpy as np
from itertools import product
from math_function import balance

from road_network import Point2D, RoadNetwork
from building_seeding import house_type
from building_encyclopedia import BUILDING_ENCYCLOPEDIA

import sys
sys.path.insert(1, '../')


def distance_to_road(x, z, road_network):
    net = road_network.network
    l = road_network.length
    w = road_network.width

    if net[x, z]:
        d = 0

    else:
        d = -1
        for i in range(1, max(l, w)):

            for z_bis in range(-i, i + 1):

                if -1 < x + i < l and -1 < z + z_bis < w and net[x + i, z + z_bis]:
                    d = i
                    break

                if -1 < x - i < l and -1 < z + z_bis < w and net[x - i, z + z_bis]:
                    d = i
                    break

            for x_bis in range(-i, i + 1):

                if -1 < x + x_bis < l and -1 < z + i < w and net[x + x_bis, z + i]:
                    d = i
                    break

                if -1 < x + x_bis < l and -1 < z - i < w and net[x + x_bis, z - i]:
                    d = i
                    break

            if d != -1:
                break

    return d


def local_accessibility(x, z, building_type, scenario, road_network):
    lambda_min, lambda_0, lambda_max = BUILDING_ENCYCLOPEDIA[scenario]["Accessibility"][building_type.name]
    distance = distance_to_road(x, z, road_network)
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
    from pre_processing import Map, MapStock

    # Accessibility test

    N = 130
    import time

    p1, p2, p3 = Point2D(0, 28), Point2D(27, 17), Point2D(129, 23)
    road_net = RoadNetwork(N, N)
    road_net.find_road(p1, p2)
    road_net.find_road(p2, p3)
    road_cmap = matplotlib.colors.ListedColormap(['forestgreen', 'beige'])
    road_map = Map("road_network", N, road_net.network, road_cmap, (0, 1), ['Grass', 'Road'])
    start_time = time.time()
    print("Compute accessibility...")
    access_net = accessibility(house_type, "Flat_scenario", road_net, (N, N))
    print("--- %s seconds ---" % (time.time() - start_time))
    access_cmap = "jet"
    access_map = Map("accessibility_map", N, access_net, access_cmap, (-1, 1))

    the_stock = MapStock("interest_test", N, clean_dir=True)
    the_stock.add_map(road_map)
    the_stock.add_map(access_map)
