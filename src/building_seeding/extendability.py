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
