from PyQt5.QtCore import Qt, pyqtSignal


class Ctrl_GraphicsItem:

    def __init__(self):
        self._being_moved = False

    def hoverEnterEvent(self, event):
        self._item.pinch()
        self.scene().hovered.emit(self._item)

    def hoverLeaveEvent(self, event):
        self._item.release()

    def mousePressEvent(self, event):
        event.accept()
        button = event.button()
        item = self._item
        if button == Qt.LeftButton:
            drag_point = self.scene().mapToBox2D(event.pos())
            item.start_dragging(drag_point)
        elif button == Qt.RightButton:
            for picked_up_item in item.model.picked_up_items:
                if item in picked_up_item.ancestors: return
            item.toggle_picked_up()

    def mouseMoveEvent(self, event):
        event.accept()
        if event.buttons() != Qt.LeftButton: return
        self._being_moved = True
        drag_target = self.scene().mapToBox2D(self.mapToParent(event.pos()))
        self._item.drag(drag_target)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton: return
        item = self._item
        if self._being_moved:
            item.finish_dragging()
            self._being_moved = False
        elif item.model.picked_up_items:  # just a mouse click, not a drag
            if item.picked_up: return
            throwing_target = self.scene().mapToBox2D(event.pos())
            item.take_picked_up(throwing_target)

    def mouseDoubleClickEvent(self, event):
        event.accept()
        if event.button() != Qt.RightButton: return
        item = self._item
        picked_up_descendants = \
                set(item.descendants) & set(item.model.picked_up_items)
        if picked_up_descendants:
            # unpick picked up descendants
            for picked_up_descendant in picked_up_descendants:
                picked_up_descendant.toggle_picked_up()
        else:
            # pick up or give up all siblings
            for sibling in item.parent.children:
                if sibling.picked_up == item.picked_up: continue
                sibling.toggle_picked_up()


class Ctrl_GraphicsScene:

    hovered = pyqtSignal(object)

    def mapToBox2D(self, pos):
        return [x/self.scale for x in (pos.x(), pos.y())]

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if event.isAccepted(): return
        self.hovered.emit(self._model)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.isAccepted(): return
        if event.button() != Qt.LeftButton: return
        if not self._model.picked_up_items: return
        throwing_target = self.mapToBox2D(event.scenePos())
        self._model.take_picked_up(throwing_target)

    def mouseDoubleClickEvent(self, event):
        super().mouseDoubleClickEvent(event)
        if event.isAccepted(): return
        if event.button() != Qt.RightButton: return
        picked_up_descendants = \
                set(self._model.descendants) & set(self._model.picked_up_items)
        if not picked_up_descendants: return
        # unpick picked up descendants
        for picked_up_descendant in picked_up_descendants:
            picked_up_descendant.toggle_picked_up()


class Ctrl_GraphicsView:

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


class Ctrl_MainWindow:

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Space:
            self._model.toggle_gentle()