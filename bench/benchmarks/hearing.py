from typing import List
from bench.benchmarks.benchmark import Benchmark
from bench.utils import create_percentile_columns, Column

class HearingBenchmarkResult:
    def __init__(self, json):
        self.text = json['text']
        self.input_seconds = json['duration']
        self.transcribe_time = json['transcribe_time'] / 1000
        self.speedup = self.input_seconds / self.transcribe_time

class HearingBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            Column("elapsed time", True, 
                   lambda results: sum(r.time for r in results),
                   lambda x: f"{round(x, 2)}s"),
            Column("avg watts", True, 
                   lambda results: sum(r.watts for r in results) / len(results),
                   lambda x: f"{round(x, 2)} W"),
            Column("total input seconds", True, 
                   lambda results: sum(r.input_seconds for r in results),
                   lambda x: f"{round(x, 2)}"),
            Column("total transcribe time", True, 
                   lambda results: sum(r.transcribe_time for r in results),
                   lambda x: f"{round(x, 2)}"),
            Column("avg speedup", True, 
                   lambda results: sum(r.speedup for r in results) / len(results),
                   lambda x: f"[magenta]{round(x, 2)}x[/magenta]"),
            Column("avg speedup/watt", True, 
                   lambda results: (sum(r.speedup for r in results) / len(results)) / 
                                   (sum(r.watts for r in results) / len(results)),
                   lambda x: f"{round(x, 2)}"),
        ]

    def get_columns(self):
        return [col.name for col in self._benchmark_columns()]

    def _compute_results(self, results: List[HearingBenchmarkResult]):
        return {col.name: col.compute(results) for col in self._benchmark_columns()}

    def _update_display(self, tag: str, data: dict):
        self.bench_logger.update_row(tag, {
            col.name: col.format(data[col.name])
            for col in self._benchmark_columns()
            if col.display
        })

    def get_display_columns(self):
        return [col.name for col in self._benchmark_columns() if col.display]