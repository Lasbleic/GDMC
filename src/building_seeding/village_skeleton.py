"""
Village skeleton growth
"""

from time import time
from typing import List

import numpy as np

import map.maps
from building_pool import BuildingPool, BuildingType
from interest import InterestSeeder
from parcel import Parcel
from utils import Point2D


class VillageSkeleton:

    def __init__(self, scenario, maps, ghost_position, parcel_list, parcel_size=7):
        # type: (str, map.maps.Maps, Point2D, List[Parcel], int) -> VillageSkeleton
        assert(parcel_size % 2)  # assert parcel_size is odd
        self.scenario = scenario
        self.size = (maps.width, maps.length)
        self.maps = maps
        self.ghost = ghost_position
        buildable_surface = maps.width * maps.length - maps.fluid_map.as_obstacle_array.sum()
        self.building_iterator = BuildingPool(buildable_surface)
        self.__parcel_list = parcel_list
        self.parcel_size = parcel_size
        # self.map_stock = MapStock("Village_skeleton_test", maps.width, clean_dir=True)
        self.map_stock = None

        parcel_list.append(Parcel(ghost_position, BuildingType.from_name('ghost'), maps))
        self.__interest = InterestSeeder(maps, parcel_list, scenario)

    def map_log(self, interest_map=None, accessibility_map=None, sociability_map=None, building_type=None, obstacle_map=None):

        iteration = len(self.__parcel_list)
        suffix = "_{}".format(building_type.name) if building_type is not None else ""
        N = self.size[0]

        # if accessibility_map is not None:
        #     self.map_stock.add_map(Map("{}1_accessibility_map{}".format(iteration, suffix), N, accessibility_map, "jet", (0, 1)))
        # if sociability_map is not None:
        #     self.map_stock.add_map(Map("{}2_sociability_map{}".format(iteration, suffix), N, sociability_map, "jet", (0, 1)))
        # if interest_map is not None:
        #     self.map_stock.add_map(Map("{}3_interest_map{}".format(iteration, suffix), N, interest_map, "jet", (0, 1)))
        # if obstacle_map is not None:
        #     self.map_stock.add_map(Map("{}3_interest_map{}".format(iteration, suffix), N, obstacle_map, colors.ListedColormap(['red', 'blue']), (0, 1), ['No', 'Yes']))

        minecraft_map = np.copy(self.maps.road_network.network)

        COLORS = {"house": 2,
                  "crop": 3,
                  "windmill": 4}

        for parcel in self.__parcel_list:
            xmin, xmax = parcel.minx, parcel.maxx
            zmin, zmax = parcel.minz, parcel.maxz

            minecraft_map[xmin:xmax, zmin:zmax] = COLORS[parcel.building_type.name]
            # minecraft_map[parcel.center.x, parcel.center.z] = COLORS[parcel.building_type.name]

            minecraft_map[parcel.entry_point.x, parcel.entry_point.z] = 6

        village_center = self.ghost.center
        minecraft_map[village_center.x, village_center.z] = 5

        # minecraft_cmap = colors.ListedColormap(['forestgreen', 'beige', 'indianred', 'darkkhaki', 'orange', 'red', 'purple'])
        """
        self.map_stock.add_map(Map("{}{}_minecraft_map{}".format(iteration, 4 if iteration else 0, suffix),
                                   N,
                                   minecraft_map,
                                   minecraft_cmap,
                                   (0, 6),
                                   ['Grass', 'Road', 'House', 'Crop', 'Windmill', 'VillageCenter', 'EntryPoint']))
        """

    def grow(self, do_limit):
        print("Seeding parcels")
        # self.map_log()

        t0 = time()
        for building_type in self.building_iterator:

            print("\nTrying to place {} - #{} out of {}".format(building_type.name, self.building_iterator.count, self.building_iterator.size))

            # try:
            # Village Element Seeding Process
            self.__interest.reuse_existing_parcel(building_type)  # If succeeds should update building_type in place
            building_position = self.__interest.get_seed(building_type)

            # interest_map, accessibility_map, sociability_map = interest(building_type, self.scenario, self.maps, [self.ghost] + self.__parcel_list, self.size, self.parcel_size)
            # building_position = random_interest(interest_map)
            if building_position is None:
                print("No suitable position found")
                continue

            print("Placed at x:{}, z:{}".format(building_position.x, building_position.z))
            new_parcel = Parcel(building_position, building_type, self.maps)
            self.__parcel_list.append(new_parcel)
            self.maps.obstacle_map.add_parcel_to_obstacle_map(new_parcel, 2)

            # Road Creation Process
            self.maps.road_network.connect_to_network(new_parcel.entry_point)
            # self.map_log(interest_map, accessibility_map, sociability_map, building_type)
            # except Exception:
            #     print("Failed")
            #     continue

            if do_limit and time() - t0 >= 9 * 60:
                print("Time limit reached: early stopping parcel seeding")
                break


