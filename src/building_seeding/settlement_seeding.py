from typing import List, Set, Tuple
import numpy as np
import numba
import random
from matplotlib import pyplot as plt
from sklearn.cluster import KMeans
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from terrain import TerrainMaps
from terrain.map import Map
from utils import Point, product, manhattan, full, BuildArea, bernouilli, euclidean
from utils.misc_objects_functions import argmax, argmin


class Districts:
    """
    Districts construction -> partitions the build area and select zones that will become settlements.
    Was implemented to add structure to large inputs
    """
    def __init__(self, area: BuildArea):
        self.width = area.width
        self.length = area.length
        self.__cluster_map = full((self.width, self.length), 0)
        self.__scaler = StandardScaler()
        self.__coord_scale = 1
        self.seeds: List[Point] = None
        self.town_centers: List[Point] = None
        self.district_map: Map = None
        self.cluster_size = {}
        self.cluster_suitability = {}
        self.built_seeds = set()

    def build(self, maps: TerrainMaps, **kwargs):
        visualize = kwargs.get("visualize", False)
        X, Xu = self.__build_data(maps)
        cluster_approx = np.sqrt(self.width * self.length) // 50
        print("cluster approx", cluster_approx)
        min_clusters = int(cluster_approx / 2)
        max_clusters = int(np.ceil(cluster_approx * 1.3))
        if max_clusters < 2:
            kwargs["n_clusters"] = 1
        print(f"there'll be between {min_clusters} and {max_clusters} districts")
        min_clusters = max(2, min_clusters)
        max_clusters = min(12, max_clusters)

        def select_best_model():
            if kwargs.get("n_clusters", 0):
                return self.__kmeans(X, kwargs.get("n_clusters"), visualize)

            models, scores = [], []
            for n_clusters in range(max(2, min_clusters), max_clusters + 1):
                model: KMeans = self.__kmeans(X, n_clusters, visualize)
                models.append(model)
                if X.shape[0] < 10000:
                    scores.append(silhouette_score(X, model.labels_))
                else:
                    sample = np.random.randint(X.shape[0], size=10000)
                    scores.append(silhouette_score(X[sample, :], model.labels_[sample]))
                print("silhouette", scores[-1])

            if visualize:
                plt.plot(range(2, max_clusters + 1), scores)
                plt.title("Silhouette score as a function of n_clusters")
                plt.show()

            index = argmax(range(len(models)), key=lambda i: scores[i])
            return models[index]

        model = select_best_model()

        labels = set(model.labels_)
        for label in labels:
            cluster = X[model.labels_ == label]
            score = cluster[:, 2].mean()
            self.cluster_suitability[label] = score
            self.cluster_size[label] = cluster.shape[0]

        centers = self.__scaler.inverse_transform(model.cluster_centers_ / self.__coord_scale)
        seeds = [Point(round(_[0]), round(_[1])) for _ in centers]
        samples = [Point(Xu[i, 0], Xu[i, 1]) for i in range(Xu.shape[0])]
        self.seeds = [argmin(samples, key=lambda sample: euclidean(seed, sample)) for seed in seeds]

        def select_town_clusters():
            surface_to_build = X.shape[0] * .25
            surface_built = 0
            for index, _ in sorted(self.cluster_suitability.items(), key=lambda _: _[1], reverse=True):
                self.built_seeds.add(index)
                surface_built += self.cluster_size[index]
                if surface_built >= surface_to_build:
                    break
            return list(sorted(self.built_seeds, key=(lambda i: self.cluster_suitability[i]), reverse=True))

        town_indexes = select_town_clusters()
        self.town_centers = [self.seeds[index] for index in town_indexes]

        self.__build_cluster_map(model, Xu, town_indexes)

    def __build_data(self, maps: TerrainMaps, coord_scale=1.15):
        n_samples = min(1e5, self.width * self.length)
        keep_rate = n_samples / (self.width * self.length)
        Xu = np.array([[x, z, Districts.suitability(x, z, maps)]
                      for x, z in product(range(maps.width), range(maps.length))
                      if bernouilli(keep_rate) and not maps.fluid_map.is_close_to_fluid(x, z)])
        X = self.__scaler.fit_transform(Xu)
        X[:, :2] = X[:, :2] * coord_scale
        self.__coord_scale = coord_scale
        print(f"{X.shape[0]} samples to select districts")
        return X, Xu

    def __kmeans(self, X: np.ndarray, n_clusters, visualize=False, coord_scale=1.15):
        print(f"Selecting {n_clusters} districts")
        kmeans = KMeans(n_clusters=n_clusters, tol=1e-5).fit(X)
        if visualize:
            Xu = self.__scaler.inverse_transform(X)
            x, y = Xu[:, 0], -Xu[:, 1]
            color = ["#" + ''.join([random.choice("ABCDEF0123456789") for j in range(6)]) for i in range(len(kmeans.cluster_centers_))]
            c = [color[cluster] for cluster in kmeans.labels_]
            plt.scatter(x, y, c=c)
            xc = self.__scaler.inverse_transform(kmeans.cluster_centers_)[:, 0]
            yc = -self.__scaler.inverse_transform(kmeans.cluster_centers_)[:, 1]
            plt.scatter(xc, yc, s=100, c='k', marker='+')
            plt.title(f"{n_clusters} clusters - scaling factor: {coord_scale}")
            plt.show()

        return kmeans

    @staticmethod
    def suitability(x, z, terrain: TerrainMaps):
        return terrain.height_map.steepness(x, z)

    def __build_cluster_map(self, clusters: KMeans, samples: np.ndarray, town_indexes: List[int]):
        town_score = {label: 1 / (index + 1) for (index, label) in enumerate(town_indexes)}
        label_score = np.array([town_score[label] if (label in town_score) else 0 for label in range(max(clusters.labels_) + 1)], dtype=np.float32)
        propagation = KNeighborsClassifier(n_neighbors=3, n_jobs=-1)
        propagation.fit(samples[:, :2], clusters.labels_)

        # all locations of the build area in a flattened array
        distribution = np.array([[x, z] for x, z in product(range(self.width), range(self.length))])

        # cluster index for each of these locations
        neighborhood = propagation.predict(distribution)  # type: np.ndarray

        # reshaped cluster matrix
        neighborhood = neighborhood.reshape((self.width, self.length))

        # transform this matrix to interest of building here
        values = np.vectorize(lambda label: label_score[label])(neighborhood)

        # store results
        self.district_map = Map(neighborhood)
        self.score_map = Map(values)

    @property
    def n_districts(self):
        return len(self.seeds)

    @property
    def buildable_surface(self):
        return sum(self.cluster_size[i] for i in self.built_seeds)


