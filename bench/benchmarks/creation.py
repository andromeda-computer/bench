from typing import List
from bench.benchmarks.benchmark import Benchmark
from bench.utils import create_percentile_columns, Column

class CreationBenchmarkResult():

    def __init__(self, total_time, raw_k_samp_time, model_load_time):
        self.total_time = (total_time)
        self.model_load_time = (model_load_time)
        self.compute_time = self.total_time - self.model_load_time
        self.raw_k_samp_time = (raw_k_samp_time)
        self.k_samp_time = (sum(raw_k_samp_time))
        self.k_samp_percentage = (self.k_samp_time / self.compute_time)
        self.avg_sec_iter = (self.k_samp_time / len(raw_k_samp_time))
        self.avg_iter_sec = 1 / self.avg_sec_iter

class CreationBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            Column("elapsed time", True, lambda results: sum(r.time for r in results)),
            Column("model load time", True, lambda results: sum(r.model_load_time for r in results)),
            Column("avg watts", True, lambda results: sum(r.watts for r in results) / len(results)),
            Column("avg iter/sec", True, 
                   lambda results: sum(r.avg_iter_sec for r in results) / len(results),
                   lambda x: f"[cyan]{round(x, 2)}[/cyan]"),
            Column("avg sec/iter", True, 
                   lambda results: sum(r.avg_sec_iter for r in results) / len(results),
                   lambda x: f"[magenta]{round(x, 2)}[/magenta]"),
            Column("avg time to image", True, 
                   lambda results: sum(r.total_time for r in results) / len(results),
                   lambda x: f"[green]{round(x, 2)}s[/green]"),
            Column("compute time to image", True, 
                   lambda results: sum(r.compute_time for r in results) / len(results),
                   lambda x: f"[yellow]{round(x, 2)}s[/yellow]"),
            Column("avg iter/sec/watt", True, 
                   lambda results: (sum(r.avg_iter_sec for r in results) / len(results)) / 
                                   (sum(r.watts for r in results) / len(results)),
                   lambda x: f"{round(x, 4)}"),
            Column("k samp percentage", False,
                   lambda results: sum(r.k_samp_percentage for r in results) / len(results),
                   lambda x: f"{round(x, 2)}"),
        ]

    def get_columns(self):
        return [col.name for col in self._benchmark_columns()]

    def _compute_results(self, results: List):
        return {col.name: col.compute(results) for col in self._benchmark_columns()}

    def _update_display(self, tag: str, data: dict):
        self.bench_logger.update_row(tag, {
            col.name: col.format(data[col.name])
            for col in self._benchmark_columns()
            if col.display
        })

    def get_display_columns(self):
            return [col.name for col in self._benchmark_columns() if col.display]