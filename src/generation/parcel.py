from __future__ import division, print_function

from utils import Point2D
from enum import Enum
from map.maps import Maps

MIN_PARCEL_SIZE = 7
MAX_PARCEL_AREA = 100
MIN_RATIO_SIDE = 7 / 11


class Direction(Enum):
    Top = "top"
    Bottom = "bottom"
    Right = "right"
    Left = "left"


class Parcel:

    def __init__(self, building_position, mc_map=None):
        # type: (Point2D) -> Parcel
        self.__center = building_position
        shifted_x = max(0,building_position.x - (MIN_PARCEL_SIZE - 1) / 2)
        shifted_z = max(0, building_position.z - (MIN_PARCEL_SIZE - 1) / 2)
        self.origin = Point2D(shifted_x, shifted_z)
        self.width = MIN_PARCEL_SIZE
        self.height = MIN_PARCEL_SIZE
        self.__map = mc_map

    def __expand_top(self):
        if self.origin.z > 0:
            self.origin.z -= 1
            self.height += 1
        # TODO: update obstacle_map

    def __expand_bottom(self):
        # TODO: if self.__origin.x < self.__map.height
        self.height += 1
        # TODO: update obstacle_map

    def __expand_left(self):
        if self.origin.z > 0:
            self.origin.x -= 1
            self.width += 1
        # TODO: update obstacle_map

    def __expand_right(self):
        # TODO: if self.__origin.x < self.__map.width
        self.width += 1
        # TODO: update obstacle_map

    def expand(self, direction):
        # type: (Direction) -> void
        if direction == Direction.Top:
            self.__expand_top()
        elif direction == Direction.Bottom:
            self.__expand_bottom()
        elif direction == Direction.Left:
            self.__expand_left()
        elif direction == Direction.Right:
            self.__expand_right()
