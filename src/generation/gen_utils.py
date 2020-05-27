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


Direction.East = Direction(1, 0, 0)
Direction.West = Direction(-1, 0, 0)
Direction.South = Direction(0, 0, 1)
Direction.North = Direction(0, 0, -1)
Direction.Top = Direction(0, 1, 0)
Direction.Bottom = Direction(0, -1, 0)

if __name__ == '__main__':
    assert -Direction(-3, 0, 0) == Direction.East
    assert -Direction.North == Direction(0, 0, 1)
    assert str(-Direction(0, 1, 0)) == str(Direction.Bottom) == 'Bottom direction'
