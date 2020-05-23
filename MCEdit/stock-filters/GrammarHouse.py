from __future__ import division
from random import random, randint
from numpy.random import geometric
from pymclevel import BoundingBox, alphaMaterials
from pymclevel.block_fill import fillBlocks
from itertools import product
import numpy as np
from CharliesDataExtraction import compute_height_map


displayName = "Grammar House"

inputs = (
    ('Grammatically generated simple house', 'label'),
    ('(hope it works)', 'label'),
    ('by Charlie <3', 'label')
)


def perform(level, box, options):
    print('building house in box', box)
    palette = {'base': alphaMaterials.Cobblestone, 'wall': alphaMaterials.WoodPlanks,
               'roof': alphaMaterials.BrickStairs, 'pillar': alphaMaterials.Wood, 'window': alphaMaterials.GlassPane}
    house = HouseSymbol()
    house.generate(level, box, palette)


class Symbol:
    def __init__(self, name='abstract'):
        self.children = []
        self.name = name
        self.box = None

    def generate(self, level, box, palette):
        for child in self.children:
            box = child.generate(level, box, palette)
        return box


class HouseSymbol(Symbol):
    def __init__(self, name='house'):
        Symbol.__init__(self, name)

    def generate(self, level, box, palette):
        self.children.append(BaseSymbol())

        # make dimensions uneven
        new_width, new_length = box.width, box.length
        new_width -= 1 - (new_width % 2)
        new_length -= 1 - (new_length % 2)
        box = BoundingBox(box.origin, (new_width, box.height, new_length))
        Symbol.generate(self, level, box, palette)


class BaseSymbol(Symbol):
    def __init__(self, name='basement'):
        Symbol.__init__(self, name)

    def generate(self, level, box, palette):
        h = compute_height_map(level, box)
        print(h, np.mean(h) + 1)
        box = BoundingBox((box.minx, np.min(h), box.minz), (box.width, np.mean(h) + 2 - np.min(h), box.length))
        # print('filling base', box)
        fillBlocks(level, box, palette['base'])
        return Symbol.generate(self, level, box, palette)


class StoreySymbol(Symbol):

    def __init__(self, has_door=False, name='storey'):
        Symbol.__init__(self, name)
        self.has_door = has_door

    def generate(self, level, box, palette):
        max_rec = 10 #geometric(0.4)
        # print(max_rec)
        box2 = BoundingBox((box.minx, box.maxy, box.minz), (box.width, 4, box.length))
        self.children.append(RoomSymbol(self, has_door=True, box=box2))
        r_i = 0  # type: int
        while r_i < len(self.children):
            # print self.children[r_i].box
            # print self.children[r_i].neighbour
            if max_rec == 0:
                break

            if not self.children[r_i].try_to_split():
                r_i += 1
            else:
                max_rec -= 1
        return Symbol.generate(self, level, None, palette)

        # def try_to_split(self, room):
        #     """
        #     Try to randomly split a RoomSymbol, return True if succeeds,
        #     False if the split is not both rooms are valid
        #     todo: split in two instead ? and join adjacent rooms
        #     """
        #     b = room.box
        #     if b.width >= 5 and b.length <= 3:
        #         return room._xsplit
        # if b.width >= 7 and b.length >= 7 and random():
        #     x, y, z = [b.minx, b.maxx], b.miny, [b.minz, b.maxz]
        #     xr = x[0] + 2 * randint(1, b.width // 2 - 1)
        #     zr = z[0] + 2 * randint(1, b.width // 2 - 1)
        #     w = [xr + 1 - x[0], x[1] - xr]  # sub rooms' widths
        #     l = [zr + 1 - z[0], z[1] - zr]  # sub rooms' lengths
        #     h = b.height
        #     x[1], z[1] = xr, zr
        #     if (w[0] >= 5 or w[1] >= 5) and (l[0] >= 5 or l[1] >= 5):  # assert that sub rooms are large enough
        #         self.children.remove(room)
        #         sub_rooms = []
        #         for idx, idz in product([0, 1], [0, 1]):
        #             sub_rooms.append(RoomSymbol(self, box=BoundingBox((x[idx], y, z[idz]), (w[idx], h, l[idz]))))
        #         # one of the four sub rooms is deleted, the smaller the room is the higher the chance is
        #         probs = [1.0/(room.box.width * room.box.length)**2 for room in sub_rooms]
        #         probs = [p/sum(probs) for p in probs]  # norm
        #         sub_rooms.remove(np.random.choice(sub_rooms, p=probs))
        #         if room.has_door:
        #             sub_rooms[randint(0, 2)].has_door = True  # todo: mark shared walls so that doors don't gen on them
        #         self.children.extend(sub_rooms)
        #         return True
        # return False


