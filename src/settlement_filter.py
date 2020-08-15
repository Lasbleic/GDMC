# Name to display in MCEdit filter menu

import logging
from time import gmtime, strftime, time

from flat_settlement import FlatSettlement
from map.maps import Maps
from pymclevel import BoundingBox, MCLevel
from utils import TransformBox

displayName = "Create a settlement"

# Dictionary representing different options
inputs = (
    ("Authors: team charretiers", "label"),
    ("10' limit", True),
    ("debug mode", False)
)

logging.basicConfig(filename='settlement_log_{}.log'.format(strftime('%Y-%m-%d_%H-%M-%S', gmtime())), level=logging.INFO)


# Necessary function to be considered as a filter by MCEdit. This is the function that will be executed when the filter
# will be applied
def perform(level, box, options):
    # type: (MCLevel, BoundingBox, dict) -> None
    t0 = time()
    print("Hello Settlers!")
    box = TransformBox(box)
    maps = Maps(level, box)
    settlement = FlatSettlement(maps)
    settlement.init_road_network()  # define outside connections
    settlement.init_town_center()   # define town settlement as point close to roads and geometric center of the box
    settlement.build_skeleton(options["10' limit"])     # define buildings list and seed them
    try:
        settlement.define_parcels()     # define parcels around seeds
    except RuntimeWarning:
        pass
    settlement.generate(level, options["debug mode"])      # build buildings on parcels
    logging.debug('{} seconds of execution'.format(time() - t0))
