from random import choice, randint
from time import sleep

from generation import ProcHouseGenerator
from generation.building_palette import biome_palettes, HousePalette

from terrain import TerrainMaps
from utils import TransformBox, dump

displayName = "House generator test filter"

if __name__ == '__main__':
    terrain = TerrainMaps.request()
    x, z = terrain.area.x, terrain.area.z
    w, l = terrain.area.width, terrain.area.length
    y = terrain.height_map[0, 0]
    box = TransformBox((x, y, z), (w, randint(4, 16), l))

    all_palettes = []
    for palettes in biome_palettes.values():
        if isinstance(palettes, HousePalette):
            all_palettes.append(palettes)
        else:
            all_palettes.extend(palettes)
    palette = choice(all_palettes)
    ProcHouseGenerator(box).generate(terrain, terrain.height_map.box_height(box, False), choice(all_palettes))
    dump()
    while not input():
        terrain.undo()
        palette = choice(all_palettes)
        ProcHouseGenerator(box).generate(terrain, terrain.height_map.box_height(box, False), palette)
        dump()
    terrain.undo()
