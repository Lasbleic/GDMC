from random import randint

from utils import BlockAPI

b = BlockAPI.blocks


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

oak_house_palette1 = HousePalette(b.Cobblestone, b.SprucePlanks, b.OakWood, b.OakPlanks,
                                  b.WhiteStainedGlassPane, 'gable', b.StoneBrick, 'oak')

birch_house_palette1 = HousePalette(b.Cobblestone, b.OakPlanks, b.BirchWood, b.BirchPlanks,
                                    b.WhiteStainedGlassPane, 'gable', b.StoneBrick, 'birch')

dark_oak_house_palette1 = HousePalette(b.Cobblestone, b.SprucePlanks, b.DarkOakWood, b.DarkOakPlanks,
                                       b.WhiteStainedGlassPane, 'gable', b.StoneBrick, 'dark_oak')

spruce_house_palette1 = HousePalette(b.Cobblestone, b.OakPlanks, b.SpruceWood, b.SprucePlanks,
                                     b.LightGrayStainedGlassPane, 'gable', b.StoneBrick, 'spruce')

acacia_house_palette1 = HousePalette(b.Cobblestone, b.BirchPlanks, b.AcaciaWood, b.AcaciaPlanks,
                                     b.WhiteStainedGlassPane, 'gable', b.StoneBrick, 'acacia')

jungle_house_palette1 = HousePalette(b.Cobblestone, b.OakPlanks, b.JungleWood, b.JunglePlanks,
                                     b.WhiteStainedGlassPane, 'gable', b.StoneBrick, 'jungle')

sand_house_palette1 = HousePalette(b.Cobblestone, b.SprucePlanks, b.SmoothSandstone, b.Sandstone,
                                   b.BirchFence, 'flat', b.ChiseledSandstone, 'oak')

red_sand_house_palette1 = HousePalette(b.Cobblestone, b.SprucePlanks, b.SmoothRedSandstone, b.RedSandstone,
                                       b.BirchFence, 'flat', b.ChiseledRedSandstone, 'oak')

terracotta_palette1 = HousePalette(b.RedSandstone, b.SprucePlanks, b.OakWood, b.Clay,
                                   b.SpruceFence, 'flat', b.Terracotta, 'oak')

# Defines for each biome the acceptable palettes. Adapted from pymclevel.biome_types
biome_palettes = {
    'badlands': [terracotta_palette1, red_sand_house_palette1],
    'badlands_plateau': [terracotta_palette1],
    'bamboo_jungle': [jungle_house_palette1],
    'bamboo_jungle_hills': [jungle_house_palette1],
    # 'basalt_deltas': [],
    'beach': [oak_house_palette1],
    'birch_forest': [birch_house_palette1],
    'birch_forest_hills': [birch_house_palette1],
    # 'cold_ocean': [],
    # 'crimson_forest': [],
    'dark_forest': [dark_oak_house_palette1],
    'dark_forest_hills': [dark_oak_house_palette1],
    # 'deep_cold_ocean': [],
    # 'deep_frozen_ocean': [],
    # 'deep_lukewarm_ocean': [],
    # 'deep_ocean': [],
    # 'deep_warm_ocean': [],
    'desert': [sand_house_palette1],
    'desert_hills': [sand_house_palette1],
    'desert_lakes': [sand_house_palette1],
    # 'end_barrens': [],
    # 'end_highlands': [],
    # 'end_midlands': [],
    'eroded_badlands': [terracotta_palette1],
    'flower_forest': [oak_house_palette1, birch_house_palette1],
    'forest': [oak_house_palette1, birch_house_palette1, dark_oak_house_palette1],
    # 'frozen_ocean': [],
    # 'frozen_river': [],
    'giant_spruce_taiga': [spruce_house_palette1],
    'giant_spruce_taiga_hills': [spruce_house_palette1],
    'giant_tree_taiga': [spruce_house_palette1],
    'giant_tree_taiga_hills': [spruce_house_palette1],
    'gravelly_mountains': [spruce_house_palette1],
    'ice_spikes': [spruce_house_palette1, oak_house_palette1],
    'jungle': [jungle_house_palette1],
    'jungle_edge': [jungle_house_palette1],
    'jungle_hills': [jungle_house_palette1],
    # 'lukewarm_ocean': [],
    'modified_badlands_plateau': [terracotta_palette1],
    'modified_gravelly_mountains': [spruce_house_palette1],
    'modified_jungle': [jungle_house_palette1],
    'modified_jungle_edge': [jungle_house_palette1],
    'modified_wooded_badlands_plateau': [terracotta_palette1, oak_house_palette1],
    'mountain_edge': [spruce_house_palette1, oak_house_palette1],
    'mountains': [spruce_house_palette1, oak_house_palette1],
    'mushroom_field_shore': [],
    'mushroom_fields': [],
    # 'nether_wastes': [],
    # 'ocean': [],
    'plains': [oak_house_palette1],
    'river': [oak_house_palette1],
    'savanna': [acacia_house_palette1],
    'savanna_plateau': [acacia_house_palette1],
    'shattered_savanna': [acacia_house_palette1],
    'shattered_savanna_plateau': [acacia_house_palette1],
    # 'small_end_islands': [],
    'snowy_beach': [oak_house_palette1],
    'snowy_mountains': [spruce_house_palette1],
    'snowy_taiga': [spruce_house_palette1],
    'snowy_taiga_hills': [spruce_house_palette1],
    'snowy_taiga_mountains': [spruce_house_palette1],
    'snowy_tundra': [spruce_house_palette1],
    # 'soul_sand_valley': [],
    'stone_shore': [oak_house_palette1],
    'sunflower_plains': [oak_house_palette1],
    'swamp': [oak_house_palette1],
    'swamp_hills': [oak_house_palette1],
    'taiga': [spruce_house_palette1],
    'taiga_hills': [spruce_house_palette1],
    'taiga_mountains': [spruce_house_palette1],
    'tall_birch_forest': [birch_house_palette1],
    'tall_birch_hills': [birch_house_palette1],
    # 'the_end': [],
    # 'the_void': [],
    # 'warm_ocean': [],
    # 'warped_forest': [],
    'wooded_badlands_plateau': [terracotta_palette1, oak_house_palette1],
    'wooded_hills': [oak_house_palette1],
    'wooded_mountains': [spruce_house_palette1, oak_house_palette1]
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
