from typing import List
from bench.benchmarks.benchmark import Benchmark
from bench.utils import Column

class VisionBenchmarkResult:
    def __init__(self, time, watts, n_prompt_tokens, n_generated_tokens, prompt_tps, generated_tps, ttft):
        self.time = time
        self.watts = watts
        self.n_prompt_tokens = n_prompt_tokens
        self.n_generated_tokens = n_generated_tokens
        self.prompt_tps = prompt_tps
        self.generated_tps = generated_tps
        self.ttft = ttft

class VisionBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            Column("elapsed time", True, 
                   lambda results: sum(r.time for r in results),
                   lambda x: f"{round(x, 2)}s"),
            Column("avg watts", True, 
                   lambda results: sum(r.watts for r in results) / len(results),
                   lambda x: f"{round(x, 2)}W"),
            Column("# prompt tokens", True, 
                   lambda results: sum(r.n_prompt_tokens for r in results)),
            Column("# generated tokens", True, 
                   lambda results: sum(r.n_generated_tokens for r in results)),
            Column("prompt tps", True, 
                   lambda results: sum(r.prompt_tps for r in results) / len(results),
                   lambda x: f"[cyan]{round(x, 2)}[/cyan]"),
            Column("generate tps", True, 
                   lambda results: sum(r.generated_tps for r in results) / len(results),
                   lambda x: f"[magenta]{round(x, 2)}[/magenta]"),
            Column("throughput", True, 
                   lambda results: len(results) / sum(r.time for r in results),
                   lambda x: f"[purple4]{round(x, 2)} imgs/sec[/purple4]"),
            Column("avg ttft", True, 
                   lambda results: sum(r.ttft for r in results) / len(results),
                   lambda x: f"[green]{round(x)}ms[/green]"),
            Column("prompt tps/watt", True, 
                   lambda results: (sum(r.prompt_tps for r in results) / len(results)) / 
                                   (sum(r.watts for r in results) / len(results))),
            Column("generate tps/watt", True, 
                   lambda results: (sum(r.generated_tps for r in results) / len(results)) / 
                                   (sum(r.watts for r in results) / len(results))),
        ]

    def get_columns(self):
        return [col.name for col in self._benchmark_columns()]

    def _compute_results(self, results: List[VisionBenchmarkResult]):
        return {col.name: col.compute(results) for col in self._benchmark_columns()}

    def _update_display(self, tag: str, data: dict):
        self.bench_logger.update_row(tag, {
            col.name: col.format(data[col.name])
            for col in self._benchmark_columns()
            if col.display
        })

    def get_display_columns(self):
        return [col.name for col in self._benchmark_columns() if col.display]