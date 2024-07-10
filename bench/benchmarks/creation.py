
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
            # "resolution",
            # "k_samp time",
            # "k_samp percentage",
            "avg iter/sec",
            "avg sec/iter",
            "avg time to image",
            "avg iter/sec/watt",
        ]

    def _compute_results(self, results: List):
        avg_watts = sum(result.watts for result in results) / len(results)
        avg_iter_sec = sum(result.avg_iter_sec for result in results) / len(results)
        avg_sec_iter = sum(result.avg_sec_iter for result in results) / len(results)
        avg_total_time = sum(result.total_time for result in results) / len(results)
        avg_iter_sec_watt = avg_iter_sec / avg_watts
        k_samp_time = sum(result.k_samp_time for result in results)
        k_samp_percentage = sum(result.k_samp_percentage for result in results) / len(results)

        return {
            "elapsed_time": sum(result.time for result in results),
            "avg_watts": avg_watts,
            "avg_iter_sec": avg_iter_sec,
            "avg_sec_iter": avg_sec_iter,
            "avg_total_time": avg_total_time,
            "avg_iter_sec_watt": avg_iter_sec_watt,
            "k_samp_time": k_samp_time,
            "k_samp_percentage": k_samp_percentage
        }

    def _update_display(self, tag: str, data: dict):
        self.bench_logger.update_row(tag, {
            "elapsed time": f"{round(data['elapsed_time'], 2)}s",
            "avg watts": f"{round(data['avg_watts'], 2)} W",
            "avg iter/sec": f"[cyan]{round(data['avg_iter_sec'], 2)}[/cyan]",
            "avg sec/iter": f"[magenta]{round(data['avg_sec_iter'], 2)}[/magenta]",
            "avg time to image": f"[green]{round(data['avg_total_time'], 2)}s[/green]",
            "avg iter/sec/watt": f"{round(data['avg_iter_sec_watt'], 4)}",
        })