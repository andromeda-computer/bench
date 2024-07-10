from typing import List
from bench.benchmarks.benchmark import Benchmark
from bench.benchmarks.benchmark_test import BenchmarkResult

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
    
    def _compute_results(self, results):
        elapsed_time = sum(result.time for result in results)
        avg_watts = sum(result.watts for result in results) / len(results)
        num_prompt_tokens = sum(result.n_prompt_tokens for result in results)
        num_generated_tokens = sum(result.n_generated_tokens for result in results)
        prompt_tps = sum(result.prompt_tps for result in results) / len(results)
        generated_tps = sum(result.generated_tps for result in results) / len(results)
        throughput = len(results) / elapsed_time
        avg_ttft = sum(result.ttft for result in results) / len(results)
        prompt_tps_watt = prompt_tps / avg_watts
        generate_tps_watt = generated_tps / avg_watts

        return {
            "elapsed_time": elapsed_time,
            "avg_watts": avg_watts,
            "num_prompt_tokens": num_prompt_tokens,
            "num_generated_tokens": num_generated_tokens,
            "prompt_tps": prompt_tps,
            "generated_tps": generated_tps,
            "throughput": throughput,
            "avg_ttft": avg_ttft,
            "prompt_tps_watt": prompt_tps_watt,
            "generate_tps_watt": generate_tps_watt,
        }

    def _update_display(self, tag, data):
        self.bench_logger.update_row(tag, {
            "elapsed time": f"{round(data['elapsed_time'], 2)}s",
            "avg watts": f"{round(data['avg_watts'], 2)}W",
            "# prompt tokens": data['num_prompt_tokens'],
            "# generated tokens": data['num_generated_tokens'],
            "prompt tps": f"[cyan]{round(data['prompt_tps'], 2)}[/cyan]",
            "generate tps": f"[magenta]{round(data['generated_tps'], 2)}[/magenta]",
            "throughput": f"[purple4]{round(data['throughput'], 2)} imgs/sec[/purple4]",
            "avg ttft": f"[green]{round(data['avg_ttft'])}ms[/green]",
            "prompt tps/watt": f"{round(data['prompt_tps_watt'], 2)}",
            "generate tps/watt": f"{round(data['generate_tps_watt'], 2)}",
        })