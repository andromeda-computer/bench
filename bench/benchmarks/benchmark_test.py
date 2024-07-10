import abc
from numbers import Number
from bench.benchmarks.model import Model
from bench.runtimes.runtime import Runtime
from bench.system.system import system

class BenchmarkResult(abc.ABC):

    def __init__(self, data, test_time, watts, samples):
        vars(self).update(vars(data))
        self.time = test_time
        self.watts = watts
        self.power_samples = samples

class BenchmarkTest():

    def __init__(self, model: Model, model_runtime: Runtime, variant = None):
        self.model = model
        self.variant = variant
        self.runtime = model_runtime
        self.tag = f"{model.name}-{self.runtime.name}-{self.variant.get('resolution', None) if self.variant else None}"

        self.results = []

    def start_runtime(self):
        return self.runtime.start(self.model)
    
    def stop_runtime(self):
        return self.runtime.stop()
    
    def run(self, data):
        start_time = system.power_start("individual_bench_run")
        bench_result = self.runtime.benchmark(self.model, data, self.variant)
        watts, samples, end_time = system.power_stop("individual_bench_run")
        test_time = end_time - start_time

        result = BenchmarkResult(bench_result, test_time, watts, samples)
        self.results.append(result)

        return result

    def get_results(self):
        return self.results