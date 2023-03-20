from math import pi, sqrt, hypot

from Box2D import b2World, b2Body, b2_staticBody, b2_dynamicBody


class BodyBase:

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
    def area(self): return pi * self.radius*self.radius
    @area.setter
    def area(self, area): self.radius = sqrt(area/pi)

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

    def pinch_body(self): self.b2body.type = b2_staticBody
    def release_body(self): self.b2body.type = b2_dynamicBody


class BodyContainerMixin(BodyBase):

    def __init__(self, target_fps):
        super().__init__()
        self._time_step = 1.0 / target_fps
        self.b2subworld: b2World

    @property
    def total_mass(self): return self.mass
    @total_mass.setter
    def total_mass(self, mass): self.mass = mass

    def create_subworld(self):
        self.b2subworld = b2World(gravity=(0.0,0.0))

    def create_body(self):
        self.b2body = self.parent.b2subworld.CreateDynamicBody()
        mass = self.self_mass
        area = self.self_volume
        self.b2body.CreateCircleFixture(
            radius = sqrt(area/pi),
            friction = 1.0,
            density = mass/area,
            restitution = 0.3
            )
        self.b2body.linearDamping = 1.0
        self.b2body.angularDamping = 1.0
        self.b2body.userData = self

    def b2subworld_step(self):
        parent_radius = self.radius
        for child in self.children:
            distance = hypot(*child.position)  # between centers
            depth = distance + child.radius - parent_radius  # of intersection
            if depth <= 0.0: continue
            depth = min(depth, 2*child.radius)
            # linear approximation of intersection area
            intersection_area = depth * child.radius
            factor = -500 * intersection_area / distance
            f = [x*factor for x in child.position]
            child.b2body.ApplyForce(force=f, point=(0.0,0.0), wake=False)
        self.b2subworld.Step(self._time_step, 10, 10)

    def b2subworlds_step(self):
        if not self.children: return
        for child in self.children: child.b2subworlds_step()
        self.b2subworld_step()

    def b2superworld_step(self): self.parent.b2subworld_step()

    def b2superworlds_step(self):
        if not self.parent: return
        self.b2superworld_step()
        self.parent.b2superworlds_step()


class BodyModelMixin:

    @property
    def b2world(self): return self.b2subworld
