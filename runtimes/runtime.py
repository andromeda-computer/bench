import abc

class Runtime(abc.ABC):
    def __init__(self, logger):
        self.logger = logger

    @abc.abstractmethod
    def download(self):
        pass

    @abc.abstractmethod
    def benchmark(self, model, datasets):
        pass
