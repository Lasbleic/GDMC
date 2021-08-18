from itertools import product
from typing import List, Set

import numpy

from terrain import TerrainMaps
from utils import Position, connected_component, building_positions, getBlockRelativeAt, BlockAPI
from building_seeding import Parcel, MaskedParcel, BuildingType


class StructureDetector:
    def __init__(self, terrain: TerrainMaps):
        self.terrain = terrain

    def get_structure_parcels(self) -> List[Parcel]:
        return self.__detect_buildings() + self.__detect_mines()

    def __detect_buildings(self) -> List[Parcel]:
        hm = self.terrain.level.heightmaps
        struct_height = hm["MOTION_BLOCKING"] - hm["MOTION_BLOCKING_NO_LEAVES"]

        def is_building(p: Position):
            return self.terrain.trees[p] == 0

        x_list, z_list = numpy.where(struct_height > 0)
        structure_points = {Position(x_list[i], z_list[i]) for i in range(len(x_list))}
        structure_points = set(filter(is_building, structure_points))

        parcels = self.__connected_components(structure_points, BuildingType.structure)
        for p in parcels:
            heights = [struct_height[p.minx + dx, p.minz + dz] for dx, dz in product(range(p.width), range(p.length)) if
                       p.mask[dx, dz]]
            if numpy.median(heights) == 1 or p.width < 3 or p.length < 3:
                parcels.remove(p)

        return parcels

    def __detect_mines(self) -> List[Parcel]:
        def is_cave(p: Position):
            y = self.terrain.height_map.lower_height(p)
            block = self.terrain.level.getBlockAt((p.abs_x, y + 1, p.abs_z))
            return block.endswith("cave_air")

        structure_points = set(filter(is_cave, building_positions()))
        return self.__connected_components(structure_points, BuildingType.cave)

    def __connected_components(self, points_to_explore: Set[Position], btype: BuildingType):
        components = []

        while points_to_explore:
            struct_origin, struct_mask = connected_component(points_to_explore.pop(),
                                                             lambda _, p: Position(p.x, p.z) in points_to_explore)
            for dx, dz in product(range(struct_mask.shape[0]), range(struct_mask.shape[1])):
                if struct_mask[dx, dz]:
                    pos = Position(struct_origin.x + dx, struct_origin.z + dz)
                    if pos in points_to_explore:
                        points_to_explore.remove(pos)
            components.append(MaskedParcel(struct_origin, btype, self.terrain, struct_mask))

        return components
