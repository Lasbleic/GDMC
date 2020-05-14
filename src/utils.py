from math import sqrt
from random import random

from road_network import Point2D


def bernouilli(p=.5):
    # type: (float) -> bool
    return random() >= p


def euclidean(p1, p2):
    # type: (Point2D, Point2D) -> float
    return sqrt((p1.x - p2.x)**2 + (p1.z - p2.z)**2)
