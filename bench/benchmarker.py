import time
import yaml
from typing import List

from bench.benchmarks.creation import CreationBenchmark
from bench.benchmarks.hearing import HearingBenchmark
from bench.benchmarks.language import LanguageBenchmark
from bench.benchmarks.vision import VisionBenchmark
from bench.config import CONFIG_FILE
from bench.downloader import get_downloader
from bench.runtimes.comfy import ComfyRuntime
from bench.runtimes.docker import DockerRuntime
from bench.runtimes.ggml import LlamafileRuntime, WhisperfileRuntime
from bench.logger import logger
from bench.system.system import system

ALL_BENCHMARKS = ["language", "hearing", "vision", "creation"]

def get_benchmark_class(benchmark):
    if benchmark == "language":
        return LanguageBenchmark
    elif benchmark == "hearing":
        return HearingBenchmark
    elif benchmark == "vision":
        return VisionBenchmark
    elif benchmark == "creation":
        return CreationBenchmark
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
        self.downloader = get_downloader()

    async def download(self):
        await self.downloader.wait_for_downloads()

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
            elif name == "comfy":
                runtimes[name] = ComfyRuntime(runtime)
            else:
                logger.warning(f"Runtime {runtime} not supported")
        
        return runtimes

    def benchmark(self, benchmark: str):
        print("Gathering System Info...")
        system.print_sys_info()

        to_run = ALL_BENCHMARKS
        if benchmark != "all":
            to_run = benchmark.split(',')

        logger.info(f"Running benchmarks: {to_run}")

        for bench in to_run:
            if bench in self.benchmarks:
                self.benchmarks[bench].benchmark()
            else:
                logger.warning(f"Benchmark {bench} not supported")