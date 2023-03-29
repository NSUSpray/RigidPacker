from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsScene

from graphics import Ui_GraphicsItem, Ui_InteractiveGraphics


class _GraphicsCircle(QGraphicsEllipseItem, Ui_GraphicsItem):

    def __init__(self, item):
        self._item = item
        r = item.radius * self.graphics_ratio
        super().__init__(-r, -r, 2.0*r, 2.0*r)  # left top width height
        Ui_GraphicsItem.__init__(self)

    def setRadius(self, r):
        r *= self.graphics_ratio
        self.setRect(-r, -r, 2.0*r, 2.0*r)  # left top width height

    def setPos(self, x, y):
        super().setPos(x*self.graphics_ratio, y*self.graphics_ratio)


class _InteractiveGraphicsCircle(_GraphicsCircle, Ui_InteractiveGraphics):

    def __init__(self, item):
        super().__init__(item)
        Ui_InteractiveGraphics.__init__(self)

    def mapToBox2D(self, pos):
        return [x/self.graphics_ratio for x in (pos.x(), pos.y())]

    def hoverEnterEvent(self, event):
        self._item.pinch()

    def hoverLeaveEvent(self, event):
        self._item.release()

    def mousePressEvent(self, event):
        button = event.button()
        if button == Qt.LeftButton:
            self._item.start_dragging(self.mapToBox2D(event.pos()))
        elif button == Qt.RightButton:
            self._item.toggle_picked_up()

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.LeftButton: return
        self._item.drag(self.mapToBox2D(self.mapToParent(event.pos())))

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton: return
        self._item.finish_dragging()


class GraphicsContainerMixin:

    def __init__(self):
        self.q_item: _InteractiveGraphicsCircle

    def create_graphics(self):
        q_item = _InteractiveGraphicsCircle(self)
        if self.parent.is_root:
            self.parent.q_scene.addItem(q_item)
        else:
            q_item.setParentItem(self.parent.q_item)
        self.q_item = q_item
        self.q_item_move()

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
