from building_seeding import Parcel
from building_seeding.interest.math_function import balance
from utils import *


def density(shape, parcels, lambdas):
    # type: (tuple, List[Parcel], tuple) -> ndarray
    assert len(shape) == 2 and len(lambdas) == 3
    settlement_dimension = min(shape) / 2
    interest_matrix = full(shape, -1)
    center = parcels[0].center
    l_min, l_opt, l_max = lambdas
    for x, z in product(range(shape[0]), range(shape[1])):
        distance = euclidean(Point(x, z), center) / settlement_dimension
        interest_matrix[x, z] = balance(distance, l_min, l_opt, l_max)
    return interest_matrix


# def local_density(shape, parcels, lambdas, position):
#     # type: (tuple, List[Parcel], tuple, Point) -> float
#     assert len(shape) == 2 and len(lambdas) == 3 and isinstance(position, Point)
#     settlement_dimension = min(shape) / 2
#     center = parcels[0].center
#     l_min, l_opt, l_max = lambdas
#     distance = euclidean(position, center) / settlement_dimension
#     return balance(distance, l_min, l_opt, l_max)
