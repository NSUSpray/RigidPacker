from random import random
from typing import List

import pygame
from PyQt5.QtCore import QThread, pyqtSignal

from storage import ItemData, Storage
from model_body import BodyContainerMixin, BodyHierarchyMixin
from model_graphics import GraphicsContainerMixin, GraphicsHierarchyMixin


DEFAULT_TARGET_FPS = 60.077


class ContainerItem(ItemData):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent: ContainerItem = None
        self.children: List[ContainerItem] = []

    def stuff_by(self, items):
        self.children = items
        for child in self.children: child.parent = self


class BodyGraphicsContainer(
        ContainerItem,
        BodyContainerMixin,
        GraphicsContainerMixin
        ):

    # shape area ~ real item volume

    def __init__(self, item, target_fps=DEFAULT_TARGET_FPS):
        super().__init__(item.id, item.name, item.product_name)
        BodyContainerMixin.__init__(self, target_fps)
        GraphicsContainerMixin.__init__(self)

    def stuff_by(self, items):
        super().stuff_by(items)
        self.create_subworld()
        for child in self.children:
            child.create_body()
            r = 10.0 * self.radius
            child.position = [2.0*r*random() - r for _ in range(2)]
            child.create_graphics()
            child.q_item_move()
        self.adjust_total_mass()
        self.adjust_area()

    def adjust_total_mass(self):
        total_mass = self.self_mass
        if self.children:
            children_mass = sum(child.total_mass for child in self.children)
            total_mass += children_mass
        self.total_mass = total_mass
        if self.parent: self.parent.adjust_total_mass()

    def adjust_area(self):
        area = self.self_volume
        if self.children:
            children_area = 1.62 * sum(child.area for child in self.children)
            area += children_area
        self.area = area
        if self.parent:
            self.q_item.setRadius(self.radius)
            self.parent.adjust_area()


class BodyGraphicsHierarchy(
        BodyGraphicsContainer,
        BodyHierarchyMixin,
        GraphicsHierarchyMixin
        ):

    ''' Has connection to the database and can stuff self recursively '''

    def __init__(self, storage, target_fps=DEFAULT_TARGET_FPS):
        super().__init__(storage.root, target_fps)
        self._storage: Storage = storage
        self._target_fps = target_fps
        self._radius: float
        self._total_mass: float
        self.descendants: List[BodyGraphicsContainer] = []
        self.hovered_item: BodyGraphicsContainer = None
        BodyHierarchyMixin.__init__(self)
        GraphicsHierarchyMixin.__init__(self)
        self.area = self.self_volume
        self.total_mass = self.self_mass

    @property
    def position(self): return (0.0, 0.0)

    @property
    def radius(self): return self._radius
    @radius.setter
    def radius(self, radius): self._radius = radius

    @property
    def total_mass(self): return self._total_mass
    @total_mass.setter
    def total_mass(self, mass): self._total_mass = mass

    def stuff(self, container=None):
        container = container or self
        container.model = self
        protos = self._storage.children_of(container)
        if not protos: return
        children = [
            BodyGraphicsContainer(proto, self._target_fps) for proto in protos
            ]
        container.stuff_by(children)
        for child in container.children: self.stuff(child)
        self.descendants += container.children


class Model(BodyGraphicsHierarchy, QThread):

    updated = pyqtSignal()

    def __init__(self, storage, target_fps=DEFAULT_TARGET_FPS):
        super().__init__(storage, target_fps)
        QThread.__init__(self)
        pygame.init()
        self._clock = pygame.time.Clock()
        self._running: bool
        self.gentle_mode = False
        self.updated.connect(self.q_items_move)

    def __del__(self): pygame.quit()

    def run(self):
        self._running = True
        while self._running:
            if self.gentle_mode:
                if self.hovered_item:
                    hovered = self.hovered_item
                    if hovered.children: hovered.b2subworld_step()
                    hovered.b2superworlds_step()
                else:
                    self.b2subworld_step()
            else:
                self.b2subworlds_step()  # 20% CPU
            self.updated.emit()  # 10% CPU
            self._clock.tick(self._target_fps)

    def quit(self):
        self._running = False
        super().quit()
        self.wait()

    def pause(self): self.gentle_mode = True
    def resume(self): self.gentle_mode = False
