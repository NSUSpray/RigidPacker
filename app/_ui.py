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
        first_letter = name[0].lower()
        if first_letter == 'ё': first_letter = 'е'
        for bounds in {('a', 'z'), ('а', 'я'), ('0', '9')}:
            if bounds[0] <= first_letter <= bounds[1]: break
        else:
            return Ot.white
        min_ord, max_ord = [ord(bound) for bound in bounds]
        hue = (ord(first_letter) - min_ord) / (max_ord - min_ord + 1)
        min_len, max_len = (265, 645)  # wavelen bounds in nanometers
        wavelen = max_len - hue*min_len
        return QColor.fromRgb(*rgb(wavelen))

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
