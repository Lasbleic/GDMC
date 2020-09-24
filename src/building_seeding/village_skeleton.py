"""
Village skeleton growth
"""

from time import time

from numpy import argmin
from statistics import mean

import terrain_map.maps
from building_pool import BuildingPool, BuildingType
from building_seeding.interest.pre_processing import VisuHandler
from building_seeding.parcel import MaskedParcel
from interest import InterestSeeder
from parameters import MIN_PARCEL_SIDE
from parcel import Parcel
from utils import *


class VillageSkeleton:

    def __init__(self, scenario, maps, ghost_position, parcel_list):
        # type: (str, terrain_map.maps.Maps, Point2D, List[Parcel]) -> VillageSkeleton
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

    def __create_new_parcel(self, seed, building_type):
        new_parcel = Parcel(seed, building_type, self.maps)
        self.__parcel_list.append(new_parcel)
        self.maps.obstacle_map.add_parcel_to_obstacle_map(new_parcel, 1)

    def grow(self, do_limit, do_visu):
        print("Seeding parcels")
        map_plots = VisuHandler(do_visu, self.size, self.__parcel_list, self.maps.road_network)

        t0 = time()
        for building_type in self.building_iterator:

            print("\nTrying to place {} - #{} out of {}".format(building_type.name, self.building_iterator.count,
                                                                self.building_iterator.size))

            # Village Element Seeding Process
            self.__interest.reuse_existing_parcel(building_type)  # If succeeds should update building_type in place
            building_position = self.__interest.get_seed(building_type)

            if building_position is None:
                print("No suitable position found")
                continue

            print("Placed at x:{}, z:{}".format(building_position.x, building_position.z))
            self.__create_new_parcel(building_position, building_type)

            # Road Creation Process
            cycles = self.maps.road_network.connect_to_network(self.__parcel_list[-1].entry_point)
            map_plots.handle_new_parcel(self.__interest[building_type])  # does nothing if not do_visu

            for road_cycle in cycles:
                city_block = CityBlock(road_cycle, self.maps)
                block_parcel = city_block.parcels()
                seed = block_parcel.center
                # block_seed = Point2D(int(mean(p.x for p in road_cycle)), int(mean(p.z for p in road_cycle)))
                block_type = self.__interest.get_optimal_type(seed)
                if block_type:
                    self.__create_new_parcel(seed, block_type)
                    # self._create_masked_parcel(block_seed, BuildingType().ghost)
                    # parcel is considered already linked to road network
                else:
                    # if there already is a parcel in the block, or very close, it is moved to the block seed
                    dist_to_parcels = list(map(lambda parcel: euclidean(parcel.center, seed), self.__parcel_list))
                    if min(dist_to_parcels) <= 4:
                        block_parcel = self.__parcel_list[int(argmin(dist_to_parcels))]
                        block_parcel.move_center(seed)
                    else:
                        # self.__create_new_parcel(block_seed, BuildingType().ghost)
                        block_parcel.building_type.copy(BuildingType().ghost)
                        self.__parcel_list.append(block_parcel)
                        self.maps.obstacle_map.add_parcel_to_obstacle_map(block_parcel, 0)

            if do_limit and time() - t0 >= 9 * 60:
                print("Time limit reached: early stopping parcel seeding")
                break


class CityBlock:
    def __init__(self, road_cycle, maps):
        self.__road_points = road_cycle
        self.__maps = maps
        self.__origin = Point2D(min(_.x for _ in road_cycle), min(_.z for _ in road_cycle))
        self.__limits = Point2D(max(_.x for _ in road_cycle), max(_.z for _ in road_cycle))

    @staticmethod
    def connection(src_point, dst_point, maps):
        return not maps.road_network.is_road(dst_point)

    def parcels(self):
        seed = Point2D(int(mean(p.x for p in self.__road_points)), int(mean(p.z for p in self.__road_points)))
        origin, mask = connected_component(self.__maps, seed, CityBlock.connection)
        parcel_origin = Point2D(max(origin.x, self.minx), max(origin.z, self.minz))
        parcel_limits = Point2D(min(origin.x+mask.shape[0], self.maxx), min(origin.z+mask.shape[1], self.maxz))
        parcel_shapes = Point2D(1, 1) + parcel_limits - parcel_origin
        parcel_mask = mask[(parcel_origin.x - origin.x): (parcel_origin.x - origin.x + parcel_shapes.x),
                           (parcel_origin.z - origin.z): (parcel_origin.z - origin.z + parcel_shapes.z)]
        return MaskedParcel(parcel_origin, parcel_mask, BuildingType(), self.__maps)

    @property
    def minx(self):
        return self.__origin.x

    @property
    def maxx(self):
        return self.__limits.x

    @property
    def minz(self):
        return self.__origin.z

    @property
    def maxz(self):
        return self.__limits.z


if __name__ == '__main__':
    from utils import TransformBox
    from terrain_map import Maps
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
    # print("Creating Flat terrain_map")
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

