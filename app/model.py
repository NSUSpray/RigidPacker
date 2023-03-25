from typing import List

import pygame
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

from storage import ItemData, Storage
from model_body import BodyContainerMixin, BodyHierarchyMixin
from model_graphics import GraphicsContainerMixin, GraphicsHierarchyMixin
from geometry import enclosing_area_ratio


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
        self._create_subworld()
        for child in self.children:
            child.create_body()
        self.adjust_area()
        self.adjust_total_mass()
        for child in self.children:
            child.throw_in()
            child.create_graphics()

    def adjust_area(self):
        ''' calculate area with all children and adjust parent area '''
        area = self.self_volume
        if self.children:
            children_len = len(self.children)
            children_area = sum(child.area for child in self.children)
            if children_len == 1:
                area += children_area
            else:
                area1 = area + children_area
                area2 = enclosing_area_ratio(
                    [child.radius for child in self.children]
                    ) * children_area
                area = max(area1, area2)
        self.area = area
        if self.parent:
            self.q_item.setRadius(self.radius)
            self.parent.adjust_area()


class UpdatedHierarchyMixin(QThread):

    updated = pyqtSignal()

    def __init__(self, target_fps=DEFAULT_TARGET_FPS, gentle=False):
        super().__init__()
        pygame.init()
        self._running: bool
        self._target_fps = target_fps
        self.gentle = gentle
        self.updated.connect(self.q_items_move)

    def __del__(self): pygame.quit()

    def run(self):
        b2subworld_step = self.b2subworld_step
        b2subworlds_step = self.b2subworlds_step
        updated_emit = self.updated.emit
        target_fps = self._target_fps
        clock = pygame.time.Clock()
        tick = clock.tick
        self._running = True
        while self._running:
            if self.gentle:
                hovered = self.hovered_item
                if hovered:
                    if hovered.children: hovered.b2subworld_step()
                    if hovered.parent: hovered.b2superworlds_step()
                elif self.children:
                    b2subworld_step()
            elif self.children:
                b2subworlds_step()  # 20% CPU
            updated_emit()  # 10% CPU
            tick(target_fps)

    def quit(self):
        self._running = False
        super().quit()
        self.wait()

    def toggle_gentle(self): self.gentle = not self.gentle


class Model(
        BodyGraphicsContainer,
        BodyHierarchyMixin,
        GraphicsHierarchyMixin,
        UpdatedHierarchyMixin
        ):

    ''' Has connection to the database and can stuff self recursively '''

    def __init__(
            self,
            storage,
            target_fps = DEFAULT_TARGET_FPS,
            gentle = False
            ):
        super().__init__(storage.root, target_fps)
        self._storage: Storage = storage
        self._radius: float
        self._total_mass: float
        self.descendants: List[BodyGraphicsContainer] = []
        self.hovered_item: BodyGraphicsContainer = None
        BodyHierarchyMixin.__init__(self)
        GraphicsHierarchyMixin.__init__(self)
        UpdatedHierarchyMixin.__init__(self, target_fps, gentle)
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
        ''' create and place all container’s descendants '''
        container = container or self
        protos = self._storage.children_of(container)
        if not protos: return
        children = [
            BodyGraphicsContainer(proto, self._target_fps) for proto in protos
            ]
        for child in children: child.model = self
        container.stuff_by(children)
        QApplication.processEvents()
        self.descendants += container.children
        for child in container.children: self.stuff(child)
