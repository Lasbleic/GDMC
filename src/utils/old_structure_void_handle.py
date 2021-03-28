# from pymclevel import alphaMaterials, materials
# from pymclevel.materials import blockstateToID
# from pymclevel.schematic import StructureNBT
#
#
# class VoidStructureNBT(StructureNBT):
#     """
#     Extends StructureNBT to handle structure void
#     """
#
#     def __init__(self, filename=None, root_tag=None, size=None, mats=alphaMaterials):
#         super(VoidStructureNBT, self).__init__(filename, root_tag, size, mats)
#
#         self._blocks.fill((217, 0))  # fills structure bounds with void, instead of air
#         for palette_block in self._palette:
#             if 'Properties' in palette_block and 'shape' in palette_block['Properties']:
#                 palette_block['Properties']['shape'] = u'outer_right'
#         for block in self._root_tag["blocks"]:
#             # loads blocks referenced in the nbt
#             x, y, z = [p.value for p in block["pos"].value]
#             self._blocks[x, y, z] = blockstateToID(*self.get_state(block["state"].value))
#
#
# all_but_void = range(materials.id_limit)
# all_but_void.remove(alphaMaterials["Structure Void"].ID)
