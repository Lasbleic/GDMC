from numpy.random import choice

from numba.core.types import UniTuple
from numba import i8, njit, jit
import numba
import numpy as np

from utils.misc_objects_functions import _in_limits

maxint = 1 << 32


def a_star(root_point, ending_point, dimensions, cost_function):
    # type: (Point, Point, Callable[[RoadNetwork, Point, Point], int]) -> List[Point]
    """
    Parameters
    ----------
    root_point path origin
    ending_point path destination
    cost_function (RoadNetwork, Point, Point) -> int

    Returns
    -------
    best first path from root_point to ending_point if any exists
    """
    distance_map, neighbors, predecessor_map = astar_env = _init(root_point, dimensions)

    clst_neighbor = root_point
    n_steps = 0
    while len(neighbors) > 0 and (clst_neighbor != ending_point):
        n_steps += 1
        clst_neighbor = _closest_neighbor(astar_env, ending_point)
        neighbors.remove(clst_neighbor)
        _update_distances(astar_env + (cost_function,), dimensions, clst_neighbor)

    if clst_neighbor != ending_point:
        return []
    else:
        return _path_to_dest(astar_env, root_point, ending_point)


def _init(point, dims):
    x, z = point
    _distance_map = np.full(dims, maxint)
    _distance_map[x][z] = 0
    _neighbours = {point}
    _predecessor_map = np.empty(dims, dtype=list)
    return _distance_map, _neighbours, _predecessor_map


@njit(cache=True)
def _closest_neighbor(env, destination):

    distance_map, neighbors = env[:2]
    closest_neighbors = [(0, 0)]
    min_heuristic = maxint
    for neighbor in neighbors:
        heuristic = _heuristic(neighbor, destination)
        x, z = neighbor
        current_heuristic = distance_map[x, z] + heuristic
        if current_heuristic < min_heuristic:
            closest_neighbors = [neighbor]
            min_heuristic = current_heuristic
        elif current_heuristic == min_heuristic:
            closest_neighbors += [neighbor]
    return closest_neighbors[np.random.randint(0, len(closest_neighbors))]


@njit(cache=True)
def _heuristic(point, destination):
    x0, z0 = point
    xf, zf = destination
    return 1.1 * np.sqrt((xf - x0) ** 2 + (zf - z0) ** 2)


@jit(forceobj=True, cache=True)
def _update_distance(env, updated_point, neighbor):
    distance_map, neighbors, predecessor_map, cost = env
    edge_cost = cost(updated_point, neighbor)
    if edge_cost == maxint:
        return

    new_distance = distance_map[updated_point] + edge_cost
    previous_distance = distance_map[neighbor]
    if previous_distance >= maxint:
        neighbors.add(neighbor)
        # neighbors.append(neighbor)
    if previous_distance > new_distance:
        distance_map[neighbor] = new_distance
        predecessor_map[neighbor] = updated_point


@jit(forceobj=True, cache=True)
def _update_distances(env, dims, point):
    x, z = point  # type: int, int
    for xz in _exploration_neighbourhood(x, z, *dims):
        _update_distance(env, point, xz)


def _path_to_dest(env, origin, destination):
    distance_map, neighbors, predecessor_map = env
    current_point = destination
    path = [destination]
    while current_point != origin:
        current_point = predecessor_map[current_point]
        path.append(current_point)
    return list(reversed(path))


@njit(cache=True)
def _exploration_neighbourhood(x, z, width, length):
    neighbourhood = set()
    for dx, dz in [(0, 1), (-1, 2), (0, 2), (1, 2)]:
        for _ in numba.prange(4):
            dx, dz = dz, -dx
            x0, z0 = x+dx, z+dz
            if _in_limits((x0, 0, z0), width, length):
                neighbourhood.add((x0, z0))
    return neighbourhood
