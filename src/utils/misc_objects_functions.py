from math import sqrt
from os.path import realpath, sep
from random import random, shuffle
from typing import Iterable

from numpy import array, argmax

from pymclevel import BoundingBox, MCInfdevOldLevel, alphaMaterials as Block
from utilityFunctions import setBlock
from itertools import product


class Point2D:

    def __init__(self, x, z):
        self.x = x
        self.z = z

    def __str__(self):
        return "(x:" + str(self.x) + "; z:" + str(self.z) + ")"

    def __eq__(self, other):
        return other.x == self.x and other.z == self.z

    def __add__(self, other):
        assert isinstance(other, Point2D)
        return Point2D(self.x + other.x, self.z + other.z)

    def __sub__(self, other):
        assert isinstance(other, Point2D)
        return Point2D(self.x - other.x, self.z - other.z)

    def __mul__(self, other):
        if type(other) == int or type(other) == float:
            return Point2D(self.x * other, self.z * other)

        assert isinstance(other, Point2D)
        return Point2D(self.x * other.x, self.z * other.z)

    def dot(self, other):
        assert isinstance(other, Point2D)
        mult = self * other
        return mult.x + mult.z


def bernouilli(p=.5):
    # type: (float) -> bool
    return random() <= p


def euclidean(p1, p2):
    # type: (Point2D, Point2D) -> float
    return sqrt((p1.x - p2.x) ** 2 + (p1.z - p2.z) ** 2)


def get_project_path():
    this_path = realpath(__file__)
    proj_path = sep.join(this_path.split(sep)[:-2])
    return proj_path


class TransformBox(BoundingBox):
    """
    Adds class methods to the BoundingBox to transform the box's shape and position
    """

    def translate(self, dx=0, dy=0, dz=0, inplace=False):
        if inplace:
            self._origin += (dx, dy, dz)
            return self
        else:
            return TransformBox(self.origin + (dx, dy, dz), self.size)

    def split(self, dx=None, dy=None, dz=None):
        assert (dx is not None) ^ (dy is not None) ^ (dz is not None)
        if dx is not None:
            b0 = TransformBox(self.origin, (dx, self.height, self.length))
            b1 = TransformBox((self.origin + (dx, 0, 0)), (self.size - (dx, 0, 0)))
        elif dy is not None:
            b0 = TransformBox(self.origin, (self.width, dy, self.length))
            b1 = TransformBox((self.origin + (0, dy, 0)), (self.size - (0, dy, 0)))
        else:
            b0 = TransformBox(self.origin, (self.width, self.height, dz))
            b1 = TransformBox((self.origin + (0, 0, dz)), (self.size - (0, 0, dz)))
        return [b0, b1]

    def expand(self, dx_or_dir, dy=None, dz=None, inplace=False):
        # if isinstance(dx_or_dir, Direction):
        if dx_or_dir.__class__.__name__ == 'Direction':
            direction = dx_or_dir
            dpos = (min(direction.x, 0), min(direction.y, 0), min(direction.z, 0))
            dsize = (abs(direction.x), abs(direction.y), abs(direction.z))
            expanded_box = TransformBox(self.origin + dpos, self.size + dsize)
        else:
            expanded_box = TransformBox(BoundingBox.expand(self, dx_or_dir, dy, dz))
        return self.copy_from(expanded_box) if inplace else expanded_box

    def enlarge(self, direction, reverse=False, inplace=False):
        # type: (Direction, bool, bool) -> TransformBox
        """
        For example, TransformBox((0, 0, 0), (1, 1, 1)).expand(East) -> TransformBox((-1, 0, 0), (3, 1, 1))
        """
        copy_box = TransformBox(self.origin, self.size)
        dx, dz = 1 - abs(direction.x), 1 - abs(direction.z)
        if reverse:
            dx, dz = -dx, -dz
        copy_box = copy_box.expand(dx, 0, dz)
        if inplace:
            self.copy_from(copy_box)
        else:
            return copy_box

    def copy_from(self, other):
        self._origin = other.origin
        self._size = other.size
        return self

    def __sub__(self, other):
        # type: (TransformBox) -> TransformBox
        """
        exclusion operator, only works if self is an extension of other in a single direction
        should work well with self.expand(Direction), eg box.expand(South) - box -> southern extension of box
        todo: test this
        """
        same_coords = [self.minx == other.minx, self.maxx == other.maxx, self.minz == other.minz,
                       self.maxz == other.maxz]
        assert sum(same_coords) == 3  # only one of the 4 bool should be False
        if not same_coords[0]:  # supposedly self.minx < other.minx
            return self.split(dx=1)[0]
        elif not same_coords[1]:  # supposedly self.minx < other.minx
            return self.split(dx=self.width - 1)[1]
        elif not same_coords[2]:  # supposedly self.minx < other.minx
            return self.split(dz=1)[0]
        else:  # supposedly self.minx < other.minx
            return self.split(dz=self.length - 1)[1]

    @property
    def surface(self):
        return self.width * self.length


