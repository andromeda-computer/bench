import abc
import threading
import yaml
from config import CONFIG_FILE, FileDataset, Model, PromptDataset
from runtimes.docker import DockerRuntime
from runtimes.ggml import LlamafileRuntime, WhisperfileRuntime
from sys_info import system
from logger import logger

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

    def benchmark(self):
        bench_logger = BenchmarkLogger(self._benchmark_columns(), self.name.capitalize())
        update_thread = threading.Thread(target=bench_logger.start_live_updates)
        update_thread.start()

        for _, model in self.models.items():
            runtime = self.runtimes.get(model.runtime, None)

            if not runtime:
                logger.warning(f"Runtime: {model.runtime} not supported")
                continue

            logger.info(f"Benchmarking {model.name} with {model.runtime} runtime...")
            runtime.benchmark(model, self.datasets, bench_logger)
        
        bench_logger.stop()


class LanguageBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            "status", 
            "model",
            "# prompt tokens",
            "# generated tokens",
            "prompt tps",
            "generate tps",
            "prompt tps/watt",
            "generate tps/watt",
            "avg watts"
        ]

class HearingBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            "status", 
            "model",
            "total input seconds",
            "total transcribe time",
            "avg speedup",
            "avg speedup/watt",
            "avg watts"
        ]

class VisionBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            "status", 
            "model",
            "# images",
            "# prompt tokens",
            "# generated tokens",
            "clip time",
            "prompt tps",
            "generate tps",
            "prompt tps/watt",
            "generate tps/watt",
            "avg watts"
        ]

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