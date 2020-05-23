from __future__ import division
from random import randint
from numpy.random import geometric

from building_pool import BuildingPool, crop_type, house_type
from road_network import RoadNetwork, Point2D
from utils import bernouilli, euclidean


class FlatSettlement:
    """
    Intermediate project: generate a realistic village on a flat terrain
    """

    def __init__(self, box):
        self.limits = box
        self.road_network = RoadNetwork(box.width, box.length)
        surface = box.width * box.length
        self.building_pool = BuildingPool(surface)

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
        print('First border point @{}'.format(str(out_connections[0])))
        road_count = geometric(.5)  # todo: make this probability dependant of the settlement surface ?
        print('New settlement will have {} roads B)'.format(road_count))

        for road_id in xrange(road_count):
            min_distance_to_roads = min(self.limits.width, self.limits.length) * 1. / (road_id+1)  # todo: calibrate
            print('Generating road #{}'.format(road_id+1))
            # generate new border point far enough from existing points
            while True:
                new_road_point = self.__random_border_point()
                distances = [euclidean(road_point, new_road_point) for road_point in out_connections]
                if min(distances) > min_distance_to_roads:
                    out_connections.append(new_road_point)
                    print('\tSettled on border point @{}'.format(str(new_road_point)))
                    break

            # update road network
            if road_id == 0:
                self.road_network.find_road(out_connections[0], out_connections[1])
            else:
                self.road_network.connect_to_network(out_connections[-1])

    def init(self):
        self.__init_road_network()

    def generate(self, level):
        # todo: replace this
        # crop_town = crop_type.new_instance(self.limits)
        # crop_town.generate(level)

        single_house_town = house_type.new_instance(self.limits)
        single_house_town.generate(level)


