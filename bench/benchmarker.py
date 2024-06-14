import time
import yaml
from typing import List

from bench.benchmarks.hearing import HearingBenchmark
from bench.benchmarks.language import LanguageBenchmark
from bench.benchmarks.vision import VisionBenchmark
from bench.config import CONFIG_FILE
from bench.runtimes.docker import DockerRuntime
from bench.runtimes.ggml import LlamafileRuntime, WhisperfileRuntime
from bench.logger import logger
from bench.system.system import system

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

        # a name for this benchmark run
        self.name = round(time.time())
        self.cfg = yaml.safe_load(cfg_file)
        self.runtimes = self._init_runtimes(self.cfg['runtimes'])
        self.benchmarks = self._init_benchmarks(self.cfg['benchmarks'], **kwargs)

    def _init_benchmarks(self, cfg, **kwargs):
        benchmarks = {}
        for benchmark, value in cfg.items():
            BenchClass = get_benchmark_class(benchmark)
            if BenchClass:
                benchmarks[benchmark] = BenchClass(benchmark, value, self.runtimes, self.name, **kwargs)

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