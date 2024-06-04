from abc import ABC
from model import PORT
import requests
from jinja2 import Template


class LanguageBenchmarkResult:

    def __init__(self, prompt, json):
        timings = json['timings']

        self.prompt = prompt
        self.t_prompt_eval = timings['prompt_ms']
        self.t_generation = timings['predicted_ms']
        self.n_prompt_tokens = timings['prompt_n']
        self.n_generated_tokens = timings['predicted_n']
        self.prompt_tps = timings['prompt_per_second']
        self.generated_tps = timings['predicted_per_second']
        self.response = json['content']

PROMPTS = [
    "What is the capital of France?",
    "What is the meaning of life",
    "What is the square root of 2?",
    "What is your favorite fruit?",
    'how do i make a post request to an endpoint "/completion" in python',
    '''i am getting

OSError: [Errno 8] Exec format error: '.models/language/TinyLlama-1.1B-Chat-v1.0.Q5_K_M.llamafile'

when running: proc = subprocess.Popen([llamafile, "--nobrowser"])

but when i execute it directly on the commandline there is no issue'''
]

class LanguageBenchmark:

    def __init__(self):
        self.data = []

    def benchmark_model(self, template: Template, model: str):
        url = f"http://127.0.0.1:{PORT}/completion"
        results = []
        for p, i in enumerate(PROMPTS):
            prompt = template.render(prompt=p)
            data = {"prompt": prompt, "stop": ["<|eot_id|>"], "temperature": 0}
            
            response = requests.post(url, json=data)
            json = response.json()

            result = LanguageBenchmarkResult(prompt, json)
            results.append(result)

        # compute the model benchmark result based on each row
        return {
            "model": model,
            "params": "TBD",
            "prompt_tokens": sum(r.n_prompt_tokens for r in results),
            "generated_tokens": sum(r.n_generated_tokens for r in results),
            "prompt_tps": round(sum(r.prompt_tps for r in results) / len(results), 2),
            "generated_tps": round(sum(r.generated_tps for r in results) / len(results), 2),
            "raw": results
        }


def benchmark_vision():
    pass

def benchmark_hearing():
    pass

def benchmark_speaking():
    pass