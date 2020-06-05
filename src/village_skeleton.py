"""
Village skeleton growth
"""

from typing import List
from building_seeding import BuildingPool, ghost_type, interest, random_interest
from generation import Parcel
from utils import Point2D
import map.maps


class VillageSkeleton:

    def __init__(self, scenario, maps, ghost_position, parcel_list):
        # type: (str, map.maps.Maps, Point2D, List[Parcel]) -> VillageSkeleton
        self.scenario = scenario
        self.size = (maps.width, maps.length)
        self.maps = maps
        self.ghost = Parcel(ghost_position, ghost_type)
        self.building_iterator = BuildingPool(maps.width * maps.length)
        self.parcel_list = parcel_list

    def grow(self):

        for building_type in self.building_iterator:
            # Village Element Seeding Process

            interest_map = interest(building_type, self.scenario, self.maps.road_network,[self.ghost] + self.parcel_list, self.size)
            building_position = random_interest(interest_map)
            new_parcel = Parcel(building_position, building_type, self.maps)

            self.parcel_list.append(new_parcel)

            self.maps.obstacle_map.add_parcel_to_obstacle_map(new_parcel)

            # Road Creation Process
            self.maps.road_network.connect_to_network(new_parcel.entry_point)


# if __name__ == '__main__':
#     from gen_utils import TransformBox
#     from maps import Maps
#     from flat_settlement import FlatSettlement
#     from map.road_network import RoadNetwork
#
#     my_bounding_box = TransformBox((0, 0, 0), (100, 0, 100))
#     my_maps = Maps(None, my_bounding_box)
#     my_flat_settlement = FlatSettlement(my_maps)
#     print(my_flat_settlement._road_network.network)
#     my_flat_settlement.init_road_network()
#     print(my_flat_settlement._road_network.network)
