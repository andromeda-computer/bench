import abc
import os

from bench.benchmarks.model import Model
from bench import config

class Runtime(abc.ABC):
    def __init__(self, cfg):
        self.name = cfg['name']
        self.version = cfg.get('version', None)
        self.display_name = self.name if self.version is None else f"{self.name}-{self.version}"
        self.cfg = cfg
        self.dir = os.path.join(config.RUNTIME_STORE_DIR, self.name)
        self.started = False

        self._download()

    # TODO remove model from this, instead have explicit load methods for the model to run
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
    def benchmark(self, model, data, config = None):
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
