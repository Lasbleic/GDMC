"""
Village skeleton growth
"""

from time import time

from numpy import argmin
from statistics import mean

import terrain_map.maps
from building_seeding.building_pool import BuildingPool, BuildingType
from building_seeding.interest.pre_processing import VisuHandler
from building_seeding.parcel import MaskedParcel
from interest import InterestSeeder
from parameters import MIN_PARCEL_SIDE, AVERAGE_PARCEL_SIZE
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

    def add_parcel(self, seed, building_type):
        if isinstance(seed, Point2D):
            if building_type.name in ["crop"]:
                new_parcel = MaskedParcel(seed, building_type, self.maps)
            else:
                new_parcel = Parcel(seed, building_type, self.maps)
        elif isinstance(seed, Parcel):
            new_parcel = seed
            new_parcel.building_type.copy(BuildingType().ghost)
        else:
            raise TypeError("Expected Point2D or Parcel, found {}".format(seed.__class__))
        self.__parcel_list.append(new_parcel)
        new_parcel.mark_as_obstacle(self.maps.obstacle_map)

    def __handle_new_road_cycles(self, cycles):

        for road_cycle in cycles:
            city_block = CityBlock(road_cycle, self.maps)
            block_parcel = city_block.parcels()
            seed = block_parcel.center
            # block_seed = Point2D(int(mean(p.x for p in road_cycle)), int(mean(p.z for p in road_cycle)))
            block_type = self.__interest.get_optimal_type(seed)
            if block_type:
                self.add_parcel(seed, block_type)
                # self._create_masked_parcel(block_seed, BuildingType().ghost)
                # parcel is considered already linked to road network
            else:
                # if there already is a parcel in the block, or very close, it is moved to the block seed
                dist_to_parcels = list(map(lambda parcel: euclidean(parcel.center, seed), self.__parcel_list))
                if min(dist_to_parcels) <= AVERAGE_PARCEL_SIZE / 2:
                    index = int(argmin(dist_to_parcels))
                    old_parcel = self.__parcel_list[index]
                    self.maps.obstacle_map.hide_obstacle(old_parcel.origin, old_parcel.mask, False)
                    block_parcel.mark_as_obstacle(self.maps.obstacle_map)
                    block_parcel.building_type.copy(old_parcel.building_type)
                    self.__parcel_list[index] = block_parcel
                else:
                    # add a park or plaza in the new cycle
                    self.add_parcel(block_parcel, BuildingType().ghost)

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
            self.add_parcel(building_position, building_type)

            # Road Creation Process
            cycles = self.maps.road_network.connect_to_network(self.__parcel_list[-1].entry_point)
            map_plots.handle_new_parcel(self.__interest[building_type])  # does nothing if not do_visu
            self.__handle_new_road_cycles(cycles)
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
        return MaskedParcel(parcel_origin, BuildingType(), self.__maps, parcel_mask)

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
