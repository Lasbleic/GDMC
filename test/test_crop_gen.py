from building_seeding import Parcel
from generation import CropGenerator
from generation.building_palette import spruce_house_palette1
from terrain.maps import Maps
from pymclevel import Entity, MCLevel, BoundingBox
from utils import TransformBox, Point2D

displayName = "Crop generator test filter"

inputs = (("type", ("Cow", "Naive", "Harvested")), ("Creator: Charlie", "label"))


def perform(level, box, options):
    # type: (MCLevel, BoundingBox, dict) -> None
    box = TransformBox(box)
    maps = Maps(level, box)
    gen = CropGenerator(box)
    height_map = maps.height_map.box_height(box, False)
    if options['type'] in Entity.entityList:
        gen._gen_animal_farm(level, height_map, spruce_house_palette1, options['type'])  # don't try this at home
    elif options['type'] == "Harvested":
        gen._gen_harvested_crop(level, height_map)
    else:
        gen._gen_crop_v1(level, height_map)
