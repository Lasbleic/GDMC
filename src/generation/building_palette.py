from random import randint

from pymclevel import alphaMaterials as Block


class HousePalette(dict):

    def __init__(self, base_bloc, floor_block, struct_block, wall_block, window_block, roof_type, roof_block, door_mat):
        super(HousePalette, self).__init__()
        self['roofType'] = roof_type
        self['roofBlock'] = roof_block
        self['base'] = base_bloc
        self['structure'] = struct_block
        self['wall'] = wall_block
        self['window'] = window_block
        self['floor'] = floor_block
        self['door'] = door_mat

    def get_roof_block(self, facing, direction=None):
        if direction is None:
            roof_block = '{} Slab ({})'.format(self['roofBlock'], facing)
        elif self['roofType'] == 'flat':
            roof_block = self['roofBlock']
        else:
            roof_block = '{} Stairs ({}, {})'.format(self['roofBlock'], facing, direction)
        return Block[roof_block]

    def get_structure_block(self, direction):
        try:
            return Block['{} ({})'.format(self['structure'], direction)]
        except KeyError:
            try:
                wood_type = self['structure'][:-5]
                return Block['{} ({}, {})'.format(self['structure'], direction, wood_type)]
            except KeyError:
                return Block[self['structure']]


stony_palette = {"Cobblestone": 0.7, "Gravel": 0.2, "Stone": 0.1}

oak_house_palette1 = HousePalette('Cobblestone', 'Spruce Wood Planks', 'Oak Wood', 'Oak Wood Planks',
                                  'White Stained Glass Pane', 'gable', 'Stone Brick', 'Oak')

birch_house_palette1 = HousePalette('Cobblestone', 'Oak Wood Planks', 'Birch Wood', 'Birch Wood Planks',
                                    'White Stained Glass Pane', 'gable', 'Stone Brick', 'Birch')

dark_oak_house_palette1 = HousePalette('Cobblestone', 'Spruce Wood Planks', 'Dark Oak Wood', 'Dark Oak Wood Planks',
                                       'White Stained Glass Pane', 'gable', 'Stone Brick', 'Dark Oak')

spruce_house_palette1 = HousePalette('Cobblestone', 'Oak Wood Planks', 'Spruce Wood', 'Spruce Wood Planks',
                                     'Light Gray Stained Glass Pane', 'gable', 'Stone Brick', 'Spruce')

acacia_house_palette1 = HousePalette('Cobblestone', 'Birch Wood Planks', 'Acacia Wood', 'Acacia Wood Planks',
                                     'White Stained Glass Pane', 'gable', 'Stone Brick', 'Acacia')

jungle_house_palette1 = HousePalette('Cobblestone', 'Oak Wood Planks', 'Jungle Wood', 'Jungle Wood Planks',
                                     'White Stained Glass Pane', 'gable', 'Stone Brick', 'Jungle')

sand_house_palette1 = HousePalette('Cobblestone', 'Spruce Wood Planks', 'Smooth Sandstone', 'Sandstone',
                                   'Birch Fence', 'flat', 'Chiseled Sandstone', 'Oak')

red_sand_house_palette1 = HousePalette('Cobblestone', 'Spruce Wood Planks', 'Smooth Red Sandstone', 'Red Sandstone',
                                       'Birch Fence', 'flat', 'Chiseled Red Sandstone', 'Oak')

terracotta_palette1 = HousePalette('Red Sandstone', 'Spruce Wood Planks', 'Oak Wood', 'Hardened Clay',
                                   'Spruce Fence', 'flat', 'Hardened Clay', 'Oak')

# Defines for each biome the acceptable palettes. Adapted from pymclevel.biome_types
biome_palettes = {
    '(Uncalculated)': [oak_house_palette1],
    'Ocean': [oak_house_palette1],
    'Plains': [oak_house_palette1],
    'Desert': [sand_house_palette1],
    'Extreme Hills': [oak_house_palette1],
    'Forest': [oak_house_palette1, birch_house_palette1],
    'Taiga': [spruce_house_palette1],
    'Swamppland': [oak_house_palette1],
    'River': [oak_house_palette1],
    'Hell (Nether)': [oak_house_palette1],
    'Sky (End)': [oak_house_palette1],
    'Frozen Ocean': [spruce_house_palette1],
    'Frozen River': [spruce_house_palette1],
    'Ice Plains': [spruce_house_palette1],
    'Ice Mountains': [spruce_house_palette1],
    'Mushroom Island': [oak_house_palette1],
    'Mushroom Island Shore': [oak_house_palette1],
    'Beach': [sand_house_palette1],
    'Desert Hills': [sand_house_palette1],
    'Forest Hills': [oak_house_palette1, birch_house_palette1],
    'Taiga Hills': [spruce_house_palette1],
    'Extreme Hills Edge': [oak_house_palette1],
    'Jungle': [jungle_house_palette1],
    'Jungle Hills': [jungle_house_palette1],
    'Jungle Edge': [jungle_house_palette1],
    'Deep Ocean': [oak_house_palette1],
    'Stone Beach': [spruce_house_palette1],
    'Cold Beach': [spruce_house_palette1],
    'Birch Forest': [oak_house_palette1],
    'Birch Forest Hills': [oak_house_palette1],
    'Roofed Forest': [dark_oak_house_palette1],
    'Cold Taiga': [spruce_house_palette1],
    'Cold Taiga Hills': [spruce_house_palette1],
    'Mega Taiga': [spruce_house_palette1],
    'Mega Taiga Hills': [spruce_house_palette1],
    'Extreme Hills+': [oak_house_palette1, spruce_house_palette1],
    'Savanna': [acacia_house_palette1],
    'Savanna Plateau': [acacia_house_palette1],
    'Messa': [red_sand_house_palette1],
    'Messa Plateau F': [terracotta_palette1],
    'Messa Plateau': [terracotta_palette1],
    'Sunflower Plains': [oak_house_palette1],
    'Desert M': [sand_house_palette1],
    'Extreme Hills M': [oak_house_palette1],
    'Flower Forest': [oak_house_palette1],
    'Taiga M': [spruce_house_palette1],
    'Swampland M': [oak_house_palette1, spruce_house_palette1],
    'Ice Plains Spikes': [spruce_house_palette1],
    'Ice Mountains Spikes': [spruce_house_palette1],
    'Jungle M': [jungle_house_palette1],
    'JungleEdge M': [oak_house_palette1],
    'Birch Forest M': [jungle_house_palette1],
    'Birch Forest Hills M': [birch_house_palette1],
    'Roofed Forest M': [dark_oak_house_palette1],
    'Cold Taiga M': [spruce_house_palette1],
    'Mega Spruce Taiga': [spruce_house_palette1],
    'Mega Spruce Taiga 2': [spruce_house_palette1],
    'Extreme Hills+ M': [oak_house_palette1, spruce_house_palette1],
    'Savanna M': [acacia_house_palette1],
    'Savanna Plateau M': [acacia_house_palette1],
    'Mesa (Bryce)': [terracotta_palette1],
    'Mesa Plateau F M': [terracotta_palette1],
    'Mesa Plateau M': [terracotta_palette1]
}


def get_biome_palette(biome):
    try:
        palette_options = biome_palettes[biome]
        if len(palette_options) == 0:
            return palette_options[0]
        else:
            palette_index = randint(0, len(palette_options) - 1)
            return palette_options[palette_index]
    except Exception:
        print("Exception occurred when getting palette for biome: {}".format(biome))
        return oak_house_palette1
