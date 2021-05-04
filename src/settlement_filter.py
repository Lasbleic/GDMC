"""
Main script
TODO : wait for GDMC instructions on how to link the client to the server
"""
import logging
from pstats import SortKey, Stats
from time import gmtime, strftime, time

from flat_settlement import Settlement
from terrain import TerrainMaps
from utils import interfaceUtils, WorldSlice, BuildArea

logging.basicConfig(filename='settlement_log_{}.log'.format(strftime('%Y-%m-%d_%H-%M-%S', gmtime())), level=logging.INFO)

time_limit = "time_limit"  # "10' limit"
debug = "debug"  # "Debug mode: does not catch exceptions in generation"
visu = "visualization"  # "Visualization tool: plots iterations of building placement"


def main(**options):
    t0 = time()
    print("Hello Settlers!")
    # get & parse building zone
    terrain: TerrainMaps = TerrainMaps.request()

    settlement = Settlement(terrain)
    settlement.build_districts(visualize=False)
    # exit(0)
    t2 = time()
    settlement.build_skeleton(options.get(time_limit, None), options.get(visu, False))  # define buildings list and seed them
    print("calcul du squelette", time() - t2)
    try:
        settlement.define_parcels()  # define parcels around seeds
    except RuntimeWarning:
        pass
    settlement.terraform()
    settlement.generate(terrain, options.get(debug, False))      # build buildings on parcels
    print('{} seconds of execution'.format(time() - t0))

    if options.get(debug, False):
        do_undo = input("Undo ? [y]/n").lower()
        if do_undo in {"", "y"}:
            terrain.undo()


if __name__ == '__main__':
    import cProfile
    # main(debug=True)
    stats: Stats = cProfile.run(f"main({time_limit}=900)", sort=SortKey.CUMULATIVE)
