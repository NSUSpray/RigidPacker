from typing import List
from math import pi

import pygame
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
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
        # needed for a marginal increase in performance in the main loop
        self.ancestors: List[_ContainerItem] = []
        self.descendants: List[_ContainerItem] = []

    '''
    @property
    def ancestors(self):
        return (self.parent, *self.parent.ancestors) if self.parent else ()
        # yield self.parent or ()
        # for ancestor in self.parent.ancestors: yield ancestor
    '''

    @property
    def nesting_level(self):
        return self.parent.nesting_level + 1 if self.parent else 0

    def stuff_by(self, new_children):
        self.children += new_children  # +C
        self_and_ancestors = (self, *self.ancestors)
        for new_child in new_children:
            new_child.parent = self  # +P
            new_child_and_descendants = (new_child, *new_child.descendants)
            for new_child_or_descendant in new_child_and_descendants:  # +DA
                new_child_or_descendant.ancestors += self_and_ancestors
            for self_or_ancestor in self_and_ancestors:  # +AD
                self_or_ancestor.descendants += new_child_and_descendants

    def shake_out(self):
        self_and_descendants = (self, *self.descendants)
        for ancestor in self.ancestors:
            for self_or_descendant in self_and_descendants:  # −AD
                ancestor.descendants.remove(self_or_descendant)
            for descendant in self.descendants:  # −DA
                descendant.ancestors.remove(ancestor)
        self.ancestors = []  # −DA
        self.parent.children.remove(self)  # −C
        self.parent = None  # −P


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
        self.picked_up = False
        self.model: Model
        # self if it has children + descendants with children
        # needed for a significant increase in performance in the main loop
        self.and_childrened_descendants: List[_BodyGraphicsContainer] = []

    def stuff_by(self, new_children, throwing_target=None):
        if not self.children:
            for self_or_ancestor in (self, *self.ancestors):
                self_or_ancestor.and_childrened_descendants.append(self)
        for self_or_ancestor in (self, *self.ancestors):
            for new_child in new_children:
                self_or_ancestor.and_childrened_descendants += \
                        new_child.and_childrened_descendants
        if not self.b2subworld: self._create_subworld()
        super().stuff_by(new_children)
        for new_child in new_children: new_child.create_body()
        for self_or_ancestor in (self, *self.ancestors):
            self_or_ancestor.adjust_area()
            self_or_ancestor.adjust_total_mass()
        self.throw_in(new_children, throwing_target)
        for new_child in new_children:
            if not new_child.q_item: new_child.create_graphics()
            new_child.set_graphics_parent()
            new_child.q_item_move()

    def shake_out(self):
        parent = self.parent
        ancestors = self.ancestors[:]
        super().shake_out()
        for ancestor in ancestors:
            for self_or_childrened_descendant \
                    in self.and_childrened_descendants:
                ancestor.and_childrened_descendants.remove(
                    self_or_childrened_descendant
                    )
        if not parent.children:
            for ancestor in ancestors:
                ancestor.and_childrened_descendants.remove(parent)
        for ancestor in ancestors:
            ancestor.adjust_area()
            ancestor.adjust_total_mass()
            for b2body in ancestor.b2subworld.bodies:
                b2body.awake = True

    def adjust_area(self):
        ''' calculate area with all children and adjust parent area '''
        area = self.self_volume
        if self.children:
            children_len = len(self.children)
            children_area = sum(child.area for child in self.children)
            if children_len == 1:
                area += children_area
            else:
                radii = sorted(child.radius for child in self.children)
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
        self.q_item.setToolTip(
            f'{self.name}\nS = {self.area}\nm = {self.total_mass}\n'
            f'ρ·S = {self.density*self.area}'
            )
        self.model.hovered_item = self
        self._pinch_body()
        self.q_item.paint_pinched()

    def release(self):
        self.model.hovered_item = None
        self._release_body()
        if self.picked_up:
            self.q_item.paint_picked_up()
        else:
            self.q_item.paint_initial()

    def start_dragging(self, drag_point):
        self.drag_point = drag_point
        self.b2body.bullet = True

    def drag(self, drag_target):
        self.drag_target = drag_target
        self._release_body_calmly()

    def finish_dragging(self):
        self.drag_target = None
        def set_bullet_to_false(): self.b2body.bullet = False
        QTimer.singleShot(3000, set_bullet_to_false)
        self.pinch()

    def toggle_picked_up(self):
        self.picked_up = not self.picked_up
        if self.picked_up:
            self.model.picked_up_items.append(self)
            self._release_body()
            self.q_item.paint_picked_up()
            for descendant in self.descendants:
                descendant.q_item.paint_picked_up_descendant()
        else:
            self.model.picked_up_items.remove(self)
            for item in (self, *self.descendants):
                item.q_item.paint_initial()

    def take_picked_up(self, throwing_target):
        picked_up_items = self.model.picked_up_items
        for picked_up in picked_up_items:
            picked_up.shake_out()
        self.stuff_by(picked_up_items, throwing_target)
        for picked_up in picked_up_items[:]:
            picked_up.toggle_picked_up()


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
                b2subworlds_step()  # 25–13% CPU
            '''
            b2subworlds_step()  # 25–13% CPU
            if self.b2bodies_to_destroy: self._destroy_b2bodies_to_destroy()
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
        self.picked_up_items: List[_BodyGraphicsContainer] = []

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
        for child in children: self.stuff(child)
