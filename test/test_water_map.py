from generation import ProcHouseGenerator
from map.maps import Maps
from pre_processing import Map, MapStock
from matplotlib import colors
from pymclevel import BoundingBox, MCLevel
from utils import TransformBox

displayName = "Water map test filter"

inputs = ()


def perform(level, box, options):
    # type: (MCLevel, BoundingBox, dict) -> None
    box = TransformBox(box)
    maps = Maps(level, box)
    color_map = colors.ListedColormap(['forestgreen', 'darkcyan', 'lightseagreen', 'aquamarine'])
    water_map = Map("water_map", max(maps.width, maps.length), maps.fluid_map.water.T, color_map, (0, 3),
                    ["No water", "Ocean", "River", "Swamp"]
                    )
    img_stock = MapStock("water_map_test", max(maps.width, maps.length), True)
    img_stock.add_map(water_map)
