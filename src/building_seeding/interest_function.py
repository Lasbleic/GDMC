"""
Function used to compute interests
"""

from __future__ import division

import matplotlib
import numpy as np
from itertools import product
from math_function import attraction_repulsion, balance
from math import log, sqrt, exp
import sys

sys.path.insert(1, '../')
from road_network import Point2D, RoadNetwork

sys.path.insert(1, '../../visu')
from pre_processing import Map, MapStock

BUILDING_ENCYCLOPEDIA = {
    "Flat_scenario": {
        "Sociability": {
            "House-House": (15, 25, 100),
            "House-Church": (20, 30, 100),
            "House-Mill": (25, 35, 100),
            "Church-Mill": (25, 35, 100)
        },
        "Accessibility": {
            "House": (5, 10, 25),
            "Church": (5, 10, 25),
            "Mill": (10, 15, 35),
        }
    }
}

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


def accessibility(building_type, scenario, road_network):
    lambda_min, lambda_0, lambda_max = BUILDING_ENCYCLOPEDIA[scenario]["Accessibility"][building_type]
    accessibility_map = np.zeros((road_network.length, road_network.width))

    for x, z, in product(range(road_network.length), range(road_network.width)):
        # point_to_connect = Point2D(x, z)
        # path, distance = road_network.dijkstra(point_to_connect, lambda point: road_network.is_road(point))
        distance = distance_to_road(x, z, road_network)
        accessibility_map[x, z] = balance(distance, lambda_min, lambda_0, lambda_max)
    return accessibility_map


if __name__ == '__main__':


    p1, p2, p3 = Point2D(0, 28), Point2D(27, 17), Point2D(49, 23)
    road_net = RoadNetwork(50, 50)
    road_net.find_road(p1, p2)
    road_net.find_road(p2, p3)
    road_cmap = matplotlib.colors.ListedColormap(['forestgreen', 'beige'])
    road_map = Map("road_network", 50, road_net.network, road_cmap)

    access_net = accessibility("House", "Flat_scenario", road_net)
    access_cmap = "jet"
    access_map = Map("accessibility_map", 50, access_net, access_cmap)

    the_stock = MapStock("interest_test", 50, clean_dir=True)
    the_stock.add_map(road_map)
    the_stock.add_map(access_map)


    # p1, p2 = Point2D(0, 25), Point2D(29, 16)
    # road_net = RoadNetwork(30, 30)
    # road_net.find_road(p1, p2)
    # print(road_net.network[0, 25])
    # print(road_net.network[25, 0])