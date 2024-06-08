import abc
import os

from config import RUNTIME_STORE_DIR

class Runtime(abc.ABC):
    def __init__(self, cfg):
        self.name = cfg['name']
        self.cfg = cfg
        self.dir = os.path.join(RUNTIME_STORE_DIR, self.name)

        self._download()
        
    @abc.abstractmethod
    def _download(self):
        pass

    @abc.abstractmethod
    def benchmark(self, model, datasets, benchmark_logger):
        pass
