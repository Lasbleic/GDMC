from __future__ import division, print_function

from building_seeding import BuildingType
from map.maps import Maps
from utils import Point2D
from gen_utils import Direction, TransformBox, cardinal_directions

MIN_PARCEL_SIZE = 7
MAX_PARCEL_AREA = 100
MIN_RATIO_SIDE = 7 / 11


class Parcel:

    def __init__(self, building_type, building_position, mc_map=None):
        # type: (BuildingType, Point2D, Maps) -> Parcel
        self.__center = building_position
        self.__box = TransformBox((0, 0, 0), (0, 0, 0))  # type: TransformBox
        self.__map = mc_map  # type: Maps
        self.__entry_point = Point2D(0, 0)  # type: Point2D  # todo: compute this, input parameter
        self.__building_type = building_type

        # build parcel box
        shifted_x = max(0, building_position.x - (MIN_PARCEL_SIZE - 1) / 2)
        shifted_z = max(0, building_position.z - (MIN_PARCEL_SIZE - 1) / 2)
        origin = (shifted_x, mc_map.height_map[shifted_x, shifted_z], shifted_z)
        size = (MIN_PARCEL_SIZE, 1, MIN_PARCEL_SIZE)
        self.__box = TransformBox(origin, size)

        # todo: build entrance

    def expand(self, direction):
        # type: (Direction) -> None
        assert self.is_expendable(direction)  # trust the user
        self.__box.expand(direction)
        # mark parcel points on obstacle map
        self.__map.obstacle_map.map[self.__box.minz:self.__box.maxz, self.__box.minx + self.__box.maxx] = False

    def is_expendable(self, direction=None):
        # type: (Direction or None) -> bool
        if direction is None:
            for direction in cardinal_directions():
                if not self.is_expendable(direction):
                    return False
            return True
        else:
            expanded = self.__box.expand(direction)
            obstacle = self.__map.obstacle_map
            # todo: add possibility to truncate road leading to this parcel
            no_obstacle = obstacle[expanded.minx:expanded.maxx, expanded.minz:expanded.maxz].all()
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
    def minz(self):
        return self.__box.minz
