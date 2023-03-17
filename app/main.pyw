#! python3.7
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow

from storage import Storage
from model import Model
from view import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Ui_MainWindow.__init__(self)
        self._graphics_view.setScene(model.q_scene)
        self._model = model

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape: self.close()
        elif event.key() == Qt.Key_Space:
            if self._model._thread._running: self._model.stop()
            else: self._model.run()


app = QApplication(sys.argv)
# storage = Storage('../../inventory.db')
storage = Storage('../sample.db')
model = Model(storage, target_fps=30.0385)
window = MainWindow(model)
window.showMaximized()
model.run()
app.exec()
model.stop()
