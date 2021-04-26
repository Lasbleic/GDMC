import numba
from numba.typed import List as nbList
from numpy import uint8
from numba.core.types.containers import UniTuple
from typing import Tuple

from terrain import HeightMap
from terrain.map import Map
from utils import *


class TreesMap(Map):
    def __init__(self, level: WorldSlice, height: HeightMap):
        self.__trees = {}
        values = self.__process(level, height)
        super().__init__(values)

    @numba.jit()
    def __process(self, level: WorldSlice, height: HeightMap):
        values = zeros((height.width, height.length))
        trunks = set()

        def neighbours_not_trees():
            return all((p + direction) not in trunks for direction in all_directions())

        def is_tree(bid):
            return is_trunk(bid) or any(_ in bid for _ in ['_leaves', 'mushroom_block'])

        def is_trunk(block):
            return any(_ in block for _ in ['log', '_stem'])

        # Look for tree trunks
        trunk_height = 255
        tree_height = 0
        for x, z in product(range(height.width), range(height.length)):
            y = height[x, z] + 1
            p = Point(x, z, y)
            block = level.getBlockRelativeAt(x, y, z)
            if is_trunk(block) and neighbours_not_trees():
                trunks.add(p)
                trunk_height = min(trunk_height, y)
                while is_tree(level.getBlockRelativeAt(x, y, z)):
                    y += 1
                tree_height = max(tree_height, y)


        lvl = zeros((height.width, tree_height - trunk_height, height.length), dtype=uint8)
        b_to_id = {}
        id_to_b = nbList()

        for x, z, y in product(range(height.width), range(height.length), range(trunk_height, tree_height)):
            b = level.getBlockRelativeAt(x, y, z)
            if b not in b_to_id:
                index = len(b_to_id)
                b_to_id[b] = index
                id_to_b.append(b)
            else:
                index = b_to_id[b]
            lvl[x, y-trunk_height, z] = index

        # trees = _detect_trees(lvl, height[:], level.rect[0], trunk_height, level.rect[1], id_to_b)
        # print(trees[0])
        # return values
        # Look for tree trunks
        for x, z in product(range(height.width), range(height.length)):
            y = height[x, z] + 1
            p = Point(x, z, y)
            block = level.getBlockRelativeAt(x, y, z)
            if is_trunk(block) and neighbours_not_trees():
                trunks.add(p)

        # Initialize tree structure & propagation
        tree_blocks, marked_blocks = [], set()
        for tree_index, trunk_pos in enumerate(trunks):
            tree_index += 1  # start enumeration at 1
            self.__trees[tree_index] = set()
            tree_blocks.append((trunk_pos, tree_index))
            marked_blocks.add(trunk_pos)

        # propagate trees through trunks and leaves (and mushrooms)
        while tree_blocks:
            # Get the oldest element in the blocks to process
            tree_point, tree_index = tree_blocks.pop(0)  # type: Point, int

            # add it to the structure of its tree
            self.__trees[tree_index].add(tree_point + height.area.origin)
            if not values[tree_point.x, tree_point.z]:
                values[tree_point.x, tree_point.z] = tree_index

            # check if neighbours for possible other tree points
            for dx, dy, dz in product(range(-1, 2), range(-1, 2), range(-1, 2)):
                possible_tree_point = tree_point + Point(dx, dy, dz)
                if (possible_tree_point + height.area.origin in height.area) and (possible_tree_point not in marked_blocks) \
                        and (is_tree(level.getBlockRelativeAt(possible_tree_point))):
                    marked_blocks.add(possible_tree_point)
                    tree_blocks.append((possible_tree_point, tree_index))

        return values

    def remove_tree_at(self, position: Point):
        if self[position] not in self.__trees:
            return

        tree_index = self[position]
        for tree_block in self.__trees[tree_index]:
            setBlock(tree_block, BlockAPI.blocks.Air)
        del self.__trees[tree_index]


@numba.njit
def _detect_trees(level: ndarray, height_map: ndarray, origin_x: int, origin_y: int, origin_z: int, palette: List[str]):
    dxyz: List[Tuple[int, int, int]] = [(-1, -1, -1), (-1, -1, 0), (-1, -1, 1), (-1, 0, -1), (-1, 0, 0), (-1, 0, 1), (-1, 1, -1), (-1, 1, 0), (-1, 1, 1), (0, -1, -1), (0, -1, 0), (0, -1, 1), (0, 0, -1), (0, 0, 1), (0, 1, -1), (0, 1, 0), (0, 1, 1), (1, -1, -1), (1, -1, 0), (1, -1, 1), (1, 0, -1), (1, 0, 0), (1, 0, 1), (1, 1, -1), (1, 1, 0), (1, 1, 1)]
    trunks: Set[Tuple[int, int, int]] = set()
    tmp = nbList()
    tmp.append((0, 0, 0))
    trees = nbList()
    trees.append(tmp)
    trees.remove(tmp)
    width, height, length = level.shape

    p: Tuple[int, int, int]
    # Look for tree trunks
    for x in range(width):
        for z in range(length):
            y = max(0, height_map[x, z] + 1 - origin_y)
            p = (x, y, z)
            block = palette[level[x, y, z]]
            if _is_trunk(block) and _neighbours_not_trees(p, trunks):
                trunks.add(p)

    # Initialize tree structure & propagation
    tree_blocks, marked_blocks = [], set()
    for tree_index, trunk_pos in enumerate(trunks):  # type: int, Tuple[int, int, int]
        tmp = nbList()
        tmp.append(trunk_pos)
        trees.append(tmp)
        trees[tree_index].append(trunk_pos)
        tree_blocks.append(trunk_pos + (tree_index,))
        marked_blocks.add(trunk_pos)

    # propagate trees through trunks and leaves (and mushrooms)
    while tree_blocks:
        # Get the oldest element in the blocks to process
        tree_x, tree_y, tree_z, tree_index = tree_blocks.pop(0)  # type: int, int, int, int

        # add it to the structure of its tree

        # check if neighbours for possible other tree points
        for dx, dy, dz in dxyz:
            possible_tree = (tree_x + dx, tree_y + dy, tree_z + dz)
            if (_in_limits(possible_tree, width, length, height)) and (possible_tree not in marked_blocks) \
                    and (_is_tree(palette[level[possible_tree[0], possible_tree[1], possible_tree[2]]])):
                marked_blocks.add(possible_tree)
                tree_blocks.append(possible_tree + (tree_index,))
                trees[tree_index].append(possible_tree)

    return trees

@numba.njit
def _neighbours_not_trees(p, trunks):
    dlat = [(-1, 0, 0), (1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, -1), (0, 0, 1)]
    for d in dlat:
        dp = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
        if dp in trunks:
            return False
    return True


@numba.njit
def _is_trunk(block):
    return 'log' in block or 'stem' in block


@numba.njit
def _is_tree(bid):
    return _is_trunk(bid) or '_leaves' in bid or 'mushroom_block' in bid


@numba.njit
def _in_limits(xyz0: Tuple[int, int, int], width, length, height):
    x0, y0, z0 = xyz0
    return 0 <= x0 < width and 0 <= z0 < length and 0 <= y0 < height


def remove_tree_at(self, position: Point):
    if self[position] not in self.__trees:
        return

    tree_index = self[position]
    for tree_block in self.__trees[tree_index]:
        setBlock(tree_block, BlockAPI.blocks.Air)
    del self.__trees[tree_index]
