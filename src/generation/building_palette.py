import random

from gdpc import lookup

from utils import BlockAPI
from utils.block_utils import random_block, random_material

b = BlockAPI.blocks


class HousePalette(dict):
    __material_main: str  # roofs
    __material_alt: str  # under roofs, inside stairs
    __wall_block_alt: str  # roofed wall

    def __init__(self, base_bloc, floor_block, struct_block, wall_block, window_block, roof_type, roof_block, door_mat, roof_alt=None, wall_alt=None):
        super(HousePalette, self).__init__()
        self['roofType'] = roof_type
        self['roofBlock'] = roof_block
        self['base'] = base_bloc
        self['structure'] = struct_block
        self['wall'] = wall_block
        self['window'] = window_block
        self['floor'] = floor_block
        self['door'] = door_mat
        self['roofAlt'] = roof_alt if roof_alt else roof_block
        self['wallAlt'] = wall_alt if wall_alt else wall_block

    def get_roof_block(self, facing, direction=None, alternate=None):
        if direction is None:
            roof_block = BlockAPI.getSlab(self['roofBlock'], type=facing)
        elif self['roofType'] == 'flat':
            roof_block = self['roofBlock']
        else:
            if alternate is None:
                alternate = (facing == 'top')
            roof_block = BlockAPI.getStairs(self['roofAlt'] if alternate else self['roofBlock'], half=facing, facing=direction)
        return roof_block

    def get_structure_block(self, axis):
        block = self['structure'].replace('minecraft:', '')
        from utils.block_utils import BlockStateDict
        blockstates = BlockStateDict()
        if 'axis' in blockstates[block]:
            return f"{block}[axis={axis}]"
        return self['structure']


stony_palette = {"cobblestone": 0.7, "gravel": 0.2, "stone": 0.1}

oak_palette1 = HousePalette(b.Cobblestone, b.SprucePlanks, b.OakLog, b.OakPlanks,
                            b.WhiteStainedGlassPane, 'gable', b.StoneBrick, 'oak')

oak_palette2 = HousePalette(b.Stone, b.SprucePlanks, b.StrippedOakLog, b.Cobblestone,
                                  b.WhiteStainedGlassPane, 'gable', 'oak', 'oak')

oak_palette3 = HousePalette(b.Stone, b.SprucePlanks, b.StrippedOakLog, b.StoneBricks,
                                  b.WhiteStainedGlassPane, 'gable', 'oak', 'oak')

oak_spruce_palette = HousePalette(b.Stone, b.SprucePlanks, b.StrippedSpruceLog, b.OakPlanks,
                                  b.WhiteStainedGlassPane, 'gable', 'spruce', 'oak')

oak_birch_palette = HousePalette(b.Stone, b.SprucePlanks, b.StrippedOakLog, b.BirchPlanks,
                                  b.WhiteStainedGlassPane, 'gable', 'oak', 'oak')

birch_house_palette1 = HousePalette(b.Cobblestone, b.OakPlanks, b.BirchLog, b.BirchPlanks,
                                    b.WhiteStainedGlassPane, 'gable', b.StoneBrick, 'birch')

dark_oak_house_palette1 = HousePalette(b.Cobblestone, b.SprucePlanks, b.DarkOakLog, b.DarkOakPlanks,
                                       b.WhiteStainedGlassPane, 'gable', b.StoneBrick, 'dark_oak')

spruce_palette1 = HousePalette(b.Cobblestone, b.OakPlanks, b.SpruceLog, b.SprucePlanks,
                               b.LightGrayStainedGlassPane, 'gable', b.StoneBrick, 'spruce')

spruce_palette4 = HousePalette(b.Stone, b.OakPlanks, b.SpruceLog, b.MossyCobblestone,
                                     b.LightGrayStainedGlassPane, 'gable', 'spruce', 'spruce')

spruce_palette2 = HousePalette(b.MossyCobblestone, b.OakPlanks, b.SpruceLog, b.SprucePlanks,
                               b.LightGrayStainedGlassPane, 'gable', b.Cobblestone, 'spruce')

spruce_palette3 = HousePalette(b.MossyCobblestone, b.OakPlanks, b.StrippedSpruceLog, b.SprucePlanks,
                               b.LightGrayStainedGlassPane, 'gable', b.Cobblestone, 'spruce')

acacia_house_palette1 = HousePalette(b.Cobblestone, b.BirchPlanks, b.AcaciaLog, b.AcaciaPlanks,
                                     b.WhiteStainedGlassPane, 'gable', b.StoneBrick, 'acacia')

jungle_house_palette1 = HousePalette(b.Cobblestone, b.OakPlanks, b.JungleLog, b.JunglePlanks,
                                     b.WhiteStainedGlassPane, 'gable', b.StoneBrick, 'jungle')

sand_house_palette1 = HousePalette(b.Cobblestone, b.SprucePlanks, b.SmoothSandstone, b.Sandstone,
                                   b.BirchFence, 'flat', b.ChiseledSandstone, 'oak')

