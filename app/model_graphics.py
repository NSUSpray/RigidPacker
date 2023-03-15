from math import pi, sqrt

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsScene
from PyQt5.QtGui import QColor


GRAPHICS_RATIO = 200


class Circle(QGraphicsEllipseItem):

    def __init__(self, r):
        super().__init__(-r, -r, 2*r, 2*r)  # left top width height
        self.setPen(Qt.transparent)
        # self.setBrush(Qt.white)
        # self.setFlag(self.ItemIsMovable)
        self.setAcceptHoverEvents(True)
        self._radius = r

    def setPos(self, x, y, r=None):
        if r:
            super().setRect(-r, -r, 2*r, 2*r)  # left top width height
            self._radius = r
        super().setPos(x, y)

    def hoverEnterEvent(self, event): self.setPen(Qt.black)

    def hoverLeaveEvent(self, event): self.setPen(Qt.transparent)


def make_color_from(s):
    sat = 255 / len(s)**0.2
    s = s[0].lower()
    if 'a' <= s <= 'z':
        hue = (ord(s) - ord('a'))/(ord('z') - ord('a'))*255
    elif 'а' <= s <= 'я' or s == 'ё':
        if s == 'ё': s = 'е'
        hue = (ord(s) - ord('а'))/(ord('я') - ord('а'))*255
    else:
        return Qt.white
    return QColor.fromHsv(hue, sat, 255)


class GraphicsContainerMixin:

    def __init__(self):
        self.q_item: Circle# = None

    def _create_graphics_for(self, child):
        r = sqrt(child.total_area / pi)
        q_item = Circle(r*GRAPHICS_RATIO)
        if self.parent:
            q_item.setParentItem(self.q_item)
        else:
            self.q_scene.addItem(q_item)
        q_item.setData(0, self)
        q_item.setToolTip(child.name)
        color = make_color_from(child.name)
        q_item.setBrush(color)
        child.q_item = q_item

    def create_graphics_for_children(self):
        for child in self.children:
            self._create_graphics_for(child)
            child.q_item_move()

    def q_item_move(self):
        if not self.parent: return
        r = sqrt(self.total_area / pi)
        pos = [x*GRAPHICS_RATIO for x in self.position]
        self.q_item.setPos(pos[0], pos[1], r*GRAPHICS_RATIO)

    def q_items_move(self):
        for child in self.children:
            child.q_items_move()
        self.q_item_move()


class GraphicsModelMixin:

    def __init__(self): self.q_scene = QGraphicsScene()
