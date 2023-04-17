from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsView, QFrame
from PyQt5.QtGui import QPainter


class GraphicsView(QGraphicsView):

    def wheelEvent(self, event):
        """https://stackoverflow.com/questions/19113532"""
        self.setTransformationAnchor(self.NoAnchor)
        pos = self.mapToScene(event.pos())
        self.translate(pos.x(), pos.y())
        zoom_factor = 1.0015**event.angleDelta().y()
        self.scale(zoom_factor, zoom_factor)
        self.translate(-pos.x(), -pos.y())

    def keyPressEvent(self, event):
        if event.key() in {Qt.Key_Minus, Qt.Key_Equal}:
            self.setTransformationAnchor(self.NoAnchor)
            center = (self.width() / 2, self.height() / 2)
            pos = self.mapToScene(*center)
            self.translate(pos.x(), pos.y())
            zoom_factor = 1.2
            if event.key() == Qt.Key_Minus:
                zoom_factor = 1 / zoom_factor
            self.scale(zoom_factor, zoom_factor)
            self.translate(-pos.x(), -pos.y())
        else:
            super().keyPressEvent(event)


class Ui_MainWindow:

    def __init__(self):
        view = GraphicsView()
        view.setBackgroundBrush(Qt.gray)
        view.setRenderHint(QPainter.Antialiasing)
        view.setFrameShape(QFrame.NoFrame)
        width = view.viewport().width() * 5
        height = view.viewport().height() * 5
        view.setSceneRect(  # always centered
            -width/2, -height/2, width, height
        )
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
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
