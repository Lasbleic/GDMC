from math import sqrt


class Point2D:

    def __init__(self, x, z):
        self.x = x
        self.z = z

    def __str__(self):
        return "(x:" + str(self.x) + "; z:" + str(self.z) + ")"

    def __eq__(self, other):
        return other.x == self.x and other.z == self.z

    def __hash__(self):
        return hash(str(self))

    def __add__(self, other):
        assert isinstance(other, Point2D)
        return Point2D(self.x + other.x, self.z + other.z)

    def __neg__(self):
        return Point2D(0, 0) - self

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

    @property
    def toInt(self):
        return Point2D(int(round(self.x)), int(round(self.z)))


class Point3D(Point2D):
    def __init__(self, x, y, z):
        Point2D.__init__(self, x, z)
        self._y = y

    @property
    def y(self):
        return self._y

    def __add__(self, other):
        assert isinstance(other, Point3D) or isinstance(other, Point2D)
        if isinstance(other, Point2D):
            other = Point3D(other.x, 0, other.z)
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __neg__(self):
        return Point3D(-self.x, -self.y, -self.z)

    def __sub__(self, other):
        return self + (-other)


def euclidean(p1, p2):
    # type: (Point2D, Point2D) -> float
    return sqrt((p1.x - p2.x) ** 2 + (p1.z - p2.z) ** 2)


def manhattan(p1, p2):
    # type: (Point2D or Point3D, Point2D or Point3D) -> float
    return abs(p1.x - p2.x) + abs(p1.z - p2.z)
