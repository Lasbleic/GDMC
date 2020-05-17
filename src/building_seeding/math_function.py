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


if __name__ == '__main__':

    functions_to_test = [attraction_repulsion, balance]

    for function in functions_to_test:

        lbd_min = 5
        lbd_0 = 10
        lbda_max = 25

        x_range = np.arange(0, lbda_max + 10, 0.1)
        y_range = np.array([])
        for x in x_range:
            y = function(x, lbd_min, lbd_0, lbda_max)
            y_range = np.append(y_range, y)

        plt.plot(x_range, y_range)
        plt.title(function.__name__ + "\nlambda_0 : {} ; lambda_min : {} ; lambda_max : {}".format(lbd_0, lbd_min, lbda_max))

        plt.show()
