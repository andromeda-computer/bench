from bench.benchmarks.benchmark import Benchmark
from bench.models.model import Model

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
            "status", 
            "model",
            "quant",
            "elapsed time",
            "avg watts",
            "# prompt tokens",
            "# generated tokens",
            "prompt tps",
            "generate tps",
            "avg ttft",
            "prompt tps/watt",
            "generate tps/watt",
        ]

    def _update_row(self, model: Model, results):
        avg_watts = sum(result['watts'] for result in results) / len(results)
        prompt_tps = sum(result['data'].prompt_tps for result in results) / len(results)
        generated_tps = sum(result['data'].generated_tps for result in results) / len(results)
        avg_ttft = sum(result['data'].ttft for result in results) / len(results)

        self.bench_logger.update_row(model.tag, {
            "elapsed time": f"{round(sum(result['time'] for result in results), 2)}s",
            "avg watts": f"{round(avg_watts, 2)} W",
            "# prompt tokens": sum(result['data'].n_prompt_tokens for result in results),
            "# generated tokens": sum(result['data'].n_generated_tokens for result in results),
            "prompt tps": f"[cyan]{round(prompt_tps, 2)}[/cyan]",
            "generate tps": f"[magenta]{round(generated_tps, 2)}[/magenta]",
            "avg ttft": f"[green]{round(avg_ttft)}ms[/green]",
            "prompt tps/watt": f"{round(prompt_tps / avg_watts, 2)}",
            "generate tps/watt": f"{round(generated_tps / avg_watts, 2)}",
        })