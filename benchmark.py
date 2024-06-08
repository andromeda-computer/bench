import abc
import threading
import yaml
from config import CONFIG_FILE, FileDataset, Model, PromptDataset
from runtimes.docker import DockerRuntime
from runtimes.llamafile import LlamafileRuntime
from sys_info import system
from logger import logger

from utils import BenchmarkLogger

class Benchmark(abc.ABC):

    def __init__(self, name, cfg, **kwargs):
        # TODO set up proper logging for each benchmark

        self.name = name
        self.models = {}
        self.datasets = {}

        print("Setting up models...")
        for model in cfg['models']:
            name = model['name']
            self.models[name] = Model(model)

        print("Setting up datasets...")
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
        logger = BenchmarkLogger(self._benchmark_columns(), self.name.capitalize())
        update_thread = threading.Thread(target=logger.start_live_updates)
        update_thread.start()

        # with Live(layout, refresh_per_second=4) as live:
        for _, model in self.models.items():
            # Create a layout for the live display
            runtime = None
            if model.runtime == "llamafile":
                runtime = LlamafileRuntime(logger)
            elif model.runtime == "docker":
                runtime = DockerRuntime(logger)
            else:
                logger.warning(f"Runtime: {model.runtime} not supported")
                continue

            runtime.benchmark(model, self.datasets)
        
        logger.stop()

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
            "generate tps/watt"
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
            "generate tps/watt"
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
        self.benchmarks = self._init_benchmarks(self.cfg['benchmarks'], **kwargs)

    def _init_benchmarks(self, cfg, **kwargs):
        benchmarks = {}
        for benchmark, value in cfg.items():
            BenchClass = get_benchmark_class(benchmark)
            if BenchClass:
                benchmarks[benchmark] = BenchClass(benchmark, value, **kwargs)

        return benchmarks

    def benchmark(self):
        print("Gathering System Info...")
        system.print_sys_info()

        print("Benchmarking...")
        self.benchmark_language()
        self.benchmark_vision()
        self.benchmark_hearing()

    def benchmark_vision(self):
        self.benchmarks['vision'].benchmark()

    def benchmark_hearing(self):
        self.benchmarks['hearing'].benchmark()

    def benchmark_language(self):
        self.benchmarks['language'].benchmark()