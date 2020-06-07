"""
Village skeleton growth
"""

from typing import List
from building_seeding import BuildingPool, ghost_type, interest, random_interest
from generation.parcel import Parcel
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



if __name__ == '__main__':

    from gen_utils import TransformBox
    from maps import Maps
    from flat_settlement import FlatSettlement
    from map.road_network import RoadNetwork

    import sys

    sys.path.insert(1, '../../visu')
    from pre_processing import Map, MapStock
    import numpy as np
    from matplotlib import colors

    N = 200

    my_bounding_box = TransformBox((0, 0, 0), (N, 0, N))
    my_maps = Maps(None, my_bounding_box)

    print("Creating Flat map")
    my_flat_settlement = FlatSettlement(my_maps)

    road_cmap = colors.ListedColormap(['forestgreen', 'beige'])
    road_map = Map("road_network", N, np.copy(my_flat_settlement._road_network.network), road_cmap, (0, 1), ['Grass', 'Road'])

    print("Initializing road network")
    my_flat_settlement.init_road_network()

    road_map2 = Map("road_network_2", N, np.copy(my_flat_settlement._road_network.network), road_cmap, (0, 1), ['Grass', 'Road'])

    print("Initializing town center")
    my_flat_settlement.init_town_center()

    print("Building skeleton")
    my_flat_settlement.build_skeleton()

    print("Parcel list has length:", len(my_flat_settlement._parcels))

    minecraft_net = np.copy(my_flat_settlement._road_network.network)

    COLORS = {"house": 2,
              "crop": 3,
              "windmill": 4}

    minecraft_cmap = colors.ListedColormap(['forestgreen', 'beige', 'indianred', 'darkkhaki', 'orange', 'red'])

    for parcel in my_flat_settlement._parcels:
        xmin, xmax = parcel.minx, parcel.maxx
        zmin, zmax = parcel.minz, parcel.maxz

        minecraft_net[zmin:zmax, xmin:xmax] = COLORS[parcel.building_type.name]

    village_center = my_flat_settlement._village_skeleton.ghost.center
    minecraft_net[village_center.z, village_center.x] = 5

    minecraft_map = Map("minecraft_map", N, minecraft_net, minecraft_cmap, (0, 5), ['Grass', 'Road', 'House', 'Crop', 'Windmill', 'VillageCenter'])

    the_stock = MapStock("road_network_test", N, clean_dir=True)
    the_stock.add_map(road_map)
    the_stock.add_map(road_map2)
    the_stock.add_map(minecraft_map)
