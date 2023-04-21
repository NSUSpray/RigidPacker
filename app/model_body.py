from math import pi, sqrt, sin, cos, hypot, atan2
from random import random

from Box2D import b2World, b2Body, b2_staticBody, b2_dynamicBody
from PyQt5.QtCore import QTimer

from utilities.geometry import outersected


_ZERO_VECTOR = (0.0, 0.0)


class _BodyBase:

    def __init__(self):
        self.b2body: b2Body = None

    @property
    def position(self): return self.b2body.position
    @position.setter
    def position(self, position): self.b2body.position = position

    @property
    def _fixture(self): return self.b2body.fixtures[0]
    @property
    def _shape(self): return self._fixture.shape

    @property
    def radius(self): return self._shape.radius

    @radius.setter
    def radius(self, radius):
        mass = self.mass
        self._shape.radius = radius
        self.density = mass / self.area

    @property
    def area(self): r = self.radius; return pi * r*r
    @area.setter
    def area(self, area): self.radius = sqrt(area/pi)

    @property
    def mass(self): return self.b2body.mass or self.density*self.area
    # density-area option is needed when the body is static (pinched)

    @mass.setter
    def mass(self, mass): self.density = mass / self.area

    @property
    def density(self): return self._fixture.density

    @density.setter
    def density(self, density):
        self._fixture.density = density
        self.b2body.ResetMassData()


class _InteractiveBodyMixin:

    def __init__(self):
        self._last_velocity = _ZERO_VECTOR
        self.drag_point = _ZERO_VECTOR
        self.drag_target = None

    def _pinch_b2body(self):
        self._last_velocity = self.b2body.linearVelocity.copy()
        self.b2body.type = b2_staticBody

    def _release_b2body(self):
        self.b2body.type = b2_dynamicBody
        self.b2body.linearVelocity = self._last_velocity

    def _release_b2body_calmly(self):
        self.b2body.type = b2_dynamicBody

    def _start_dragging_b2body(self, drag_point):
        self.drag_point = drag_point
        self.b2body.bullet = True

    def _drag_b2body(self, drag_target):
        self.drag_target = drag_target
        self._release_b2body_calmly()

    def _finish_dragging_b2body(self):
        self.drag_target = None
        def set_bullet_to_false(): self.b2body.bullet = False
        QTimer.singleShot(3000, set_bullet_to_false)

    def drag_b2body(self):
        factor = -10.0 / self.total_mass  # real inertia
        # factor = -10.0 / sqrt(self.total_mass)  # compromise
        # factor = -10.0  # best dynamism
        velocity = [
            (point + pos - target)*factor for point, target, pos
                in zip(self.drag_point, self.drag_target, self.position)
            ]
        self.b2body.linearVelocity = velocity


class BodyContainerMixin(_InteractiveBodyMixin, _BodyBase):

    def __init__(self, time_step):
        _InteractiveBodyMixin.__init__(self)
        _BodyBase.__init__(self)
        self.time_step = time_step
        self.b2subworld: b2World = None

    @property
    def total_mass(self): return self.mass
    @total_mass.setter
    def total_mass(self, mass): self.mass = mass

    def _create_subworld(self):
        if self.b2subworld: return
        self.b2subworld = b2World(gravity=_ZERO_VECTOR)

    def destroy_b2body(self):
        self.parent.b2subworld.DestroyBody(self.b2body)
        self.b2body = None

    def create_b2body(self):
        if self.b2body:
            mass, area = self.total_mass, self.area
            self.model.queue_to_destroy(self)
        else:
            mass, area = self.self_mass, self.self_volume
        b2body = self.parent.b2subworld.CreateDynamicBody()
        b2body.CreateCircleFixture(
            radius = sqrt(area/pi),
            friction = 1.0,
            density = mass / area,
            restitution = 0.3,
            )
        b2body.linearDamping = 1.0
        b2body.angularDamping = 1.0
        b2body.userData = self
        self.b2body = b2body

    def _awake_b2bodies(self):
        for b2body in self.b2subworld.bodies:
            b2body.awake = True

    def throw_in(self, children, target=None):
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
            start = [distance*f(azimuth) for f in cos_sin]
            factor = 5*random()
            velocity = [factor*(t - s) for t, s in zip(target, start)]
            child.position = start
            child.b2body.linearVelocity = velocity

    def rake_in(self, outersected_):
        radius = self.radius
        position = self.position
        factor = -3000.0*outersected_ * radius*radius / position.length
        force = [pos*factor for pos in position]
        # point = (0.0, 0.0)  # TODO: touchpoint
        self.b2body.ApplyForce(force=force, point=_ZERO_VECTOR, wake=False)

    def b2subworld_step(self):
        parent_radius = self.radius
        for child in self.children:
            outersected_ = outersected(
                child.radius, parent_radius, child.position.length
                )
            if outersected_: child.rake_in(outersected_)
            if child.drag_target: child.drag_b2body()
        self.b2subworld.Step(self.time_step, 10, 10)
        self.b2subworld.ClearForces()

    def b2subworlds_step(self):
        '''
        for child in self.children:
            if not child.children: continue
            child.b2subworlds_step()
        self.b2subworld_step()
        '''
        for item in self.and_childrened_descendants:
            item.b2subworld_step()

    def b2superworld_step(self): self.parent.b2subworld_step()

    def b2superworlds_step(self):
        '''
        self.b2superworld_step()
        if self.parent.parent: self.parent.b2superworlds_step()
        '''
        for ancestor in self.ancestors:
            ancestor.b2subworld_step()


class BodyHierarchyMixin:
    '''
    _radius, _total_mass, position, radius, total_mass are dummies
    for root instances (without b2body)
    '''
    def __init__(self):
        self._radius: float
        self._total_mass: float
        self.area = self.self_volume
        self.total_mass = self.self_mass
        self.b2bodies_to_destroy = []

    def _set_time_step(self, time_step):
        for descendant in self.descendants:
            descendant.time_step = time_step

    @property
    def position(self): return _ZERO_VECTOR

    @property
    def radius(self): return self._radius
    @radius.setter
    def radius(self, radius): self._radius = radius

    @property
    def total_mass(self): return self._total_mass
    @total_mass.setter
    def total_mass(self, mass): self._total_mass = mass

    def _destroy_b2bodies_to_destroy(self):
        for b2body in self.b2bodies_to_destroy:
            b2body.world.DestroyBody(b2body)
        self.b2bodies_to_destroy = []

    def queue_to_destroy(self, item):
        self.b2bodies_to_destroy.append(item.b2body)
