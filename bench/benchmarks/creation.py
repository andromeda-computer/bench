
from typing import List
from bench.benchmarks.benchmark import Benchmark
from bench.models.model import Model


class CreationBenchmarkResult():

    def __init__(self):
        self.total_time = 0
        self.k_samp_time = 0
        self.k_samp_percentage = self.k_samp_time / self.total_time
        self.avg_iter_sec = 0
        self.avg_sec_iter = 0

class CreationBenchmar(Benchmark):

    def _benchmark_columns(self):
        return [
            "status",
            "model",
            "quant",
            "elapsed time",
            "avg watts",
            "k_samp time",
            "k_samp percentage",
            "avg iter/sec",
            "avg sec/iter",
            "avg iter/sec/watt",
        ]
    
    def _update_row(self, model: Model, results: List):
        avg_watts = sum(result['watts'] for result in results) / len(results)
        avg_iter_sec = sum(result['data'].avg_iter_sec for result in results) / len(results)
        avg_sec_iter = sum(result['data'].avg_sec_iter for result in results) / len(results)
        avg_iter_sec_watt = avg_iter_sec / avg_watts

        self.bench_logger.update_row(model.name, {
            "elapsed time": f"{round(sum(result['time'] for result in results), 2)}s",
            "avg watts": f"{round(avg_watts, 2)} W",
            "k_samp time": round(sum(result['data'].k_samp_time for result in results), 2),
            "k_samp percentage": round(sum(result['data'].k_samp_percentage for result in results), 2),
            "avg iter/sec": f"[cyan]{round(avg_iter_sec, 2)}[/cyan]",
            "avg sec/iter": f"[magenta]{round(avg_sec_iter, 2)}[/magenta]",
            "avg iter/sec/watt": f"{round(avg_iter_sec_watt, 2)}",
        })