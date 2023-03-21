from math import pi, sqrt

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsScene
from PyQt5.QtGui import QColor


GRAPHICS_RATIO = 200.0


class GraphicsCircle(QGraphicsEllipseItem):

    def __init__(self, item):
        r = item.radius * GRAPHICS_RATIO
        super().__init__(-r, -r, 2.0*r, 2.0*r)  # left top width height
        self._item = item
        self.setPen(Qt.transparent)
        self._fill()
        # self.setToolTip(str(item))
        # self.setFlag(self.ItemIsMovable)
        self.setFlag(self.ItemClipsChildrenToShape)
        self.setAcceptHoverEvents(True)

    def setRadius(self, r):
        r *= GRAPHICS_RATIO
        self.setRect(-r, -r, 2.0*r, 2.0*r)  # left top width height

    def setPos(self, x, y, r=None):
        if r: self.setRadius(r)
        super().setPos(x*GRAPHICS_RATIO, y*GRAPHICS_RATIO)

    def hoverEnterEvent(self, event):
        self.setFlag(self.ItemClipsChildrenToShape, enabled=False)
        # self._initial_pen = self.pen()
        # self.setPen(Qt.gray)
        self._item.model.hovered_item = self._item
        self._item.pinch_body()

    def hoverLeaveEvent(self, event):
        self.setFlag(self.ItemClipsChildrenToShape)
        # self.setPen(self._initial_pen)
        self._item.model.hovered_item = None
        self._item.release_body()

    def _fill(self):
        name = self._item.name
        sat = 255 / len(name)**0.2
        c = name[0].lower()
        if 'a' <= c <= 'z':
            hue = (ord(c) - ord('a'))/(ord('z') - ord('a'))*255
        elif 'а' <= c <= 'я' or c == 'ё':
            if c == 'ё': c = 'е'
            hue = (ord(c) - ord('а'))/(ord('я') - ord('а'))*255
        elif '0' <= c <= '9':
            hue = (ord(c) - ord('0'))/(ord('9') - ord('0'))*255
        else:
            self.setBrush(QColor.white)
        return self.setBrush(QColor.fromHsv(hue, sat, 255))


class GraphicsContainerMixin:

    def __init__(self):
        self.q_item: GraphicsCircle

    def create_graphics(self):
        q_item = GraphicsCircle(self)
        if self.parent.is_root:
            self.parent.q_scene.addItem(q_item)
        else:
            q_item.setParentItem(self.parent.q_item)
        self.q_item = q_item

    def q_item_move(self): self.q_item.setPos(*self.position)#, self.radius)

    def q_items_move(self):
        '''
        for child in self.children:
            child.q_items_move()
            child.q_item_move()
        '''
        for descendant in self.descendants: descendant.q_item_move()


class GraphicsHierarchyMixin:

    def __init__(self):
        self.q_scene = QGraphicsScene()
