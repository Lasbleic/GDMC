from .pymclevel import *
from .geometry_utils import Point, Position, building_positions, euclidean, manhattan, Direction, \
    cardinal_directions, all_directions, BuildArea, TransformBox, Bounds, absolute_distance
from .custom_2darray import PointArray
from .block_utils import BlockAPI, setBlock, water_blocks, lava_blocks, fillBlocks, clear_tree_at, \
    place_torch, ground_blocks, getBlockRelativeAt, dump
from .entities import *
from .misc_objects_functions import *

import numpy as np
X_ARRAY: np.ndarray = np.array([[x for z in range(BuildArea().length)] for x in range(BuildArea().width)])
Z_ARRAY: np.ndarray = np.array([[z for z in range(BuildArea().length)] for x in range(BuildArea().width)])
alpha = BlockAPI.blocks
