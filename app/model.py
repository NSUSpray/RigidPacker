from typing import List
from math import pi

import pygame
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

from storage import ItemData, Storage
from model_body import BodyContainerMixin, BodyHierarchyMixin
from model_graphics import GraphicsContainerMixin, GraphicsHierarchyMixin
from geometry import packing_specific_area


class _ContainerItem(ItemData):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent: _ContainerItem = None
        self.children: List[_ContainerItem] = []
        self.ancestors: List[_ContainerItem] = []
        self.descendants: List[_ContainerItem] = []

    '''
    @property
    def ancestors(self):
        return (self.parent, *self.parent.ancestors) if self.parent else ()
        # yield self.parent or ()
        # for ancestor in self.parent.ancestors: yield ancestor
    '''

    def stuff_by(self, items):
        for item in items: item.parent = self
        self.children = items
        for item in items:
            item.ancestors = [self, *self.ancestors]
        for item in (self, *self.ancestors):
            item.descendants += items


class _BodyGraphicsContainer(
        BodyContainerMixin,
        GraphicsContainerMixin,
        _ContainerItem,
        ):

    # shape area ~ real item volume

    def __init__(self, item, target_fps):
        _ContainerItem.__init__(self, item.id, item.name, item.product_name)
        BodyContainerMixin.__init__(self, 1.0/target_fps)
        GraphicsContainerMixin.__init__(self)
        self._picked_up = False
        self.model: Model
        self.self_and_desc_with_children: List[_BodyGraphicsContainer] = [self]

    def stuff_by(self, items):
        super().stuff_by(items)
        for ancestor in self.ancestors:
            ancestor.self_and_desc_with_children.append(self)
        self._create_subworld()
        for child in self.children:
            child.create_body()
        for item in (self, *self.ancestors):
            item.adjust_area()
            item.adjust_total_mass()
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
                radii = sorted([child.radius for child in self.children])
                area1 = area + children_area
                area2 = packing_specific_area(radii) * children_area
                top2radii = sum(radii[-2:])
                area3 = pi * top2radii*top2radii
                area = max(area1, area2, area3)
        self.area = area
        if self.parent: self.q_item.setRadius(self.radius)

    def adjust_total_mass(self):
        ''' calculate mass with all children and adjust parent mass '''
        total_mass = self.self_mass
        if self.children:
            children_mass = sum(child.total_mass for child in self.children)
            total_mass += children_mass
        self.total_mass = total_mass

    def pinch(self):
        self.model.hovered_item = self
        self._pinch_body()
        self.q_item.paint_pinched()

    def release(self):
        self.model.hovered_item = None
        self._release_body()
        self.q_item.paint_released()

    def start_dragging(self, drag_point):
        self.drag_point = drag_point
        self.b2body.bullet = True

    def drag(self, drag_target):
        self.drag_target = drag_target
        self._release_body_calmly()

    def finish_dragging(self):
        self.drag_target = None
        self.b2body.bullet = False
        self.pinch()

    def toggle_picked_up(self):
        if self._picked_up:
            self.q_item.paint_dropped()
        else:
            self._release_body()
            self.q_item.paint_picked_up()
        self._picked_up = not self._picked_up


class _UpdatableHierarchyMixin(QThread):

    updated = pyqtSignal()

    def __init__(self, target_fps):
        super().__init__()
        pygame.init()
        self._running: bool
        self._target_fps = target_fps
        self.gentle = False
        self.updated.connect(self.q_items_move)

    def __del__(self): pygame.quit()

    def run(self):
        b2subworld_step = self.b2subworld_step
        b2subworlds_step = self.b2subworlds_step
        updated_emit = self.updated.emit
        clock = pygame.time.Clock()
        tick = clock.tick
        self._running = True
        while self._running and not self.children:
            tick(self.target_fps)
        while self._running:
            '''
            if self.gentle:
                hovered = self.hovered_item
                if hovered:
                    if hovered.children: hovered.b2subworld_step()
                    if hovered.parent: hovered.b2superworlds_step()
                else:
                    b2subworld_step()
            else:
            '''
            b2subworlds_step()  # 25–13% CPU
            updated_emit()  # 17–5% CPU
            tick(self.target_fps)

    def quit(self):
        self._running = False
        super().quit()
        self.wait()

    def toggle_gentle(self): self.gentle = not self.gentle


class Model(
        BodyHierarchyMixin,
        GraphicsHierarchyMixin,
        _BodyGraphicsContainer,
        _UpdatableHierarchyMixin,
        ):

    ''' Has connection to the database and can stuff self recursively '''

    def __init__(self, storage, target_fps):
        _BodyGraphicsContainer.__init__(self, storage.root, target_fps)
        BodyHierarchyMixin.__init__(self)
        GraphicsHierarchyMixin.__init__(self)
        _UpdatableHierarchyMixin.__init__(self, target_fps)
        self._storage: Storage = storage
        self.hovered_item: _BodyGraphicsContainer = None

    @property
    def target_fps(self):
        return self._target_fps

    @target_fps.setter
    def target_fps(self, fps):
        self._target_fps = fps
        self._set_time_step(1.0/fps)

    def stuff(self, container=None):
        ''' create and place all container’s descendants '''
        container = container or self
        protos = self._storage.children_of(container)
        if not protos: return
        children = [
            _BodyGraphicsContainer(proto, self._target_fps) for proto in protos
            ]
        for child in children: child.model = self
        container.stuff_by(children)
        QApplication.processEvents()
        for child in container.children: self.stuff(child)
