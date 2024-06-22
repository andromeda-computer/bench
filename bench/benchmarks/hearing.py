from typing import List

from bench.benchmarks.benchmark import Benchmark
from bench.models.model import Model

class HearingBenchmarkResult():

    # TODO json really should be an adapter in the runtime instead.
    def __init__(self, json):
        self.text = json['text']
        self.input_seconds = json['duration']
        self.transcribe_time = json['transcribe_time'] / 1000
        self.speedup = self.input_seconds / self.transcribe_time

class HearingBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            "status", 
            "model",
            "quant",
            "elapsed time",
            "avg watts",
            "total input seconds",
            "total transcribe time",
            "avg speedup",
            "avg speedup/watt",
        ]

    def _update_row(self, model: Model, results: List):
        avg_watts = sum(result['watts'] for result in results) / len(results)
        avg_speedup = sum(result['data'].speedup for result in results) / len(results)

        self.bench_logger.update_row(model.tag, {
            "elapsed time": f"{round(sum(result['time'] for result in results), 2)}s",
            "avg watts": f"{round(avg_watts, 2)} W",
            "total input seconds": round(sum(result['data'].input_seconds for result in results), 2),
            "total transcribe time": round(sum(result['data'].transcribe_time for result in results), 2),
            "avg speedup": f"[magenta]{round(avg_speedup, 2)}x[/magenta]",
            "avg speedup/watt": round(avg_speedup / avg_watts, 2),
        })