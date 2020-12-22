"""Classes for fiber bundles and quotient metrics."""

from scipy.optimize import minimize

import geomstats.backend as gs
from geomstats.geometry.manifold import Manifold
from geomstats.geometry.riemannian_metric import RiemannianMetric


class FiberBundle(Manifold):
    """Class for (principal) fiber bundles.

    This class implements abstract methods for fiber bundles, or more
    generally manifolds, with a submersion map, or a right Lie group action.

    Parameters
    ----------
    total_space : Manifold
        Total space of the bundle.
    base : Manifold
        Base manifold of the bundle.
        Optional. Default : None.
    group : LieGroup
        Group that acts on the total space by the right.
        Optional. Default : None.
        Either the group or the group action must be given.
    group_action : callable
        Right group action. It must take as input a point of the total space
        and an element of the group, and return a point of the total space.
    dim : int
        Dimension of the base manifold.
        Optional. If available the dimension of the base manifold is used,
        or the difference between the dimension of the total space and the
        group. Either dim, base or group must be given as input.
    """

    def __init__(self, total_space, base=None, group=None, group_action=None,
                 dim=None, **kwargs):

        if dim is None:
            if base is not None:
                dim = base.dim
            elif group is not None:
                dim = total_space.dim - group.dim
            else:
                raise ValueError('Either the base manifold, '
                                 'its dimension, or the group acting on the '
                                 'total space must be provided.')

        super(FiberBundle, self).__init__(dim=dim, **kwargs)

        self.base = base
        self.total_space = total_space
        self.group = group

        if group_action is None and group is not None:
            group_action = group.compose
        self.group_action = group_action

    def belongs(self, point, atol=1e-6):
        """Evaluate if a point belongs to the base manifold.

        Evaluate if a point belongs to the base manifold when it is given,
        otherwise to the total space.

        Parameters
        ----------
        point : array-like, shape=[..., dim]
            Point to evaluate.
        atol : float
            Absolute tolerance.
            Optional, default: 1e-6.

        Returns
        -------
        belongs : array-like, shape=[...,]
            Boolean evaluating if point belongs to the manifold.
        """
        if self.base is not None:
            return self.base.belongs(point, atol=atol)
        return self.total_space.belongs(point, atol=atol)

    def submersion(self, point):
        """Project a point to base manifold.

        This is the projection of the fiber bundle, defined on the total
        space, with values in the base manifold. This map is surjective.
        By default, the base manifold  is not explicit but is identified with a
        local section of the fiber bundle, so the submersion is the identity
        map.

        Parameters
        ----------
        point: array-like, shape=[..., {ambient_dim, [n, n]}]
            Point of the total space.

        Returns
        -------
        projection: array-like, shape=[..., {dim, [n, n]}]
            Point of the base manifold.
        """
        return point

    def lift(self, point):
        """Lift a point to total space.

        This is a section of the fiber bundle, defined on the base manifold,
        with values in the total space. It means that submersion applied after
        lift results in the identity map. By default, the base manifold
        is not explicit but is identified with a section of the fiber bundle,
        so the lift is the identity map.

        Parameters
        ----------
        point: array-like, shape=[..., {dim, [n, n]}]
            Point of the base manifold.

        Returns
        -------
        lift: array-like, shape=[..., {ambient_dim, [n, n]}]
            Point of the total space.
        """
        return point

    def tangent_submersion(self, tangent_vec, base_point):
        """Project a tangent vector to base manifold.

        This is the differential of the projection of the fiber bundle,
        defined on the tangent space of a point of the total space,
        with values in the tangent space of the projection of this point in the
        base manifold. This map is surjective. By default, the base manifold
        is not explicit but is identified with a horizontal section of the
        fiber bundle, so the tangent submersion is the horizontal projection.

        Parameters
        ----------
        tangent_vec :  array-like, shape=[..., ambient_dim, [n , n]}]
            Tangent vector to the total space at `base_point`.
        base_point: array-like, shape=[..., {ambient_dim, [n, n]}]
            Point of the total space.

        Returns
        -------
        projection: array-like, shape=[..., {dim, [n, n]}]
            Tangent vector to the base manifold.
        """
        return self.horizontal_projection(tangent_vec, base_point)

    def align(self, point, base_point, max_iter=25, verbose=False, tol=1e-6):
        """Align point to base_point.

        Find the optimal group element g such that the base point and
        point.g are well positioned, meaning that the total space distance is
        minimized. This also means that the geodesic joining the base point
        and the aligned point is horizontal. By default, this is solved by a
        gradient descent in the Lie algebra.

        Parameters
        ----------
        point : array-like, shape=[..., {ambient_dim, [n, n]}]
            Point on the manifold.
        base_point : array-like, shape=[..., {ambient_dim, [n, n]}]
            Point on the manifold.
        max_iter : int
            Maximum number of gradient steps.
            Optional, default : 25.
        verbose : bool
            Verbosity level.
            Optional, default : False.
        tol : float
            Tolerance for the stopping criterion.
            Optional, default : 1e-6

        Returns
        -------
        aligned : array-like, shape=[..., {ambient_dim, [n, n]}]
            Action of the optimal g on point.
        """
        group = self.group
        initial_distance = self.total_space.metric.squared_dist(
            point, base_point)
        if isinstance(initial_distance, float) or initial_distance.shape == ():
            n_samples = 1
        else:
            n_samples = len(initial_distance)

        max_shape = (n_samples, group.dim) if n_samples > 1 else \
            (group.dim, )

        def wrap(param):
            """Wrap a parameter vector to a group element."""
            algebra_elt = gs.array(param)
            algebra_elt = gs.cast(algebra_elt, dtype=base_point.dtype)
            algebra_elt = group.lie_algebra.matrix_representation(
                algebra_elt)
            group_elt = group.exp(algebra_elt)
            return self.group_action(point, group_elt)

        objective_with_grad = gs.autograd.value_and_grad(
            lambda param: self.total_space.metric.squared_dist(
                wrap(param), base_point))

        tangent_vec = gs.flatten(gs.random.rand(*max_shape))
        res = minimize(
            objective_with_grad, tangent_vec, method='L-BFGS-B', jac=True,
            options={'disp': verbose, 'maxiter': max_iter}, tol=tol)

        return wrap(res.x)

    def horizontal_projection(self, tangent_vec, base_point):
        r"""Project to horizontal subspace.

        Compute the horizontal component of a tangent vector at a
        base point by removing the vertical component,
        or by computing a horizontal lift of the tangent projection.

        Parameters
        ----------
        tangent_vec : array-like, shape=[..., {ambient_dim, [n, n]}]
            Tangent vector to the total space at `base_point`.
        base_point : array-like, shape=[..., {ambient_dim, [n, n]}]
            Point on the total space.

        Returns
        -------
        horizontal : array-like, shape=[..., {ambient_dim, [n, n]}]
            Horizontal component of `tangent_vec`.
        """
        try:
            return tangent_vec - self.vertical_projection(
                tangent_vec, base_point)
        except (RecursionError, NotImplementedError):
            return self.horizontal_lift(
                self.tangent_submersion(tangent_vec, base_point),
                base_point)

    def vertical_projection(self, tangent_vec, base_point):
        r"""Project to vertical subspace.

        Compute the vertical component of a tangent vector :math: `w` at a
        base point :math: `x` by removing the horizontal component.

        Parameters
        ----------
        tangent_vec : array-like, shape=[..., {ambient_dim, [n, n]}]
            Tangent vector to the total space at `base_point`.
        base_point : array-like, shape=[..., {ambient_dim, [n, n]}]
            Point on the total space.

        Returns
        -------
        vertical : array-like, shape=[..., {ambient_dim, [n, n]}]
            Vertical component of `tangent_vec`.
        """
        try:
            return tangent_vec - self.horizontal_projection(
                tangent_vec, base_point)
        except RecursionError:
            raise NotImplementedError

    def is_horizontal(self, tangent_vec, base_point, atol=1e-6):
        """Evaluate if the tangent vector is horizontal at base_point.

        Parameters
        ----------
        tangent_vec : array-like, shape=[..., {ambient_dim, [n, n]}]
            Tangent vector.
        base_point : array-like, shape=[..., {ambient_dim, [n, n]}]
            Point on the manifold.
            Optional, default: None.
        atol : float
            Absolute tolerance.
            Optional, default: 1e-6.

        Returns
        -------
        is_horizontal : bool
            Boolean denoting if tangent vector is horizontal.
        """
        return gs.all(gs.isclose(
            tangent_vec, self.horizontal_projection(tangent_vec, base_point),
            atol=atol), axis=(-2, -1))

    def is_vertical(self, tangent_vec, base_point, atol=1e-6):
        """Evaluate if the tangent vector is vertical at base_point.

        Parameters
        ----------
        tangent_vec : array-like, shape=[..., {ambient_dim, [n, n]}]
            Tangent vector.
        base_point : array-like, shape=[..., {ambient_dim, [n, n]}]
            Point on the manifold.
            Optional, default: None.
        atol : float
            Absolute tolerance.
            Optional, default: 1e-6.

        Returns
        -------
        is_vertical : bool
            Boolean denoting if tangent vector is vertical.
        """
        return gs.all(gs.isclose(
            tangent_vec, self.vertical_projection(tangent_vec, base_point),
            atol=atol), axis=(-2, -1))

    def horizontal_lift(self, tangent_vec, point=None, base_point=None):
        """Lift a tangent vector to a horizontal vector in the total space.

        It means that horizontal lift is the inverse of the restriction of the
        tangent submersion to the horizontal space at point, where point must
        be in the fiber above the base point. By default, the base manifold
        is not explicit but is identified with a horizontal section of the
        fiber bundle, so the horizontal lift is the horizontal projection.

        Parameters
        ----------
        tangent_vec : array-like, shape=[..., {dim, [n, n]}]
        point: array-like, shape=[..., {ambient_dim, [n, n]}]
            Point of the total space.
            Optional, default : None. The `lift` method is used to compute a
            point at which to compute a tangent vector.
        base_point : array-like, shape=[..., {dim, [n, n]}]
            Point of the base space.
            Optional, default : None. In this case, point must be given,
            and `submersion` is used to compute the base_point if needed.

        Returns
        -------
        horizontal_lift : array-like, shape=[..., {ambient_dim, [n, n]}]
            Tangent vector to the total space at point.
        """
        if point is None:
            if base_point is not None:
                point = self.lift(base_point)
            else:
                raise ValueError('Either a point (of the total space) or a '
                                 'base point (of the base manifold) must be '
                                 'given.')
        return self.horizontal_projection(tangent_vec, point)


