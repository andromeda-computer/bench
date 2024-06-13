import abc
import threading
from typing import List

from bench.logger import logger
from bench.datasets.dataset import FileDataset, PromptDataset
from bench.models.model import Model
from bench.utils import BenchmarkLogger
from bench.system.system import system

class Benchmark(abc.ABC):

    def __init__(self, name, cfg, runtimes, **kwargs):
        # TODO set up proper logging for each benchmark
        print(f"Preparing {name} benchmark...")

        self.name = name
        self.models = {}
        self.datasets = {}
        self.runtimes = runtimes

        logger.info(f"Preparing models for {name}")
        for model in cfg['models']:
            name = model['name']
            self.models[name] = Model(model)

        logger.info(f"Preparing datasets for {name}")
        for dataset in cfg['datasets']:
            name = dataset['name']
            if dataset['type'] == "file":
                self.datasets[name] = FileDataset(self.name, dataset, **kwargs)
            elif dataset['type'] == "prompt":
                self.datasets[name] = PromptDataset(self.name, dataset, **kwargs)
            else:
                logger.warning(f"Dataset type: {dataset['type']} not supported")
                continue

        logger.info(f"Benchmark {self.name} has {len(self.models)} models and {len(self.datasets)} datasets")

    @abc.abstractmethod
    def _benchmark_columns(self):
        pass

    @abc.abstractmethod
    def _update_row(self, model: Model, results: List):
        pass

    def benchmark(self):
        self.bench_logger = BenchmarkLogger(self._benchmark_columns(), self.name.capitalize())
        update_thread = threading.Thread(target=self.bench_logger.start_live_updates)
        update_thread.start()

        for _, model in self.models.items():
            runtime = self.runtimes.get(model.runtime, None)

            if not runtime:
                logger.warning(f"Runtime: {model.runtime} not supported")
                continue

            # TODO model.benchmark(runtime, ...??)
            # almost certainly this is the way
            # the model would know what type it is so it can call the right benchmark method
            # with type hints
            logger.info(f"Benchmarking {model.name} with {model.runtime} runtime...")
            started = runtime.start(model)

            if not started:
                logger.warning(f"Failed to start runtime: {model.runtime}")
                continue

            results = []
            count = 0
            total_count = sum([len(dataset.data) for _, dataset in self.datasets.items()])
            self.bench_logger.add_row(model.name, {
                "status": f"[{count}/{total_count}]",  
                "model": model.name,
                "quant": model.quant,
            })

            for _, dataset in self.datasets.items():
                for data in dataset.data:
                    count += 1
                    self.bench_logger.update_row(model.name, {
                        "status": f"[{count}/{total_count}]"
                    })

                    # TODO it might make more sense to calculate tok/sec/watt directly here
                    start_time = system.power_start("individual_bench_run")
                    result = runtime.benchmark(model, data)
                    watts, samples, end_time = system.power_stop("individual_bench_run")
                    total_time = end_time - start_time

                    if result:
                        # TODO a class?
                        results.append({"data": result, "time": total_time, "watts": watts})
                        self._update_row(model, results)

            runtime.stop()
        self.bench_logger.stop()