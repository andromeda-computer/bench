from typing import List
from bench.benchmarks.benchmark import Benchmark
from bench.models.model import Model

class VisionBenchmark(Benchmark):

    def _benchmark_columns(self):
        return [
            "status", 
            "model",
            "quant",
            "elapsed time",
            "avg watts",
            "# prompt tokens",
            "# generated tokens",
            "prompt tps",
            "generate tps",
            "throughput",
            "avg ttft",
            "prompt tps/watt",
            "generate tps/watt",
        ]

    def _update_row(self, model: Model, results: List):
        avg_watts = sum(result['watts'] for result in results) / len(results)
        prompt_tps = sum(result['data'].prompt_tps for result in results) / len(results)
        generated_tps = sum(result['data'].generated_tps for result in results) / len(results)
        elapsed_time = sum(result['time'] for result in results)
        avg_ttft = sum(result['data'].ttft for result in results) / len(results)

        self.bench_logger.update_row(model.name, {
            "elapsed time": f"{round(elapsed_time, 2)} sec",
            "avg watts": f"{round(avg_watts, 2)} W",
            "throughput": f"[purple4]{round(len(results) / elapsed_time, 2)} imgs/sec[/purple4]",
            "# prompt tokens": sum(result['data'].n_prompt_tokens for result in results),
            "# generated tokens": sum(result['data'].n_generated_tokens for result in results),
            "prompt tps": f"[cyan]{round(prompt_tps, 2)}[/cyan]",
            "generate tps": f"[magenta]{round(generated_tps, 2)}[/magenta]",
            "avg ttft": f"[green]{round(avg_ttft)}ms[/green]",
            "prompt tps/watt": f"{round(prompt_tps / avg_watts, 2)}",
            "generate tps/watt": f"{round(generated_tps / avg_watts, 2)}",
        })