from __future__ import division

import logging
from math import exp
from random import choice

from numpy import percentile
from numpy.random import geometric, normal
from typing import List

from building_seeding import Parcel, VillageSkeleton, BuildingType
from building_seeding.parcel import MaskedParcel
from generation.building_palette import get_biome_palette
from parameters import MAX_HEIGHT, BUILDING_HEIGHT_SPREAD, MIN_PARCEL_SIDE
from terrain_map.maps import Maps
from terrain_map.road_network import RoadNetwork
from utils import Direction, TransformBox
from utils import bernouilli, euclidean, Point2D

MEAN_ROAD_COVERED_SURFACE = 64  # to compute number of roads, max 1 external connexion per 1/64 of the settlement size
SETTLEMENT_ACCESS_DIST = 25  # maximum distance from settlement center to road net


class FlatSettlement:
    """
    Intermediate project: generate a realistic village on a flat terrain
    """
    def __init__(self, maps):
        # type: (Maps) -> FlatSettlement
        self._maps = maps  # type: Maps
        self.__origin = maps.box.origin
        self.limits = TransformBox(maps.box)  # type: TransformBox
        self.limits.translate(dx=-self.__origin.x, dz=-self.__origin.z)  # use coordinates relative to BuildingBox
        self._road_network = maps.road_network  # type: RoadNetwork
        self._center = None  # type: Point2D
        self._village_skeleton = None  # type: VillageSkeleton
        self._parcels = []  # type: List[Parcel]

    def __random_border_point(self):
        # type: () -> Point2D
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
        self._road_network.create_road(self._center, out_connections[0])
        max_road_count = max(1, min(self.limits.width, self.limits.length) // MEAN_ROAD_COVERED_SURFACE)
        logging.debug('Max road count: {}'.format(max_road_count))
        road_count = min(geometric(1./max_road_count), max_road_count*3//2)
        logging.debug('New settlement will have {} roads B)'.format(road_count))
        logging.debug('First border point @{}'.format(str(out_connections[0])))

        for road_id in xrange(road_count):
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

            random_center = Point2D(dx, dz)
            distance = self._road_network.get_distance(random_center)
            if self._maps.fluid_map.is_close_to_fluid(random_center) or distance < MIN_PARCEL_SIDE:
                continue
            elif self._maps.height_map.steepness(random_center.x, random_center.z, margin=6) < stp_thresh:
                self._center = random_center
                logging.debug('Settlement center placed @{}, {}m away from road'.format(str(random_center), distance))
                break
            else:
                stp_thresh *= 1.1
        self._parcels.append(Parcel(self._center, BuildingType().ghost, self._maps))

    def build_skeleton(self, time_limit, do_visu=False):
        self._village_skeleton = VillageSkeleton('Flat_scenario', self._maps, self.town_center, self._parcels)
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
            obs.add_parcel_to_obstacle_map(parcel, 1)
        obs.map += self._maps.fluid_map.as_obstacle_array
        expendable_parcels = self._parcels[:]  # type: List[Parcel]
        # most parcels should initially be expendable, except the ghost one
        expendable_parcels = filter(Parcel.is_expendable, expendable_parcels)

        while expendable_parcels:
            # extend expendables parcels while there still are some

            for parcel in expendable_parcels:
                # direction computation
                road_dir_x = parcel.entry_x - parcel.mean_x
                road_dir_z = parcel.entry_z - parcel.mean_z
                road_dir = Direction(road_dir_x, 0, road_dir_z)
                lateral_dir = road_dir.rotate() if bernouilli() else -road_dir.rotate()

                priority_directions = [road_dir, lateral_dir, -lateral_dir, -road_dir]
                for direction in priority_directions:
                    if parcel.is_expendable(direction):
                        parcel.expand(direction)
                        break

            expendable_parcels = filter(Parcel.is_expendable, expendable_parcels)

        # set parcels heights
        def define_parcels_heights(__parcel):
            # type: (Parcel) -> None
            min_y = percentile(__parcel.height_map, 25)
            max_y = percentile(__parcel.height_map, 75)
            road_y = self._maps.height_map.altitude(__parcel.entry_x, __parcel.entry_z)
            y = road_y
            if road_y > max_y:
                y = max_y
            elif road_y < min_y:
                y = min_y
            y += 1
            d = min(euclidean(__parcel.center, _.center) for _ in filter(lambda p: p.building_type.name == "ghost", self._parcels))
            h = int(MAX_HEIGHT * exp(-d / BUILDING_HEIGHT_SPREAD))
            __parcel.set_height(y, h)

        print("Defining parcels' and buildings' heights")
        map(define_parcels_heights, self._parcels)
        # translate all parcels to absolute coordinates
        map(lambda _parcel: _parcel.translate_to_absolute_coords(self.__origin), self._parcels)

    def generate(self, level, print_stack=False):
        self._road_network.generate(level)

        for parcel in self._parcels[1:]:  # type: Parcel
            parcel_biome = parcel.biome(level)
            palette = get_biome_palette(parcel_biome)
            if isinstance(parcel, MaskedParcel):
                obstacle_mask = self._maps.obstacle_map.box_obstacle(parcel.bounds)
                parcel.add_mask(obstacle_mask)
            if print_stack:
                parcel.generator.generate(level, parcel.height_map, palette)
            else:
                try:
                    parcel.generator.generate(level, parcel.height_map, palette)
                except Exception:
                    print("FAIL")

    @property
    def town_center(self):
        return self._center