class QuotientMetric(RiemannianMetric):
    """Quotient metric.

    Given a (principal) fiber bundle, or more generally a manifold with a
    Lie group acting on it by the right, the quotient space is the space of
    orbits under this action. The quotient metric is defined such that the
    canonical projection is a Riemannian submersion, i.e. it is isometric to
    the restriction of the metric of the total space to horizontal subspaces.

    Parameters
    ----------
    fiber_bundle : FiberBundle
        Bundle structure to define the quotient.
    group : LieGroup
        Group acting on the right.
        Optional, default : None. In this case the group must be passed to
        the fiber bundle instance.
    ambient_metric : RiemannianMetric
        Metric of the total space.
        Optional, default : None. In this case, the total space must have a
        metric as an attribute.
    """

    def __init__(self, fiber_bundle, group=None, ambient_metric=None):
        super(QuotientMetric, self).__init__(
            dim=fiber_bundle.dim,
            default_point_type=fiber_bundle.default_point_type)

        self.fiber_bundle = fiber_bundle
        if group is None:
            group = fiber_bundle.group
        if ambient_metric is None:
            ambient_metric = fiber_bundle.total_space.metric

        self.group = group
        self.ambient_metric = ambient_metric

    def inner_product(
            self, tangent_vec_a, tangent_vec_b, base_point=None, point=None):
        """Compute the inner-product of two tangent vectors at a base point.

        Parameters
        ----------
        tangent_vec_a : array-like, shape=[..., {dim, [n, n]}]
            Tangent vector to the quotient manifold.
        tangent_vec_b : array-like, shape=[..., {dim, [n, n]}]
            Tangent vector to the quotient manifold.
        base_point : array-like, shape=[..., {dim, [n, n]}]
            Point on the quotient manifold.
            Optional, default: None.
        point : array-like, shape=[..., {dim, [n, n]}]
            Point on the total space, lift of `base_point`, i.e. such that
            `submersion` applied to `point` results in `base_point`.
            Optional, default: None. In this case, it is computed using the
            method lift.

        Returns
        -------
        inner_product : float, shape=[...]
            Inner products
        """
        if point is None:
            if base_point is not None:
                point = self.fiber_bundle.lift(base_point)
            else:
                raise ValueError('Either a point (of the total space) or a '
                                 'base point (of the quotient manifold) must '
                                 'be given.')
        horizontal_a = self.fiber_bundle.horizontal_lift(tangent_vec_a, point)
        horizontal_b = self.fiber_bundle.horizontal_lift(tangent_vec_b, point)
        return self.ambient_metric.inner_product(
            horizontal_a, horizontal_b, point)

    def exp(self, tangent_vec, base_point, **kwargs):
        """Compute the Riemannian exponential of a tangent vector.

        Parameters
        ----------
        tangent_vec : array-like, shape=[..., {dim, [n, n]}]
            Tangent vector to the quotient manifold.
        base_point : array-like, shape=[..., {dim, [n, n]}]
            Point on the quotient manifold.
            Optional, default: None.

        Returns
        -------
        exp : array-like, shape=[..., {dim, [n, n]}]
            Point on the quotient manifold.
        """
        lift = self.fiber_bundle.lift(base_point)
        horizontal_vec = self.fiber_bundle.horizontal_lift(
            tangent_vec, lift)
        return self.fiber_bundle.submersion(
            self.ambient_metric.exp(horizontal_vec, lift))

    def log(self, point, base_point, **kwargs):
        """Compute the Riemannian logarithm of a point.

        Parameters
        ----------
        point : array-like, shape=[..., {dim, [n, n]}]
            Point on the quotient manifold.
        base_point : array-like, shape=[..., {dim, [n, n]}]
            Point on the quotient manifold.

        Returns
        -------
        log : array-like, shape=[..., {dim, [n, n]}]
            Tangent vector at the base point equal to the Riemannian logarithm
            of point at the base point.
        """
        point_fiber = self.fiber_bundle.lift(point)
        bp_fiber = self.fiber_bundle.lift(base_point)
        aligned = self.fiber_bundle.align(point_fiber, bp_fiber, **kwargs)
        return self.fiber_bundle.tangent_submersion(
            self.ambient_metric.log(aligned, base_point), base_point)

    def squared_dist(self, point_a, point_b, **kwargs):
        """Squared geodesic distance between two points.

        Parameters
        ----------
        point_a : array-like, shape=[...,  {dim, [n, n]}]
            Point.
        point_b : array-like, shape=[...,  {dim, [n, n]}]
            Point.

        Returns
        -------
        sq_dist : array-like, shape=[...,]
            Squared distance.
        """
        lift_a = self.fiber_bundle.lift(point_a)
        lift_b = self.fiber_bundle.lift(point_b)
        aligned = self.fiber_bundle.align(lift_a, lift_b, **kwargs)
        return self.ambient_metric.squared_dist(aligned, lift_b)
