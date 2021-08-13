# Relevant generic imports throughout the project
from numpy import ndarray, array

import utils.parameters
from utils.block_utils import BlockAPI, setBlock, water_blocks, lava_blocks, fillBlocks, clear_tree_at, \
    connected_component, place_torch, ground_blocks, getBlockRelativeAt
from utils.geometry_utils import Point, Position, building_positions, euclidean, manhattan, Direction, \
    cardinal_directions, all_directions, BuildArea, TransformBox
from utils.misc_objects_functions import sym_range, pos_bound, bernouilli, get_project_path, argmin, mean
from utils.pymclevel import *

X_ARRAY: ndarray = array([[x for z in range(BuildArea().length)] for x in range(BuildArea().width)])
Z_ARRAY: ndarray = array([[z for z in range(BuildArea().length)] for x in range(BuildArea().width)])
alpha = BlockAPI.blocks
