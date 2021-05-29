import numba
import numpy as np

from building_seeding.interest import balance, X_ARRAY, Z_ARRAY
from building_seeding import Districts
from utils import *


def density(shape, districts, lambdas):
    # type: (tuple, Districts, tuple) -> ndarray
    assert len(shape) == 2 and len(lambdas) == 3
    # settlement_dimension = min(shape) / 2
    # interest_matrix = full(shape, -1)
    # from building_seeding import BuildingType
    # centers = [_.center for _ in filter(lambda parcel: parcel.building_type is BuildingType.ghost, districts)]
    # l_min, l_opt, l_max = lambdas
    # for x, z in product(range(shape[0]), range(shape[1])):
    #     distance = min(euclidean(Point(x, z), center) for center in centers) / settlement_dimension
    #     interest_matrix[x, z] = balance(distance, l_min, l_opt, l_max)

    density_matrix = None
    for town_index in districts.town_indexes:
        center = districts.district_centers[town_index]
        dist = districts.seeders[town_index]
        sig_x = dist.stdev_x
        sig_z = dist.stdev_z

        if density_matrix is None:
            density_matrix = density_one_district((center.x, center.z), (sig_x, sig_z))
        else:
            district_density = density_one_district((center.x, center.z), (sig_x, sig_z))
            density_matrix = np.minimum(density_matrix, district_density)

    interest_matrix = np.vectorize(lambda d: balance(d, *lambdas))(density_matrix)
    return interest_matrix


@numba.njit()
def density_one_district(xz, sigma):
    x, z = xz
    sig_x, sig_z = sigma

    x_dist = np.abs(X_ARRAY - x) / sig_x
    z_dist = np.abs(Z_ARRAY - z) / sig_z

    dist = np.sqrt(x_dist ** 2 + z_dist ** 2)
    return dist

# def local_density(shape, parcels, lambdas, position):
#     # type: (tuple, List[Parcel], tuple, Point) -> float
#     assert len(shape) == 2 and len(lambdas) == 3 and isinstance(position, Point)
#     settlement_dimension = min(shape) / 2
#     center = parcels[0].center
#     l_min, l_opt, l_max = lambdas
#     distance = euclidean(position, center) / settlement_dimension
#     return balance(distance, l_min, l_opt, l_max)
