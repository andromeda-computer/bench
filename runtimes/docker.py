from config import Model
from runtimes.runtime import Runtime

class DockerRuntime(Runtime):

    def _download(self):
        pass

    def benchmark(self, model, datasets):
        pass

    def _start(self, model: Model) -> bool:
        pass
    
    def _stop(self) -> bool:
        pass