from math import pi, sqrt, sin, cos
from random import random

from Box2D import b2World, b2Body, b2_staticBody, b2_dynamicBody

from geometry import outersected


_ZERO_VECTOR = (0.0, 0.0)


class _BodyBase:

    def __init__(self):
        self.b2body: b2Body

    @property
    def position(self): return self.b2body.position
    @position.setter
    def position(self, position): self.b2body.position = position

    @property
    def _fixture(self): return self.b2body.fixtures[0]
    @property
    def _shape(self): return self._fixture.shape

    @property
    def radius(self):
        return self._shape.radius

    @radius.setter
    def radius(self, radius):
        mass = self.mass
        self._shape.radius = radius
        self.density = mass / self.area

    @property
    def area(self):
        r = self.radius
        return pi * r*r

    @area.setter
    def area(self, area):
        self.radius = sqrt(area/pi)

    @property
    def mass(self): return self.b2body.mass
    @mass.setter
    def mass(self, mass): self.density = mass / self.area

    @property
    def density(self):
        return self._fixture.density

    @density.setter
    def density(self, density):
        self._fixture.density = density
        self.b2body.ResetMassData()


class _InteractiveBodyMixin:

    def __init__(self):
        self._last_velocity = _ZERO_VECTOR
        self.drag_point = _ZERO_VECTOR
        self.drag_target = None

    def _pinch_body(self):
        self._last_velocity = self.b2body.linearVelocity.copy()
        self.b2body.type = b2_staticBody

    def _release_body(self):
        self.b2body.type = b2_dynamicBody
        self.b2body.linearVelocity = self._last_velocity

    def _release_body_calmly(self):
        self.b2body.type = b2_dynamicBody

    def drag_body(self):
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
        super().__init__()
        _InteractiveBodyMixin.__init__(self)
        self.time_step = time_step
        self.b2subworld: b2World

    @property
    def total_mass(self): return self.mass
    @total_mass.setter
    def total_mass(self, mass): self.mass = mass

    def _create_subworld(self):
        self.b2subworld = b2World(gravity=(0.0,0.0))

    def create_body(self):
        b2body = self.parent.b2subworld.CreateDynamicBody()
        mass = self.self_mass
        area = self.self_volume
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

    def throw_in(self):
        distance = self.parent.radius + self.radius
        azimuth = 2*pi * random()
        cos_sin = (cos, sin)
        start_position = [distance*f(azimuth) for f in cos_sin]
        throw_in_angle = pi/2 * (random() - 0.5)
        velocity = [
            -2.0 * xy * f(throw_in_angle)
                for xy, f in zip(start_position, cos_sin)
            ]
        self.position = start_position
        self.b2body.linearVelocity = velocity

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
            if child.drag_target: child.drag_body()
        self.b2subworld.Step(self.time_step, 10, 10)

    def b2subworlds_step(self):
        '''
        for child in self.children:
            if not child.children: continue
            child.b2subworlds_step()
        self.b2subworld_step()
        '''
        for item in self.self_and_desc_with_children:
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

    def __init__(self):
        self._radius: float
        self._total_mass: float
        self.area = self.self_volume
        self.total_mass = self.self_mass

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
