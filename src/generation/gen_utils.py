from pymclevel import BoundingBox


class TransformBox(BoundingBox):
    """
    Adds class methods to the BoundingBox to transform the box's shape and position
    """
    def transpose(self, dx=0, dy=0, dz=0):
        self._origin += (dx, dy, dz)
