from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsScene

from graphics import Ui_InteractiveGraphics


class _GraphicsCircle(QGraphicsEllipseItem):

    def __init__(self, item):
        self._item = item
        r = item.radius * self.graphics_ratio
        super().__init__(-r, -r, 2.0*r, 2.0*r)  # left top width height

    def setRadius(self, r):
        r *= self.graphics_ratio
        self.setRect(-r, -r, 2.0*r, 2.0*r)  # left top width height

    def setPos(self, x, y):
        super().setPos(x*self.graphics_ratio, y*self.graphics_ratio)


class _InteractiveGraphicsMixin(Ui_InteractiveGraphics):

    def __init__(self):
        super().__init__()
        self._being_moved = False

    def mapToBox2D(self, pos):
        return [x/self.graphics_ratio for x in (pos.x(), pos.y())]

    def hoverEnterEvent(self, event): self._item.pinch()
    def hoverLeaveEvent(self, event): self._item.release()

    def mousePressEvent(self, event):
        button = event.button()
        item = self._item
        if button == Qt.LeftButton:
            drag_point = self.mapToBox2D(event.pos())
            item.start_dragging(drag_point)
        elif button == Qt.RightButton:
            for picked_up_item in item.model.picked_up_items:
                if item in picked_up_item.ancestors: return
            item.toggle_picked_up()

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.LeftButton: return
        self._being_moved = True
        drag_target = self.mapToBox2D(self.mapToParent(event.pos()))
        self._item.drag(drag_target)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton: return
        item = self._item
        if self._being_moved:
            item.finish_dragging()
            self._being_moved = False
        elif item.model.picked_up_items:  # just a mouse click, not a drag
            if item.picked_up: return
            throwing_target = self.mapToBox2D(event.pos())
            item.take_picked_up(throwing_target)

    def mouseDoubleClickEvent(self, event):
        if event.button() != Qt.RightButton: return
        item = self._item
        picked_up_descendants = \
                set(item.descendants) & set(item.model.picked_up_items)
        if picked_up_descendants:
            # unpick picked up descendants
            for picked_up_descendant in picked_up_descendants:
                picked_up_descendant.toggle_picked_up()
        else:
            # pick up or give up all siblings
            for sibling in item.parent.children:
                if sibling.picked_up == item.picked_up: continue
                sibling.toggle_picked_up()


class _InteractiveGraphicsCircle(_InteractiveGraphicsMixin, _GraphicsCircle):

    def __init__(self, item):
        _GraphicsCircle.__init__(self, item)
        _InteractiveGraphicsMixin.__init__(self)


class GraphicsContainerMixin:

    def __init__(self):
        self.q_item: _InteractiveGraphicsCircle = None

    def create_graphics(self):
        self.q_item = _InteractiveGraphicsCircle(self)

    def set_graphics_parent(self):
        if self.parent.is_root:
            self.parent.q_scene.addItem(self.q_item)
        else:
            self.q_item.setParentItem(self.parent.q_item)

    def q_item_move(self): self.q_item.setPos(*self.position)

    '''
    def q_items_move(self):
        for child in self.children:
            child.q_items_move()
            child.q_item_move()
    '''

class GraphicsHierarchyMixin:

    def __init__(self):
        self.q_scene = QGraphicsScene()

    def q_items_move(self):
        for descendant in self.descendants: descendant.q_item_move()
