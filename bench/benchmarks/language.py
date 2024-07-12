from typing import List
from bench.benchmarks.benchmark import Benchmark
from bench.utils import create_percentile_columns, Column

class LanguageBenchmarkResult:
    def __init__(self, prompt, json, response, ttft):
        timings = json['timings']
        self.prompt = prompt
        self.t_prompt_eval = timings['prompt_ms']
        self.t_generation = timings['predicted_ms']
        self.t_total = self.t_prompt_eval + self.t_generation
        self.n_prompt_tokens = timings['prompt_n']
        self.n_generated_tokens = timings['predicted_n']
        self.prompt_tps = timings['prompt_per_second']
        self.generated_tps = timings['predicted_per_second']
        self.response = response
        self.ttft = ttft

class LanguageBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            Column("elapsed time", True, 
                   lambda results: sum(r.time for r in results),
                   lambda x: f"{round(x, 2)}s"),
            Column("avg watts", True, 
                   lambda results: sum(r.watts for r in results) / len(results),
                   lambda x: f"{round(x, 2)} W"),
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
            Column("avg ttft", True, 
                   lambda results: sum(r.ttft for r in results) / len(results),
                   lambda x: f"[green]{round(x)}ms[/green]"),
            Column("prompt tps/watt", True, 
                   lambda results: (sum(r.prompt_tps for r in results) / len(results)) / 
                                   (sum(r.watts for r in results) / len(results)),
                   lambda x: f"{round(x, 2)}"),
            Column("generate tps/watt", True, 
                   lambda results: (sum(r.generated_tps for r in results) / len(results)) / 
                                   (sum(r.watts for r in results) / len(results)),
                   lambda x: f"{round(x, 2)}"),
        ] + create_percentile_columns("ttft", lambda r: r.ttft)

    def get_columns(self):
        return [col.name for col in self._benchmark_columns()]

    def _compute_results(self, results: List[LanguageBenchmarkResult]):
        return {col.name: col.compute(results) for col in self._benchmark_columns()}

    def _update_display(self, tag: str, data: dict):
        self.bench_logger.update_row(tag, {
            col.name: col.format(data[col.name])
            for col in self._benchmark_columns()
            if col.display
        })

    def get_display_columns(self):
        return [col.name for col in self._benchmark_columns() if col.display]