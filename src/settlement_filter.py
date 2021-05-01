"""
Main script
TODO : wait for GDMC instructions on how to link the client to the server
"""
import logging
from time import gmtime, strftime, time

from flat_settlement import FlatSettlement
from terrain import TerrainMaps
from utils import interfaceUtils, WorldSlice, BuildArea

logging.basicConfig(filename='settlement_log_{}.log'.format(strftime('%Y-%m-%d_%H-%M-%S', gmtime())), level=logging.INFO)

option_time_limit = "time_limit"  # "10' limit"
option_debug = "debug"  # "Debug mode: does not catch exceptions in generation"
option_visu = "visualization"  # "Visualization tool: plots iterations of building placement"

# #%%
# import numpy as np
# import matplotlib.pyplot as plt
# from sklearn.preprocessing import StandardScaler
# from utils import bernouilli
# forget_rate = .7
# coord_scales = [_/100. for _ in range(75, 126, 5)]
# coord_scales = [1.15]
# for coord_scale in coord_scales:
#     n_clusters = 12
#     X = np.array([[x, y, terrain.height_map.steepness(x, y),
#                    terrain.height_map.lower_height(x, y)]
#                   for x, y in product(range(terrain.width), range(terrain.length))
#                   if bernouilli(1-forget_rate) and not terrain.fluid_map.is_close_to_fluid(x, y)])
#     x, y = X[:, 0], -X[:, 1]
#     print(X.shape[0], "samples")
#     scaler = StandardScaler().fit(X)
#     Xs = scaler.transform(X)
#     Xs[:, :2] = Xs[:, :2] * coord_scale
#     kmeans = KMeans(n_clusters=n_clusters).fit(Xs)
#     color = ["#" + ''.join([random.choice(hexadecimal_alphabets) for j in range(6)]) for i in range(len(kmeans.cluster_centers_))]
#     c = [color[cluster] for cluster in kmeans.labels_]
#     plt.scatter(x, y, c=c)
#     xc = scaler.inverse_transform(kmeans.cluster_centers_)[:, 0]
#     yc = -scaler.inverse_transform(kmeans.cluster_centers_)[:, 1]
#     plt.scatter(xc, yc, s=100, c='k', marker='+')
#     plt.title(f"{n_clusters} clusters - scaling factor: {coord_scale}")
#     plt.show()
#
# #%%
# from collections import Counter
# dist = Counter(kmeans.labels_)
# ndist = {u: v/len(kmeans.labels_) for u, v in dist.items()}
# weak_labels = {u for u, v in dist.items() if v < 0.05}
# #%%
# labels = [-1 if _ in weak_labels else _ for _ in kmeans.labels_]
# nn = 3
# tol = 1
# labelsProp = LabelPropagation('knn', n_neighbors=nn, tol=tol).fit(Xs[:, :2], labels)
# labels2 = labelsProp.predict(Xs[:, :2])
# c2 = [color[cluster] for cluster in labels2]
# plt.scatter(x, y, c=c2)
# plt.title(f"knn:{nn} tol:{tol}")
# plt.show()
# #%%
# labels = set(kmeans.labels_)
# cluster_score, cluster_size = {}, {}
# XY = np.append(X, kmeans.labels_.reshape(-1, 1), 1)
# for label in labels:
#     cluster = Xy[Xy[:, 4] == label]
#     score = cluster[:, 2].mean()
#     cluster_score[label] = score
#     cluster_size[label] = cluster.shape[0]
# #%%


if __name__ == '__main__':
    options = {
        option_time_limit: "600",
        option_debug: False,
        option_visu: False
    }
    t0 = time()
    print("Hello Settlers!")
    # get & parse building zone
    terrain = TerrainMaps.request()
    # exit(0)

    settlement = FlatSettlement(terrain)
    settlement.init_town_center()   # define town settlement as point close to roads and geometric center of the box
    settlement.init_road_network()  # define outside connections
    # exit(0)
    t2 = time()
    settlement.build_skeleton(options[option_time_limit], options[option_visu])  # define buildings list and seed them
    print("calcul du squelette", time() - t2)
    try:
        settlement.define_parcels()     # define parcels around seeds
    except RuntimeWarning:
        pass
    settlement.generate(terrain, options[option_debug])      # build buildings on parcels
    print('{} seconds of execution'.format(time() - t0))

