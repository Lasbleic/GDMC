from __future__ import division

import logging
from random import randint
from numpy.random import geometric, normal
from building_seeding import BuildingPool, house_type
from pymclevel import BoundingBox
from road_network import RoadNetwork, Point2D
from utils import bernouilli, euclidean

mean_road_covered_surface = 64  # to compute number of roads, max 1 external connexion per 1/64 of the settlement size
settlement_access_dist = 12  # maximum distance from settlement center to road net


class FlatSettlement:
    """
    Intermediate project: generate a realistic village on a flat terrain
    """

    def __init__(self, box):
        # type: (BoundingBox) -> FlatSettlement
        self.limits = box
        self.road_network = RoadNetwork(box.width, box.length)
        surface = box.width * box.length
        self.building_pool = BuildingPool(surface)
        self._center = None

    def __random_border_point(self):
        # type: () -> Point2D
        width, length = self.limits.width, self.limits.length
        # random draw to decide on what side the border will be. Favors larger sides
        if bernouilli(width / (width + length)):
            # border point along x border
            x = 0 if bernouilli() else self.limits.width - 1
            z = randint(0, length - 1)
        else:
            # border point along z border
            x = randint(0, width - 1)
            z = 0 if bernouilli() else self.limits.length - 1
        return Point2D(x, z)

    def __init_road_network(self):
        out_connections = [self.__random_border_point()]
        max_road_count = min(self.limits.width, self.limits.length) // mean_road_covered_surface
        logging.debug('Max road count: {}'.format(max_road_count))
        road_count = min(geometric(min(1, 1./max_road_count)), max_road_count*3//2)
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
            if road_id == 0:
                self.road_network.find_road(out_connections[0], out_connections[1])
            else:
                self.road_network.connect_to_network(out_connections[-1])

    def init(self):
        self.__init_road_network()
        print('road placement done')
        self.__init_town_center()

    def generate(self, level):
        # todo: replace this
        # crop_town = crop_type.new_instance(self.limits)
        # crop_town.generate(level)

        single_house_town = house_type.new_instance(self.limits)
        single_house_town.generate(level)

    def __init_town_center(self):
        while True:
            mean_x = (self.limits.minx + self.limits.maxx) / 2
            dx = normal(mean_x, self.limits.width / 6)
            dx = int(min(self.limits.maxx, max(self.limits.minx, dx)))

            mean_z = (self.limits.minz + self.limits.maxz) / 2
            dz = normal(mean_z, self.limits.width / 6)
            dz = int(min(self.limits.maxz, max(self.limits.minz, dz)))

            random_center = Point2D(dx, dz)
            distance = self.road_network.get_distance(random_center)
            if distance <= settlement_access_dist:
                self._center = random_center
                logging.debug('Settlement center placed @{}, {}m away from road'.format(str(random_center), distance))
                break

    @property
    def town_center(self):
        return self._center