class Direction:
    """
    Custom direction class
    """

    __known_dirs = {'0 0 1': 'South', '0 1 0': 'Top', '1 0 0': 'East',
                    '0 0 -1': 'North', '0 -1 0': 'Bottom', '-1 0 0': 'West'}

    def __init__(self, dx=0, dy=0, dz=0):
        """
        Given a 3D vector, return the closer cardinal direction
        """
        assert not (dx == 0 and dy == 0 and dz == 0)  # assert that at least one coordinate is not null
        # keep only one non null coordinate
        kept_dir = argmax(abs(array([dx, dy, dz])))
        if kept_dir == 0:
            dy = dz = 0
        elif kept_dir == 1:
            dx = dz = 0
        else:
            dx = dy = 0

        # each direction is set to -1 or 1
        self._dir_x = int(dx / abs(dx)) if dx else 0  # 1, 0, or -1
        self._dir_y = int(dy / abs(dy)) if dy else 0
        self._dir_z = int(dz / abs(dz)) if dz else 0
        tmp_key = '{} {} {}'.format(self._dir_x, self._dir_y, self._dir_z)
        self._name = self.__known_dirs[tmp_key] if tmp_key in self.__known_dirs else 'Unknown'

    def __eq__(self, other):
        if isinstance(other, Direction):
            return (self.x == other.x) and (self.y == other.y) and (self.z == other.z)
        return False

    def __str__(self):
        return self._name

    def __hash__(self):
        return hash(str(self))

    def __neg__(self):
        return Direction(-self._dir_x, -self._dir_y, -self._dir_z)

    def __abs__(self):
        return Direction(abs(self._dir_x), abs(self._dir_y), abs(self._dir_z))

    @property
    def x(self):
        return self._dir_x

    @property
    def y(self):
        return self._dir_y

    @property
    def z(self):
        return self._dir_z

    @property
    def asPoint2D(self):
        return Point2D(self._dir_x, self._dir_z)

    def rotate(self):
        """
        Rotates direction anti-normally, East.rotate() == South
        Returns anti-normal rotation of self
        -------

        """
        return Direction(dx=-self._dir_z, dz=self._dir_x)

    @classmethod
    def from_string(cls, dir_str):
        str_to_coord = {value.lower(): key for key, value in Direction.__known_dirs.items()}  # reversed dict
        x, y, z = list(map(int, str_to_coord[dir_str].split(' ')))
        return Direction(x, y, z)


East = Direction(1, 0, 0)
West = Direction(-1, 0, 0)
South = Direction(0, 0, 1)
North = Direction(0, 0, -1)
Top = Direction(0, 1, 0)
Bottom = Direction(0, -1, 0)


def cardinal_directions():
    # type: () -> Iterable[Direction]
    directions = [East, South, West, North]
    shuffle(directions)
    return iter(directions)


def all_directions():
    # type: () -> Iterable[Direction]
    directions = [East, South, West, North, Top, Bottom]
    shuffle(directions)
    return iter(directions)


def clear_tree_at(level, box, point):
    # type: (MCInfdevOldLevel, TransformBox, Point2D) -> None

    def is_tree(bid):
        block = level.materials[bid]
        return block.stringID in ['leaves', 'log', 'leaves2', 'log2', 'brown_mushroom_block', 'red_mushroom_block']

    y = level.heightMapAt(point.x, point.z) - 1
    if not is_tree(level.blockAt(point.x, y, point.z)):
        return

    possible_tree_blocks = [(point.x, y, point.z)]
    while possible_tree_blocks:
        x0, y0, z0 = possible_tree_blocks.pop()
        setBlock(level, (0, 0), x0, y0, z0)

        if level.materials[level.blockAt(x0, y0, z0)].stringID != 'red_mushroom_block':
            # explore top/bottom diagonal blocks
            for direction, dy in product(cardinal_directions(), [-1, 1]):
                x, y, z = x0 + direction.x, y0 + dy, z0 + direction.z
                if is_tree(level.blockAt(x, y, z)) and (x, y, z) in box:
                    possible_tree_blocks.append((x, y, z))

        for direction in all_directions():
            x = x0 + direction.x
            y = y0 + direction.y
            z = z0 + direction.z
            if is_tree(level.blockAt(x, y, z)) and (x, y, z) in box:
                possible_tree_blocks.append((x, y, z))


def place_torch(level, x, y, z):
    if not level.blockAt(x, y, z):
        torch = Block["Torch (Up)"]
        setBlock(level, (torch.ID, torch.blockData), x, y, z)


def sym_range(v, dv, vmax=None):
    v0 = max(0, v-dv)
    v1 = min(vmax, v+dv+1) if vmax is not None else v+dv+1
    return range(v0, v1)


if __name__ == '__main__':
    assert -Direction(-3, 0, 0) == East
    assert -North == Direction(0, 0, 1)
    assert str(-Direction(0, 1, 0)) == str(Bottom) == 'Bottom'
    assert Direction.from_string('east') == East
