# Name to display in MCEdit filter menu
from flat_settlement import FlatSettlement
import logging
from time import gmtime, strftime, time

from pymclevel import BoundingBox

displayName = "Create a settlement"

# Dictionary representing different options
inputs = ()

logging.basicConfig(filename='settlement_log_{}.log'.format(strftime('%Y-%m-%d_%H-%M-%S', gmtime())), level=logging.DEBUG)


# Necessary function to be considered as a filter by MCEdit. This is the function that will be executed when the filter
# will be applied
def perform(level, box, options):
    t0 = time()
    print("Hello World!")
    settlement = FlatSettlement(box)
    settlement.init()
    settlement.generate(level)
    logging.debug('{} seconds of execution'.format(time() - t0))


if __name__ == '__main__':
    t0 = time()
    print('Hello World')
    settlement = FlatSettlement(BoundingBox((0, 0, 0), (256, 16, 256)))
    settlement.init()
    logging.debug('Total execution took {:0.3f}s (approx. limit: 600s)'.format(time() - t0))

