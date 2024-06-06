import abc

class Runtime(abc.ABC):
    @abc.abstractmethod
    def download(self):
        pass

    @abc.abstractmethod
    def benchmark(self, model, datasets):
        pass
