"""
Main script
TODO : wait for GDMC instructions on how to link the client to the server
"""
import logging
from time import gmtime, strftime, time

from flat_settlement import FlatSettlement
from terrain import TerrainMaps
from utils import interfaceUtils, WorldSlice, BuildArea

logging.basicConfig(filename='settlement_log_{}.log'.format(strftime('%Y-%m-%d_%H-%M-%S', gmtime())), level=logging.INFO)

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
    build_area = BuildArea(interfaceUtils.requestBuildArea())
    level = WorldSlice((build_area.x, build_area.z, build_area.width, build_area.length))

    # analyze the terrain
    terrain = TerrainMaps(level, build_area)

    settlement = FlatSettlement(terrain)
    settlement.init_town_center()   # define town settlement as point close to roads and geometric center of the box
    settlement.init_road_network()  # define outside connections
    settlement.build_skeleton(options[option_time_limit], options[option_visu])  # define buildings list and seed them
    try:
        settlement.define_parcels()     # define parcels around seeds
    except RuntimeWarning:
        pass
    settlement.generate(terrain, options[option_debug])      # build buildings on parcels
    print('{} seconds of execution'.format(time() - t0))

