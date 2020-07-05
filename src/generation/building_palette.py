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
            return Block[self['structure']]


plain_house_palette1 = HousePalette('Cobblestone', 'Spruce Wood Planks', 'Oak Wood', 'Oak Wood Planks',
                                    'White Stained Glass Pane', 'gable', 'Stone Brick', 'Oak')

desert_house_palette1 = HousePalette('Cobblestone', 'Spruce Wood Planks', 'Smooth Sandstone', 'Sandstone',
                                     'Birch Fence', 'flat', 'Chiseled Sandstone', 'Oak')

# Defines for each biome the acceptable palettes. Adapted from pymclevel.biome_types
biome_palettes = {
    '(Uncalculated)': [plain_house_palette1],
    'Ocean': [plain_house_palette1],
    'Plains': [plain_house_palette1],
    'Desert': [plain_house_palette1],
    'Extreme Hills': [plain_house_palette1],
    'Forest': [plain_house_palette1],
    'Taiga': [plain_house_palette1],
    'Swamppland': [plain_house_palette1],
    'River': [plain_house_palette1],
    'Hell (Nether)': [plain_house_palette1],
    'Sky (End)': [plain_house_palette1],
    'Frozen Ocean': [plain_house_palette1],
    'Frozen River': [plain_house_palette1],
    'Ice Plains': [plain_house_palette1],
    'Ice Mountains': [plain_house_palette1],
    'Mushroom Island': [plain_house_palette1],
    'Mushroom Island Shore': [plain_house_palette1],
    'Beach': [plain_house_palette1],
    'Desert Hills': [plain_house_palette1],
    'Forest Hills': [plain_house_palette1],
    'Taiga Hills': [plain_house_palette1],
    'Extreme Hills Edge': [plain_house_palette1],
    'Jungle': [plain_house_palette1],
    'Jungle Hills': [plain_house_palette1],
    'Jungle Edge': [plain_house_palette1],
    'Deep Ocean': [plain_house_palette1],
    'Stone Beach': [plain_house_palette1],
    'Cold Beach': [plain_house_palette1],
    'Birch Forest': [plain_house_palette1],
    'Birch Forest Hills': [plain_house_palette1],
    'Roofed Forest': [plain_house_palette1],
    'Cold Taiga': [plain_house_palette1],
    'Cold Taiga Hills': [plain_house_palette1],
    'Mega Taiga': [plain_house_palette1],
    'Mega Taiga Hills': [plain_house_palette1],
    'Extreme Hills+': [plain_house_palette1],
    'Savanna': [plain_house_palette1],
    'Savanna Plateau': [plain_house_palette1],
    'Messa': [plain_house_palette1],
    'Messa Plateau F': [plain_house_palette1],
    'Messa Plateau': [plain_house_palette1],
    'Sunflower Plains': [plain_house_palette1],
    'Desert M': [plain_house_palette1],
    'Extreme Hills M': [plain_house_palette1],
    'Flower Forest': [plain_house_palette1],
    'Taiga M': [plain_house_palette1],
    'Swampland M': [plain_house_palette1],
    'Ice Plains Spikes': [plain_house_palette1],
    'Ice Mountains Spikes': [plain_house_palette1],
    'Jungle M': [plain_house_palette1],
    'JungleEdge M': [plain_house_palette1],
    'Birch Forest M': [plain_house_palette1],
    'Birch Forest Hills M': [plain_house_palette1],
    'Roofed Forest M': [plain_house_palette1],
    'Cold Taiga M': [plain_house_palette1],
    'Mega Spruce Taiga': [plain_house_palette1],
    'Mega Spruce Taiga 2': [plain_house_palette1],
    'Extreme Hills+ M': [plain_house_palette1],
    'Savanna M': [plain_house_palette1],
    'Savanna Plateau M': [plain_house_palette1],
    'Mesa (Bryce)': [plain_house_palette1],
    'Mesa Plateau F M': [plain_house_palette1],
    'Mesa Plateau M': [plain_house_palette1]
}
