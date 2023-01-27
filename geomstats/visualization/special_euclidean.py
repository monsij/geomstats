"""Visualization for Geometric Statistics.

consolidated version

Lead authors: past
"""


import logging

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # NOQA

import geomstats.backend as gs
from geomstats.geometry.special_euclidean import SpecialEuclidean
import geomstats.visualization as visualization

SE2_GROUP = SpecialEuclidean(n=2, point_type="matrix")
SE2_VECT = SpecialEuclidean(n=2, point_type="vector")
LEFT_METRIC = SE2_VECT.left_canonical_metric
RIGHT_METRIC = SE2_VECT.right_canonical_metric

class SpecialEuclidean2:
    """Class used to plot points in the 2d special euclidean group."""

    def __init__(self, points=None, point_type="matrix"):
        self.points = []
        self.point_type = point_type
        if points is not None:
            self.add_points(points)

    @staticmethod
    def set_ax(ax=None, x_lim=None, y_lim=None):
        if ax is None:
            ax = plt.subplot()
        if x_lim is not None:
            ax.set_xlim(x_lim)
        if y_lim is not None:
            ax.set_ylim(y_lim)
        return ax

    def add_points(self, points):
        if self.point_type == "vector":
            points = SE2_VECT.matrix_from_vector(points)
        if not gs.all(SE2_GROUP.belongs(points)):
            logging.warning("Some points do not belong to SE2.")
        if not isinstance(points, list):
            points = list(points)
        self.points.extend(points)

    def draw_points(self, ax, points=None, **kwargs):
        if points is None:
            points = gs.array(self.points)
        translation = points[..., :2, 2]
        frame_1 = points[:, :2, 0]
        frame_2 = points[:, :2, 1]
        ax.quiver(
            translation[:, 0],
            translation[:, 1],
            frame_1[:, 0],
            frame_1[:, 1],
            width=0.005,
            color="b",
        )
        ax.quiver(
            translation[:, 0],
            translation[:, 1],
            frame_2[:, 0],
            frame_2[:, 1],
            width=0.005,
            color="r",
        )
        ax.scatter(translation[:, 0], translation[:, 1], s=16, **kwargs)
    
    
    def plot_geodesic():  #add points, N_STEPS, kwargs
        """
        Plots a geodesic of SE(2).
        """
        N_STEPS = 40
        initial_point = SE2_VECT.identity
        initial_tangent_vec = gs.array([1.8, 0.2, 0.3])
        geodesic = LEFT_METRIC.geodesic(
            initial_point=initial_point, initial_tangent_vec=initial_tangent_vec
        )

        t = gs.linspace(-3.0, 3.0, N_STEPS)

        points = geodesic(t)
        points_mat = SE2_VECT.matrix_from_vector(points)  # required as plot for SpecialEuclidean2 expects matrix form
        visualization.plot(points_mat, space="SE2_GROUP")
        #plt.show() # prevents pytest warning

        



SE3_GROUP = SpecialEuclidean(n=3, point_type="matrix")
SE3_VECT = SpecialEuclidean(n=3, point_type="vector")
METRIC = SE3_VECT.left_canonical_metric
        
class SpecialEuclidean3:
    """Class used to plot points in the 3d special euclidean group."""

    def __init__(self, points=None, point_type="matrix"):
        self.points = []
        self.point_type = point_type
        if points is not None:
            self.add_points(points)

    @staticmethod
    def set_ax(ax=None, x_lim=None, y_lim=None):
        if ax is None:
            ax = plt.subplot(111, projection='3d')
        if x_lim is not None:
            ax.set_xlim(x_lim)
        if y_lim is not None:
            ax.set_ylim(y_lim)
        return ax

    def add_points(self, points):
        if self.point_type == "vector":
            points = SE3_VECT.matrix_from_vector(points)
        if not gs.all(SE3_GROUP.belongs(points)):
            logging.warning("Some points do not belong to SE3.")
        if not isinstance(points, list):
            points = list(points)
        self.points.extend(points)

    def draw_points(self, ax, points=None, **kwargs):
        if points is None:
            points = gs.array(self.points)
        translation = points[..., :3, 3]
        frame_1 = points[:, :3, 0]
        frame_2 = points[:, :3, 1]
        frame_3 = points[:, :3, 2]
        ax.quiver(
            translation[:, 0],
            translation[:, 1],
            translation[:, 2],
            frame_1[:, 0],
            frame_1[:, 1],
            frame_1[:, 2],
            color="b",
        )
        ax.quiver(
            translation[:, 0],
            translation[:, 1],
            translation[:, 2],
            frame_2[:, 0],
            frame_2[:, 1],
            frame_2[:, 2],
            color="r",
        )
        ax.quiver(
            translation[:, 0],
            translation[:, 1],
            translation[:, 2],
            frame_3[:, 0],
            frame_3[:, 1],
            frame_3[:, 2],
            color="g",
        )
        ax.scatter(translation[:, 0], translation[:, 1], translation[:, 2], s=20, **kwargs)
    
    def plot_geodesic():
        N_STEPS = 40
        initial_point = SE3_VECT.identity
        initial_tangent_vec = gs.array([1.8, 0.2, 0.3, 3.0, 3.0, 1.0])
        geodesic = METRIC.geodesic(
            initial_point=initial_point, initial_tangent_vec=initial_tangent_vec
        )

        t = gs.linspace(-3.0, 3.0, N_STEPS)

        points = geodesic(t)

        visualization.plot(points, space="SE3_GROUP")
        #plt.show()  # prevents pytest warning