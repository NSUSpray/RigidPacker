from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


def _color_by_name(name):
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
        return Qt.white
    return QColor.fromHsv(hue, sat, 255)


class Ui_GraphicsItem:

    graphics_ratio = 230.0
    initial_pen = Qt.transparent

    def __init__(self):
        self.setPen(self.initial_pen)
        self.initial_brush = _color_by_name(self._item.name)
        self.setBrush(self.initial_brush)
        # self.setToolTip(str(item))
        # self.setFlag(self.ItemClipsToShape)
        self.setFlag(self.ItemClipsChildrenToShape)
        self.setFlag(self.ItemContainsChildrenInShape)


class Ui_InteractiveGraphics(Ui_GraphicsItem):

    pinched_pen = Qt.darkGray
    picked_pen = Qt.gray
    picked_brush = Qt.lightGray

    def __init__(self):
        super().__init__()
        self.setAcceptHoverEvents(True)

    def paint_pinched(self):
        # self.setFlag(self.ItemClipsToShape)
        self.setFlag(self.ItemClipsChildrenToShape, enabled=False)
        self.setFlag(self.ItemContainsChildrenInShape, enabled=False)
        # for child in item.children:
        #     child.q_item.setFlag(self.ItemClipsToShape)
        self.setPen(self.pinched_pen)
        self.setZValue(1)

    def paint_released(self):
        # self.setFlag(self.ItemClipsToShape, enabled=False)
        self.setFlag(self.ItemClipsChildrenToShape)
        self.setFlag(self.ItemContainsChildrenInShape)
        # for child in item.children:
        #     child.q_item.setFlag(self.ItemClipsToShape, enabled=False)
        self.setPen(self.initial_pen)
        self.setZValue(0)

    def paint_picked_up(self):
        self.setPen(self.picked_pen)
        self.setBrush(self.picked_brush)
        self.setAcceptedMouseButtons(Qt.RightButton)
        for descendant in self._item.descendants:
            q_item = descendant.q_item
            q_item.setPen(q_item.picked_pen)
            q_item.setBrush(q_item.picked_brush)
            q_item.setAcceptedMouseButtons(Qt.NoButton)
            q_item.setAcceptHoverEvents(False)

    def paint_dropped(self):
        self.setPen(self.initial_pen)
        self.setBrush(self.initial_brush)
        self.setAcceptedMouseButtons(Qt.AllButtons)
        for descendant in self._item.descendants:
            q_item = descendant.q_item
            q_item.setPen(q_item.initial_pen)
            q_item.setBrush(q_item.initial_brush)
            q_item.setAcceptedMouseButtons(Qt.AllButtons)
            q_item.setAcceptHoverEvents(True)
