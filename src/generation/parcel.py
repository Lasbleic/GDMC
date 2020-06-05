from __future__ import division, print_function

from building_seeding import BuildingType
from utils import Point2D, bernouilli
from gen_utils import Direction, TransformBox, cardinal_directions
import map

MIN_PARCEL_SIZE = 7
MAX_PARCEL_AREA = 100
MIN_RATIO_SIDE = 7 / 11


class Parcel:

    def __init__(self, building_position, building_type, mc_map=None):
        # type: (Point2D, BuildingType, map.Maps) -> Parcel
        self.__center = building_position
        self.__building_type = building_type
        self.__map = mc_map  # type: map.Maps
        self.__entry_point = self.__center  # type: Point2D  # todo: compute this, input parameter
        self.__box = TransformBox((building_position.x, 0, building_position.z), (1, 1, 1))  # type: TransformBox
        if mc_map is not None:
            self.__compute_entry_point()
            self.__initialize_limits()

    def __compute_entry_point(self):
        road_net = self.__map.road_network
        # todo: gerer le cas des parcelles trop eloignees du reseau
        if road_net.is_accessible(self.__center):
            nearest_road_point = road_net.path_map[self.__center.z][self.__center.x][0]
            distance_threshold = MIN_PARCEL_SIZE + map.RoadNetwork.MAX_ROAD_LENGTH // 2
            if road_net.get_distance(self.__center) <= distance_threshold:
                # beyond this distance, no need to build a new road, parcel is considered accessible
                self.__entry_point = nearest_road_point
                return
            # compute the local direction of the road
            target_road_pt = road_net.path_map[self.__center.z][self.__center.x][distance_threshold]
        else:
            target_road_pt = Point2D(self.__map.width//2, self.__map.length//2)

        local_road_x = target_road_pt.x - self.__center.x
        local_road_z = target_road_pt.z - self.__center.z
        local_road_dir = Direction(dx=local_road_x, dz=local_road_z)

        # compute the secondary local direction of the road (orthogonal to the main one)
        # this direction determines what side of the parcel will be along the road
        resid_road_x = local_road_x if local_road_dir.z else 0  # note: resid for residual
        resid_road_z = local_road_z if local_road_dir.x else 0
        if resid_road_z * resid_road_x != 0:
            resid_road_dir = Direction(dx=resid_road_x, dz=resid_road_z)
        else:
            resid_road_dir = local_road_dir.rotate() if bernouilli() else -local_road_dir.rotate()
        self.__entry_point = self.__center + resid_road_dir.asPoint2D * map.RoadNetwork.MAX_ROAD_LENGTH

    def __initialize_limits(self):
        # build parcel box
        shifted_x = min(max(0, self.__center.x - (MIN_PARCEL_SIZE - 1) // 2), self.__map.width - MIN_PARCEL_SIZE)  # type: int
        shifted_z = min(max(0, self.__center.z - (MIN_PARCEL_SIZE - 1) // 2), self.__map.length - MIN_PARCEL_SIZE)  # type: int
        origin = (shifted_x, self.__map.height_map[shifted_x, shifted_z], shifted_z)
        size = (MIN_PARCEL_SIZE, 1, MIN_PARCEL_SIZE)
        self.__box = TransformBox(origin, size)

    def expand(self, direction):
        # type: (Direction) -> None
        assert self.is_expendable(direction)  # trust the user
        self.__box.expand(direction)
        # mark parcel points on obstacle map
        self.__map.obstacle_map.map[self.__box.minz:self.__box.maxz, self.__box.minx + self.__box.maxx] = False

    def is_expendable(self, direction=None):
        # type: (Direction or None) -> bool
        if self.__map is None:
            return False
        if direction is None:
            for direction in cardinal_directions():
                if self.is_expendable(direction):
                    return True
            return False
        else:
            expanded = self.__box.expand(direction)
            obstacle = self.__map.obstacle_map
            # todo: add possibility to truncate road leading to this parcel
            no_obstacle = obstacle.map[expanded.minz:expanded.maxz, expanded.minx:expanded.maxx].all()
            valid_sizes = expanded.surface <= MAX_PARCEL_AREA
            valid_ratio = MIN_RATIO_SIDE <= expanded.length / expanded.width <= 1/MIN_RATIO_SIDE
            max_x, max_z = self.__map.width, self.__map.length
            valid_coord = (0 <= expanded.minx < expanded.maxx <= max_x) and (0 <= expanded.minz < expanded.maxz <= max_z)
            return no_obstacle and valid_sizes and valid_ratio and valid_coord

    def translate_to_absolute_coords(self, origin):
        self.__box.translate(dx=origin.x, dz=origin.z)

    @property
    def entry_x(self):
        return self.__entry_point.x

    @property
    def entry_z(self):
        return self.__entry_point.z

    @property
    def mean_x(self):
        return self.__center.x

    @property
    def mean_z(self):
        return self.__center.z

    @property
    def minx(self):
        return self.__box.minx

    @property
    def maxx(self):
        return self.__box.maxx

    @property
    def minz(self):
        return self.__box.minz

    @property
    def maxz(self):
        return self.__box.maxz

    @property
    def generator(self):
        return self.__building_type.new_instance(self.__box)

    @property
    def height_map(self):
        return self.__map.height_map[self.minx:self.maxx, self.minz:self.maxz]

    @property
    def center(self):
        return self.__center

    @property
    def entry_point(self):
        return self.__entry_point

    @property
    def building_type(self):
        return self.__building_type

    @property
    def width(self):
        return self.__box.width

    @property
    def length(self):
        return self.__box.length
