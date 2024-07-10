from bench.benchmarks.benchmark_test import BenchmarkTest
from bench.runtimes.runtime import Runtime

class DockerRuntime(Runtime):

    def _download(self):
        pass

    def benchmark(self, model, datasets):
        pass

    def _start(self, model: BenchmarkTest) -> bool:
        pass
    
    def _stop(self) -> bool:
        pass