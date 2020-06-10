from generation import TransformBox, WindmillGenerator
from map.maps import Maps
from pymclevel import MCLevel, BoundingBox

displayName = "Windmill generator test filter"

inputs = (("hello there", "label"), ("Creator: Charlie", "label"))


def perform(level, box, options):
    # type: (MCLevel, BoundingBox, dict) -> None
    box = TransformBox(box)
    maps = Maps(level, box)
    gen = WindmillGenerator(box)
    gen.generate(level, maps.height_map)