if __name__ == '__main__':

    from utils import TransformBox
    from map import Maps
    from flat_settlement import FlatSettlement

    N = 100
    
    my_bounding_box = TransformBox((0, 0, 0), (N, 0, N))
    my_maps = Maps(None, my_bounding_box)
    
    print("Creating Flat map")
    my_flat_settlement = FlatSettlement(my_maps)

    print("Initializing road network")
    my_flat_settlement.init_road_network()
    
    print("Initializing town center")
    my_flat_settlement.init_town_center()

    print("Building skeleton")
    my_flat_settlement.build_skeleton(False)

    # N = 50
    # 
    # my_bounding_box = TransformBox((0, 0, 0), (N, 0, N))
    # my_maps = Maps(None, my_bounding_box)
    # 
    # print("Creating Flat map")
    # my_flat_settlement = FlatSettlement(my_maps)
    # 
    # road_cmap = colors.ListedColormap(['forestgreen', 'beige'])
    # road_map = Map("road_network", N, np.copy(my_flat_settlement._road_network.network), road_cmap, (0, 1), ['Grass', 'Road'])
    # 
    # print("Initializing road network")
    # my_flat_settlement.init_road_network()
    # 
    # road_map2 = Map("road_network_2", N, np.copy(my_flat_settlement._road_network.network), road_cmap, (0, 1), ['Grass', 'Road'])
    # 
    # print("Initializing town center")
    # my_flat_settlement.init_town_center()
    # 
    # print("Building skeleton")
    # my_flat_settlement.build_skeleton()
    # 
    # print("Parcel list has length:", len(my_flat_settlement._parcels))
    # 
    # minecraft_net = np.copy(my_flat_settlement._road_network.network)
    # 
    # COLORS = {"house": 2,
    #           "crop": 3,
    #           "windmill": 4}
    # 
    # minecraft_cmap = colors.ListedColormap(['forestgreen', 'beige', 'indianred', 'darkkhaki', 'orange', 'white'])
    # 
    # for parcel in my_flat_settlement._parcels:
    #     xmin, xmax = parcel.minx, parcel.maxx
    #     zmin, zmax = parcel.minz, parcel.maxz
    # 
    #     # minecraft_net[zmin:zmax, xmin:xmax] = COLORS[parcel.building_type.name]
    #     minecraft_net[parcel.center.z, parcel.center.x] = COLORS[parcel.building_type.name]
    # 
    # village_center = my_flat_settlement._village_skeleton.ghost.center
    # minecraft_net[village_center.z, village_center.x] = 5
    # 
    # minecraft_map = Map("minecraft_map", N, minecraft_net, minecraft_cmap, (0, 5), ['Grass', 'Road', 'House', 'Crop', 'Windmill', 'VillageCenter'])
    # 
    # the_stock = MapStock("village_skeleton_test", N, clean_dir=True)
    # the_stock.add_map(road_map)
    # the_stock.add_map(road_map2)
    # the_stock.add_map(minecraft_map)
