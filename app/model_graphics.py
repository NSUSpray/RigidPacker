from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsScene

from controller import InteractiveGraphicsMixin


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


class _InteractiveGraphicsCircle(InteractiveGraphicsMixin, _GraphicsCircle):

    def __init__(self, item):
        _GraphicsCircle.__init__(self, item)
        InteractiveGraphicsMixin.__init__(self)


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
