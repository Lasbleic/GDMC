from itertools import product
from typing import List, Set

import numpy

from building_seeding import Parcel, MaskedParcel, BuildingType
from terrain import TerrainMaps
from utils import Position, BuildArea, PointArray
from utils.algorithms.graphs import connected_component, GridGraph, point_set_as_array


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
            block = self.terrain.level.getBlockAt(p.abs_x, y + 1, p.abs_z)
            return block.endswith("cave_air")

        structure_points = set(filter(is_cave, BuildArea.building_positions()))
        return self.__connected_components(structure_points, BuildingType.cave)

    def __connected_components(self, points_to_explore: Set[Position], btype: BuildingType):
        components = []

        while points_to_explore:
            def connection(n1, n2):
                return n2 in points_to_explore
            component = connected_component(GridGraph(False), points_to_explore.pop(), connection)
            struct_origin, struct_mask = point_set_as_array(component)
            struct_origin, struct_mask = struct_origin.view(Position), struct_mask.view(PointArray)
            points_to_explore.difference_update(component)
            components.append(MaskedParcel(struct_origin, btype, self.terrain, struct_mask))

        return components
