import abc
import threading
import yaml
from benchmarks.hearing import HearingBenchmarkResult
from benchmarks.language import LanguageBenchmarkResult
from config import CONFIG_FILE, FileDataset, Model, PromptDataset
from runtimes.docker import DockerRuntime
from runtimes.ggml import LlamafileRuntime, WhisperfileRuntime
from sys_info import system
from logger import logger
from typing import List

from utils import BenchmarkLogger

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
                "model": model.name
            })

            for _, dataset in self.datasets.items():
                for data in dataset.data:
                    count += 1
                    self.bench_logger.update_row(model.name, {
                        "status": f"[{count}/{total_count}]"
                    })

                    system.power_start("individual_bench_run")
                    result = runtime.benchmark(model, data)
                    power = system.power_stop("individual_bench_run")
                    if result:
                        results.append(result)
                        # TODO calculate power stats
                        self._update_row(model, results)
                        # TODO runtime.benchmark(model, data, bench_logger)

            runtime.stop()

            # runtime.benchmark(model, self.datasets, bench_logger)
        
        self.bench_logger.stop()


class LanguageBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            "status", 
            "model",
            "# prompt tokens",
            "# generated tokens",
            "prompt tps",
            "generate tps",
            # "prompt tps/watt",
            # "generate tps/watt",
            # "avg watts"
        ]
    
    def _update_row(self, model: Model, results: List[LanguageBenchmarkResult]):
        self.bench_logger.update_row(model.name, {
            "# prompt tokens": sum(result.n_prompt_tokens for result in results),
            "# generated tokens": sum(result.n_generated_tokens for result in results),
            "prompt tps": sum(result.prompt_tps for result in results) / len(results),
            "generate tps": sum(result.generated_tps for result in results) / len(results),
            # "prompt tps/watt": sum(result.prompt_tps_watt for result in results) / len(results),
            # "generate tps/watt": sum(result.generated_tps_watt for result in results) / len(results),
            # "avg watts": sum(result.avg_watts for result in results) / len(results)
        })

class HearingBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            "status", 
            "model",
            "total input seconds",
            "total transcribe time",
            "avg speedup",
            # "avg speedup/watt",
            # "avg watts"
        ]

    def _update_row(self, model: Model, results: List[HearingBenchmarkResult]):
        self.bench_logger.update_row(model.name, {
            "total input seconds": sum(result.input_seconds for result in results),
            "total transcribe time": sum(result.transcribe_time for result in results),
            "avg speedup": sum(result.speedup for result in results) / len(results),
            # "avg speedup/watt": sum(result.speedup_watt for result in results) / len(results),
            # "avg watts": sum(result.avg_watts for result in results) / len(results)
        })

class VisionBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            "status", 
            "model",
            "# images",
            "# prompt tokens",
            "# generated tokens",
            # "clip time",
            "prompt tps",
            "generate tps",
            # "prompt tps/watt",
            # "generate tps/watt",
            # "avg watts"
        ]

    def _update_row(self, model: Model, results: List[LanguageBenchmarkResult]):
        self.bench_logger.update_row(model.name, {
            "# images": len(results),
            "# prompt tokens": sum(result.n_prompt_tokens for result in results),
            "# generated tokens": sum(result.n_generated_tokens for result in results),
            # "clip time": sum(result.clip_time for result in results),
            "prompt tps": sum(result.prompt_tps for result in results) / len(results),
            "generate tps": sum(result.generated_tps for result in results) / len(results),
            # "prompt tps/watt": sum(result.prompt_tps_watt for result in results) / len(results),
            # "generate tps/watt": sum(result.generated_tps_watt for result in results) / len(results),
            # "avg watts": sum(result.avg_watts for result in results) / len(results)
        })

def get_benchmark_class(benchmark):
    if benchmark == "language":
        return LanguageBenchmark
    elif benchmark == "hearing":
        return HearingBenchmark
    elif benchmark == "vision":
        return VisionBenchmark
    else:
        logger.warning(f"Benchmark {benchmark} not supported")
        return None

class Benchmarker():

    def __init__(self, **kwargs):
        cfg_file = open(CONFIG_FILE, 'r')

        self.cfg = yaml.safe_load(cfg_file)
        self.runtimes = self._init_runtimes(self.cfg['runtimes'])
        self.benchmarks = self._init_benchmarks(self.cfg['benchmarks'], **kwargs)

    def _init_benchmarks(self, cfg, **kwargs):
        benchmarks = {}
        for benchmark, value in cfg.items():
            BenchClass = get_benchmark_class(benchmark)
            if BenchClass:
                benchmarks[benchmark] = BenchClass(benchmark, value, self.runtimes, **kwargs)

        return benchmarks

    def _init_runtimes(self, cfg):
        runtimes = {}
        for runtime in cfg:
            name = runtime['name']
            if name == "docker":
                runtimes[name] = DockerRuntime(runtime)
            elif name == "llamafile":
                runtimes[name] = LlamafileRuntime(runtime)
            elif name == "whisperfile":
                runtimes[name] = WhisperfileRuntime(runtime)
            else:
                logger.warning(f"Runtime {runtime} not supported")
        
        return runtimes

    def benchmark(self):
        print("Gathering System Info...")
        system.print_sys_info()

        print("Benchmarking...")
        self.benchmark_language()
        self.benchmark_vision()
        self.benchmark_hearing()

    # TODO remove these and do in a loop instead
    def benchmark_vision(self):
        self.benchmarks['vision'].benchmark()

    def benchmark_hearing(self):
        self.benchmarks['hearing'].benchmark()

    def benchmark_language(self):
        self.benchmarks['language'].benchmark()