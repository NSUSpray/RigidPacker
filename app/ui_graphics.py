from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter

from utilities.wavelength_to_rgb import rgb


class Ui_GraphicsItem:

    initialPen = Qt.transparent

    def __init__(self):
        self.initialBrush = self._make_color()
        self.paintInitial()

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

    def paintInitial(self):
        self.setPen(self.initialPen)
        if self._item.nesting_level % 2:
            brush = self.initialBrush.lighter(120)
        else:
            brush = self.initialBrush.darker(110)
        self.setBrush(brush)
        # self.setFlag(self.ItemClipsToShape)
        self.setFlag(self.ItemClipsChildrenToShape)
        self.setFlag(self.ItemContainsChildrenInShape)


class Ui_InteractiveGraphics:

    pinchedPen = QColor.fromRgbF(0, 0, 0, 0.25)
    pickedPen = QColor.fromRgbF(0, 0, 0, 0.125)
    pickedBrush = Qt.transparent

    def paintInitial(self):
        # for child in item.children:
        #     child.q_item.setFlag(self.ItemClipsToShape, enabled=False)
        self.setZValue(0)
        self.setAcceptedMouseButtons(Qt.AllButtons)
        self.setAcceptHoverEvents(True)

    def paintPinched(self):
        self.setPen(self.pinchedPen)
        # self.setFlag(self.ItemClipsToShape)
        self.setFlag(self.ItemClipsChildrenToShape, enabled=False)
        self.setFlag(self.ItemContainsChildrenInShape, enabled=False)
        # for child in item.children:
        #     child.q_item.setFlag(self.ItemClipsToShape)
        self.setZValue(1)

    def paintPickedUp(self):
        self.setPen(self.pickedPen)
        self.setBrush(self.pickedBrush)
        self.setAcceptedMouseButtons(Qt.RightButton)

    def paintPickedUpDescendant(self):
        self.setPen(self.pickedPen)
        self.setBrush(self.pickedBrush)
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.setAcceptHoverEvents(False)


class Ui_GraphicsScene:
    scale = 230.0  # pixels per meter


class Ui_GraphicsView:

    def __init__(self, *args, **kwargs):
        self.setBackgroundBrush(Qt.gray)
        self.setRenderHint(QPainter.Antialiasing)
        self.setFrameShape(self.NoFrame)
        width = self.viewport().width() * 5
        height = self.viewport().height() * 5
        self.setSceneRect(  # always centered
            -width/2, -height/2, width, height
        )
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


class Ui_MainWindow:

    def __init__(self):
        self.setCentralWidget(self._graphics_view)
        self.setWindowTitle('Rigid Packer')
        self.statusBar().setStyleSheet('background-color: darkgray;')
        self.resize(800, 600)

    def updateStatusBar(self, item):
        message = (
            f'id: {item.id}'
            f'    m: {round(item.total_mass)}'
            f'    V: {round(item.area*1000)}'
            f'   │   {item.name}'
            )
        self.statusBar().showMessage(message)
