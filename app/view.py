from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsView, QFrame
from PyQt5.QtGui import QPainter


class Ui_MainWindow:

    def __init__(self):
        view = QGraphicsView()
        view.setBackgroundBrush(Qt.lightGray)
        view.setRenderHint(QPainter.Antialiasing)
        view.setFrameShape(QFrame.NoFrame)
        view.setSceneRect(-1, -1, 2, 2)  # always centered
        self.setCentralWidget(view)
        self._graphics_view = view
