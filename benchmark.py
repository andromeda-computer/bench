from abc import ABC
import os
from downloader import MODEL_STORE
from model import PORT
import requests
from jinja2 import Template
from sys_info import system
from config import config
import subprocess
import time
from jinja2 import Template
import os
from utils import kill
from rich.console import Console

class LanguageBenchmarkResult:

    def __init__(self, prompt, json, power):
        timings = json['timings']

        self.prompt = prompt
        self.t_prompt_eval = timings['prompt_ms']
        self.t_generation = timings['predicted_ms']
        self.t_total = self.t_prompt_eval + self.t_generation
        self.n_prompt_tokens = timings['prompt_n']
        self.n_generated_tokens = timings['predicted_n']
        self.prompt_tps = timings['prompt_per_second']
        self.generated_tps = timings['predicted_per_second']
        self.response = json['content']
        self.power_raw = power

        # TODO improve this calculation by monitoring continously in python
        # then can more accurately get the start/stop times and calculate. 
        # Can be done at the ms level probably?
        self.prompt_tps_watt = self.prompt_tps / power[2]
        self.generated_tps_watt = self.generated_tps / power[2]

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

# Define the column names and their widths
columns = [
    ("MODEL", 25),
    ("PARAMS", 8),
    ("# PRMPT TKNS", 14),
    ("# GEN TKNS", 12),
    ("PRMPT TPS", 11),
    ("GEN TPS", 10),
    ("PRMPT TPS/WATT", 16),
    ("GEN TPS/WATT", 15)
]

class LanguageBenchmark:

    def __init__(self):
        self.data = []

        # TODO really should move this into Config class. for now this is fine.
        self.models = config.suites["language"]
        self.base_dir = os.path.join(MODEL_STORE, "language")
        print("\nLanguage")
        self.console = Console()

        # Print the header
        header = ""
        for col_name, col_width in columns:
            header += f"{col_name:<{col_width}}"
        self.console.print(header)

    def print_benchmark_row(self, result):
        row = ""
        row += f"{result['model']:<{columns[0][1]}}"
        row += f"{result['params']:<{columns[1][1]}}"
        row += f"{result['prompt_tokens']:<{columns[2][1]}}"
        row += f"{result['generated_tokens']:<{columns[3][1]}}"
        row += f"{result['prompt_tps']:<{columns[4][1]}}"
        row += f"{result['generated_tps']:<{columns[5][1]}}"
        row += f"{result['prompt_tps_watt']:<{columns[6][1]}}"
        row += f"{result['generated_tps_watt']:<{columns[7][1]}}"
        self.console.print(row)

    def benchmark(self):
        for model in self.models:
            if (model['runtime'] != "llamafile"):
                continue

            filename = model['url'].split("/")[-1]
            llamafile = os.path.join(self.base_dir, filename)

            # run the model
            cmd_str = f"{llamafile} --nobrowser --port {PORT} -ngl 9999"
            try: 
                proc = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
                # stderr_output, _ = proc.communicate()
                # print(stderr_output.decode())  # print the stderr output as a string
                while True:
                    stderr_line = proc.stderr.readline()
                    if not stderr_line:
                        break

                    line = stderr_line.decode()
                    if ("GGML_ASSERT" in line):
                        # TODO recompile it
                        # TODO add flag to force a recompile
                        print("ERROR", line, proc.stderr.readline().decode(), proc.stderr.readline().decode())
                        raise Exception("GGML_ASSERT")

                    if ("llama server listening" in line):
                        break

                # wait for the server to start
                url = f"http://127.0.0.1:{PORT}/health"
                attempt = 1
                while True:
                    try:
                        response = requests.get(url)
                        if response.status_code == 200:
                            break
                    except requests.exceptions.ConnectionError as e:
                        attempt += 1
                        time.sleep(5)

                result = self.benchmark_model(Template(model['prompt_template']), model['name'])
                self.print_benchmark_row(result)

                kill(proc.pid)
            except:
                kill(proc.pid)


    def benchmark_model(self, template: Template, model: str):
        url = f"http://127.0.0.1:{PORT}/completion"
        results = []
        for p, i in enumerate(PROMPTS):
            prompt = template.render(prompt=p)
            data = {"prompt": prompt, "stop": ["<|eot_id|>"], "temperature": 0}
            
            system.power_start("lang_run")
            response = requests.post(url, json=data)
            power = system.power_stop("lang_run")
            json = response.json()

            result = LanguageBenchmarkResult(prompt, json, power)
            results.append(result)

        # compute the model benchmark result based on each row
        return {
            "model": model,
            "params": "TBD",
            "prompt_tokens": sum(r.n_prompt_tokens for r in results),
            "generated_tokens": sum(r.n_generated_tokens for r in results),
            "prompt_tps": round(sum(r.prompt_tps for r in results) / len(results), 2),
            "generated_tps": round(sum(r.generated_tps for r in results) / len(results), 2),
            "prompt_tps_watt": round(sum(r.prompt_tps_watt for r in results) / len(results), 2),
            "generated_tps_watt": round(sum(r.generated_tps_watt for r in results) / len(results), 2),
            "raw": results
        }


class VisionBenchmark:

    def __init__(self):
        self.data = []

        # TODO really should move this into Config class. for now this is fine.
        self.models = config.suites["vision"]
        self.base_dir = os.path.join(MODEL_STORE, "vision")
        # self.datasets = 
        print("\nVision")
        self.console = Console()

        # Print the header
        header = ""
        for col_name, col_width in columns:
            header += f"{col_name:<{col_width}}"
        self.console.print(header)

def benchmark_vision():
    pass

def benchmark_hearing():
    pass

def benchmark_speaking():
    pass