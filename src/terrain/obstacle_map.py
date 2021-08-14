import numpy as np

from utils import *
from .map import Map


class ObstacleMap(Map, metaclass=Singleton):

    def __init__(self, values: np.ndarray = None, maps=None):
        super().__init__(values)
        self.__all_maps = maps
        self.__hidden_obstacles = []

    @classmethod
    def from_terrain(cls, terrain):
        height_map: np.ndarray = terrain.height_map[:]
        avg_height: float = np.percentile(height_map, 50)
        reachable: np.ndarray = (height_map == avg_height)
        points_to_explore = {(_[0], _[1]) for _ in np.argwhere(reachable).tolist()}
        explored_points = set()
        while points_to_explore:
            point = points_to_explore.pop()
            for dx, dz in map(lambda direction: (direction.x, direction.z), cardinal_directions()):
                neighbour = point[0] + dx, point[1] + dz

                if neighbour in explored_points:
                    continue
                try:
                    if abs(height_map[point] - height_map[neighbour]) <= 1:
                        reachable[neighbour] = True
                        points_to_explore.add(neighbour)
                    else:
                        explored_points.add(neighbour)
                except IndexError:
                    continue
            explored_points.add(point)

        # reachable = True -> 0, unreachable = False -> 1
        obstacle_from_reachability = (~reachable).astype(int)
        obs = cls(obstacle_from_reachability, terrain)
        from terrain.structure_detection import StructureDetector
        for parcel in StructureDetector(terrain).get_structure_parcels():
            obs.add_obstacle(*parcel.obstacle(2))
        return obs

    def add_obstacle(self, point, mask=None):
        # type: (Point, ndarray) -> None
        """
        Main function to add an obstacle
        Parameters
        ----------
        point lower bounds of the rectangular obstacle surface
        mask boolean array indicating obstacle points in the obstacle surface
        Returns None
        -------
        """
        if mask is None:
            mask = full((1, 1), True)
        self.__add_obstacle(point, mask, 1)

    def is_accessible(self, point):
        # type: (Point) -> bool
        return self[point.x, point.z] == 0

    def __set_obstacle(self, x, z, cost=1):
        self._values[x, z] += cost

    def __add_obstacle(self, point, mask, cost):
        for dx, dz in product(range(mask.shape[0]), range(mask.shape[1])):
            p = point + Point(dx, dz)
            if self.__all_maps.in_limits(p, False) and mask[dx, dz]:
                self.__set_obstacle(p.x, p.z, cost)

    def hide_obstacle(self, point, mask=None, store_obstacle=True):
        """Hide an obstacle on the map, if store_obstacle, the obstacle will be stored in self._hidden_obstacles
        and later added again with reveal_obstacles()"""
        if mask is None:
            mask = full((1, 1), True)
        self.__add_obstacle(point, mask, -1)
        if store_obstacle:
            self.__hidden_obstacles.append((Point(point.x, point.z), array(mask)))

    def reveal_obstacles(self):
        """Adds all hidden obstacles"""
        while self.__hidden_obstacles:
            p, mask = self.__hidden_obstacles.pop()
            self.__add_obstacle(p, mask, 1)

    def add_network_to_obstacle_map(self):
        from terrain.road_network import RoadNetwork
        if self.__all_maps is not None:
            network = self.__all_maps.road_network  # type: RoadNetwork
            for x0, z0 in product(range(self.width), range(self.length)):
                if network.is_road(x0, z0):
                    # build a circular obstacle of designated width around road point
                    margin = network.get_road_width(x0, z0) / 2 - .5
                    for x1, z1 in product(sym_range(x0, margin, self.width), sym_range(z0, margin, self.length)):
                        if not self[x1, z1]:
                            self.__set_obstacle(x1, z1)

    def box_obstacle(self, box):
        matrix = self[box.minx: box.maxx, box.minz:box.maxz]
        return matrix <= 1