red_sand_house_palette1 = HousePalette(b.Cobblestone, b.SprucePlanks, b.SmoothRedSandstone, b.RedSandstone,
                                       b.BirchFence, 'flat', b.ChiseledRedSandstone, 'oak')

terracotta_palette1 = HousePalette(b.RedSandstone, b.SprucePlanks, b.OakLog, b.Terracotta,
                                   b.SpruceFence, 'flat', b.Terracotta, 'oak')

oak_palettes = (oak_palette1, oak_palette2, oak_palette3)
spruce_palettes = (spruce_palette1, spruce_palette2, spruce_palette3, spruce_palette4, oak_spruce_palette)

# Defines for each biome the acceptable palettes. Adapted from pymclevel.biome_types
biome_palettes = {
    'badlands': [terracotta_palette1, red_sand_house_palette1],
    'badlands_plateau': [terracotta_palette1],
    'bamboo_jungle': [jungle_house_palette1],
    'bamboo_jungle_hills': [jungle_house_palette1],
    # 'basalt_deltas': [],
    'beach': [*oak_palettes],
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
    'flower_forest': [*oak_palettes, birch_house_palette1],
    'forest': [*oak_palettes, birch_house_palette1, oak_birch_palette, oak_spruce_palette],
    # 'frozen_ocean': [],
    # 'frozen_river': [],
    'giant_spruce_taiga': [*spruce_palettes],
    'giant_spruce_taiga_hills': [*spruce_palettes],
    'giant_tree_taiga': [*spruce_palettes],
    'giant_tree_taiga_hills': [*spruce_palettes],
    'gravelly_mountains': [*spruce_palettes],
    'ice_spikes': [*spruce_palettes, *oak_palettes],
    'jungle': [jungle_house_palette1],
    'jungle_edge': [jungle_house_palette1],
    'jungle_hills': [jungle_house_palette1],
    # 'lukewarm_ocean': [],
    'modified_badlands_plateau': [terracotta_palette1],
    'modified_gravelly_mountains': [*spruce_palettes],
    'modified_jungle': [jungle_house_palette1],
    'modified_jungle_edge': [jungle_house_palette1],
    'modified_wooded_badlands_plateau': [terracotta_palette1, oak_palette1],
    'mountain_edge': [*spruce_palettes, *oak_palettes],
    'mountains': [*spruce_palettes, oak_palette2, oak_palette3],
    'mushroom_field_shore': [],
    'mushroom_fields': [],
    # 'nether_wastes': [],
    # 'ocean': [],
    'plains': [*oak_palettes, oak_birch_palette],
    'river': [*oak_palettes],
    'savanna': [acacia_house_palette1],
    'savanna_plateau': [acacia_house_palette1],
    'shattered_savanna': [acacia_house_palette1],
    'shattered_savanna_plateau': [acacia_house_palette1],
    # 'small_end_islands': [],
    'snowy_beach': [*oak_palettes],
    'snowy_mountains': [spruce_palette1],
    'snowy_taiga': [spruce_palette1],
    'snowy_taiga_hills': [spruce_palette1],
    'snowy_taiga_mountains': [spruce_palette1],
    'snowy_tundra': [spruce_palette1],
    # 'soul_sand_valley': [],
    'stone_shore': [*oak_palettes],
    'sunflower_plains': [*oak_palettes],
    'swamp': [*oak_palettes, *spruce_palettes],
    'swamp_hills': [*oak_palettes],
    'taiga': [*spruce_palettes],
    'taiga_hills': [*spruce_palettes],
    'taiga_mountains': [*spruce_palettes],
    'tall_birch_forest': [birch_house_palette1, oak_birch_palette],
    'tall_birch_hills': [birch_house_palette1, oak_birch_palette],
    # 'the_end': [],
    # 'the_void': [],
    # 'warm_ocean': [],
    # 'warped_forest': [],
    'wooded_badlands_plateau': [terracotta_palette1, oak_palette1],
    'wooded_hills': [oak_palette1],
    'wooded_mountains': [spruce_palette1, oak_palette1]
}


def get_biome_palette(biome):
    try:
        palette_options = biome_palettes[biome]
        if len(palette_options) == 0:
            return palette_options[0]
        else:
            return random.choice(palette_options)
    except Exception:
        print("Exception occurred when getting palette for biome: {}".format(biome))
        return oak_palette1


def random_palette() -> HousePalette:
    """
    Generates a random palette, mostly for debug purposes, could be nice to have a cool palette generator
    :return: block palette to generate buildings
    """
    roof_type = random.choice(['gable'] * 3 + ['flat'])
    roof_block = random_material(lookup.SLABS, lookup.STAIRS) if roof_type == 'gable' else random_block()
    return HousePalette(
        random_block(),
        random_block(),
        random_block(),
        random_block(),
        random.choice(lookup.GLASS),
        roof_type,
        roof_block,
        random_material(lookup.DOORS, lookup.FENCES, lookup.GATES),
        random_material(lookup.STAIRS),
        random_block()
    )