class RoomSymbol(Symbol):

    def __init__(self, parent, name='room', has_door=False, box=None):
        Symbol.__init__(self, name)
        self.parent = parent  # type: StoreySymbol
        self.neighbour = [None for _ in xrange(4)]  # type: [RoomSymbol]
        self.box = box
        self.has_door = has_door

    def generate(self, level, box, palette):
        # print('filling walls', box)
        box = self.box

        # for x, z in product([box.minx, box.maxx-1], [box.minz, box.maxz-1]):
        for n, x, z in [[3, box.minx, box.minz], [2, box.minx, box.maxz-1],
                        [1, box.maxx-1, box.maxz-1], [0, box.maxx-1, box.minz]]:
            self.children.append(PillarSymbol(x, z, is_heavy=True))
            self.children.append(WallSymbol(x, z, is_heavy=(self.neighbour[n] is None)))
        if self.has_door:
            heavy_walls = [w for w in self.children if isinstance(w, WallSymbol) and w.is_heavy]
            heavy_walls[randint(0, len(heavy_walls)-1)].has_door = True  # max bound of randint is included

        return Symbol.generate(self, level, box, palette)

    def try_to_split(self):
        b = self.box
        if b.width >= 7 or b.length >= 7:
            split_t = b.length**2 / (b.width**2 + b.length**2)
            if min(b.width, b.length) == 5:
                return False
            elif b.length <= 3 or (b.width > 3 and random() > split_t):
                return self._xsplit(b.minx + 2*randint(1, b.width//2-1))
            else:
                return self._zsplit(b.minz + 2*randint(1, b.length//2-1))
        return False

    def _xsplit(self, x):
        print("splitting box in x", self.box, self.neighbour)
        # split generation box
        b0 = self.box
        b1 = BoundingBox(b0.origin, (x+1-b0.minx, b0.height, b0.length))
        b2 = BoundingBox((x, b0.miny, b0.minz), (b0.maxx-x, b0.height, b0.length))
        # instantiate sub rooms within the boxes
        r1 = RoomSymbol(self.parent, box=b1)
        r2 = RoomSymbol(self.parent, box=b2)
        # update neighbours relationships
        for n_index in xrange(4):
            n = self.neighbour[n_index]
            if n is not None:
                RoomSymbol(n).neighbour[(n_index+2) % 4] = None
                r2.neighbour[n_index] = r1.neighbour[n_index] = n
        keep1 = (random() > 1. / r1.box.width) and r1.surface() > 9
        keep2 = (random() > 1. / r2.box.width) and r2.surface() > 9

        kept_rooms = []
        if (keep1 or keep2) and max(b1.width, b2.width) >= 5:
            # r1.neighbour[0] = r2.neighbour[2] = None
            if keep1:
                r2.neighbour[2] = r1
                r1.has_door = self.has_door
                self.parent.children.append(r1)
                print("sub box in", r1.box, r1.neighbour)
            elif r1.neighbour[2] is not None:
                # could break building connectedness [other room][room 1 to delete][room 2]
                return False
            if keep2:
                r1.neighbour[0] = r2
                r2.has_door = self.has_door if not keep1 else False
                self.parent.children.append(r2)
                print("sub box in", r2.box, r2.neighbour)
            elif r2.neighbour[0] is not None:
                return False
            self.parent.children.remove(self)
            return True
        return False

    def _zsplit(self, z):
        print("splitting box in z", self.box, self.neighbour)
        # split generation box
        b0 = self.box
        b1 = BoundingBox(b0.origin, (b0.width, b0.height, z+1-b0.minz))
        b2 = BoundingBox((b0.minx, b0.miny, z), (b0.width, b0.height, b0.maxz-z))
        # instantiate sub rooms within the boxes
        r1 = RoomSymbol(self.parent, box=b1)
        r2 = RoomSymbol(self.parent, box=b2)
        # update neighbours relationships
        for n_index in xrange(4):
            n = self.neighbour[n_index]
            if n is not None:
                RoomSymbol(n).neighbour[(n_index+2) % 4] = None
                r2.neighbour[n_index] = r1.neighbour[n_index] = n
        keep1 = (random() > 1. / r1.box.length) and r1.surface() > 9
        keep2 = (random() > 1. / r2.box.length) and r2.surface() > 9
        if (keep1 or keep2) and max(b1.length, b2.length) >= 5:
            # r1.neighbour[1] = r2.neighbour[3] = None
            if keep1:
                r2.neighbour[3] = r1
                r1.has_door = self.has_door
                self.parent.children.append(r1)
                print("sub box in", r2.box, r2.neighbour)
            elif r1.neighbour[3] is not None:
                return False
            if keep2:
                r1.neighbour[1] = r2
                r2.has_door = self.has_door if not keep1 else False
                self.parent.children.append(r2)
                print("sub box in", r2.box, r2.neighbour)
            elif r2.neighbour[1] is not None:
                return False
            self.parent.children.remove(self)
            return True
        return False

    def surface(self):
        s = self.box.width * self.box.length
        return s


class PillarSymbol(Symbol):
    def __init__(self, x, z, name='pillar', is_heavy=True):
        Symbol.__init__(self, name)
        self.x = x
        self.z = z
        self.is_heavy = is_heavy

    def generate(self, level, box, palette):
        box2 = BoundingBox((self.x, box.miny, self.z), (1, box.height, 1))
        material = palette['pillar'] if self.is_heavy else palette['wall']
        # print('filling pillar in', box)
        fillBlocks(level, box2, material)
        return box


class WallSymbol(PillarSymbol):
    def __init__(self, x, z, name='pillar', is_heavy=False):
        PillarSymbol.__init__(self, x, z, name, is_heavy)
        self.has_door = False

    def generate(self, level, box, palette):
        x, y, z = self.x, box.miny, self.z
        b1, b2 = x == box.minx, z == box.minz
        try:
            if b1 ^ b2:
                # wall at constant x
                box2 = BoundingBox((x, box.miny, box.minz+1), (1, box.height, box.length-2))
                print('filling {} wall in'.format('heavy' if self.is_heavy else 'light'), box2)
                if self.is_heavy:
                    fillBlocks(level, box2, palette['wall'])
                    for c in range(box.length//2 - 1):
                        z = box.minz + 2*(c+1)
                        fillBlocks(level, BoundingBox((x, y+1, z), (1, 2, 1)), palette['window'])
                    if self.has_door:
                        zdoor = box.minz + 2*randint(1, box.length//2-1)
                        fillBlocks(level, BoundingBox((x, y, zdoor), (1, 3, 1)), alphaMaterials.Air)
                else:
                    fillBlocks(level, box2, alphaMaterials.Air)
            else:
                # wall at constant z
                box2 = BoundingBox((box.minx+1, box.miny, z), (box.width-2, box.height, 1))
                print('filling {} wall in'.format('heavy' if self.is_heavy else 'light'), box2)
                if self.is_heavy:
                    fillBlocks(level, box2, palette['wall'])
                    # for x in range(box.minx+2, box.maxx-2, 2):
                        # fillBlocks(level, BoundingBox((x, y+1, z), (1, 2, 1)), palette['window'])
                    if self.has_door:
                        xdoor = box.minx + 2*randint(1, box.width//2-1)
                        fillBlocks(level, BoundingBox((xdoor, y, z), (1, 3, 1)), alphaMaterials.Air)
                else:
                    fillBlocks(level, box2, alphaMaterials.Air)
        except ValueError:
            fillBlocks(level, BoundingBox(box.origin, (1, 3, 1)), alphaMaterials.Air)
        return box


class RoofSymbol(Symbol):
    def generate(self, level, box, palette):
        box = BoundingBox((box.minx, box.maxy, box.minz), (box.width, 1, box.length))
        # print('filling roof', box)
        r = random()
        t = float(box.length**2) / (box.width**2 + box.length**2)
        roof_in_width = r > t  # higher probability to have a lower & longer triangular roof

        if roof_in_width:
            for dz in xrange(box.length//2):
                # north line
                roof_box = BoundingBox((box.minx, box.miny+dz, box.minz+dz), (box.width, 1, 1))
                fillBlocks(level, roof_box, alphaMaterials[palette['roof'].ID, 2])  # this way to access oriented blocks is ugly

                # wood fill
                for x in [box.minx, box.maxx-1]:
                    roof_box = BoundingBox((x, box.miny+dz, box.minz+dz+1), (1, 1, box.length - 2*(dz+1)))
                    fillBlocks(level, roof_box, palette['wall'])

                # south line
                roof_box = BoundingBox((box.minx, box.miny+dz, box.maxz-dz-1), (box.width, 1, 1))
                fillBlocks(level, roof_box, alphaMaterials[palette['roof'].ID, 3])

                if box.length % 2:
                    # todo: build arete -> il faut recuperer le materiau du toit en slab, ou block
                    pass

        else:
            for dx in xrange(box.width//2):
                roof_box = BoundingBox((box.minx+dx, box.miny+dx, box.minz), (1, 1, box.length))
                fillBlocks(level, roof_box, alphaMaterials[palette['roof'].ID, 0])

                for z in [box.minz, box.maxz-1]:
                    roof_box = BoundingBox((box.minx+dx+1, box.miny+dx, z), (box.width - 2*(dx+1), 1, 1))
                    fillBlocks(level, roof_box, palette['wall'])

                roof_box = BoundingBox((box.maxx-dx-1, box.miny+dx, box.minz), (1, 1, box.length))
                fillBlocks(level, roof_box, alphaMaterials[palette['roof'].ID, 1])

                if box.width % 2:
                    #todo: same
                    pass

        return Symbol.generate(self, level, box, palette)






