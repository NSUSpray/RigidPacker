#! python3.7
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow

from storage import Storage
from model import Model
from view import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Ui_MainWindow.__init__(self)
        self._model: Model = model
        self._graphics_view.setScene(model.q_scene)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Space:
            self._model.toggle_gentle()


app = QApplication([])
storage = Storage('../sample.db')
model = Model(storage, target_fps=30.0385)
window = MainWindow(model)
model.start()
window.showMaximized()
model.stuff()  # 15–18% CPU
app.exec()
model.quit()
