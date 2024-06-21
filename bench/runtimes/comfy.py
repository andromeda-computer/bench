
from bench.models.model import Model
from bench.runtimes.runtime import Runtime


class ComfyRuntime(Runtime):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.pid = None

    def _download(self):
        pass

    def _start(self, model: Model):
        return self._start_server(model)

    def benchmark(self, model: Model, data):
        if (model.type == "creation"):
            return self._benchmark_creation(model, data)
    
    def _benchmark_creation(self, model: Model, data):
        pass