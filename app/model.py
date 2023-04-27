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
        self._parent: _ContainerItem = None
        self._children: List[_ContainerItem] = []
        # needed for a marginal increase in performance in the main loop
        self._ancestors: List[_ContainerItem] = []
        self._descendants: List[_ContainerItem] = []

    '''
    @property
    def _ancestors(self):
        return (self._parent, *self._parent._ancestors) if self._parent else ()
        # yield self._parent or ()
        # for ancestor in self._parent._ancestors: yield ancestor
    '''

    @property
    def nesting_level(self):
        return self._parent.nesting_level + 1 if self._parent else 0

    def stuff_by(self, new_children):
        self._children += new_children  # +C
        self_and_ancestors = (self, *self._ancestors)
        for new_child in new_children:
            new_child._parent = self  # +P
            new_child_and_descendants = (new_child, *new_child._descendants)
            for new_child_or_descendant in new_child_and_descendants:  # +DA
                new_child_or_descendant._ancestors += self_and_ancestors
            for self_or_ancestor in self_and_ancestors:  # +AD
                self_or_ancestor._descendants += new_child_and_descendants

    def shake_out(self):
        self_and_descendants = (self, *self._descendants)
        for ancestor in self._ancestors:
            for self_or_descendant in self_and_descendants:  # −AD
                ancestor._descendants.remove(self_or_descendant)
            for descendant in self._descendants:  # −DA
                descendant._ancestors.remove(ancestor)
        self._ancestors = []  # −DA
        self._parent._children.remove(self)  # −C
        self._parent = None  # −P


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
        self.__picked_up = False
        self._model: Model
        # self if it has children + descendants with children
        # needed for a significant increase in performance in the main loop
        self._and_childrened_descendants: List[_BodyGraphicsContainer] = []

    def __adjust_area(self):
        ''' calculate area with all children and adjust parent area '''
        area = self.self_volume
        if self._children:
            children_len = len(self._children)
            children_area = sum(child._area for child in self._children)
            if children_len == 1:
                area += children_area
            else:
                radii = sorted(child.radius for child in self._children)
                area1 = area + children_area
                area2 = packing_specific_area(radii) * children_area
                top2radii = sum(radii[-2:])
                area3 = pi * top2radii*top2radii
                area = max(area1, area2, area3)
        self._area = area
        if self._parent: self._q_item.setRadius(self.radius)

    def __adjust_total_mass(self):
        ''' calculate mass with all children and adjust parent mass '''
        total_mass = self.self_mass
        if self._children:
            children_mass = sum(child._total_mass for child in self._children)
            total_mass += children_mass
        self._total_mass = total_mass

    @property
    def __picked_up_descendants(self):
        return [item for item in self._descendants if item.__picked_up]

    def __toggle_picked_up(self):
        self.__picked_up = not self.__picked_up
        if self.__picked_up:
            self._release_b2body()
            self._q_item.paintPickedUp()
            for descendant in self._descendants:
                descendant._q_item.paintPickedUpDescendant()
        else:
            for item in (self, *self._descendants):
                item._q_item.paintInitial()

    def stuff_by(self, new_children, throwing_target=None):
        if not self._children:
            for self_or_ancestor in (self, *self._ancestors):
                self_or_ancestor._and_childrened_descendants.append(self)
        for self_or_ancestor in (self, *self._ancestors):
            for new_child in new_children:
                self_or_ancestor._and_childrened_descendants += \
                        new_child._and_childrened_descendants
        self._create_subworld()
        super().stuff_by(new_children)
        for new_child in new_children: new_child._create_b2body()
        for self_or_ancestor in (self, *self._ancestors):
            self_or_ancestor.__adjust_area()
            self_or_ancestor.__adjust_total_mass()
        self._throw_in(new_children, throwing_target)
        for new_child in new_children:
            if new_child._q_item:
                new_child._adopt_parent_q_item()
            else:
                new_child._create_q_item()
            new_child.move_q_item()

    def shake_out(self):
        parent = self._parent
        ancestors = self._ancestors[:]
        super().shake_out()
        for ancestor in ancestors:
            for self_or_childrened_descendant \
                    in self._and_childrened_descendants:
                ancestor._and_childrened_descendants.remove(
                    self_or_childrened_descendant
                    )
        if not parent._children:
            for ancestor in ancestors:
                ancestor._and_childrened_descendants.remove(parent)
        for ancestor in ancestors:
            ancestor.__adjust_area()
            ancestor.__adjust_total_mass()
            ancestor._awake_b2bodies()

    def pinch(self):
        self._model.hover_over(self)
        self._pinch_b2body()
        self._q_item.paintPinched()

    def release(self):
        self._model.hover_over(None)
        self._release_b2body()
        if self.__picked_up:
            self._q_item.paintPickedUp()
        else:
            self._q_item.paintInitial()

    def start_dragging(self, drag_point):
        self._start_dragging_b2body(drag_point)

    def drag(self, drag_target): self._drag_b2body(drag_target)

    def finish_dragging(self):
        self._finish_dragging_b2body()
        self.pinch()

    def toggle_picked_up(self):
        if set(self._descendants) & set(self._model.__picked_up_descendants):
            return
        self.__toggle_picked_up()

    def toggle_picked_up_siblings(self):
        if self.is_root: return
        for sibling in self._parent._children:
            if sibling.__picked_up == self.__picked_up: continue
            sibling.__toggle_picked_up()

    def unpick_descendants(self):
        picked_up_descendants = \
            set(self._descendants) & set(self._model.__picked_up_descendants)
        if not picked_up_descendants: return False
        # unpick picked up descendants
        for picked_up_descendant in picked_up_descendants:
            picked_up_descendant.__toggle_picked_up()

    def take_picked_up(self, throwing_target):
        if self.__picked_up: return
        picked_up_items = self._model.__picked_up_descendants
        if not picked_up_items: return
        for picked_up in picked_up_items:
            picked_up.shake_out()
        self.stuff_by(picked_up_items, throwing_target)
        self._model._repository.shift(picked_up_items, self)
        for picked_up in picked_up_items:
            picked_up.__toggle_picked_up()


