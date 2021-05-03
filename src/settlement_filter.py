"""
Main script
TODO : wait for GDMC instructions on how to link the client to the server
"""
import logging
from time import gmtime, strftime, time

from flat_settlement import Settlement
from terrain import TerrainMaps
from utils import interfaceUtils, WorldSlice, BuildArea

logging.basicConfig(filename='settlement_log_{}.log'.format(strftime('%Y-%m-%d_%H-%M-%S', gmtime())), level=logging.DEBUG)

option_time_limit = "time_limit"  # "10' limit"
option_debug = "debug"  # "Debug mode: does not catch exceptions in generation"
option_visu = "visualization"  # "Visualization tool: plots iterations of building placement"

if __name__ == '__main__':
    options = {
        option_time_limit: "600",
        option_debug: False,
        option_visu: False
    }
    t0 = time()
    print("Hello Settlers!")
    # get & parse building zone
    terrain: TerrainMaps = TerrainMaps.request()
    # exit(0)

    settlement = Settlement(terrain)
    settlement.build_districts(visualize=False)
    # exit(0)
    t2 = time()
    settlement.build_skeleton(options[option_time_limit], options[option_visu])  # define buildings list and seed them
    print("calcul du squelette", time() - t2)
    try:
        settlement.define_parcels()  # define parcels around seeds
    except RuntimeWarning:
        pass
    settlement.terraform()
    settlement.generate(terrain, options[option_debug])      # build buildings on parcels
    print('{} seconds of execution'.format(time() - t0))

    if options[option_debug]:
        do_undo = input("Undo ? [y]/n").lower()
        if do_undo in {"", "y"}:
            terrain.undo()
