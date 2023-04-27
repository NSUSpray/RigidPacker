from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsScene

from _ctrl import Ctrl_GraphicsItem, Ctrl_GraphicsScene
from _ui import Ui_GraphicsItem, Ui_InteractiveGraphics, Ui_GraphicsScene


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
        r *= self.__scale
        self.setRect(-r, -r, 2.0*r, 2.0*r)  # left top width height

    def setPos(self, x, y):
        super().setPos(x*self.__scale, y*self.__scale)

    def adoptScale(self):
        self.__scale = self.scene().scale
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
        self._q_item: _Circle = None

    def _create_q_item(self):
        if self._parent.is_root:
            self._q_item = _Circle(self)
            self._parent._q_scene.addItem(self._q_item)
        else:
            self._q_item = _Circle(self, self._parent._q_item)

    def _adopt_parent_q_item(self):
        parent_q_item = None if self._parent.is_root else self._parent._q_item
        self._q_item.setParentItem(parent_q_item)

    def move_q_item(self): self._q_item.setPos(*self.position)
    '''
    def _move_q_items(self):
        for child in self._children:
            child._move_q_items()
            child.move_q_item()
    '''


class GraphicsHierarchyMixin:

    def __init__(self):
        self._q_scene = _Scene(self)

    def _move_q_items(self):
        for descendant in self._descendants: descendant.move_q_item()
