# coding=utf-8
from generation import Generator
from utils import Point2D, TransformBox

from numpy import array


class Sewers(Generator):

    def __init__(self, road_net, origin):
        # type: (array, Point2D) -> None
        __origin = (origin.x, 0, origin.z)
        __size = (road_net.shape[0], 256, road_net.shape[1])
        Generator.__init__(self, TransformBox(__origin, __size))

    def generate(self, level, height_map=None, palette=None):
        """
        génère un réseau d'égouts
        les bouches sont des trappes au niveau de la route qui ouvrent sur des échelles descendants dans un réseau
        de tunnels souterrains. Chercher un point d'évacuation vers rivière/océan/station d'épuration.
        On peut lier cette classe / méthode aux maisons du village pour aménager des systèmes d'évacuation/ des caves
        Générer des squelettes / des cachots ?
        """
        # TODO: cette classe
        if height_map is None:
            return
        pass
