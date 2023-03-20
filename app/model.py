from random import random
from typing import List

import pygame
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject

from storage import ItemData, Storage
from model_body import BodyContainerMixin, BodyModelMixin
from model_graphics import GraphicsContainerMixin, GraphicsModelMixin


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


class Model(
        BodyGraphicsContainer,
        BodyModelMixin,
        GraphicsModelMixin,
        QObject
        ):

    ''' Has connection to the database and can stuff self recursively '''

    updated = pyqtSignal()

    def __init__(self, storage, target_fps=DEFAULT_TARGET_FPS):
        super().__init__(storage.root, target_fps)
        self._storage: Storage = storage
        self._target_fps = target_fps
        self._thread = ModelThread(self)
        self._radius: float
        self._total_mass: float
        self.descendants: List[BodyGraphicsContainer] = []
        self.hovered_item: BodyGraphicsContainer = None
        self.gentle_mode = False
        BodyModelMixin.__init__(self)
        GraphicsModelMixin.__init__(self)
        QObject.__init__(self)
        self.area = self.self_volume
        self.total_mass = self.self_mass
        self.updated.connect(self.q_items_move)

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

    def run(self):
        self._thread.start()

    def stop(self):
        self._thread.stop()
        self._thread.wait()

    def pause(self): self.gentle_mode = True
    def resume(self): self.gentle_mode = False


class ModelThread(QThread):

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pygame.init()
        self._clock = pygame.time.Clock()
        self._model = model
        self._running: bool

    def __del__(self): pygame.quit()

    def run(self):
        model = self._model
        self._running = True
        while self._running:
            if model.gentle_mode:
                if model.hovered_item:
                    hovered = model.hovered_item
                    if hovered.children: hovered.b2subworld_step()
                    hovered.b2superworlds_step()
                else:
                    model.b2subworld_step()
            else:
                model.b2subworlds_step()  # 20% CPU
            model.updated.emit()  # 10% CPU
            self._clock.tick(model._target_fps)

    def stop(self): self._running = False
