from random import randint

from utils import BlockAPI


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
            roof_block = BlockAPI.getSlab(self['roofBlock'], type=facing)
        elif self['roofType'] == 'flat':
            roof_block = self['roofBlock']
        else:
            roof_block = BlockAPI.getStairs(self['roofBlock'], half=facing, facing=direction)
        return roof_block

    def get_structure_block(self, direction):
        return self['structure']
        # try:
        #     return '{} ({})'.format(self['structure'], direction)
        # except KeyError:
        #     try:
        #         wood_type = self['structure'][:-5]
        #         return '{} ({}, {})'.format(self['structure'], direction, wood_type)
        #     except KeyError:
        #         return self['structure']


stony_palette = {"cobblestone": 0.7, "gravel": 0.2, "stone": 0.1}

oak_house_palette1 = HousePalette(BlockAPI.blocks.Cobblestone, BlockAPI.blocks.SprucePlanks, BlockAPI.blocks.OakWood, BlockAPI.blocks.OakPlanks,
                                  BlockAPI.blocks.WhiteStainedGlassPane, 'gable', BlockAPI.blocks.StoneBrick, 'oak')

birch_house_palette1 = HousePalette(BlockAPI.blocks.Cobblestone, BlockAPI.blocks.OakPlanks, BlockAPI.blocks.BirchWood, BlockAPI.blocks.BirchPlanks,
                                    BlockAPI.blocks.WhiteStainedGlassPane, 'gable', BlockAPI.blocks.StoneBrick, 'birch')

dark_oak_house_palette1 = HousePalette(BlockAPI.blocks.Cobblestone, BlockAPI.blocks.SprucePlanks, 'Dark Oak Wood', 'Dark Oak Wood Planks',
                                       BlockAPI.blocks.WhiteStainedGlassPane, 'gable', BlockAPI.blocks.StoneBrick, 'dark_oak')

spruce_house_palette1 = HousePalette(BlockAPI.blocks.Cobblestone, BlockAPI.blocks.OakPlanks, BlockAPI.blocks.SpruceWood, BlockAPI.blocks.SprucePlanks,
                                     'Light Gray Stained Glass Pane', 'gable', BlockAPI.blocks.StoneBrick, 'spruce')

acacia_house_palette1 = HousePalette(BlockAPI.blocks.Cobblestone, 'Birch Wood Planks', 'Acacia Wood', 'Acacia Wood Planks',
                                     BlockAPI.blocks.WhiteStainedGlassPane, 'gable', BlockAPI.blocks.StoneBrick, 'acacia')

jungle_house_palette1 = HousePalette(BlockAPI.blocks.Cobblestone, BlockAPI.blocks.OakPlanks, 'Jungle Wood', 'Jungle Wood Planks',
                                     BlockAPI.blocks.WhiteStainedGlassPane, 'gable', BlockAPI.blocks.StoneBrick, 'jungle')

sand_house_palette1 = HousePalette(BlockAPI.blocks.Cobblestone, BlockAPI.blocks.SprucePlanks, BlockAPI.blocks.SmoothSandstone, BlockAPI.blocks.Sandstone,
                                   BlockAPI.blocks.BirchFence, 'flat', BlockAPI.blocks.ChiseledSandstone, 'oak')

red_sand_house_palette1 = HousePalette(BlockAPI.blocks.Cobblestone, BlockAPI.blocks.SprucePlanks, 'Smooth Red Sandstone', 'Red Sandstone',
                                       'Birch Fence', 'flat', 'Chiseled Red Sandstone', 'oak')

terracotta_palette1 = HousePalette('Red Sandstone', BlockAPI.blocks.SprucePlanks, 'Oak Wood', 'Hardened Clay',
                                   'Spruce Fence', 'flat', 'Hardened Clay', 'Oak')

# Defines for each biome the acceptable palettes. Adapted from pymclevel.biome_types
biome_palettes = {
    'ocean': [oak_house_palette1],
    'plains': [oak_house_palette1],
    'desert': [sand_house_palette1],
    'extreme_hills': [oak_house_palette1],
    'forest': [oak_house_palette1, birch_house_palette1],
    'taiga': [spruce_house_palette1],
    'swamp': [oak_house_palette1],
    'river': [oak_house_palette1],
    'hell_(nether)': [oak_house_palette1],
    'sky_(end)': [oak_house_palette1],
    'frozen_ocean': [spruce_house_palette1],
    'frozen_river': [spruce_house_palette1],
    'ice_plains': [spruce_house_palette1],
    'ice_mountains': [spruce_house_palette1],
    'mushroom_island': [oak_house_palette1],
    'mushroom_island_shore': [oak_house_palette1],
    'beach': [sand_house_palette1],
    'desert_hills': [sand_house_palette1],
    'wooded_hills': [oak_house_palette1, birch_house_palette1],
    'taiga_hills': [spruce_house_palette1],
    'extreme_hills_edge': [oak_house_palette1],
    'jungle': [jungle_house_palette1],
    'bamboo_jungle': [jungle_house_palette1],
    'jungle_hills': [jungle_house_palette1],
    'jungle_edge': [jungle_house_palette1],
    'deep_ocean': [oak_house_palette1],
    'stone_beach': [spruce_house_palette1],
    'cold_beach': [spruce_house_palette1],
    'birch_forest': [oak_house_palette1],
    'birch_forest_hills': [oak_house_palette1],
    'roofed_forest': [dark_oak_house_palette1],
    'cold_taiga': [spruce_house_palette1],
    'cold_taiga_hills': [spruce_house_palette1],
    'mega_taiga': [spruce_house_palette1],
    'mega_taiga_hills': [spruce_house_palette1],
    'extreme_hills+': [oak_house_palette1, spruce_house_palette1],
    'savanna': [acacia_house_palette1],
    'savanna_plateau': [acacia_house_palette1],
    'badlands': [red_sand_house_palette1],
    'badlands_plateau_f': [terracotta_palette1],
    'badlands_plateau': [terracotta_palette1],
    'sunflower_plains': [oak_house_palette1],
    'modified_desert': [sand_house_palette1],
    'modified_extreme_hills': [oak_house_palette1],
    'flower_forest': [oak_house_palette1],
    'modified_taiga': [spruce_house_palette1],
    'modified_swampland': [oak_house_palette1, spruce_house_palette1],
    'ice_plains_spikes': [spruce_house_palette1],
    'ice_mountains_spikes': [spruce_house_palette1],
    'modified_jungle': [jungle_house_palette1],
    'modified_birch_forest': [jungle_house_palette1],
    'modified_birch_forest_hills': [birch_house_palette1],
    'modified_roofed_forest': [dark_oak_house_palette1],
    'modified_cold_taiga': [spruce_house_palette1],
    'mega_spruce_taiga': [spruce_house_palette1],
    'mega_spruce_taiga_2': [spruce_house_palette1],
    'modified_extreme_hills+': [oak_house_palette1, spruce_house_palette1],
    'modified_savanna': [acacia_house_palette1],
    'modified_savanna_plateau': [acacia_house_palette1],
    'badlands_(bryce)': [terracotta_palette1],
    'modified_badlands_plateau_f': [terracotta_palette1],
    'modified_badlands_plateau': [terracotta_palette1],

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
