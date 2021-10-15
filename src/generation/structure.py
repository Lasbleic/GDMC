from utils import BoundingBox, Position, Point
from numpy import zeros, int32
from utils.block_utils import setBlock


class Structure(BoundingBox):
    def __init__(self, origin, size):
        super().__init__(origin, size)
        self.__priority = zeros(size, dtype=int32)

    @classmethod
    def from_box(cls, box: BoundingBox):
        return cls(box.origin, box.size)

    def set(self, pos: Position, blockstate: str, priority: int = 1):
        if pos.coords not in self:
            return
        struct_pos: Point = pos - self.origin
        prev_priority = self.__priority[struct_pos.coords]

        if priority > prev_priority:
            setBlock(pos, blockstate)
            self.__priority[struct_pos.coords] = priority

    def fill(self, box: BoundingBox, blockstate: str, priority: int = 1):
        for x, y, z, in box.positions:
            p = Position(x, z, y)
            self.set(p, blockstate, priority)

    @property
    def origin(self) -> Position:
        return Position(self.minx, self.minz, self.miny)
