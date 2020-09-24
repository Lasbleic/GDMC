from __future__ import division, print_function

from random import randint

from building_seeding.building_pool import BuildingType
from generation.generators import Generator, MaskedGenerator
from parameters import *
from building_encyclopedia import BUILDING_ENCYCLOPEDIA
from pymclevel.biome_types import biome_types
from utils import *
import terrain_map

ENTRY_POINT_MARGIN = (MIN_PARCEL_SIDE + MAX_ROAD_WIDTH) // 2


class Parcel:

    max_surfaces = BUILDING_ENCYCLOPEDIA["Flat_scenario"]["MaxSurface"]

    def __init__(self, seed, building_type, mc_map=None):
        # type: (Point2D, BuildingType, terrain_map.Maps) -> Parcel
        self._center = seed
        self._building_type = building_type
        self._map = mc_map  # type: terrain_map.Maps
        self._entry_point = self._center  # type: Point2D
        self._relative_box = TransformBox((seed.x, 0, seed.z),
                                          (1, 1, 1))  # type: TransformBox
        self._box = None  # type: TransformBox
        if mc_map is not None:
            self.__initialize_limits()
            self.__compute_entry_point()

    def __eq__(self, other):
        if not isinstance(other, Parcel):
            return False
        return self.center == other.center and self.building_type == other.building_type

    def __str__(self):
        return "{} parcel at {}".format(self.building_type.name, self.center)

    def __compute_entry_point(self):
        road_net = self._map.road_network
        if road_net.is_accessible(self._center):
            path = road_net.path_map[self._center.x, self._center.z]
            nearest_road_point = path[0] if path else self.center
            distance_threshold = MIN_PARCEL_SIDE + MAX_ROAD_WIDTH // 2
            if len(path) <= distance_threshold:
                # beyond this distance, no need to build a new road, parcel is considered accessible
                self._entry_point = nearest_road_point
                return
            # compute the local direction of the road
            index = max(0, len(path) - distance_threshold)
            target_road_pt = path[index]
        else:
            target_road_pt = Point2D(self._map.width // 2, self._map.length // 2)

        local_road_x = target_road_pt.x - self._center.x
        local_road_z = target_road_pt.z - self._center.z
        local_road_dir = Direction(dx=local_road_x, dz=local_road_z)

        # compute the secondary local direction of the road (orthogonal to the main one)
        # this direction determines what side of the parcel will be along the road
        resid_road_x = local_road_x if local_road_dir.z else 0  # note: resid for residual
        resid_road_z = local_road_z if local_road_dir.x else 0
        if resid_road_z != 0 or resid_road_x != 0:
            resid_road_dir = Direction(dx=resid_road_x, dz=resid_road_z)
        else:
            resid_road_dir = local_road_dir.rotate() if bernouilli() else -local_road_dir.rotate()
        self._entry_point = self._center + resid_road_dir.asPoint2D * ENTRY_POINT_MARGIN
        if not (0 <= self.entry_x < self._map.width and 0 <= self.entry_z < self._map.length):
            self._entry_point = target_road_pt

    def __initialize_limits(self):
        # build parcel box
        margin = MIN_PARCEL_SIDE // 2
        shifted_x = pos_bound(self._center.x - margin, self._map.width - MIN_PARCEL_SIDE)  # type: int
        shifted_z = pos_bound(self._center.z - margin, self._map.length - MIN_PARCEL_SIDE)  # type:int
        origin = (shifted_x, self._map.height_map.altitude(shifted_x, shifted_z), shifted_z)
        size = (MIN_PARCEL_SIDE, 1, MIN_PARCEL_SIDE)
        self._relative_box = TransformBox(origin, size)
        # in cases where the parcel hits the limits, does not change anything otherwise
        self._center = Point2D(shifted_x + margin, shifted_z + margin)

    def expand(self, direction):
        # type: (Direction) -> None
        assert self.is_expendable(direction)  # trust the user
        self._map.obstacle_map.unmark_parcel(self, 1)
        self._relative_box.expand(direction, inplace=True)
        # mark parcel points on obstacle terrain_map
        self._map.obstacle_map.add_parcel_to_obstacle_map(self, 1)

    def is_expendable(self, direction=None):
        # type: (Direction or None) -> bool
        if self._map is None:
            return False
        if direction is None:
            for direction in cardinal_directions():
                if self.is_expendable(direction):
                    return True
            return False
        else:
            # try:
            expanded = self._relative_box.expand(direction)  # expanded parcel
            obstacle = self._map.obstacle_map  # type: terrain_map.ObstacleMap  # obstacle terrain_map
            ext = expanded - self._relative_box  # extended part of the expanded parcel

            if ext.minx < 0 or ext.minz < 0 or ext.maxx >= obstacle.width or ext.maxz >= obstacle.length:
                return False

            obstacle.unmark_parcel(self, 1)
            no_obstacle = obstacle[ext.minx:ext.maxx, ext.minz:ext.maxz].all()
            h = self._map.height_map.box_height(expanded, True)
            flat_extend = (h.max() - h.min()) / min(expanded.width, expanded.length) <= 0.7
            obstacle.add_parcel_to_obstacle_map(self, 1)
            # except IndexError:
            #     obstacle.add_parcel_to_obstacle_map(self, 1)
            #     return False
            # except ValueError:
            #     print("Found empty array when trying to extend {} parcel, ({}, {})".format(self.building_type, self.width, self.length))
            #     return False
            valid_sizes = expanded.surface <= self.max_surfaces[self.building_type.name]
            valid_ratio = MIN_RATIO_SIDE <= expanded.length / expanded.width <= 1 / MIN_RATIO_SIDE
            return no_obstacle and valid_sizes and valid_ratio and flat_extend

    def translate_to_absolute_coords(self, origin):
        self._box = TransformBox(self._relative_box)
        self._box.translate(dx=origin.x, dz=origin.z, inplace=True)
        self._entry_point += Point2D(origin.x, origin.z)

    @property
    def entry_x(self):
        return self._entry_point.x

    @property
    def entry_z(self):
        return self._entry_point.z

    @property
    def mean_x(self):
        return self._center.x

    @property
    def mean_z(self):
        return self._center.z

    @property
    def minx(self):
        return self._relative_box.minx

    @property
    def maxx(self):
        return self._relative_box.maxx

    @property
    def minz(self):
        return self._relative_box.minz

    @property
    def maxz(self):
        return self._relative_box.maxz

    @property
    def generator(self):
        gen = self._building_type.new_instance(self._box)  # type: Generator
        gen._entry_point = self._entry_point
        return gen

    @property
    def height_map(self):
        box = self._relative_box
        return self._map.height_map.box_height(box, True)

    @property
    def center(self):
        return self._center

    @property
    def entry_point(self):
        return self._entry_point

    @property
    def building_type(self):
        return self._building_type

    @property
    def width(self):
        return self._relative_box.width

    @property
    def length(self):
        return self._relative_box.length

    @property
    def bounds(self):
        return self._relative_box

    def set_height(self, y, h):
        self._relative_box.translate(dy=y - self._relative_box.miny, inplace=True)
        for _ in range(h - 1):
            self._relative_box.expand(Top, inplace=True)

    def move_center(self, new_seed):
        # type: (Point2D) -> None
        self._map.obstacle_map.unmark_parcel(self, 1)
        move_x = new_seed.x - self.center.x
        move_z = new_seed.z - self.center.z
        self._relative_box.translate(dx=move_x, dz=move_z, inplace=True)
        if self._box is not None:
            self._box.translate(dx=move_x, dz=move_z, inplace=True)
        self._center = new_seed
        self._entry_point += Point2D(move_x, move_z)
        self._map.obstacle_map.add_parcel_to_obstacle_map(self, 1)  # todo: also update interest maps

    def biome(self, level):
        x = randint(self._box.minx, self._box.maxx - 1)
        z = randint(self._box.minz, self._box.maxz - 1)
        biome = biome_types[level.getChunk(x // 16, z // 16).Biomes[x & 15, z & 15]]
        return biome


class MaskedParcel(Parcel):

    def __init__(self, origin, mask, building_type, mc_map=None):
        # type: (Point2D, array, BuildingType, Maps) -> None
        seed = origin + Point2D(mask.shape[0] // 2, mask.shape[1] // 2)
        Parcel.__init__(self, seed, building_type, mc_map)
        # for these parcels, relative box is immutable
        self._relative_box = TransformBox((origin.x, 0, origin.z), (mask.shape[0], 1, mask.shape[1]))
        self.__mask = mask

    def is_expendable(self, direction=None):
        return False

    @property
    def generator(self):
        return self.building_type.generator(self._box, self.__mask, self.entry_point)  # type: MaskedGenerator

    def add_mask(self, new_mask):
        assert self.__mask.shape == new_mask.shape
        self.__mask = self.__mask & new_mask

    def move_center(self, new_seed):
        pass
