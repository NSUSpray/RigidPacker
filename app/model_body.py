from math import pi, sqrt, sin, cos, hypot, atan2
from random import random

from Box2D import b2World, b2Body, b2_staticBody, b2_dynamicBody
from PyQt5.QtCore import QTimer

from utilities.geometry import outersected


_ZERO_VECTOR = (0.0, 0.0)


class _BodyBase:

    def __init__(self):
        self._b2body: b2Body = None

    @property
    def __fixture(self): return self._b2body.fixtures[0]
    @property
    def __shape(self): return self.__fixture.shape

    @property
    def __density(self): return self.__fixture.density

    @__density.setter
    def __density(self, density):
        self.__fixture.density = density
        self._b2body.ResetMassData()

    @property
    def _area(self): r = self.radius; return pi * r*r
    @_area.setter
    def _area(self, area): self.radius = sqrt(area/pi)

    @property
    def _mass(self): return self._b2body.mass or self.__density*self._area
    # density-area option is needed when the body is static (pinched)

    @_mass.setter
    def _mass(self, mass): self.__density = mass / self._area

    @property
    def position(self): return self._b2body.position
    @position.setter
    def position(self, position): self._b2body.position = position

    @property
    def radius(self): return self.__shape.radius

    @radius.setter
    def radius(self, radius):
        mass = self._mass
        self.__shape.radius = radius
        self.__density = mass / self._area


class _InteractiveBodyMixin:

    def __init__(self):
        self.__last_velocity = _ZERO_VECTOR
        self.__drag_point = _ZERO_VECTOR
        self._drag_target = None

    def _pinch_b2body(self):
        self.__last_velocity = self._b2body.linearVelocity.copy()
        self._b2body.type = b2_staticBody

    def _release_b2body(self):
        self._b2body.type = b2_dynamicBody
        self._b2body.linearVelocity = self.__last_velocity

    def _release_b2body_calmly(self):
        self._b2body.type = b2_dynamicBody

    def _start_dragging_b2body(self, drag_point):
        self.__drag_point = drag_point
        self._b2body.bullet = True

    def _drag_b2body(self, drag_target):
        self._drag_target = drag_target
        self._release_b2body_calmly()

    def _finish_dragging_b2body(self):
        self._drag_target = None
        def set_bullet_to_false(): self._b2body.bullet = False
        QTimer.singleShot(3000, set_bullet_to_false)

    def drag_b2body(self):
        factor = -10.0 / self._total_mass  # real inertia
        # factor = -10.0 / sqrt(self._total_mass)  # compromise
        # factor = -10.0  # best dynamism
        velocity = [
            (point+pos-target)*factor for point, target, pos
            in zip(self.__drag_point, self._drag_target, self.position)
        ]
        self._b2body.linearVelocity = velocity


class BodyContainerMixin(_InteractiveBodyMixin, _BodyBase):

    def __init__(self, time_step):
        _InteractiveBodyMixin.__init__(self)
        _BodyBase.__init__(self)
        self.__b2subworld: b2World = None
        self._time_step = time_step

    def __rake_in(self, outersected_):
        radius = self.radius
        position = self.position
        factor = -3000.0*outersected_ * radius*radius / position.length
        force = [pos*factor for pos in position]
        # point = (0.0, 0.0)  # TODO: touchpoint
        self._b2body.ApplyForce(force=force, point=_ZERO_VECTOR, wake=False)

    @property
    def _total_mass(self): return self._mass
    @_total_mass.setter
    def _total_mass(self, mass): self._mass = mass

    def _create_b2subworld(self):
        if self.__b2subworld: return
        self.__b2subworld = b2World(gravity=_ZERO_VECTOR)

    def destroy_b2body(self):
        self._parent.__b2subworld.DestroyBody(self._b2body)
        self._b2body = None

    def _create_b2body(self):
        if self._b2body:
            mass, area = self._total_mass, self._area
            self._model.queue_to_destroy(self)
        else:
            mass, area = self.self_mass, self.self_volume
        b2body = self._parent.__b2subworld.CreateDynamicBody()
        b2body.CreateCircleFixture(
            radius = sqrt(area/pi),
            friction = 1.0,
            density = mass / area,
            restitution = 0.3,
        )
        b2body.linearDamping = 1.0
        b2body.angularDamping = 1.0
        b2body.userData = self
        self._b2body = b2body

    def _awake_b2bodies(self):
        for b2body in self.__b2subworld.bodies:
            b2body.awake = True

    def _throw_in(self, children, target=None):
        target = target or _ZERO_VECTOR
        target_radius = hypot(*target)
        '''
        if target_radius and self.radius and target_radius <= self.radius:
            beam_width = 2*acos(target_radius/self.radius)
            beam_width = beam_width**3/(pi*pi)
        else:
            beam_width = pi
        '''
        beam_width = (1 - target_radius/self.radius)**2 * pi
        ratio = beam_width / sum(child.radius for child in children)
        current_angle = atan2(*reversed(target)) - beam_width
        cos_sin = (cos, sin)
        for child in children:
            distance = self.radius + child.radius
            angular_radius = child.radius * ratio
            azimuth = current_angle + angular_radius
            current_angle += 2*angular_radius
            start = [distance*fn(azimuth) for fn in cos_sin]
            factor = 5*random()
            velocity = [factor*(tg-st) for tg, st in zip(target, start)]
            child.position = start
            child._b2body.linearVelocity = velocity

    def _step_b2subworld(self):
        parent_radius = self.radius
        # parent_radius = self._b2body.fixtures[0].shape.radius
        for child in self._children:
            b2body = child._b2body
            outersected_ = outersected(
                b2body.fixtures[0].shape.radius,  # child.radius,
                parent_radius,
                b2body.position.length,  # child.position.length,
            )
            if outersected_: child.__rake_in(outersected_)
            if child._drag_target: child.drag_b2body()
        self.__b2subworld.Step(self._time_step, 10, 10)
        self.__b2subworld.ClearForces()

    def _step_b2subworlds(self):
        '''
        for child in self._children:
            if not child._children: continue
            child._step_b2subworlds()
        self._step_b2subworld()
        '''
        for item in self._and_childrened_descendants:
            item._step_b2subworld()

    def _step_b2superworld(self): self._parent._step_b2subworld()

    def _step_b2superworlds(self):
        '''
        self._step_b2superworld()
        if self._parent._parent: self._parent._step_b2superworlds()
        '''
        for ancestor in self._ancestors:
            ancestor._step_b2subworld()


class BodyHierarchyMixin:
    """
    __radius, __total_mass, position, radius, _total_mass are dummies
    for root instances (without b2body)
    """

    def __init__(self):
        self.__radius: float
        self.__total_mass: float
        self._area = self.self_volume
        self._total_mass = self.self_mass
        self._b2bodies_to_destroy = []

    @property
    def _total_mass(self): return self.__total_mass
    @_total_mass.setter
    def _total_mass(self, mass): self.__total_mass = mass

    def _destroy_b2bodies_to_destroy(self):
        for b2body in self._b2bodies_to_destroy:
            b2body.world.DestroyBody(b2body)
        self._b2bodies_to_destroy = []

    @property
    def time_step(self): return self._time_step

    @time_step.setter
    def time_step(self, time_step):
        for self_or_descendant in (self, *self._descendants):
            self_or_descendant._time_step = time_step

    @property
    def position(self): return _ZERO_VECTOR

    @property
    def radius(self): return self.__radius
    @radius.setter
    def radius(self, radius): self.__radius = radius

    def queue_to_destroy(self, item):
        self._b2bodies_to_destroy.append(item._b2body)
