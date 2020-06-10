from generation import TransformBox, ProcHouseGenerator
from map.maps import Maps
from pymclevel import BoundingBox, MCLevel

displayName = "House generator test filter"

inputs = ()


def perform(level, box, options):
    # type: (MCLevel, BoundingBox, dict) -> None
    box = TransformBox(box)
    maps = Maps(level, box)
    gen = ProcHouseGenerator(box)
    gen.generate(level, height_map=maps.height_map)
