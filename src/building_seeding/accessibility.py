# coding=utf-8
"""
Function used to compute accessibility
"""

from __future__ import division

import matplotlib
import numpy as np
from itertools import product
from math_function import balance
import sys
sys.path.insert(1, '../')
from road_network import Point2D, RoadNetwork
from building_pool import house_type, crop_type, windmill_type
sys.path.insert(1, '../../visu')
from pre_processing import Map, MapStock
from building_encyclopedia import BUILDING_ENCYCLOPEDIA


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

    # Accessibility test

    p1, p2, p3 = Point2D(0, 28), Point2D(27, 17), Point2D(49, 23)
    road_net = RoadNetwork(50, 50)
    road_net.find_road(p1, p2)
    road_net.find_road(p2, p3)
    road_cmap = matplotlib.colors.ListedColormap(['forestgreen', 'beige'])
    road_map = Map("road_network", 50, road_net.network, road_cmap, (0, 1), ['Grass', 'Road'])

    access_net = accessibility(house_type, "Flat_scenario", road_net, (50, 50))
    access_cmap = "jet"
    access_map = Map("accessibility_map", 50, access_net, access_cmap, (-1, 1))

    the_stock = MapStock("interest_test", 50, clean_dir=True)
    the_stock.add_map(road_map)
    the_stock.add_map(access_map)
