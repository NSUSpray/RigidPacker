from typing import List
from math import pi

import pygame
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

from repository import ItemData, Repository
from model_body import BodyContainerMixin, BodyHierarchyMixin
from model_graphics import GraphicsContainerMixin, GraphicsHierarchyMixin
from utilities.geometry import packing_specific_area


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

    @property
    def _picked_up_descendants(self):
        return [item for item in self.descendants if item.picked_up]

    def stuff_by(self, new_children, throwing_target=None):
        if not self.children:
            for self_or_ancestor in (self, *self.ancestors):
                self_or_ancestor.and_childrened_descendants.append(self)
        for self_or_ancestor in (self, *self.ancestors):
            for new_child in new_children:
                self_or_ancestor.and_childrened_descendants += \
                        new_child.and_childrened_descendants
        self._create_subworld()
        super().stuff_by(new_children)
        for new_child in new_children: new_child.create_b2body()
        for self_or_ancestor in (self, *self.ancestors):
            self_or_ancestor.adjust_area()
            self_or_ancestor.adjust_total_mass()
        self.throw_in(new_children, throwing_target)
        for new_child in new_children:
            if new_child.q_item:
                new_child.adopt_parent_q_item()
            else:
                new_child.create_q_item()
            new_child.move_q_item()

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
            ancestor._awake_b2bodies()

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
        self.model.hover_over(self)
        self._pinch_b2body()
        self.q_item.paintPinched()

    def release(self):
        self.model.hover_over(None)
        self._release_b2body()
        if self.picked_up:
            self.q_item.paintPickedUp()
        else:
            self.q_item.paintInitial()

    def start_dragging(self, drag_point):
        self._start_dragging_b2body(drag_point)

    def drag(self, drag_target): self._drag_b2body(drag_target)

    def finish_dragging(self):
        self._finish_dragging_b2body()
        self.pinch()

    def _toggle_picked_up(self):
        self.picked_up = not self.picked_up
        if self.picked_up:
            self._release_b2body()
            self.q_item.paintPickedUp()
            for descendant in self.descendants:
                descendant.q_item.paintPickedUpDescendant()
        else:
            for item in (self, *self.descendants):
                item.q_item.paintInitial()

    def toggle_picked_up(self):
        if set(self.descendants) & set(self.model._picked_up_descendants):
            return
        self._toggle_picked_up()

    def toggle_picked_up_siblings(self):
        if self.is_root: return
        for sibling in self.parent.children:
            if sibling.picked_up == self.picked_up: continue
            sibling._toggle_picked_up()

    def unpick_descendants(self):
        picked_up_descendants = \
            set(self.descendants) & set(self.model._picked_up_descendants)
        if not picked_up_descendants: return False
        # unpick picked up descendants
        for picked_up_descendant in picked_up_descendants:
            picked_up_descendant._toggle_picked_up()

    def take_picked_up(self, throwing_target):
        if self.picked_up: return
        picked_up_items = self.model._picked_up_descendants
        if not picked_up_items: return
        for picked_up in picked_up_items:
            picked_up.shake_out()
        self.stuff_by(picked_up_items, throwing_target)
        self.model.repository.shift(picked_up_items, self)
        for picked_up in picked_up_items:
            picked_up._toggle_picked_up()


class _UpdatableHierarchyMixin(QThread):

    updated = pyqtSignal()

    def __init__(self, target_fps):
        super().__init__()
        pygame.init()
        self._running: bool
        self._target_fps = target_fps
        self.gentle = False
        self.updated.connect(self.move_q_items)

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

    def __init__(self, repository, target_fps):
        _BodyGraphicsContainer.__init__(self, repository.root, target_fps)
        BodyHierarchyMixin.__init__(self)
        GraphicsHierarchyMixin.__init__(self)
        _UpdatableHierarchyMixin.__init__(self, target_fps)
        self.repository: Repository = repository
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
        container.model = self
        protos = self.repository.children_of(container)
        if not protos: return
        children = [
            _BodyGraphicsContainer(proto, self._target_fps) for proto in protos
            ]
        container.stuff_by(children)
        QApplication.processEvents()
        for child in children: self.stuff(child)

    def hover_over(self, item): self.hovered_item = item
