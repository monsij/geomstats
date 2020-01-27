"""Riemannian and pseudo-Riemannian metrics."""

import math
import warnings

import geomstats.backend as gs

EPSILON = 1e-4
N_CENTERS = 10
TOLERANCE = 1e-5
N_REPETITIONS = 20
N_MAX_ITERATIONS = 50000


def loss(y_pred, y_true, metric):
    """Compute loss given by a Riemannian metric.

    Loss function given by a Riemannian metric expressed as the squared
    geodesic distance between the prediction and the ground truth.

    Parameters
    ----------
    y_pred
    y_true
    metric

    Returns
    -------
    loss
    """
    loss = metric.squared_dist(y_pred, y_true)
    return loss


def grad(y_pred, y_true, metric):
    """Compute closed-form for the gradient of the loss function."""
    tangent_vec = metric.log(base_point=y_pred, point=y_true)
    grad_vec = - 2. * tangent_vec

    inner_prod_mat = metric.inner_product_matrix(base_point=y_pred)

    grad = gs.einsum('ni,nij->ni',
                     grad_vec,
                     gs.transpose(inner_prod_mat, axes=(0, 2, 1)))

    return grad


class RiemannianMetric(object):
    """Class for Riemannian and pseudo-Riemannian metrics."""

    def __init__(self, dimension, signature=None):
        assert isinstance(dimension, int) or dimension == math.inf
        assert dimension > 0
        self.dimension = dimension
        self.signature = signature

    def inner_product_matrix(self, base_point=None):
        """Compute inner product matrix at the tangent space at base point.

        Parameters
        ----------
        base_point : array-like, shape=[n_samples, dimension], optional
        """
        raise NotImplementedError(
            'The computation of the inner product matrix'
            ' is not implemented.')

    def inner_product_inverse_matrix(self, base_point=None):
        """Compute inner prod. inv. matrix at the tangent space at base point.

        Parameters
        ----------
        base_point : array-like, shape=[n_samples, dimension], optional
        """
        raise NotImplementedError(
            'The computation of the inner product inv. matrix'
            ' is not implemented.')

    def inner_product(self, tangent_vec_a, tangent_vec_b, base_point=None):
        """Compute inner product between two tangent vectors at a base point.

        Parameters
        ----------
        tangent_vec_a: array-like, shape=[n_samples, dimension]
                                   or shape=[1, dimension]
        tangent_vec_b: array-like, shape=[n_samples, dimension]
                                   or shape=[1, dimension]
        base_point: array-like, shape=[n_samples, dimension]
                                or shape=[1, dimension]

        Returns
        -------
        inner_product
        """
        tangent_vec_a = gs.to_ndarray(tangent_vec_a, to_ndim=2)
        tangent_vec_b = gs.to_ndarray(tangent_vec_b, to_ndim=2)
        n_tangent_vec_a = gs.shape(tangent_vec_a)[0]
        n_tangent_vec_b = gs.shape(tangent_vec_b)[0]

        inner_prod_mat = self.inner_product_matrix(base_point)
        inner_prod_mat = gs.to_ndarray(inner_prod_mat, to_ndim=3)
        n_mats = gs.shape(inner_prod_mat)[0]

        if n_tangent_vec_a != n_mats:
            if n_tangent_vec_a == 1:
                tangent_vec_a = gs.squeeze(tangent_vec_a, axis=0)
                einsum_str_a = 'j,njk->nk'
            elif n_mats == 1:
                inner_prod_mat = gs.squeeze(inner_prod_mat, axis=0)
                einsum_str_a = 'nj,jk->nk'
            else:
                raise ValueError('Shape mismatch for einsum.')
        else:
            einsum_str_a = 'nj,njk->nk'

        aux = gs.einsum(einsum_str_a, tangent_vec_a, inner_prod_mat)
        n_auxs, _ = gs.shape(aux)

        if n_tangent_vec_b != n_auxs:
            if n_auxs == 1:
                aux = gs.squeeze(aux, axis=0)
                einsum_str_b = 'k,nk->n'
            elif n_tangent_vec_b == 1:
                tangent_vec_b = gs.squeeze(tangent_vec_b, axis=0)
                einsum_str_b = 'nk,k->n'
            else:
                raise ValueError('Shape mismatch for einsum.')
        else:
            einsum_str_b = 'nk,nk->n'

        inner_prod = gs.einsum(einsum_str_b, aux, tangent_vec_b)
        inner_prod = gs.to_ndarray(inner_prod, to_ndim=2, axis=1)

        assert gs.ndim(inner_prod) == 2, inner_prod.shape
        return inner_prod

    def squared_norm(self, vector, base_point=None):
        """Compute the squared norm of a vector.

        Squared norm of a vector associated to the inner product
        at the tangent space at a base point.

        Parameters
        ----------
        vector: array-like, shape=[n_samples, dimension]
                            or shape=[1, dimension]
        base_point: array-like, shape=[n_samples, dimension]
                                or shape=[1, dimension]

        Returns
        -------
        sq_norm
        """
        sq_norm = self.inner_product(vector, vector, base_point)
        return sq_norm

    def norm(self, vector, base_point=None):
        """Compute norm of a vector.

        Norm of a vector associated to the inner product
        at the tangent space at a base point.

        Note: This only works for positive-definite
        Riemannian metrics and inner products.

        Parameters
        ----------
        vector: array-like, shape=[n_samples, dimension]
                            or shape=[1, dimension]

        base_point: array-like, shape=[n_samples, dimension]
                                or shape=[1, dimension]

        Returns
        -------
        norm
        """
        sq_norm = self.squared_norm(vector, base_point)
        norm = gs.sqrt(sq_norm)
        return norm

    def exp(self, tangent_vec, base_point=None):
        """Compute Riemannian exponential of tangent vector wrt to base point.

        Parameters
        ----------
        tangent_vec: array-like, shape=[n_samples, dimension]
                                 or shape=[1, dimension]
        base_point: array-like, shape=[n_samples, dimension]
                                or shape=[1, dimension]

        Returns
        -------
        exp
        """
        raise NotImplementedError(
            'The Riemannian exponential is not implemented.')

    def log(self, point, base_spoint=None):
        """Compute Riemannian logarithm of a point wrt a base point.

        Parameters
        ----------
        point: array-like, shape=[n_samples, dimension]
                           or shape=[1, dimension]

        base_point: array-like, shape=[n_samples, dimension]
                                or shape=[1, dimension]

        Returns
        -------
        log
        """
        raise NotImplementedError(
            'The Riemannian logarithm is not implemented.')

    def geodesic(self, initial_point,
                 end_point=None, initial_tangent_vec=None,
                 point_type='vector'):
        """Compute geodesic curve.

        Geodesic curve defined by either:
        - an initial point and an initial tangent vector, or
        -an initial point and an end point.

        The geodesic is returned as a function parameterized by t.

        Parameters
        ----------
        initial_point
        end_point
        initial_tangent_vec
        point_type

        Returns
        -------
        point_on_geodesic : callable
        """
        point_ndim = 1
        if point_type == 'matrix':
            point_ndim = 2

        initial_point = gs.to_ndarray(initial_point,
                                      to_ndim=point_ndim + 1)

        if end_point is None and initial_tangent_vec is None:
            raise ValueError('Specify an end point or an initial tangent '
                             'vector to define the geodesic.')
        if end_point is not None:
            end_point = gs.to_ndarray(end_point,
                                      to_ndim=point_ndim + 1)
            shooting_tangent_vec = self.log(point=end_point,
                                            base_point=initial_point)
            if initial_tangent_vec is not None:
                assert gs.allclose(shooting_tangent_vec, initial_tangent_vec)
            initial_tangent_vec = shooting_tangent_vec
        initial_tangent_vec = gs.array(initial_tangent_vec)
        initial_tangent_vec = gs.to_ndarray(initial_tangent_vec,
                                            to_ndim=point_ndim + 1)

        def point_on_geodesic(t):
            """Generate a function parameterizing the geodesic.

            Parameters
            ----------
            t

            Returns
            -------
            point_at_time_t : callable
            """
            t = gs.cast(t, gs.float32)
            t = gs.to_ndarray(t, to_ndim=1)
            t = gs.to_ndarray(t, to_ndim=2, axis=1)
            new_initial_point = gs.to_ndarray(
                initial_point,
                to_ndim=point_ndim + 1)
            new_initial_tangent_vec = gs.to_ndarray(
                initial_tangent_vec,
                to_ndim=point_ndim + 1)

            if point_type == 'vector':
                tangent_vecs = gs.einsum('il,nk->ik',
                                         t,
                                         new_initial_tangent_vec)
            elif point_type == 'matrix':
                tangent_vecs = gs.einsum('il,nkm->ikm',
                                         t,
                                         new_initial_tangent_vec)

            point_at_time_t = self.exp(tangent_vec=tangent_vecs,
                                       base_point=new_initial_point)
            return point_at_time_t

        return point_on_geodesic

    def squared_dist(self, point_a, point_b):
        """Compute squared geodesic distance between two points.

        Parameters
        ----------
        point_a: array-like, shape=[n_samples, dimension]
                             or shape=[1, dimension]
        point_b: array-like, shape=[n_samples, dimension]
                             or shape=[1, dimension]

        Returns
        -------
        sq_dist
        """
        log = self.log(point=point_b, base_point=point_a)
        sq_dist = self.squared_norm(vector=log, base_point=point_a)

        return sq_dist

    def dist(self, point_a, point_b):
        """Compute geodesic distance between two points.

        Note: It only works for positive definite Riemannian metrics.

        Parameters
        ----------
        point_a: array-like, shape=[n_samples, dimension]
                             or shape=[1, dimension]
        point_b: array-like, shape=[n_samples, dimension]
                             or shape=[1, dimension]

        Returns
        -------
        dist
        """
        sq_dist = self.squared_dist(point_a, point_b)
        dist = gs.sqrt(sq_dist)
        return dist

    def variance(self,
                 points,
                 weights=None,
                 base_point=None,
                 point_type='vector'):
        """Compute variance of (weighted) points wrt a base point.

        Parameters
        ----------
        points: array-like, shape=[n_samples, dimension]
        weights: array-like, shape=[n_samples, 1], optional

        Returns
        -------
        variance
        """
        if point_type == 'vector':
            points = gs.to_ndarray(points, to_ndim=2)
        if point_type == 'matrix':
            points = gs.to_ndarray(points, to_ndim=3)
        n_points = gs.shape(points)[0]

        if weights is None:
            weights = gs.ones((n_points, 1))

        weights = gs.array(weights)
        weights = gs.to_ndarray(weights, to_ndim=2, axis=1)

        sum_weights = gs.sum(weights)

        if base_point is None:
            base_point = self.mean(points, weights)

        variance = 0.

        sq_dists = self.squared_dist(base_point, points)
        variance += gs.einsum('nk,nj->j', weights, sq_dists)

        variance = gs.array(variance)
        variance /= sum_weights

        variance = gs.to_ndarray(variance, to_ndim=1)
        variance = gs.to_ndarray(variance, to_ndim=2, axis=1)
        return variance

    def mean(self, points,
             weights=None,
             n_max_iterations=32,
             epsilon=EPSILON,
             point_type='vector',
             verbose=False):
        """Compute the Frechet mean of (weighted) points.

        Parameters
        ----------
        points: array-like, shape=[n_samples, dimension]
        weights: array-like, shape=[n_samples, 1], optional
        verbose: bool, optional

        Returns
        -------
        mean
        """
        # TODO(nina): Profile this code to study performance,
        # i.e. what to do with sq_dists_between_iterates.
        def while_loop_cond(iteration, mean, variance, sq_dist):
            result = ~gs.logical_or(
                gs.isclose(variance, 0.),
                gs.less_equal(sq_dist, epsilon * variance))
            return result[0, 0] or iteration == 0

        def while_loop_body(iteration, mean, variance, sq_dist):
            logs = self.log(point=points, base_point=mean)
            tangent_mean = gs.einsum('nk,nj->j', weights, logs)

            tangent_mean /= sum_weights

            mean_next = self.exp(
                tangent_vec=tangent_mean,
                base_point=mean)

            sq_dist = self.squared_dist(mean_next, mean)
            sq_dists_between_iterates.append(sq_dist)

            variance = self.variance(points=points,
                                     weights=weights,
                                     base_point=mean_next)

            mean = mean_next
            iteration += 1
            return [iteration, mean, variance, sq_dist]

        if point_type == 'vector':
            points = gs.to_ndarray(points, to_ndim=2)
        if point_type == 'matrix':
            points = gs.to_ndarray(points, to_ndim=3)
        n_points = gs.shape(points)[0]

        if weights is None:
            weights = gs.ones((n_points, 1))

        weights = gs.array(weights)
        weights = gs.to_ndarray(weights, to_ndim=2, axis=1)

        sum_weights = gs.sum(weights)

        mean = points[0]
        if point_type == 'vector':
            mean = gs.to_ndarray(mean, to_ndim=2)
        if point_type == 'matrix':
            mean = gs.to_ndarray(mean, to_ndim=3)

        if n_points == 1:
            return mean

        sq_dists_between_iterates = []
        iteration = 0
        sq_dist = gs.array([[0.]])
        variance = gs.array([[0.]])

        last_iteration, mean, variance, sq_dist = gs.while_loop(
            lambda i, m, v, sq: while_loop_cond(i, m, v, sq),
            lambda i, m, v, sq: while_loop_body(i, m, v, sq),
            loop_vars=[iteration, mean, variance, sq_dist],
            maximum_iterations=n_max_iterations)

        if last_iteration == n_max_iterations:
            warnings.warn('Maximum number of iterations {} reached.'
                  'The mean may be inaccurate'.format(n_max_iterations))

        if verbose:
            print('n_iter: {}, final variance: {}, final dist: {}'.format(
                last_iteration, variance, sq_dist))

        mean = gs.to_ndarray(mean, to_ndim=2)
        return mean

    def adaptive_gradientdescent_mean(self, points,
                                      weights=None,
                                      n_max_iterations=32,
                                      epsilon=1e-12,
                                      init_points=[]):
        """Compute Frechet mean of (weighted) points using adaptive time-steps.

        The loss function optimized is ||M_1(x)||_x (where M_1(x) is
        the tangent mean at x) rather than the mean-square-distance (MSD)
        because this saves computation time.

        Parameters
        ----------
        points: array-like, shape=[n_samples, dimension]
        weights: array-like, shape=[n_samples, 1], optional
        init_points: array-like, shape=[n_init, dimension]
        epsilon: tolerance for stopping the gradient descent

        Returns
        -------
        mean
        """
        # TODO(Xavier): This function assumes that all points are lists
        #  of vectors and not of matrices
        n_points = gs.shape(points)[0]

        if weights is None:
            weights = gs.ones((n_points, 1))

        weights = gs.array(weights)
        weights = gs.to_ndarray(weights, to_ndim=2, axis=1)

        sum_weights = gs.sum(weights)

        n_init = len(init_points)

        if n_init == 0:
            current_mean = points[0]
        else:
            current_mean = init_points[0]

        if n_points == 1:
            return gs.to_ndarray(current_mean, to_ndim=2)

        tau = 1.0
        iter = 0

        logs = self.log(point=points, base_point=current_mean)
        current_tangent_mean = gs.einsum('nk,nj->j', weights, logs)
        current_tangent_mean /= sum_weights
        norm_current_tangent_mean = gs.linalg.norm(current_tangent_mean)

        while (norm_current_tangent_mean > epsilon
                and iter < n_max_iterations):
            iter = iter + 1
            shooting_vector = gs.to_ndarray(
                tau * current_tangent_mean,
                to_ndim=2)
            next_mean = self.exp(
                tangent_vec=shooting_vector,
                base_point=current_mean)
            logs = self.log(point=points, base_point=next_mean)
            next_tangent_mean = gs.einsum('nk,nj->j', weights, logs)
            next_tangent_mean /= sum_weights
            norm_next_tangent_mean = gs.linalg.norm(next_tangent_mean)
            if norm_next_tangent_mean < norm_current_tangent_mean:
                current_mean = next_mean
                current_tangent_mean = next_tangent_mean
                norm_current_tangent_mean = norm_next_tangent_mean
                tau = max(1.0, 1.0511111 * tau)
            else:
                tau = tau * 0.8

        if iter == n_max_iterations:
            print('Maximum number of iterations {} reached.'
                  'The mean may be inaccurate'.format(n_max_iterations))

        return gs.to_ndarray(current_mean, to_ndim=2)

    def tangent_pca(self, points, base_point=None, point_type='vector'):
        """Perform tPCA of points on the tangent space at a base point.

        Tangent Principal Component Analysis (tPCA) of points
        on the tangent space at a base point.

        Parameters
        ----------
        points
        base_point
        point_type

        Returns
        -------
        eigenvalues
        tangent_eigenvecs
        """
        if point_type == 'matrix':
            raise NotImplementedError(
                'This is currently only implemented for vectors.')
        if base_point is None:
            base_point = self.mean(points)

        tangent_vecs = self.log(points, base_point=base_point)

        covariance_mat = gs.cov(tangent_vecs.transpose())
        eigenvalues, tangent_eigenvecs = gs.linalg.eig(covariance_mat)

        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        tangent_eigenvecs = tangent_eigenvecs[idx]

        return eigenvalues, tangent_eigenvecs

    def diameter(self, points):
        """Compute distance between the two points farthest from each other.

        Parameters
        ----------
        points

        Returns
        -------
        diameter
        """
        diameter = 0.0
        n_points = points.shape[0]

        for i in range(n_points - 1):
            dist_to_neighbors = self.dist(points[i, :], points[i + 1:, :])
            dist_to_farthest_neighbor = gs.amax(dist_to_neighbors)
            diameter = gs.maximum(diameter, dist_to_farthest_neighbor)

        return diameter

    def closest_neighbor_index(self, point, neighbors):
        """Compute closest neighbor of point among neighbors.

        Parameters
        ----------
        point
        neighbors

        Returns
        -------
        closest_neighbor_index
        """
        dist = self.dist(point, neighbors)
        closest_neighbor_index = gs.argmin(dist)

        return closest_neighbor_index
