from __future__ import division

import logging
from math import exp
from random import choice
from typing import List

from numpy import percentile
from numpy.random import geometric, normal

from building_seeding import Parcel, VillageSkeleton, BuildingType
from building_seeding.parcel import MaskedParcel
from generation.building_palette import get_biome_palette
from parameters import MAX_HEIGHT, BUILDING_HEIGHT_SPREAD, MIN_PARCEL_SIDE
from terrain import TerrainMaps
from terrain.road_network import RoadNetwork
from utils import *

MEAN_ROAD_COVERED_SURFACE = 64  # to compute number of roads, max 1 external connexion per 1/64 of the settlement size
SETTLEMENT_ACCESS_DIST = 25  # maximum distance from settlement center to road net


class FlatSettlement:
    """
    Intermediate project: generate a realistic village on a flat terrain
    """
    def __init__(self, maps):
        # type: (TerrainMaps) -> FlatSettlement
        self._maps = maps  # type: TerrainMaps
        self._origin = maps.area.origin
        self._center: Point = Point(0, 0)
        self._road_network = self._maps.road_network
        self._parcels: List[Parcel] = []
        self._village_skeleton = VillageSkeleton('Flat_scenario', self._maps, self.town_center, self._parcels)

    def __random_border_point(self):
        # type: () -> Point
        # width, length = self.limits.width, self.limits.length
        # # random draw to decide on what side the border will be. Favors larger sides
        # if bernouilli(width / (width + length)):
        #     # border point along x border
        #     x = 0 if bernouilli() else self.limits.width - 1
        #     z = randint(0, length - 1)
        # else:
        #     # border point along z border
        #     x = randint(0, width - 1)
        #     z = 0 if bernouilli() else self.limits.length - 1
        # return Point2D(x, z)
        return choice(self._maps.fluid_map.external_connections)

    def init_road_network(self):
        out_connections = [self.__random_border_point()]
        max_road_count = max(1, min(self.limits.width, self.limits.length) // MEAN_ROAD_COVERED_SURFACE)
        logging.debug('Max road count: {}'.format(max_road_count))
        road_count = min(geometric(1./max_road_count), max_road_count*3//2)
        logging.debug('New settlement will have {} roads B)'.format(road_count))
        logging.debug('First border point @{}'.format(str(out_connections[0])))
        self._road_network.create_road(self._parcels[0].entry_point, out_connections[0])

        for road_id in range(road_count):
            min_distance_to_roads = min(self.limits.width, self.limits.length) / (road_id+1)
            logging.debug('Generating road #{}'.format(road_id+1))
            # generate new border point far enough from existing points
            while True:
                new_road_point = self.__random_border_point()
                distances = [euclidean(road_point, new_road_point) for road_point in out_connections]
                distance_to_roads = min(distances)
                log_args = (str(new_road_point), distance_to_roads, min_distance_to_roads)
                if distance_to_roads >= min_distance_to_roads:
                    out_connections.append(new_road_point)
                    logging.debug('\tSettled on border point {} at {}m >= {}m'.format(*log_args))
                    break
                else:
                    logging.debug('\tDismissed point {} at {}m < {}m'.format(*log_args))
                    min_distance_to_roads *= 0.9
            # update road network
            # if road_id == 0:
            #     self._road_network.create_road(out_connections[0], out_connections[1])
            # else:
            self._road_network.connect_to_network(out_connections[-1])

    def init_town_center(self):
        stp_thresh = 1
        while True:
            mean_x = self.limits.width / 2
            dx = normal(mean_x, self.limits.width / 8)
            dx = int(min(self.limits.width-1, max(0, dx)))

            mean_z = self.limits.length / 2
            dz = normal(mean_z, self.limits.length / 8)
            dz = int(min(self.limits.length-1, max(0, dz)))

            random_center = Point(dx, dz)
            distance = self._road_network.get_distance(random_center)
            if self._maps.fluid_map.is_close_to_fluid(random_center) or distance < MIN_PARCEL_SIDE:
                continue
            elif self._maps.height_map.steepness(random_center.x, random_center.z) < stp_thresh:
                self._center = random_center
                logging.debug('Settlement center placed @{}, {}m away from road'.format(str(random_center), distance))
                break
            else:
                stp_thresh *= 1.1
        self._parcels.append(Parcel(self._center, BuildingType().ghost, self._maps))
        # self._parcels[-1].mark_as_obstacle(self._maps.obstacle_map)

    def build_skeleton(self, time_limit, do_visu=False):
        self._village_skeleton.grow(time_limit, do_visu)
        # for parcel in filter(lambda p: p.building_type.name == 'ghost', self._parcels):
        #     self._parcels.remove(parcel)

    def define_parcels(self):
        """
        Parcel extension from initialized parcels. Parcels are expended in place
        """
        print("Extending parcels")
        # self._parcels = self._parcels[1:]
        obs = self._maps.obstacle_map
        obs.map[:] = 0
        obs.add_network_to_obstacle_map()
        for parcel in self._parcels:
            parcel.mark_as_obstacle(obs)
        obs.map += self._maps.fluid_map.as_obstacle_array
        expendable_parcels: List[Parcel] = self._parcels[:]
        # most parcels should initially be expendable, except the ghost one
        expendable_parcels = list(filter(lambda _: _.is_expendable, expendable_parcels))

        surface = sum(p.bounds.volume for p in expendable_parcels)
        while expendable_parcels:
            # extend expendables parcels while there still are some

            for parcel in expendable_parcels:
                if parcel.entry_point == parcel.center:
                    self._parcels.remove(parcel)
                    expendable_parcels.remove(parcel)
                    continue
                # direction computation
                road_dir_x = parcel.entry_x - parcel.mean_x
                road_dir_z = parcel.entry_z - parcel.mean_z
                road_dir = Direction.of(road_dir_x, 0, road_dir_z)
                lateral_dir = road_dir.rotate() if bernouilli() else -road_dir.rotate()

                priority_directions = [road_dir, lateral_dir, -lateral_dir, -road_dir]
                for direction in priority_directions:
                    if parcel.is_expendable(direction):
                        parcel.expand(direction)
                        break

            expendable_parcels = list(filter(lambda _: _.is_expendable, expendable_parcels))
            tmp = surface
            surface = sum(p.bounds.volume for p in expendable_parcels)
            if tmp >= surface:
                break

        # set parcels heights
        def define_parcels_heights(__parcel):
            # type: (Parcel) -> None
            min_y = percentile(__parcel.height_map, 25)
            max_y = percentile(__parcel.height_map, 75)
            road_y = self._maps.height_map.upper_height(__parcel.entry_x, __parcel.entry_z)
            y = road_y
            if road_y > max_y:
                y = max_y
            elif road_y < min_y:
                y = min_y
            y += 1
            d = min(euclidean(__parcel.center, _.center) for _ in
                    filter(lambda p: p.building_type.name == "ghost", self._parcels)
                    )
            h = int(MAX_HEIGHT * exp(-d / BUILDING_HEIGHT_SPREAD))
            __parcel.set_height(y, h)

        print("Defining parcels' and buildings' heights")
        for p in self._parcels:
            define_parcels_heights(p)
            # translate all parcels to absolute coordinates
            p.translate_to_absolute_coords(self._origin)

    def generate(self, level, print_stack=False):
        self._road_network.generate(level)

        for parcel in self._parcels:  # type: Parcel
            parcel_biome = parcel.biome(level)
            palette = get_biome_palette(parcel_biome)
            if isinstance(parcel, MaskedParcel):
                obstacle_mask = self._maps.obstacle_map.box_obstacle(parcel.bounds)
                parcel.add_mask(obstacle_mask)
            if print_stack:
                gen = parcel.generator
                gen.choose_sub_generator(self._parcels)
                gen.generate(level, parcel.height_map, palette)
            else:
                try:
                    gen = parcel.generator
                    gen.choose_sub_generator(self._parcels)
                    gen.generate(level, parcel.height_map, palette)
                except Exception:
                    print("FAIL")

    @property
    def town_center(self):
        return self._center

    @property
    def limits(self):
        return self._maps.area
