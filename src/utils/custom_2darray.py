import numpy as np
from .geometry_utils import Point


class PointArray(np.ndarray):
    """
    Custom 2d array that can handle points at coordinates
    """
    def __new__(cls, values: np.ndarray, *args, **kwargs):
        return np.asarray(values).view(cls)

    def __array_finalize__(self, obj):
        if obj is None:
            return

    def __getitem__(self, item):
        if isinstance(item, Point):
            item = item.x, item.z
        return super(PointArray, self).__getitem__(item)

    def __setitem__(self, key, value):
        if isinstance(key, Point):
            return self.__setitem__((key.x, key.z), value)
        return super(PointArray, self).__setitem__(key, value)

    def __array_ufunc__(self, ufunc, method, *inputs, out=None, **kwargs):
        super_inputs = [a.view(np.ndarray) if isinstance(a, PointArray) else a for a in inputs]
        res = super().__array_ufunc__(ufunc, method, *super_inputs, **kwargs)
        return res.view(PointArray) if isinstance(res, np.ndarray) else res

    @property
    def width(self):
        return self.shape[0]

    @property
    def length(self):
        return self.shape[1]
