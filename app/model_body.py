from math import pi, sqrt
from random import random

from Box2D import b2World


class BodyContainerMixin:

    ''' shape area ~ real item volume '''

    initial_mass = 1  # TODO: 0 for abstractions
    initial_volume = 4/3 * pi * 0.1**3  # TODO: 0 for abstractions

    def __init__(self, target_fps):
        self.b2body = None
        self.b2subworld = None
        self._time_step = 1 / target_fps

    @property
    def position(self): return self.b2body.position

    @property
    def radius(self): return self.b2body.fixtures[0].shape.radius

    @property
    def mass(self): return self.b2body.mass

    @property
    def total_mass(self):
        mass = self.initial_mass if not self.is_root else 0
        if self.children:
            children_mass = sum(child.total_mass for child in self.children)
            mass += children_mass
        return mass

    @property
    def total_area(self):
        area = self.initial_volume if not self.is_root else 0
        if self.children:
            '''
            children_radius = max(
                sqrt(sum(x**2 for x in child.position))
                    + child.radius
                for child in self.children
                )
            children_area = pi * children_radius**2
            '''
            children_area = 1.62*sum(child.total_area for child in self.children)
            area += children_area
        return area

    def _create_body_for(self, child):
        child.b2body = self.b2subworld.CreateDynamicBody()
        mass = child.total_mass
        area = child.total_area
        child.b2body.CreateCircleFixture(
            radius = sqrt(area/pi),
            friction = 1,
            density = mass/area,
            restitution = 0.3
            )
        child.b2body.linearDamping = 1
        child.b2body.angularDamping = 1
        child.b2body.userData = child
        r = 10*sqrt(self.initial_volume/pi)
        child.b2body.position = tuple(2*r*random() - r for _ in range(2))

    def create_bodies_for_children(self):
        self.b2subworld = b2World(gravity=(0,0))
        for child in self.children:
            self._create_body_for(child)

    def b2subworld_step(self):
        parent_radius = sqrt(self.total_area/pi)
        for child in self.children:
            area = child.total_area
            r = sqrt(area/pi)
            mass = child.total_mass
            body = child.b2body
            fixture = body.fixtures[0]
            fixture.shape.radius = r
            fixture.density = mass/area

            L = sqrt(sum(x*x for x in body.position))
            if L + r - parent_radius > 0:
                # dr = max(L + r - parent_radius, 0)
                f = [-x/L for x in body.position]
                body.ApplyForce(force=f, point=(0,0), wake=False)
        self.b2subworld.Step(self._time_step, 10, 10)

    def b2subworlds_step(self):
        for child in self.children:
            if child.children: child.b2subworlds_step()
        self.b2subworld_step()

    def b2superworlds_step(self):
        if self.b2subworld: self.b2subworld_step()
        if self.parent: self.parent.b2superworlds_step()


class BodyModelMixin:

    @property
    def b2world(self): return self.b2subworld
