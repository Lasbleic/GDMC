from pymclevel import BoundingBox


class TransformBox(BoundingBox):
    """
    Adds class methods to the BoundingBox to transform the box's shape and position
    """

    def translate(self, dx=0, dy=0, dz=0):
        self._origin += (dx, dy, dz)

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
        if isinstance(dx_or_dir, Direction):
            dir = dx_or_dir
            dpos = (min(dir.x, 0), min(dir.y, 0), min(dir.z, 0))
            dsize = (abs(dir.x), abs(dir.y), abs(dir.z))
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


class Direction:
    """
    Custom direction class
    """

    def __init__(self, dx=0, dy=0, dz=0):
        """
        Given a 3D vector, return the closer cardinal direction
        """
        assert (dx != 0) ^ (dy != 0) ^ (dz != 0)  # assert only one coordinate is not null

        # each direction is set to -1 or 1
        self._dir_x = int(dx / abs(dx)) if dx else 0  # 1, 0, or -1
        self._dir_y = int(dy / abs(dy)) if dy else 0
        self._dir_z = int(dz / abs(dz)) if dz else 0
        known_dirs = {'0 0 1': 'South', '0 1 0': 'Top', '1 0 0': 'East',
                      '0 0 -1': 'North', '0 -1 0': 'Bottom', '-1 0 0': 'West'}
        tmp_key = '{} {} {}'.format(self._dir_x, self._dir_y, self._dir_z)
        self._name = known_dirs[tmp_key] if tmp_key in known_dirs else 'Unknown'

    def __eq__(self, other):
        if isinstance(other, Direction):
            return self._dir_x == other._dir_x and self._dir_y == other._dir_y and self._dir_z == other._dir_z
        return False

    def __str__(self):
        return '{} direction'.format(self._name)

    def __hash__(self):
        return hash(str(self))

    def __neg__(self):
        return Direction(-self._dir_x, -self._dir_y, -self._dir_z)

    @property
    def x(self):
        return self._dir_x

    @property
    def y(self):
        return self._dir_y

    @property
    def z(self):
        return self._dir_z


# Python enum ?
East = Direction(1, 0, 0)
West = Direction(-1, 0, 0)
South = Direction(0, 0, 1)
North = Direction(0, 0, -1)
Top = Direction(0, 1, 0)
Bottom = Direction(0, -1, 0)


def cardinal_directions():
    return iter([East, South, West, North])


if __name__ == '__main__':
    assert -Direction(-3, 0, 0) == East
    assert -North == Direction(0, 0, 1)
    assert str(-Direction(0, 1, 0)) == str(Bottom) == 'Bottom direction'
