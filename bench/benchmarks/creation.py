
from typing import List
from bench.benchmarks.benchmark import Benchmark
from bench.benchmarks.benchmark_test import BenchmarkTest

class CreationBenchmarkResult():

    def __init__(self, total_time, raw_k_samp_time):
        self.total_time = (total_time)
        self.raw_k_samp_time = (raw_k_samp_time)
        self.k_samp_time = (sum(raw_k_samp_time))
        self.k_samp_percentage = (self.k_samp_time / self.total_time)
        self.avg_iter_sec = (len(raw_k_samp_time) / self.k_samp_time)
        self.avg_sec_iter = (self.k_samp_time / len(raw_k_samp_time))

class CreationBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            "resolution",
            # "k_samp time",
            # "k_samp percentage",
            "avg iter/sec",
            "avg sec/iter",
            "avg time to image",
            "avg iter/sec/watt",
        ]
    
    def _update_row(self, model: BenchmarkTest, results: List):
        avg_watts = sum(result['watts'] for result in results) / len(results)
        avg_iter_sec = sum(result['data'].avg_iter_sec for result in results) / len(results)
        avg_sec_iter = sum(result['data'].avg_sec_iter for result in results) / len(results)
        avg_total_time = sum(result['data'].total_time for result in results) / len(results)
        avg_iter_sec_watt = avg_iter_sec / avg_watts

        # TODO add kwh consumed as well.
        self.bench_logger.update_row(model.tag, {
            "resolution": model.resolution,
            "elapsed time": f"{round(sum(result['time'] for result in results), 2)}s",
            "avg watts": f"{round(avg_watts, 2)} W",
            # "k_samp time": round(sum(result['data'].k_samp_time for result in results), 2),
            # "k_samp percentage": round(sum(result['data'].k_samp_percentage for result in results) / len(results), 2),
            "avg iter/sec": f"[cyan]{round(avg_iter_sec, 2)}[/cyan]",
            "avg sec/iter": f"[magenta]{round(avg_sec_iter, 2)}[/magenta]",
            "avg time to image": f"[green]{round(avg_total_time, 2)}s[/green]",
            "avg iter/sec/watt": f"{round(avg_iter_sec_watt, 4)}",
        })