from math import sqrt, tan, sin, cos, pi, ceil, floor, acos, atan, asin, degrees, radians, log, atan2, acos, asin
from random import *
from numpy import *
from pymclevel import alphaMaterials, MCSchematic, MCLevel, BoundingBox
from mcplatform import *
from utilityFunctions import setBlock

"""
Trying out a few things we can do with filters, displays some variables on the ground -> data visualisation
"""
inputs = (
    ("Cellular Automata SG Example", "label"),
    ("Paint mode", ("height", "steepness", "water type")),
    ("Creator: Charlie", "label"),
)

def perform(level, box, options):

    box = flatten_box(box)

    height_map = compute_height_map(level, box)
    if options["Paint mode"] == "height":
        paint_height(height_map, level, box)
    elif options["Paint mode"] == "water type":
        print("executing paint mode")
        print("Clay", alphaMaterials.StainedClay)
        paint_water(level, box)
    else:
        steep_map = compute_steep_map(height_map, box)
        paint_steep(steep_map, height_map, level, box)


def compute_height_map(level, box):
    """
    Custom height map, quite slow
    """
    xmin, xmax = box.minx, box.maxx
    zmin, zmax = box.minz, box.maxz
    ground_blocks = [alphaMaterials.Grass.ID, alphaMaterials.Gravel.ID, alphaMaterials.Dirt.ID,
                     alphaMaterials.Sand.ID, alphaMaterials.Stone.ID, alphaMaterials.Clay.ID]

    lx, lz = xmax - xmin, zmax - zmin  # length & width
    h = zeros((lx, lz), dtype=int)  # numpy height map

    for x in range(xmin, xmax):
        for z in range(zmin, zmax):
            y = 256
            # for each coord in the box, goes down from height limit until it lands on a 'ground block'
            while y >= 0 and level.blockAt(x, y, z) not in ground_blocks:
                y -= 1
            h[x - xmin, z - zmin] = y

    return h


def compute_steep_map(height, b):
    """
    Custom steepness map
    """
    steep = zeros(height.shape)
    mx, Mx, mz, Mz = b.minx, b.maxx, b.minz, b.maxz
    for x0 in range(mx, Mx):
        for z0 in range(mz, Mz):
            # gets all 4 cardinal height variation
            delta_h = []
            for x1, z1 in [(x0+1, z0), (x0, z0+1), (x0-1, z0), (x0, z0-1)]:
                if (mx <= x1 < Mx) and (mz <= z1 < Mz):
                    delta_h.append(abs(height[x0-mx, z0-mz] - height[x1-mx, z1-mz]))
            delta_h.sort()
            # print(x0, z0, delta_h)
            # computes local slope as 2 smaller variations (always defined, reached in box's corners)
            steep[x0-mx, z0-mz] = delta_h[0] + delta_h[1]
    # print(steep)
    return steep


def paint_steep(steep_map, height_map, level, box):
    for x in range(box.minx, box.maxx):
        for z in range(box.minz, box.maxz):
            y = height_map[x - box.minx, z - box.minz]
            s = steep_map[x - box.minx, z - box.minz]
            if s == 0:
                t = 13  # dark green
            elif s == 1:
                t = 5  # lime
            elif s == 2:
                t = 4  # yellow
            elif s == 3:
                t = 1  # orange
            elif s <= 5:
                t = 14  # red
            elif s <= 8:
                t = 12  # dark red
            else:
                t = 0  # black
            setBlock(level, (alphaMaterials.StainedClay.ID, t), x, y, z)


def paint_height(height_map, l, b):
    for x in range(b.minx, b.maxx):
        for z in range(b.minz, b.maxz):
            y = height_map[x - b.minx, z - b.minz]
            if y < 55:
                t = 0
            elif y < 60:
                t = 1
            elif y < 65:
                t = 2
            elif y < 70:
                t = 3
            elif y < 75:
                t = 4
            elif y < 80:
                t = 5
            else:
                t = 6
            setBlock(l, (alphaMaterials.StainedClay.ID, t), x, y, z)


def compute_block_map(height, level, box, datablock=alphaMaterials.Water, on_ground=False):
    """
    computes a boolean matrix: what is the block at surface ?
    """
    found_block = zeros((box.width, box.length), dtype=bool)
    for x, _, z in box.positions:
        y = height[x-box.minx, z-box.minz] + 1
        if on_ground:
            y -= 1
        if level.blockAt(x, y, z) == datablock.ID:
            found_block[x-box.minx, z-box.minz] = True
    return found_block


def flatten_box(box):
    """
    no need for Y coordinate
    """
    return BoundingBox(box.origin, (box.width, 1, box.length))


def paint_water(level, box):
    """
    paints water type map depending on the local biome
    ocean -> cyan
    river -> light blue
    other (pond ? shore ?) -> dark blue
    Quite useless as is, could be improved through 'label propagation' maybe.
    Use cases examples: decide whether water can be drunk, make a difference between shores and rivers,
    identify water sources
    """
    h = compute_height_map(level, box)
    if box.height > 0:
        box = flatten_box(box)

    water_type = zeros(h.shape)
    for x, y, z in box.positions:
        # print(x, y, z)
        xb, zb = x - box.minx, z - box.minz
        y = h[xb, zb]
        # print(x, y, z)
        if level.blockAt(x, y+1, z) == alphaMaterials.Water.ID:
            cx, cz = x // 16, z // 16
            biome = level.getChunk(cx, cz).Biomes[x & 15, z & 15]
            y = 62

            if biome == 0:
                water_type[xb, zb] = 1
                setBlock(level, (alphaMaterials.StainedClay.ID, 9), x, y, z)
            elif biome == 7:
                water_type[xb, zb] = 2
                setBlock(level, (alphaMaterials.StainedClay.ID, 11), x, y, z)
            else:
                water_type[xb, zb] = 3
                setBlock(level, (alphaMaterials.StainedClay.ID, 3), x, y, z)




