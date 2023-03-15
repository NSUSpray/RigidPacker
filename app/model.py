import pygame
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject

from storage import ItemBase, Storage
from model_body import BodyContainerMixin, BodyModelMixin
from model_graphics import GraphicsContainerMixin, GraphicsModelMixin


DEFAULT_TARGET_FPS = 60.077


class ContainerItem(ItemBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = None
        self.children = []

    def stuff_by(self, items):
        self.children = items
        for child in self.children:
            child.parent = self


class BodyGraphicsContainer(
    ContainerItem, BodyContainerMixin, GraphicsContainerMixin
    ):

    def __init__(self, item, target_fps=DEFAULT_TARGET_FPS):
        super().__init__(item.id, item.name, item.product_name)
        BodyContainerMixin.__init__(self, target_fps)
        GraphicsContainerMixin.__init__(self)

    def stuff_by(self, items):
        super().stuff_by(items)
        self.create_bodies_for_children()
        self.create_graphics_for_children()


class Model(
    BodyGraphicsContainer, BodyModelMixin, GraphicsModelMixin, QObject
    ):

    ''' Has connection to the database and can stuff self recursively '''

    updated = pyqtSignal()

    def __init__(self, storage, target_fps=DEFAULT_TARGET_FPS):
        self._storage: Storage = storage
        self._target_fps = target_fps
        super().__init__(storage.root, target_fps)
        BodyModelMixin.__init__(self)
        GraphicsModelMixin.__init__(self)
        QObject.__init__(self)
        self.descendants = []
        self._thread = ModelThread(self)
        self.stuff(self)
        self.updated.connect(self.q_items_move)

    def run(self): self._thread.start()

    def stop(self):
        self._thread.stop()
        self._thread.wait()

    def stuff(self, container):
        protos = self._storage.children_of(container)
        if not protos: return
        children = [
            BodyGraphicsContainer(proto, self._target_fps) for proto in protos
            ]
        container.stuff_by(children)
        for child in container.children:
            self.stuff(child)
        self.descendants += container.children

    def update(self, hovered_item=None):
        self.b2subworlds_step()
        # if hovered_item: hovered_item.b2superworlds_step()

    def render(self): self.updated.emit()


class ModelThread(QThread):

    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = model
        pygame.init()
        self._clock = pygame.time.Clock()

    def __del__(self): pygame.quit()

    def run(self):
        self._running = True
        # hovered_item = (self._model.children[1].children[2].children[0]
            # .children[2].children[4].children[9].children[0])
        # print(hovered_item.name)
        while self._running:
            self._model.update()#hovered_item)
            self._model.render()
            self._clock.tick(self._model._target_fps)

    def stop(self): self._running = False
