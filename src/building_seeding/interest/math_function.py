"""
Function used to compute interests
"""

from numba import njit
from numpy import log, sqrt, exp


@njit
def attraction_repulsion(d, lambda_min, lambda_0, lambda_max):

    if d < lambda_min:
        res = -1

    elif d > lambda_max:
        res = 0

    else:
        a = log(sqrt(2) - 1) / (lambda_min - lambda_0)
        res = 2 * exp(-a * (d - lambda_0)) - exp(-2 * a * (d - lambda_0))

    return res


@njit
def balance(d, lambda_min, lambda_0, lambda_max):

    if d < lambda_min or d > lambda_max:
        res = -1

    else:
        lambda_tilde = lambda_min if d < lambda_0 else lambda_max
        a = -1.1
        res = (1 - a) * exp(- ((d - lambda_0) / (lambda_tilde - lambda_0)) ** 2 * log((a - 1) / (a + 1))) + a

    return res


@njit
def close_distance(d, lambdas):
    # type: (float, (float, float)) -> float
    lambda_min, lambda_max = lambdas
    if d <= lambda_min or d > lambda_max:
        res = -1

    else:
        res = balance(d, 0, lambda_min, lambda_max)

    return res


@njit
def open_distance(d, lambdas):
    lambda_min, lambda_max = lambdas
    if d <= lambda_min:
        return 1
    else:
        return close_distance(d, lambdas)


@njit
def obstacle(d, lambdas):
    # type: (float, (float, float)) -> float
    """
    Obstacle type interest base function:
    below lambda min (lambdas[0]), impossible to spawn
    between lambdas, possible but unwanted
    above lambda max, neutral
    """
    lambda_min, lambda_max = lambdas
    if d <= lambda_min:
        return -1
    elif d >= lambda_max:
        return 0
    else:
        return balance(d, lambda_min, lambda_max, lambda_max)
