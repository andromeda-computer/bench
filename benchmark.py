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

class LanguageBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            "status", 
            "model",
            "elapsed time",
            "avg watts",
            "# prompt tokens",
            "# generated tokens",
            "prompt tps",
            "generate tps",
            "avg ttft",
            "prompt tps/watt",
            "generate tps/watt",
        ]
    
    def _update_row(self, model: Model, results):
        avg_watts = sum(result['watts'] for result in results) / len(results)
        prompt_tps = sum(result['data'].prompt_tps for result in results) / len(results)
        generated_tps = sum(result['data'].generated_tps for result in results) / len(results)
        avg_ttft = sum(result['data'].ttft for result in results) / len(results)

        self.bench_logger.update_row(model.name, {
            "elapsed time": f"{round(sum(result['time'] for result in results), 2)}sec",
            "avg watts": round(avg_watts, 2),
            "# prompt tokens": sum(result['data'].n_prompt_tokens for result in results),
            "# generated tokens": sum(result['data'].n_generated_tokens for result in results),
            "prompt tps": f"[cyan]{round(prompt_tps, 2)}[/cyan]",
            "generate tps": f"[magenta]{round(generated_tps, 2)}[/magenta]",
            "avg ttft": f"[green]{round(avg_ttft)}ms[/green]",
            "prompt tps/watt": f"{round(prompt_tps / avg_watts, 2)}",
            "generate tps/watt": f"{round(generated_tps / avg_watts, 2)}",
        })

class HearingBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            "status", 
            "model",
            "elapsed time",
            "avg watts",
            "total input seconds",
            "total transcribe time",
            "avg speedup",
            "avg speedup/watt",
        ]

    def _update_row(self, model: Model, results: List[HearingBenchmarkResult]):
        avg_watts = sum(result['watts'] for result in results) / len(results)
        avg_speedup = sum(result['data'].speedup for result in results) / len(results)

        self.bench_logger.update_row(model.name, {
            "elapsed time": f"{round(sum(result['time'] for result in results), 2)}sec",
            "total input seconds": round(sum(result['data'].input_seconds for result in results), 2),
            "total transcribe time": round(sum(result['data'].transcribe_time for result in results), 2),
            "avg speedup": f"[magenta]{round(avg_speedup, 2)}x[/magenta]",
            "avg speedup/watt": round(avg_speedup / avg_watts, 2),
            "avg watts": round(avg_watts, 2)
        })

class VisionBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            "status", 
            "model",
            "elapsed time",
            "avg watts",
            "# prompt tokens",
            "# generated tokens",
            "prompt tps",
            "generate tps",
            "throughput",
            "avg ttft",
            "prompt tps/watt",
            "generate tps/watt",
        ]

    def _update_row(self, model: Model, results: List):
        avg_watts = sum(result['watts'] for result in results) / len(results)
        prompt_tps = sum(result['data'].prompt_tps for result in results) / len(results)
        generated_tps = sum(result['data'].generated_tps for result in results) / len(results)
        elapsed_time = sum(result['time'] for result in results)
        avg_ttft = sum(result['data'].ttft for result in results) / len(results)

        self.bench_logger.update_row(model.name, {
            "elapsed time": f"{round(elapsed_time)}sec",
            "avg watts": round(avg_watts, 2),
            "throughput": f"[purple4]{round(len(results) / elapsed_time, 2)} imgs/sec[/purple4]",
            "# prompt tokens": sum(result['data'].n_prompt_tokens for result in results),
            "# generated tokens": sum(result['data'].n_generated_tokens for result in results),
            "prompt tps": f"[cyan]{round(prompt_tps, 2)}[/cyan]",
            "generate tps": f"[magenta]{round(generated_tps, 2)}[/magenta]",
            "avg ttft": f"[green]{round(avg_ttft)}ms[/green]",
            "prompt tps/watt": f"{round(prompt_tps / avg_watts, 2)}",
            "generate tps/watt": f"{round(generated_tps / avg_watts, 2)}",
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