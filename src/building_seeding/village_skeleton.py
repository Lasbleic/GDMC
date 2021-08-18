"""
Village skeleton growth
"""

from typing import Tuple

from building_seeding.building_pool import BuildingPool, BuildingType
from building_seeding.districts import Districts
from building_seeding.interest import InterestSeeder
from building_seeding.interest.pre_processing import VisuHandler
from building_seeding.parcel import Parcel, MaskedParcel
from parameters import MIN_PARCEL_SIZE, AVERAGE_PARCEL_SIZE, MAX_PARCELS_IN_BLOCK
from terrain import TerrainMaps, ObstacleMap, RoadNetwork
from utils import *


class VillageSkeleton:

    def __init__(self, scenario: str, maps: TerrainMaps, districts: Districts, parcel_list: List[Parcel]):
        self.scenario = scenario
        self.size = (maps.width, maps.length)
        self.maps = maps
        buildable_surface = maps.width * maps.length - maps.fluid_map.as_obstacle_array.sum()
        self.building_iterator = BuildingPool(districts.buildable_surface)
        self.__parcel_list = parcel_list
        self.parcel_size = MIN_PARCEL_SIZE

        # parcel_list.append(Parcel(ghost_position, BuildingType.from_name('ghost'), maps))
        self.__interest = InterestSeeder(maps, districts, parcel_list, scenario)

    def add_parcel(self, seed: Point or Parcel, building_type: BuildingType = None):
        if isinstance(seed, Point):
            if building_type.name in ["crop"]:
                new_parcel = MaskedParcel(seed, building_type, self.maps)
            else:
                new_parcel = Parcel(seed, building_type, self.maps)
        elif isinstance(seed, Parcel):
            new_parcel = seed
        else:
            raise TypeError("Expected Point or Parcel, found {}".format(seed.__class__))
        self.__parcel_list.append(new_parcel)
        ObstacleMap().add_obstacle(*new_parcel.obstacle(AVERAGE_PARCEL_SIZE // 3))

    def remove_parcel(self, parcel: Parcel):
        # todo: notify interest of parcel deletion
        self.__parcel_list.remove(parcel)
        ObstacleMap().hide_obstacle(*parcel.obstacle(), True)

    def __handle_new_road_cycles(self, cycles):
        for road_cycle in map(cycle_preprocess, cycles):
            city_block = CityBlock(road_cycle, self.maps)
            max_block_surface = MAX_PARCELS_IN_BLOCK * (AVERAGE_PARCEL_SIZE ** 2)

            if city_block.surface > max_block_surface:
                continue  # block to big, must subdivide with roads before parcels

            else:
                old_parcels = list(filter(lambda p: p.center in city_block, self.__parcel_list))

                if old_parcels:
                    block_type = [p.building_type for p in old_parcels][-1]
                    for parcel in old_parcels:
                        self.remove_parcel(parcel)
                else:
                    block_type = self.__interest.get_optimal_type(city_block.center)

                for new_parcel in city_block.parcels(block_type):
                    self.add_parcel(new_parcel)

    def grow(self, time_limit: int, do_visu: bool):
        print("Seeding parcels")
        map_plots = VisuHandler(do_visu, self.maps, self.__parcel_list)
        build_iter = self.building_iterator

        t0 = time()
        for building_type in build_iter:

            print(f"\nTrying to place {building_type.name} - #{build_iter.count} out of {build_iter.size}")

            # Village Element Seeding Process
            self.__interest.reuse_existing_parcel(building_type)  # If succeeds should update building_type in place
            building_position = self.__interest.get_seed(building_type)

            if building_position is None:
                print("No suitable position found")
                continue

            print("Placed at x:{}, z:{}".format(building_position.x, building_position.z))

            # Road Creation Process
            cycles = self.maps.road_network.connect_to_network(building_position, margin=AVERAGE_PARCEL_SIZE/2)
            self.add_parcel(building_position, building_type)
            map_plots.handle_new_parcel(self.__interest[building_type])  # does nothing if not do_visu
            self.__handle_new_road_cycles(cycles)
            if time_limit and time() - t0 >= time_limit:
                print("Time limit reached: early stopping parcel seeding")
                break


class CityBlock(Bounds):
    """
    Large parcel surrounded by roads. Handles detection of this parcel (based on a road cycle) and optional subdivision
    """

    def __init__(self, road_cycle, maps):
        self.__road_points = road_cycle
        self.__maps = maps
        self.__origin, self.__mask = connected_component(mean(road_cycle).asPosition, self.connection)
        super().__init__(self.__origin, Point(self.__mask.width, self.__mask.length))

    @staticmethod
    def connection(src_point: Point, dst_point: Point) -> bool:
        net: RoadNetwork = RoadNetwork.INSTANCE
        return net.get_distance(dst_point) > 0

    def parcels(self, btype: BuildingType) -> List[Parcel]:
        def subdivide(_pos: Position, _mask: posarray, _ndiv: int) -> List[Tuple[Position, ndarray]]:
            if _ndiv == 1:
                return [(_pos, _mask)]

            n1, n2 = _ndiv // 2, _ndiv - _ndiv // 2
            if n1 != n2 and bernouilli(): n1, n2 = n2, n1
            optimal_score = n1 / _ndiv
            if mask.width > mask.length:
                # cut along x -> 1st index
                scores = [mask[cut:, :].sum() / mask.sum() for cut in range(mask.width)]
                cut = argmin([abs(optimal_score - score) for score in scores])
                mask1, mask2 = mask[cut:, :], mask[:cut, :]
                orig1, orig2 = _pos, _pos + Point(cut, 0)
            else:
                # cut along z -> 2nd index
                scores = [mask[:, cut:].sum() / mask.sum() for cut in range(mask.length)]
                cut = argmin([abs(optimal_score - score) for score in scores])
                mask1, mask2 = mask[:, cut:], mask[:, :cut]
                orig1, orig2 = _pos, _pos + Point(0, cut)

            return subdivide(orig1, mask1, n1) + subdivide(orig2, mask2, n2)

        orig = self.__origin
        mask = self.__mask
        parcel_count = 1 + self.surface // (AVERAGE_PARCEL_SIZE ** 2)
        return [MaskedParcel(pos, btype, self.__maps, mask) for (pos, mask) in subdivide(orig, mask, parcel_count)]

    @property
    def surface(self):
        return int(self.__mask.sum())

    @property
    def center(self):
        return self.__origin + Point(self.width // 2, self.length // 2)

    def __contains__(self, item: Point):
        return self.minx <= item.x < self.maxx and self.minz <= item.z < self.maxz and self.__mask[item - self.__origin]


def cycle_preprocess(road_points: Set[Point]) -> Set[Point]:
    # Build graph associated to the road paths
    graph: Dict[Point, Set[Point]] = {node: set() for node in road_points}  # graph as adjacency sets
    for node in road_points:
        for dx, dz in filter(any, product(range(-1, 2), range(-1, 2))):
            neighbour = node + Point(dx, dz)
            if neighbour in road_points:
                graph[node].add(neighbour)

    # Remove nodes not belonging to cycles
    def degree(_node: Point) -> int:
        return len(graph[node])

    extremities = {node for node in graph if degree(node) < 2}
    while extremities:
        node = extremities.pop()
        for neighbour in graph[node]:
            graph[neighbour].remove(node)
            if degree(neighbour) < 2:
                extremities.add(neighbour)

    # Find the larger cycle
    cycles = []
    road_points_copy = road_points.copy()
    while road_points_copy:
        to_explore = {road_points_copy.pop()}
        cycle = set()
        while to_explore:
            node1 = to_explore.pop()
            cycle.add(node1)
            to_explore.update(graph[node1].difference(cycle))
        cycles.append(cycle)

    from utils.misc_objects_functions import argmax
    return argmax(cycles, len)
