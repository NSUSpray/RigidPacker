from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from wavelength_to_rgb import rgb


class Ui_GraphicsItem:

    graphics_ratio = 230.0
    initial_pen = Qt.transparent

    def __init__(self):
        self.initial_brush = self._make_color()
        self.setToolTip(self._item.name)
        self.paint_initial()

    def _make_color(self):
        name = self._item.name
        c = name[0].lower()
        if 'a' <= c <= 'z':
            hue = (ord(c) - ord('a'))/(ord('z') - ord('a') + 1)
        elif 'а' <= c <= 'я' or c == 'ё':
            if c == 'ё': c = 'е'
            hue = (ord(c) - ord('а'))/(ord('я') - ord('а') + 1)
        elif '0' <= c <= '9':
            hue = (ord(c) - ord('0'))/(ord('9') - ord('0') + 1)
        else:
            return Qt.white
        return QColor.fromRgb(*rgb(645 - hue*265))

    def paint_initial(self):
        self.setPen(self.initial_pen)
        if self._item.nesting_level % 2:
            brush = self.initial_brush.lighter(120)
        else:
            brush = self.initial_brush.darker(110)
        self.setBrush(brush)
        # self.setFlag(self.ItemClipsToShape)
        self.setFlag(self.ItemClipsChildrenToShape)
        self.setFlag(self.ItemContainsChildrenInShape)


class Ui_InteractiveGraphics(Ui_GraphicsItem):

    pinched_pen = QColor.fromRgbF(0, 0, 0, 0.25)
    picked_pen = QColor.fromRgbF(0, 0, 0, 0.125)
    picked_brush = Qt.transparent

    def paint_initial(self):
        super().paint_initial()
        # for child in item.children:
        #     child.q_item.setFlag(self.ItemClipsToShape, enabled=False)
        self.setZValue(0)
        self.setAcceptedMouseButtons(Qt.AllButtons)
        self.setAcceptHoverEvents(True)

    def paint_pinched(self):
        self.setPen(self.pinched_pen)
        # self.setFlag(self.ItemClipsToShape)
        self.setFlag(self.ItemClipsChildrenToShape, enabled=False)
        self.setFlag(self.ItemContainsChildrenInShape, enabled=False)
        # for child in item.children:
        #     child.q_item.setFlag(self.ItemClipsToShape)
        self.setZValue(1)

    def paint_picked_up(self):
        self.setPen(self.picked_pen)
        self.setBrush(self.picked_brush)
        self.setAcceptedMouseButtons(Qt.RightButton)

    def paint_picked_up_descendant(self):
        self.setPen(self.picked_pen)
        self.setBrush(self.picked_brush)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.setAcceptHoverEvents(False)
