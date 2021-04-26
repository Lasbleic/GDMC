from typing import List, Set, Tuple

from utils import Point, product, manhattan, full


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
    from matplotlib import pyplot as plt
    from random import randint
    SIZE = 100
    N_POINTS = 15
    points = [Point(randint(0, SIZE), randint(0, SIZE)) for _ in range(N_POINTS)]
    print(points)

    plt.scatter([_.x for _ in points], [_.z for _ in points])
    for p1, p2 in min_spanning_tree(points):
        plt.plot([p1.x, p2.x], [p1.z, p2.z])
    plt.show()