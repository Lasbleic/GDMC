"""
Classes for generating and storing maps before using the visualization tool

A script is provided to show an example of the use of the classes and for preparing data for visualization

"""

from __future__ import division
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from os.path import isdir, join, exists, abspath, dirname
from os import mkdir
from shutil import rmtree

# Sizes accepted by the visualization tool
# with the size of the figure which is saved in a .png and the width of the grid lines
ACCEPTED_MAP_SIZES = {30: 0.25,
                      50: 0.25,
                      100: 0.20,
                      200: 0.15,
                      256: 0.10,
                      300: 0.07}



# Word accepted in user input
VALID_CHOICES = {"yes": 1, "ye": 1, "y": 1, "no": 0, "n": 0, "": 0}


class Map:
    """
    A Map represents a matrix with colors
    """

    def __init__(self, name, size, matrix, color_map, extreme_values, categories=None):
        """
        Create a Map with a specific size and coloration

        :param name: (String) Map's name
        :param size: (Int) The map is a size x size square
        :param matrix: (np.Array) Numpy array that represents the map
        :param color_map: (String or matplotlib.colors.Colormap) Coloration
        """

        assert ((size, size) == matrix.shape)
        self.name = name
        self.size = size
        self.matrix = matrix
        self.color_map = color_map
        self.extreme_values = extreme_values
        self.categories = categories


class MapStock:
    """
    A MapStock manages a storage directory in which it saves given Map of the same size
    """

    def __init__(self, name, map_size, clean_dir=None):
        """
        Create a MapStock with a specific Map size parameter

        :param name: (String) MapStock's name
        :param map_size: (Int) All the Maps managed by this MapStock must be a map_size x map_size square
        :param clean_dir: (Boolean or None, Default : None) Say weather or not the MapStock directory must be clean, if
                            it exists. That can occur when two MapStock with the same name are created or if a script is
                            launch several times. If None, ask the user during execution
        """
        assert (map_size in ACCEPTED_MAP_SIZES)
        self.name = name
        self.map_size = map_size
        self.directory = join(dirname(abspath(__file__)), "stock",
                              self.name + "_{}x{}".format(self.map_size, self.map_size))
        self.manage_directory(clean_dir)

    def manage_directory(self, clean_dir):
        """
        Create a new storage directory or manage the existing one

        :param clean_dir: (Boolean or None, Default : None) Say weather or not the MapStock directory must be clean, if
                            it exists. That can occur when two MapStock with the same name are created or if a script is
                            launch several times. If None, ask the user during execution
        """

        if isdir(self.directory):

            if clean_dir is None:
                while True:

                    print("{} already exists, do you want to clean it? [y/N]".format(self.directory))
                    user_choice = raw_input().lower()
                    if user_choice in VALID_CHOICES:
                        clean_dir = VALID_CHOICES[user_choice]
                        break
                    print("Please respond with 'yes'")

            if clean_dir:
                rmtree(self.directory)
                try:
                    mkdir(self.directory)
                except:
                    mkdir(self.directory)

        else:
            mkdir(self.directory)

    def add_map(self, map):
        """
        Add a map to the MapStock

        :param map: (Map) the Map to add, with the same size than the map_size parameter
        """
        assert (map.size == self.map_size)
        print("Adding {} map to the Stock...".format(map.name))
        self.save_map_to_png(map)

    def save_map_to_png(self, map):
        """
        Save a map as a .png file into the MapStock directory

        :param map: (Map) the Map to save
        """

        # Get predefined parameters
        lw = ACCEPTED_MAP_SIZES[self.map_size]

        # Create a figure
        fig = plt.figure()

        # Draw the grid
        for x in range(self.map_size + 1):
            plt.axhline(x, lw=lw, color='k', zorder=5)
            plt.axvline(x, lw=lw, color='k', zorder=5)

        # Draw the cells
        im = plt.imshow(map.matrix, interpolation='none', cmap=map.color_map, extent=[0, self.map_size, 0, self.map_size],
                   zorder=0, vmin=map.extreme_values[0], vmax=map.extreme_values[1])

        # Turn off the axis labels
        plt.axis('off')

        cbar = plt.colorbar()
        if map.categories:
            n = len(map.categories)
            cbar.set_ticks([map.extreme_values[1]*i/(2*n) for i in range(1, n*2, 2)])
            cbar.set_ticklabels(map.categories)



        # Save the figure
        file_path = join(self.directory, map.name + ".png")
        if exists(file_path):
            print("Replacing map...")
        dpi = fig.get_dpi()
        plt.savefig(file_path, dpi=dpi*9)    # increase dpi factor to improve quality

if __name__ == '__main__':
    N = 50

    # A Minecraft map with a path
    lvl_mat = np.zeros((N, N))

    lvl_mat[22:24, :24] = 1
    lvl_mat[16:24, 24:26] = 1
    lvl_mat[16:18, 24:] = 1

    lvl_cmap = matplotlib.colors.ListedColormap(['forestgreen', 'beige'])  # Use a list of color

    lvl_map = Map("level", 50, lvl_mat, lvl_cmap)

    # A handmade heatmap representing the accessibility
    hm_mat = np.zeros((N, N))
    hm_mat[19, :21] = 1
    hm_mat[20, :22] = 2
    hm_mat[21, :23] = 1
    hm_mat[24, :26] = 1
    hm_mat[25, :27] = 2
    hm_mat[26, :28] = 1

    hm_mat[13:20, 21] = 1
    hm_mat[14:21, 22] = 2
    hm_mat[15:22, 23] = 1
    hm_mat[18:25, 26] = 1
    hm_mat[19:26, 27] = 2
    hm_mat[20:27, 28] = 1

    hm_mat[13, 21:] = 1
    hm_mat[14, 22:] = 2
    hm_mat[15, 23:] = 1
    hm_mat[18, 26:] = 1
    hm_mat[19, 27:] = 2
    hm_mat[20, 28:] = 1

    hm_cmap = "jet"  # Use a predefined continuous coloration

    hm_map = Map("heatmap", 50, hm_mat, hm_cmap)

    # Create a MapStock and store the maps
    the_stock = MapStock("example", 50, clean_dir=True)
    the_stock.add_map(lvl_map)
    the_stock.add_map(hm_map)

    # You can know see them into the stock/example_50x50 directory or through the visualization tool