class _UpdatableHierarchyMixin(QThread):

    updated = pyqtSignal()

    def __init__(self, target_fps):
        super().__init__()
        pygame.init()
        self.__running: bool
        self.__gentle = False
        self._target_fps = target_fps
        self.updated.connect(self._move_q_items)

    def __del__(self): pygame.quit()

    def run(self):
        b2subworld_step = self._b2subworld_step
        b2subworlds_step = self._b2subworlds_step
        updated_emit = self.updated.emit
        clock = pygame.time.Clock()
        tick = clock.tick
        self.__running = True
        while self.__running and not self._children:
            tick(self._target_fps)
        while self.__running:
            '''
            if self.__gentle:
                hovered = self.__hovered_item
                if hovered:
                    if hovered._children: hovered._b2subworld_step()
                    if hovered._parent: hovered._b2superworlds_step()
                else:
                    b2subworld_step()
            else:
                b2subworlds_step()  # 25–13% CPU
            '''
            b2subworlds_step()  # 25–13% CPU
            if self._b2bodies_to_destroy: self._destroy_b2bodies_to_destroy()
            updated_emit()  # 17–5% CPU
            tick(self._target_fps)

    def quit(self):
        self.__running = False
        super().quit()
        self.wait()

    def toggle_gentle(self): self.__gentle = not self.__gentle


class Model(
        BodyHierarchyMixin,
        GraphicsHierarchyMixin,
        _BodyGraphicsContainer,
        _UpdatableHierarchyMixin,
        ):

    ''' Has connection to the database and can stuff self recursively '''

    def __init__(self, repository, target_fps):
        _BodyGraphicsContainer.__init__(self, repository._root, target_fps)
        BodyHierarchyMixin.__init__(self)
        GraphicsHierarchyMixin.__init__(self)
        _UpdatableHierarchyMixin.__init__(self, target_fps)
        self.__hovered_item: _BodyGraphicsContainer = None
        self._repository: Repository = repository

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
        container._model = self
        protos = self._repository.children_of(container)
        if not protos: return
        children = [
            _BodyGraphicsContainer(proto, self._target_fps) for proto in protos
            ]
        container.stuff_by(children)
        QApplication.processEvents()
        for child in children: self.stuff(child)

    def hover_over(self, item): self.__hovered_item = item
