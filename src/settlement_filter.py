# Name to display in MCEdit filter menu
from typing import Dict

from flat_settlement import FlatSettlement
import logging
from time import gmtime, strftime, time

from generation import TransformBox
from map.maps import Maps
from pymclevel import BoundingBox, MCLevel
from village_skeleton import VillageSkeleton

displayName = "Create a settlement"

# Dictionary representing different options
inputs = ()

logging.basicConfig(filename='settlement_log_{}.log'.format(strftime('%Y-%m-%d_%H-%M-%S', gmtime())), level=logging.DEBUG)


# Necessary function to be considered as a filter by MCEdit. This is the function that will be executed when the filter
# will be applied
def perform(level, box, options):
    # type: (MCLevel, BoundingBox, dict) -> None
    t0 = time()
    print("Hello World!")
    box = TransformBox(box)
    maps = Maps(level, box)
    settlement = FlatSettlement(maps)
    settlement.init_road_network()  # define outside connections
    settlement.init_town_center()   # define town settlement as point close to roads and geometric center of the box
    settlement.build_skeleton()     # define buildings list and seed them
    settlement.define_parcels()     # define parcels around seeds
    settlement.generate(level)      # build buildings on parcels
    logging.debug('{} seconds of execution'.format(time() - t0))
