# coding=utf-8
"""
Function used to compute accessibility
"""

from __future__ import division


import numpy as np

import sys


def extendability(size, parcel_size):


    extendability_map = np.zeros(size)

    shift = parcel_size // 2
    map_width = size[0]
    map_length = size[1]

    extendability_map[0:shift, 0:map_length] = -1
    extendability_map[map_width-shift:map_width, 0:map_length] = -1
    extendability_map[0:map_width, 0:shift] = -1
    extendability_map[0:map_width, map_length-shift:map_length] = -1

    return extendability_map


if __name__ == '__main__':
    sys.path.insert(1, '../../visu')
    from pre_processing import Map, MapStock
    from matplotlib import colors


    N = 100

    access_net = extendability((N, N), 7)
    extend_map = Map("extendability_map", N, access_net, colors.ListedColormap(['blue', 'red']), (-1, 0), ['Extendable', 'Non extendable'])

    the_stock = MapStock("extend_test", N, clean_dir=True)
    the_stock.add_map(extend_map)
