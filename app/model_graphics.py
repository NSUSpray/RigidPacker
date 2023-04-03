from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsScene

from controller import InteractiveGraphicsMixin, InteractiveSceneMixin
from ui_graphics import Ui_GraphicsItem, Ui_InteractiveGraphics, Ui_Scene


class _CircleBase(QGraphicsEllipseItem, Ui_GraphicsItem):

    def __init__(self, item, parent=None):
        self._item = item
        super().__init__(parent)
        Ui_GraphicsItem.__init__(self)
        if parent: self.adoptScale()

    def adoptScale(self):
        self._scale = self.scene().scale
        self.setRadius(self._item.radius)
        self.setPos(*self._item.position)

    def setRadius(self, r):
        r *= self._scale
        self.setRect(-r, -r, 2.0*r, 2.0*r)  # left top width height

    def setPos(self, x, y):
        super().setPos(x*self._scale, y*self._scale)


class _Circle(InteractiveGraphicsMixin, _CircleBase, Ui_InteractiveGraphics):

    def __init__(self, item, parent=None):
        _CircleBase.__init__(self, item, parent)
        InteractiveGraphicsMixin.__init__(self)
        Ui_InteractiveGraphics.__init__(self)

    def paint_initial(self):
        _CircleBase.paint_initial(self)
        Ui_InteractiveGraphics.paint_initial(self)


class _SceneBase(QGraphicsScene, Ui_Scene):

    def __init__(self, model):
        super().__init__()
        Ui_Scene.__init__(self)
        self._model = model

    def addItem(self, item):
        super().addItem(item)
        item.adoptScale()


class _Scene(InteractiveSceneMixin, _SceneBase):

    def __init__(self, model):
        _SceneBase.__init__(self, model)
        InteractiveSceneMixin.__init__(self)


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

    def q_item_move(self): self.q_item.setPos(*self.position)

    '''
    def q_items_move(self):
        for child in self.children:
            child.q_items_move()
            child.q_item_move()
    '''


class GraphicsHierarchyMixin:

    def __init__(self):
        self.q_scene = _Scene(self)

    def q_items_move(self):
        for descendant in self.descendants: descendant.q_item_move()
