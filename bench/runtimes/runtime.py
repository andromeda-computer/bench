import abc
import os

from bench.config import RUNTIME_STORE_DIR
from bench.models.model import Model

class Runtime(abc.ABC):
    def __init__(self, cfg):
        self.name = cfg['name']
        self.cfg = cfg
        self.dir = os.path.join(RUNTIME_STORE_DIR, self.name)
        self.started = False

        self._download()

    def start(self, model: Model) -> bool:
        if not self.started:
            self.started = self._start(model)
            return self.started
        
    def stop(self) -> bool:
        if self.started:
            self._stop()
            self.started = False
        
    # TODO this probably should be split up a different way.
    # the handling is very ugly in Runtime.
    @abc.abstractmethod
    def benchmark(self, model, data):
        pass

    @abc.abstractmethod
    def _download(self):
        pass

    @abc.abstractmethod
    def _start(self, model: Model) -> bool:
        pass

    @abc.abstractmethod
    def _stop(self) -> bool:
        pass
