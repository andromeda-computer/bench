from typing import List
from bench.benchmarks.benchmark import Benchmark
from bench.benchmarks.benchmark_test import BenchmarkTest

class VisionBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            "# prompt tokens",
            "# generated tokens",
            "prompt tps",
            "generate tps",
            "throughput",
            "avg ttft",
            "prompt tps/watt",
            "generate tps/watt",
        ]

    def _update_row(self, model: BenchmarkTest, results: List):
        avg_watts = sum(result['watts'] for result in results) / len(results)
        prompt_tps = sum(result['data'].prompt_tps for result in results) / len(results)
        generated_tps = sum(result['data'].generated_tps for result in results) / len(results)
        elapsed_time = sum(result['time'] for result in results)
        avg_ttft = sum(result['data'].ttft for result in results) / len(results)

        # model.tag should be part of self somewhere...
        self.bench_logger.update_row(model.tag, {
            "elapsed time": f"{round(elapsed_time, 2)}s",
            "avg watts": f"{round(avg_watts, 2)} W",
            "# prompt tokens": sum(result['data'].n_prompt_tokens for result in results),
            "# generated tokens": sum(result['data'].n_generated_tokens for result in results),
            "prompt tps": f"[cyan]{round(prompt_tps, 2)}[/cyan]",
            "generate tps": f"[magenta]{round(generated_tps, 2)}[/magenta]",
            "throughput": f"[purple4]{round(len(results) / elapsed_time, 2)} imgs/sec[/purple4]",
            "avg ttft": f"[green]{round(avg_ttft)}ms[/green]",
            "prompt tps/watt": f"{round(prompt_tps / avg_watts, 2)}",
            "generate tps/watt": f"{round(generated_tps / avg_watts, 2)}",
        })