from __future__ import division, print_function

from utils import Point2D
from enum import Enum
from gen_utils import Direction, TransformBox, cardinal_directions

MIN_PARCEL_SIZE = 7
MAX_PARCEL_AREA = 100
MIN_RATIO_SIDE = 7 / 11


# todo: use generation.Direction instead
class Direction(Enum):
    Top = "top"
    Bottom = "bottom"
    Right = "right"
    Left = "left"


class Parcel:

    def __init__(self, building_position, mc_map=None):
        # type: (Point2D, Maps) -> Parcel
        self.__box = TransformBox((0, 0, 0), (0, 0, 0))  # type: TransformBox  # todo: use this instead of Point2D style
        self.__center = building_position
        shifted_x = max(0, building_position.x - (MIN_PARCEL_SIZE - 1) / 2)
        shifted_z = max(0, building_position.z - (MIN_PARCEL_SIZE - 1) / 2)
        self.__origin = Point2D(shifted_x, shifted_z)
        self.width = MIN_PARCEL_SIZE
        self.length = MIN_PARCEL_SIZE
        self.__map = mc_map
        self.__entry_point = Point2D(0, 0)  # type: Point2D  # todo: compute this, input parameter

    def __expand_top(self):
        if self.__origin.z > 0:
            self.__origin.z -= 1
            self.length += 1
        self.__map.obstacle_map.map[self.__origin.z, self.__origin.x:self.__origin.x + self.width] = False

    def __expand_bottom(self):
        if self.__origin.x < self.__map.height:
            self.length += 1
        self.__map.obstacle_map.map[self.__origin.z + self.length - 1, self.__origin.x:self.__origin.x + self.width] = False

    def __expand_left(self):
        if self.__origin.z > 0:
            self.__origin.x -= 1
            self.width += 1
        self.__map.obstacle_map.map[self.__origin.z:self.__origin.z + self.length, self.__origin.x] = False

    def __expand_right(self):
        if self.__origin.x < self.__map.width:
            self.width += 1
        self.__map.obstacle_map.map[self.__origin.z:self.__origin.z + self.length, self.__origin.x + self.width - 1] = False

    def expand(self, direction):
        # type: (Direction) -> None
        # todo: use TransformBox.expand
        if direction == Direction.Top:
            self.__expand_top()
        elif direction == Direction.Bottom:
            self.__expand_bottom()
        elif direction == Direction.Left:
            self.__expand_left()
        elif direction == Direction.Right:
            self.__expand_right()

    def is_expendable(self, obstacle_map, direction=None):
        # type: (ObstacleMap, Direction or None) -> bool
        if direction is None:
            for direction in cardinal_directions():
                if not self.is_expendable(obstacle_map, direction):
                    return False
            return True
        else:
            expanded = self.__box.expand(direction)
            # todo: add possibility to truncate
            no_obstacle = obstacle_map[expanded.minx:expanded.maxx, expanded.minz:expanded.maxz].all()
            valid_sizes = expanded.surface <= MAX_PARCEL_AREA
            valid_ratio = MIN_RATIO_SIDE <= expanded.length / expanded.width <= 1/MIN_RATIO_SIDE
            return no_obstacle and valid_sizes and valid_ratio

    def translate_to_absolute_coords(self, origin):
        self.__box.translate(dx=origin.x, dz=origin.z)

    @property
    def entry_x(self):
        return self.__entry_point.x

    @property
    def entry_z(self):
        return self.__entry_point.z

    @property
    def minx(self):
        return self.__origin.x

    @property
    def minz(self):
        return self.__origin.z
