from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsScene

from controller import Ctrl_GraphicsItem, Ctrl_GraphicsScene
from ui_graphics import Ui_GraphicsItem, Ui_InteractiveGraphics, Ui_GraphicsScene


class _Circle(
        Ctrl_GraphicsItem,
        QGraphicsEllipseItem,
        Ui_GraphicsItem,
        Ui_InteractiveGraphics,
        ):

    def __init__(self, item, parent=None):
        self._item = item
        QGraphicsEllipseItem.__init__(self, parent)
        Ui_GraphicsItem.__init__(self)
        if parent: self.adoptScale()
        Ctrl_GraphicsItem.__init__(self)
        Ui_InteractiveGraphics.__init__(self)

    def setRadius(self, r):
        r *= self._scale
        self.setRect(-r, -r, 2.0*r, 2.0*r)  # left top width height

    def setPos(self, x, y):
        super().setPos(x*self._scale, y*self._scale)

    def adoptScale(self):
        self._scale = self.scene().scale
        self.setRadius(self._item.radius)
        self.setPos(*self._item.position)

    def paintInitial(self):
        Ui_GraphicsItem.paintInitial(self)
        Ui_InteractiveGraphics.paintInitial(self)


class _Scene(Ctrl_GraphicsScene, QGraphicsScene, Ui_GraphicsScene):

    def __init__(self, model):
        QGraphicsScene.__init__(self)
        Ui_GraphicsScene.__init__(self)
        Ctrl_GraphicsScene.__init__(self)
        self._model = model

    def addItem(self, item):
        super().addItem(item)
        item.adoptScale()


class GraphicsContainerMixin:

    def __init__(self):
        self.q_item: _Circle = None

    def create_q_item(self):
        if self.parent.is_root:
            self.q_item = _Circle(self)
            self.parent.q_scene.addItem(self.q_item)
        else:
            self.q_item = _Circle(self, self.parent.q_item)

    def adopt_parent_q_item(self):
        parent_q_item = None if self.parent.is_root else self.parent.q_item
        self.q_item.setParentItem(parent_q_item)

    def move_q_item(self): self.q_item.setPos(*self.position)

    '''
    def move_q_items(self):
        for child in self.children:
            child.move_q_items()
            child.move_q_item()
    '''


class GraphicsHierarchyMixin:

    def __init__(self):
        self.q_scene = _Scene(self)

    def move_q_items(self):
        for descendant in self.descendants: descendant.move_q_item()
