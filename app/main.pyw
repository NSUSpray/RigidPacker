#! python3.7
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView

from storage import Storage
from model import Model
from controller import Ctrl_MainWindow, Ctrl_GraphicsView
from ui_graphics import Ui_MainWindow, Ui_GraphicsView


class GraphicsView(Ctrl_GraphicsView, QGraphicsView, Ui_GraphicsView):

    def __init__(self, *args, **kwargs):
        QGraphicsView.__init__(self, *args, **kwargs)
        Ctrl_GraphicsView.__init__(self)
        Ui_GraphicsView.__init__(self)


class MainWindow(Ctrl_MainWindow, QMainWindow, Ui_MainWindow):

    def __init__(self, model, *args, **kwargs):
        self._model: Model = model
        self._graphics_view = GraphicsView()
        self._graphics_view.setScene(model.q_scene)
        QMainWindow.__init__(self, *args, **kwargs)
        Ctrl_MainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        model.q_scene.hovered.connect(self.updateStatusBar)



app = QApplication([])
storage = Storage('../sample.db')
model = Model(storage, target_fps=30.0385)
window = MainWindow(model)
model.start()
window.showMaximized()
model.stuff()  # 15–18% CPU
app.exec()
model.quit()
