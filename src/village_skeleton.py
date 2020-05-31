"""
Village skeleton growth
"""

from typing import List
from building_seeding import BuildingPool, ghost_type, interest, random_interest
from pymclevel import BoundingBox
from map.road_network import RoadNetwork
from utils import Point2D


class VillageSkeleton:

    def __init__(self, scenario, size, road_network, ghost_position):
        # type: (str, List[int], RoadNetwork, Point2D) -> VillageSkeleton
        self.scenario = scenario
        self.size = size
        self.road_network = road_network
        ghost = (ghost_type, ghost_position)
        self.buildings = [ghost]
        self.building_iterator = BuildingPool(size[0] * size[1])

    def grow(self, parcels_list):
        for building_type in self.building_iterator:
            # Village Element Seeding Process

            interest_map = interest(building_type, self.scenario, self.road_network, self.buildings, self.size)
            building_position = random_interest(interest_map)
            new_building = (building_type, building_position)
            self.buildings.append(new_building)

            # Road Creation Process
            # todo: add Parcel to parcels_list (belonging to flat_settlement)
            # self.road_network.update(self.buildings, new_building)
