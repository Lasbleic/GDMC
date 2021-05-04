from __future__ import division, print_function

from random import randint

from building_seeding.building_pool import BuildingType
from generation.generators import Generator, MaskedGenerator
from parameters import *
from building_seeding.building_encyclopedia import BUILDING_ENCYCLOPEDIA
# from pymclevel.biome_types import biome_types
from terrain import ObstacleMap, TerrainMaps
from utils import *
import terrain

ENTRY_POINT_MARGIN = (MIN_PARCEL_SIDE + MAX_ROAD_WIDTH) // 2


class Parcel:

    max_surfaces = BUILDING_ENCYCLOPEDIA["Flat_scenario"]["MaxSurface"]

    def __init__(self, seed, building_type, mc_map):
        # type: (Point, BuildingType, terrain.TerrainMaps) -> Parcel
        self._center = seed
        self.building_type: BuildingType = building_type
        self._map = mc_map  # type: terrain.TerrainMaps
        self._entry_point = seed if building_type is BuildingType.ghost else self.__compute_entry_point()
        self._relative_box = None  # type: TransformBox
        self._box = None  # type: TransformBox
        self._mask = None
        self.__initialize_limits()

    def __eq__(self, other):
        if not isinstance(other, Parcel):
            return False
        return self.center == other.center and self.building_type == other.building_type

    def __str__(self):
        return "{} parcel at {}".format(self.building_type.name, self.center)

    def __compute_entry_point(self):
        road_net = self._map.road_network

        # If path from road_net to seed has already been computed, project the entry point on this path
        if road_net.is_accessible(self._center):
            path = road_net.path_map[self._center.x, self._center.z]  # path[-1] == seed
            distance_threshold = AVERAGE_PARCEL_SIZE + MAX_ROAD_WIDTH // 2
            if len(path) <= distance_threshold:
                # beyond this distance, no need to build a new road, parcel is considered accessible
                return path[0] if len(path) else self._center
            else:
                # len(path) > distance_threshold, compute the local direction of the road
                index = len(path) - distance_threshold
                target_road_pt = path[index]
        else:
            # have no clue where the nearest road is, aim for the middle of the map
            target_road_pt = Point(self._map.width // 2, self._map.length // 2)

        local_road_x = target_road_pt.x - self._center.x
        local_road_z = target_road_pt.z - self._center.z
        local_road_dir = Direction.of(dx=local_road_x, dz=local_road_z)

        # compute the secondary local direction of the road (orthogonal to the main one)
        # this direction determines what side of the parcel will be along the road
        resid_road_x = local_road_x if local_road_dir.z else 0  # note: resid for residual
        resid_road_z = local_road_z if local_road_dir.x else 0
        if resid_road_z != 0 or resid_road_x != 0:
            resid_road_dir = Direction.of(dx=resid_road_x, dz=resid_road_z)
        else:
            resid_road_dir = local_road_dir.rotate() if bernouilli() else -local_road_dir.rotate()
        entry_point = self._center + resid_road_dir.value * ENTRY_POINT_MARGIN
        if not (0 <= entry_point.x < self._map.width and 0 <= entry_point.z < self._map.length):
            entry_point = target_road_pt
        return entry_point

    def __initialize_limits(self):
        # build parcel box
        margin = AVERAGE_PARCEL_SIZE // 2
        assert margin > (MIN_PARCEL_SIDE // 2)
        shifted_x = max(margin, pos_bound(self._center.x - margin, self._map.width - margin))  # type: int
        shifted_z = max(margin, pos_bound(self._center.z - margin, self._map.length - margin))  # type:int
        self._center = Point(shifted_x + margin, shifted_z + margin)

        origin = (self.center.x - (MIN_PARCEL_SIDE // 2), 0, self.center.z - (MIN_PARCEL_SIDE // 2))
        size = (MIN_PARCEL_SIDE, 1, MIN_PARCEL_SIDE)
        self._relative_box = TransformBox(origin, size)
        self._mask = full((self.width, self.length), True)
        # in cases where the parcel hits the limits, does not change anything otherwise

    def expand(self, direction):
        # type: (Direction) -> None
        assert self.is_expendable(direction)  # trust the user
        self._map.obstacle_map.hide_obstacle(self.origin, self._mask, False)
        self._relative_box.expand(direction, inplace=True)
        self._mask = full((self.width, self.length), True)
        # mark parcel points on obstacle terrain
        self.mark_as_obstacle(self._map.obstacle_map)

    def is_expendable(self, direction=None):
        # type: (Direction or None) -> bool
        if self._map is None:
            return False
        if direction is None:
            return any(self.is_expendable(direction) for direction in cardinal_directions(False))
        else:
            # try:
            expanded = self._relative_box.expand(direction)  # expanded parcel
            obstacle = self._map.obstacle_map  # type: terrain.ObstacleMap  # obstacle terrain
            ext = expanded - self._relative_box  # extended part of the expanded parcel

            if ext.minx < 0 or ext.minz < 0 or ext.maxx >= obstacle.width or ext.maxz >= obstacle.length:
                return False

            obstacle.hide_obstacle(self.origin, self._mask)
            no_obstacle = obstacle[ext.minx:ext.maxx, ext.minz:ext.maxz].all()
            # h = self._map.height_map.box_height(expanded, True)
            # flat_extend = (h.max() - h.min()) / min(expanded.width, expanded.length) <= 0.7
            flat_extend = True
            obstacle.reveal_obstacles()
            valid_sizes = expanded.surface <= self.max_surfaces[self.building_type.name]
            valid_ratio = MIN_RATIO_SIDE <= expanded.length / expanded.width <= 1 / MIN_RATIO_SIDE
            return no_obstacle and valid_sizes and valid_ratio and flat_extend

    def translate_to_absolute_coords(self, origin):
        self._box = TransformBox(self._relative_box)
        self._box.translate(dx=origin.x, dz=origin.z, inplace=True)
        self._entry_point += Point(origin.x, origin.z)

    def mark_as_obstacle(self, obstacle_map, margin=0):
        # type: (ObstacleMap) -> None
        if margin > 0:
            point = self.origin - Point(margin, margin)
            mask = full((self.width + 2*margin, self.length + 2*margin), True)
            obstacle_map.add_obstacle(point, mask)
        else:
            obstacle_map.add_obstacle(self.origin, self._mask)

    @property
    def entry_x(self):
        return self.entry_point.x

    @property
    def entry_z(self):
        return self.entry_point.z

    @property
    def origin(self):
        return Point(self.minx, self.minz)

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
        gen = self.building_type.new_instance(self._box)  # type: Generator
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
    def absolute_mean(self):
        return Point(self._box.minx + self.width//2, self._box.minz + self.length//2)

    @property
    def entry_point(self):
        return self._entry_point

    @property
    def width(self):
        return self._relative_box.width

    @property
    def length(self):
        return self._relative_box.length

    @property
    def bounds(self):
        return self._relative_box

    @property
    def mask(self):
        return self._mask

    def set_height(self, y, h):
        self._relative_box.translate(dy=y - self._relative_box.miny, inplace=True)
        for _ in range(h - 1):
            self._relative_box.expand(Direction.Top, inplace=True)

    def move_center(self, new_seed):
        # type: (Point) -> None
        self._map.obstacle_map.hide_obstacle(self.origin, self._mask, False)
        move_x = new_seed.x - self.center.x
        move_z = new_seed.z - self.center.z
        self._relative_box.translate(dx=move_x, dz=move_z, inplace=True)
        if self._box is not None:
            self._box.translate(dx=move_x, dz=move_z, inplace=True)
        self._center = new_seed
        self._entry_point += Point(move_x, move_z)
        self.mark_as_obstacle(self._map.obstacle_map)  # todo: also update interest maps (sociability)

    def biome(self, level: TerrainMaps):
        b = self._relative_box
        x = randint(b.minx, b.maxx - 1)
        z = randint(b.minz, b.maxz - 1)
        return level.biome.getBiome(level.biome[x, z])


class MaskedParcel(Parcel):

    def __init__(self, origin, building_type, mc_map=None, mask=None):
        # type: (Point, BuildingType, Maps, array) -> None
        seed = origin + Point(mask.shape[0] // 2, mask.shape[1] // 2) if mask is not None else origin
        Parcel.__init__(self, seed, building_type, mc_map)

        if mask is not None:
            # for these parcels, relative box is immutable
            self._relative_box = TransformBox((origin.x, 0, origin.z), (mask.shape[0], 1, mask.shape[1]))
            self._mask = mask

    def __valid_extended_point(self, x, z, direction):
        """Can we extend the parcel to the point x, z from a given direction"""
        obstacle = self._map.obstacle_map
        point = Point(x, z)
        source = point - direction.value  # type: Point
        return obstacle.is_accessible(source) and obstacle.is_accessible(direction)

    def is_expendable(self, direction=None):
        # type: (Direction or None) -> bool
        if Parcel.is_expendable(self, direction):
            return True
        elif direction is None:
            return any(self.is_expendable(_) for _ in cardinal_directions(False))
        else:
            """
            Will basically try to extend the parcel's mask
            """
            obstacle = self._map.obstacle_map  # type: terrain.ObstacleMap  # obstacle terrain
            expanded = self._relative_box.expand(direction)  # expanded parcel
            ext = expanded - self._relative_box  # extended part of the expanded parcel

            out_limits = ext.minx < 0 or ext.minz < 0 or ext.maxx >= obstacle.width or ext.maxz >= obstacle.length
            valid_sizes = expanded.surface <= self.max_surfaces[self.building_type.name]
            valid_ratio = MIN_RATIO_SIDE <= expanded.length / expanded.width <= 1 / MIN_RATIO_SIDE
            if out_limits or (not valid_sizes) or (not valid_ratio):
                return False

            assert ext.height == 1

            obstacle.hide_obstacle(self.origin, self._mask)
            validity = [self.__valid_extended_point(x, z, direction) for x, y, z in ext.positions]
            obstacle.reveal_obstacles()
            return sum(validity) >= len(validity) // 2

    def expand(self, direction):
        # type: (Direction) -> None

        if Parcel.is_expendable(self, direction):
            Parcel.expand(self, direction)
            return

        self._map.obstacle_map.hide_obstacle(self.origin, self._mask, False)

        # compute extended mask and mark it on the obstacle map
        ext = self._relative_box.expand(direction) - self._relative_box
        mask_extension = [self.__valid_extended_point(x, z, direction) for x, y, z in ext.positions]
        from numpy import insert
        index = {Direction.North: 0, Direction.East: self.width, Direction.South: self.length, Direction.West: 0}
        axis = {Direction.North: 1, Direction.East: 0, Direction.South: 1, Direction.West: 0}

        self._relative_box.expand(direction, inplace=True)
        self._mask = insert(self._mask, index[direction], array(mask_extension), axis=axis[direction])
        self.mark_as_obstacle(self._map.obstacle_map)

    @property
    def generator(self):
        try:
            return self.building_type.generator(self._box, self.entry_point, self._mask)  # type: MaskedGenerator
        except TypeError:
            gen = self.building_type.new_instance(self._box)  # type: Generator
            gen._entry_point = self._entry_point
            return gen

    def add_mask(self, new_mask):
        assert self._mask.shape == new_mask.shape
        self._mask = self._mask & new_mask

    def move_center(self, new_seed):
        pass
