"""
Village skeleton growth
"""

from time import time

from typing import List

import map.maps
from building_pool import BuildingPool
from building_seeding.interest.pre_processing import VisuHandler
from interest import InterestSeeder
from parameters import MIN_PARCEL_SIDE
from parcel import Parcel
from utils import Point2D


class VillageSkeleton:

    def __init__(self, scenario, maps, ghost_position, parcel_list):
        # type: (str, map.maps.Maps, Point2D, List[Parcel]) -> VillageSkeleton
        self.scenario = scenario
        self.size = (maps.width, maps.length)
        self.maps = maps
        self.ghost = ghost_position
        buildable_surface = maps.width * maps.length - maps.fluid_map.as_obstacle_array.sum()
        self.building_iterator = BuildingPool(buildable_surface)
        self.__parcel_list = parcel_list
        self.parcel_size = MIN_PARCEL_SIDE

        # parcel_list.append(Parcel(ghost_position, BuildingType.from_name('ghost'), maps))
        self.__interest = InterestSeeder(maps, parcel_list, scenario)

    def grow(self, do_limit, do_visu):
        print("Seeding parcels")
        map_plots = VisuHandler(do_visu, self.size, self.__parcel_list, self.maps.road_network)

        t0 = time()
        for building_type in self.building_iterator:

            print("\nTrying to place {} - #{} out of {}".format(building_type.name, self.building_iterator.count, self.building_iterator.size))

            # Village Element Seeding Process
            self.__interest.reuse_existing_parcel(building_type)  # If succeeds should update building_type in place
            building_position = self.__interest.get_seed(building_type)

            if building_position is None:
                print("No suitable position found")
                continue

            print("Placed at x:{}, z:{}".format(building_position.x, building_position.z))
            new_parcel = Parcel(building_position, building_type, self.maps)
            self.__parcel_list.append(new_parcel)
            self.maps.obstacle_map.add_parcel_to_obstacle_map(new_parcel, 1)

            # Road Creation Process
            self.maps.road_network.connect_to_network(new_parcel.entry_point)
            map_plots.handle_new_parcel(self.__interest[building_type])  # does nothing if not do_visu

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
