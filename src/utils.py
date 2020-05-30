from math import sqrt
from random import random
from os.path import realpath


class Point2D:

    def __init__(self, x, z):
        self.x = x
        self.z = z

    def __str__(self):
        return "(x:" + str(self.x) + "; z:" + str(self.z) + ")"

    def __eq__(self, other):
        return other.x == self.x and other.z == self.z


def bernouilli(p=.5):
    # type: (float) -> bool
    if p >= 1:
        return True
    elif p <= 0:
        return False
    else:
        return random() >= p


def euclidean(p1, p2):
    # type: (Point2D, Point2D) -> float
    return sqrt((p1.x - p2.x)**2 + (p1.z - p2.z)**2)


def get_project_path():
    this_path = realpath(__file__)
    proj_path = '/'.join(this_path.split('/')[:-1])
    return proj_path
