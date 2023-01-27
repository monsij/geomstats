""" Testing file

"""
import numpy as np
from geomstats.geometry.special_euclidean import SpecialEuclidean
import geomstats.visualization as visualization
import matplotlib.pyplot as plt
import sys


SPACE_3 = SpecialEuclidean(n=3)
SPACE_2 = SpecialEuclidean(n=2)

def main():

    is_3D = False
    fig = plt.figure(figsize=(6,6))
    samples = 5
    viz = visualization.SpecialEuclidean2.plot_geodesic()
    plt.show()
    sys.exit()

    if is_3D:
        ax = fig.add_subplot(111, projection='3d')
        viz = visualization.SpecialEuclidean3()
        ax = viz.set_ax(ax = ax)
        
        
        random_pts = SPACE_3.random_point(n_samples = samples)
        translation = random_pts[..., :3, 3]

        make_zero_rot = False

        if make_zero_rot:
            no_rot = np.array([[1, 0, 0],[0, 1, 0],[0, 0, 1]])
            for i in range(samples):
                random_pts[i,:3,:3] = no_rot
        
    else:
        ax = fig.add_subplot(111)
        viz = visualization.SpecialEuclidean2()
        ax = viz.set_ax(ax = ax)
        viz.plot_geodesic()
        """
        random_pts = SPACE_2.random_point(n_samples = samples)
        
        make_zero_rot = False

        if make_zero_rot:
            no_rot = np.array([[1, 0],[0, 1]])
            for i in range(samples):
                random_pts[i,:2,:2] = no_rot
        """
    viz.draw_points(ax, random_pts, marker="o", c="blue")
    ax.set_xlim(-5, 5)
    ax.set_ylim(-5, 5)
    if is_3D:
        ax.set_zlim(-5, 5)

    plt.show()

    

if __name__== "__main__":
    main()