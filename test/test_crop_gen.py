from generation import CropGenerator
from map.maps import Maps
from pymclevel import Entity, MCLevel, BoundingBox
from utils import TransformBox

displayName = "Crop generator test filter"

inputs = (("type", ("Cow", "Naive")), ("Creator: Charlie", "label"))


def perform(level, box, options):
    # type: (MCLevel, BoundingBox, dict) -> None
    box = TransformBox(box)
    maps = Maps(level, box)
    gen = CropGenerator(box)
    if options['type'] in Entity.entityList:
        gen._gen_animal_farm(level, maps.height_map, options['type'])  # don't try this at home
    else:
        gen._gen_crop_v1(level)
