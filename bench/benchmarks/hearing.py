from typing import List

from bench.benchmarks.benchmark import Benchmark
from bench.benchmarks.benchmark_test import BenchmarkTest

class HearingBenchmarkResult():

    # TODO json really should be an adapter in the runtime instead.
    def __init__(self, json):
        self.text = json['text']
        self.input_seconds = (json['duration'])
        self.transcribe_time = (json['transcribe_time'] / 1000)
        self.speedup = (self.input_seconds / self.transcribe_time)

class HearingBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            "total input seconds",
            "total transcribe time",
            "avg speedup",
            "avg speedup/watt",
        ]

    def _compute_results(self, results: List):
        avg_watts = sum(result.watts for result in results) / len(results)
        avg_speedup = sum(result.speedup for result in results) / len(results)
        
        return {
            "elapsed_time": sum(result.time for result in results),
            "avg_watts": avg_watts,
            "total_input_seconds": sum(result.input_seconds for result in results),
            "total_transcribe_time": sum(result.transcribe_time for result in results),
            "avg_speedup": avg_speedup,
            "avg_speedup_per_watt": avg_speedup / avg_watts,
        }

    def _update_display(self, tag: str, data: dict):
        self.bench_logger.update_row(tag, {
            "elapsed time": f"{round(data['elapsed_time'], 2)}s",
            "avg watts": f"{round(data['avg_watts'], 2)} W",
            "total input seconds": round(data['total_input_seconds'], 2),
            "total transcribe time": round(data['total_transcribe_time'], 2),
            "avg speedup": f"[magenta]{round(data['avg_speedup'], 2)}x[/magenta]",
            "avg speedup/watt": round(data['avg_speedup_per_watt'], 2),
        })