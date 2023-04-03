from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsView, QFrame
from PyQt5.QtGui import QPainter


class Ui_MainWindow:

    def __init__(self):
        view = QGraphicsView()
        view.setBackgroundBrush(Qt.gray)
        view.setRenderHint(QPainter.Antialiasing)
        view.setFrameShape(QFrame.NoFrame)
        view.setSceneRect(-1, -1, 2, 2)  # always centered
        self.setCentralWidget(view)
        self._graphics_view = view
        self.setWindowTitle('Rigid Packer')
        self.statusBar().setStyleSheet('background-color: darkgray;')
        self.resize(800, 600)

    def _update_status_bar(self, item):
        message = (
            f'id: {item.id}'
            f'    m: {round(item.total_mass)}'
            f'    V: {round(item.area*1000)}'
            f'   │   {item.name}'
            )
        self.statusBar().showMessage(message)
