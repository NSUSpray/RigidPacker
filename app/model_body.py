from math import pi, sqrt, sin, cos
from random import random

from Box2D import b2World, b2Body, b2_staticBody, b2_dynamicBody

from geometry import outersected


class BodyBase:

    def __init__(self):
        self.b2body: b2Body
        self.drag_point = (0.0, 0.0)
        self.drag_target = None

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

    def pinch_body(self):
        self._last_velocity = self.b2body.linearVelocity.copy()
        self.b2body.type = b2_staticBody

    def release_body(self, calm=False):
        self.b2body.type = b2_dynamicBody
        if not calm: self.b2body.linearVelocity = self._last_velocity


class BodyContainerMixin(BodyBase):

    def __init__(self, target_fps):
        super().__init__()
        self._time_step = 1.0 / target_fps
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
            restitution = 0.3
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

    def b2subworld_step(self):
        parent_radius = self.radius
        for child in self.children:
            position = child.position
            body = child.b2body
            # rake in
            radius = child.radius
            distance = position.length  # between centers
            outersected_ = outersected(radius, parent_radius, distance)
            if outersected_:
                factor = -1000.0*outersected_ * radius*radius / distance
                force = [pos*factor for pos in position]
                point = (0.0, 0.0)  # TODO: touchpoint
                body.ApplyForce(force=force, point=point, wake=False)
            # drag
            drag_target = child.drag_target
            if drag_target:
                factor = -10.0 / child.total_mass  # real inertia
                # factor = -10.0 / sqrt(child.total_mass)  # compromise
                # factor = -10.0  # best dynamism
                velocity = [
                    (point + pos - target)*factor for point, target, pos
                        in zip(child.drag_point, drag_target, position)
                    ]
                body.linearVelocity = velocity
        self.b2subworld.Step(self._time_step, 10, 10)

    def b2subworlds_step(self):
        for child in self.children:
            if not child.children: continue
            child.b2subworlds_step()
        self.b2subworld_step()

    def b2superworld_step(self): self.parent.b2subworld_step()

    def b2superworlds_step(self):
        self.b2superworld_step()
        if self.parent.parent: self.parent.b2superworlds_step()


class BodyHierarchyMixin:

    @property
    def b2world(self): return self.b2subworld
