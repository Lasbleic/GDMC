from math import sqrt
from random import random
from os.path import realpath

from road_network import Point2D


def bernouilli(p=.5):
    # type: (float) -> bool
    return random() >= p


def euclidean(p1, p2):
    # type: (Point2D, Point2D) -> float
    return sqrt((p1.x - p2.x)**2 + (p1.z - p2.z)**2)


def get_project_path():
    this_path = realpath(__file__)
    proj_path = '/'.join(this_path.split('/')[:-1])
    return proj_path
