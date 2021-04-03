from terrain import HeightMap
from terrain.map import Map
from utils import *


class TreesMap(Map):
    def __init__(self, level: WorldSlice, height: HeightMap):
        self.__trees = {}
        values = self.__process(level, height)
        super().__init__(values)

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
        for x, z in product(range(height.width), range(height.length)):
            y = height[x, z] + 1
            p = Point(x, z, y)
            block = level.getBlockRelativeAt(x, y, z)
            if 'log' in block and neighbours_not_trees():
                trunks.add(p)

        # Initialize tree structure & propagation
        tree_blocks, marked_blocks = [], set()
        for tree_index, trunk_pos in enumerate(trunks):
            tree_index += 1  # start enumeration at 1
            self.__trees[tree_index] = set()
            tree_blocks.append((trunk_pos, tree_index))
            marked_blocks.add(trunk_pos)

        # propagate trees through trunks and leaves
        while tree_blocks:
            # Get the oldest element in the blocks to process
            tree_point, tree_index = tree_blocks.pop(0)  # type: Point, int

            # add it to the structure of its tree
            self.__trees[tree_index].add(tree_point + height.area.origin)
            if not values[tree_point.x, tree_point.z]:
                values[tree_point.x, tree_point.z] = tree_index

            # check if neighbours for possible other tree points
            for direction in all_directions():
                possible_tree_point = tree_point + direction
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
