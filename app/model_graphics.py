from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsScene
from PyQt5.QtGui import QColor


GRAPHICS_RATIO = 250.0


class GraphicsCircle(QGraphicsEllipseItem):

    def __init__(self, item):
        r = item.radius * GRAPHICS_RATIO
        super().__init__(-r, -r, 2.0*r, 2.0*r)  # left top width height
        self._item = item
        self.setPen(Qt.transparent)
        self._fill()
        # self.setToolTip(str(item))
        self.setFlags(0
            | self.ItemIsMovable
            # | self.ItemClipsToShape
            | self.ItemClipsChildrenToShape
            | self.ItemContainsChildrenInShape
            )
        self.setAcceptHoverEvents(True)

    def setRadius(self, r):
        r *= GRAPHICS_RATIO
        self.setRect(-r, -r, 2.0*r, 2.0*r)  # left top width height

    def setPos(self, x, y):
        super().setPos(x*GRAPHICS_RATIO, y*GRAPHICS_RATIO)

    def hoverEnterEvent(self, event):
        # self.setFlag(self.ItemClipsToShape)
        self.setFlag(self.ItemClipsChildrenToShape, enabled=False)
        self.setFlag(self.ItemContainsChildrenInShape, enabled=False)
        # for child in self._item.children:
        #     child.q_item.setFlag(self.ItemClipsToShape)
        self._last_pen = self.pen()
        self.setPen(Qt.darkGray)
        self._item.model.hovered_item = self._item
        self._item.pinch_body()
        self.setZValue(1)

    def hoverLeaveEvent(self, event):
        # self.setFlag(self.ItemClipsToShape, enabled=False)
        self.setFlag(self.ItemClipsChildrenToShape)
        self.setFlag(self.ItemContainsChildrenInShape)
        # for child in self._item.children:
        #     child.q_item.setFlag(self.ItemClipsToShape, enabled=False)
        self.setPen(self._last_pen)
        self._item.model.hovered_item = None
        self._item.release_body()
        self.setZValue(0)

    def mousePressEvent(self, event):
        pos = event.pos()
        self._item.drag_point = [x/GRAPHICS_RATIO for x in (pos.x(),pos.y())]

    def mouseReleaseEvent(self, event):
        self._item.drag_target = None
        self._item.pinch_body()

    def mouseMoveEvent(self, event):
        pos = self.mapToParent(event.pos())
        self._item.drag_target = [x/GRAPHICS_RATIO for x in (pos.x(),pos.y())]
        self._item.release_body(calm=True)

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
            return self.setBrush(QColor.white)
        self.setBrush(QColor.fromHsv(hue, sat, 255))


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
