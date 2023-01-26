# Testing visualization for SE(2) (already in geomstats)


import numpy as np
from geomstats.geometry.special_euclidean import SpecialEuclidean
import geomstats.visualization as visualization
import matplotlib.pyplot as plt

SPACE = SpecialEuclidean(n=2)   # 2x2 and 2 scalars = 3x3([],[],[0,0,1])


def main():

    fig = plt.figure(figsize=(8,8))
    ax = fig.add_subplot(111)
    viz = visualization.SpecialEuclidean2()
    ax = viz.set_ax(ax = ax)

    samples = 20
    random_pts = SPACE.random_point(n_samples = samples)
    
    make_zero_rot = False

    if make_zero_rot:
        no_rot = np.array([[1, 0],[0, 1]])
        for i in range(samples):
            random_pts[i,:2,:2] = no_rot
        

    viz.draw_points(ax, random_pts, marker="o", c="blue")
    plt.show()
    
if __name__== "__main__":
    main()