def min_spanning_tree(points: List[Point]) -> Set[Tuple[Point, Point]]:
    n = len(points)

    # Init graph
    weights = full((n, n), -1)
    edges = []

    for i, j in filter(lambda ij: ij[0] < ij[1], product(range(n), range(n))):
        weights[i, j] = weights[j, i] = manhattan(points[i], points[j])
        edges.append((i, j))
    edges.sort(key=lambda e: weights[e[0], e[1]])

    # Connected components
    p_to_comp = {i: i for i in range(n)}
    comp_to_p = {i: [i] for i in range(n)}

    def join_components(_c1, _c2):
        for _ in comp_to_p[_c2]:
            p_to_comp[_] = _c1
        comp_to_p[_c1].extend(comp_to_p[_c2])
        del comp_to_p[_c2]

    tree_edges: Set[Tuple[Point, Point]] = set()
    for (i, j) in edges:
        comp_i, comp_j = p_to_comp[i], p_to_comp[j]
        if comp_i != comp_j:
            join_components(comp_i, comp_j)
            tree_edges.add((points[i], points[j]))

    return tree_edges


if __name__ == '__main__':
    from random import randint
    SIZE = 100
    N_POINTS = 15
    points = [Point(randint(0, SIZE), randint(0, SIZE)) for _ in range(N_POINTS)]
    print(points)

    plt.scatter([_.x for _ in points], [_.z for _ in points])
    for p1, p2 in min_spanning_tree(points):
        plt.plot([p1.x, p2.x], [p1.z, p2.z])
    plt.show()