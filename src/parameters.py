MAX_LAMBDA = 30
MAX_ROAD_WIDTH = 7
MIN_ROAD_WIDTH = 3
MAX_WATER_EXPLORATION = 100
MAX_LAVA_EXPLORATION = 50
MAX_POND_EXPLORATION = 144  # should ideally be higher than the largest ponds to exterminate all of them

# Each bridge costs a initial cost + linear cost on length
BRIDGE_COST = 10
BRIDGE_UNIT_COST = 2

# buildings dimensions
MAX_HEIGHT = 15  # 12 -> max 3 floors
BUILDING_HEIGHT_SPREAD = 120  # at that distance from the center, buildings' height is a third of max height (1/e ~ .36)
AVERAGE_PARCEL_SIZE = 12
MIN_PARCEL_SIDE = 3
MIN_RATIO_SIDE = 7. / 11.

# distances
MIN_DIST_TO_LAVA = 10
MIN_DIST_TO_OCEAN = 8
MIN_DIST_TO_RIVER = 4
