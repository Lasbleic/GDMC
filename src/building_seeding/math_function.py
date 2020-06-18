"""
Function used to compute interests
"""

from __future__ import division
from math import log, sqrt, exp
import matplotlib.pyplot as plt
import numpy as np


def attraction_repulsion(d, lambda_min, lambda_0, lambda_max):

    if d < lambda_min:
        res = -1

    elif d > lambda_max:
        res = 0

    else:
        a = log(sqrt(2) - 1) / (lambda_min - lambda_0)
        res = 2 * exp(-a * (d - lambda_0)) - exp(-2 * a * (d - lambda_0))

    return res


def balance(d, lambda_min, lambda_0, lambda_max):

    if d < lambda_min or d > lambda_max:
        res = -1

    else:
        lambda_tilde = lambda_min if d < lambda_0 else lambda_max
        a = -1.1
        res = (1 - a) * exp(- ((d - lambda_0) / (lambda_tilde - lambda_0)) ** 2 * log((a - 1) / (a + 1))) + a

    return res


def close_distance(d, lambdas):
    # type: (float, (float, float)) -> float
    lambda_min, lambda_max = lambdas
    if d <= lambda_min or d > lambda_max:
        res = -1

    else:
        res = balance(d, lambda_min, lambda_min, lambda_max)

    return res


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


if __name__ == '__main__':

    functions_to_test = [attraction_repulsion, balance]
    parameters_to_use = [(15, 20, 100), (10, 15, 35)]

    for function, parameters in zip(functions_to_test, parameters_to_use):

        lbd_min, lbd_0, lbda_max = parameters

        x_range = np.arange(0, lbda_max + 10, 0.1)
        y_range = np.array([])
        for x in x_range:
            y = function(x, lbd_min, lbd_0, lbda_max)
            y_range = np.append(y_range, y)

        plt.plot(x_range, y_range)
        title = "\nlambda_0 : {} ; lambda_min : {} ; lambda_max : {}".format(lbd_0, lbd_min, lbda_max)
        plt.title(function.__name__ + title)

        plt.show()
