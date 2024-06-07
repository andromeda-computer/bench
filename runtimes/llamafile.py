import base64
import json
import os
import subprocess
import threading
import time

from jinja2 import Template
import requests
from benchmarks.hearing import HearingBenchmarkResult
from benchmarks.language import LanguageBenchmarkResult
from config import PORT, Model
from runtimes.runtime import Runtime
from utils import kill
from sys_info import system

from rich.text import Text

def read_stderr(pipe, stop_event, stderr_lines, stop_reading_event):
    while not stop_reading_event.is_set():
        line = pipe.readline()
        if not line:
            break
        decoded_line = line.decode()
        stderr_lines.append(decoded_line)
        if "GGML_ASSERT" in decoded_line:
            print("ERROR", decoded_line)
            stop_event.set()
        if "compile_nvidia" in decoded_line:
            print(decoded_line)
        if "server listening" in decoded_line:
            stop_event.set()

def read_stdout(pipe, stop_event, stderr_lines):
    while not stop_event.is_set():
        line = pipe.readline()
        # print("decoded from stdout", line.decode())

class LlamafileRuntime(Runtime):
    def download(self):
        pass

    def benchmark(self, model: Model, datasets):
        self.url = f"http://127.0.0.1:{PORT}"
        self._start_server(model)
        
        if (model.type == "vision"):
            self._benchmark_vision(model, datasets)
        elif (model.type == "hearing"):
            self._benchmark_hearing(model, datasets)
        elif (model.type == "language"):
            self._benchmark_language(model, datasets)
            print("finished language benchmark")
        else:
            print(f"Benchmark type: {model.type} not supported")

        self._kill_server()

    def _benchmark_language(self, model, datasets):
        results = []
        count = 0
        # total_count = sum([len(dataset.prompts) for _, dataset in datasets.items()])

        self.logger.add_row(model.name, {
            "status": f"[{count}]", 
            "model": model.name
        })

        for _, dataset in datasets.items():
            with open(os.path.join(dataset.dir, "prompts.json"), "r") as f:
                prompts = json.loads(f.read())

            for prompt in prompts:
                self.logger.update_row(model.name, {"status": f"{count}"})
                data = self._build_llamacpp_request(model, prompt)

                system.power_start("bench_run")
                response = requests.post(f"{self.url}/completion", json=data)
                power = system.power_stop("bench_run")

                result = LanguageBenchmarkResult(prompt, response.json(), power)
                results.append(result)

                self.logger.update_row(model.name, {
                    "status": f"{count + 1}",
                    "# prompt tokens": sum(r.n_prompt_tokens for r in results),
                    "# generated tokens": sum(r.n_generated_tokens for r in results),
                    "prompt tps": round(sum(r.prompt_tps for r in results) / len(results), 2),
                    "generate tps": round(sum(r.generated_tps for r in results) / len(results), 2),
                    "prompt tps/watt": round(sum(r.prompt_tps_watt for r in results) / len(results), 2),
                    "generate tps/watt": round(sum(r.generated_tps_watt for r in results) / len(results), 2),
                })

                count += 1
        return results

    def _benchmark_vision(self, model, datasets):
        results = []
        count = 0

        self.logger.add_row(model.name, {
            "status": f"[{count}]", 
            "model": model.name
        })

        results = []
        for _, dataset in datasets.items():
            for file in os.listdir(dataset.dir):
                self.logger.update_row(model.name, {"status": f"{count}"})
                image = os.path.join(dataset.dir, file)
                prompt = "describe this image in detail"
                data = self._build_llamacpp_request(model, prompt, image)

                system.power_start("bench_run")
                response = requests.post(f"{self.url}/completion", json=data)
                power = system.power_stop("bench_run")

                result = LanguageBenchmarkResult(prompt, response.json(), power)
                results.append(result)

                # TODO this probably goes directly in language benchmark result or something
                # would have the appropriate adapters depending on the runtime
                self.logger.update_row(model.name, {
                    "status": f"{count + 1}",
                    "# prompt tokens": sum(r.n_prompt_tokens for r in results),
                    "# generated tokens": sum(r.n_generated_tokens for r in results),
                    "prompt tps": round(sum(r.prompt_tps for r in results) / len(results), 2),
                    "generate tps": round(sum(r.generated_tps for r in results) / len(results), 2),
                    "prompt tps/watt": round(sum(r.prompt_tps_watt for r in results) / len(results), 2),
                    "generate tps/watt": round(sum(r.generated_tps_watt for r in results) / len(results), 2),
                })

                count += 1

        return results

    def _build_llamacpp_request(self, model, prompt, image = None):
        data = {}
        if image:
            b64image = base64.b64encode(open(image, "rb").read()).decode("utf-8")
            data['image_data'] = [{
                'data': b64image,
                'id': 10
            }]

        data['temperature'] = 0
        data['prompt'] = Template(model.prompt_template).render(prompt=prompt)
        data['stop'] = [model.stop]
        data['n_predict'] = 1536
        return data

    def _benchmark_hearing(self, model, datasets):

        count = 0
        results = []

        self.logger.add_row(model.name, {
            "status": f"[{count}]", 
            "model": model.name
        })

        for _, dataset in datasets.items():
            for file in os.listdir(dataset.dir):
                audio = os.path.join(dataset.dir, file)
                fs_file = open(audio, 'rb')
                files = {
                    'file': (file, fs_file)
                }
                data = {
                    'temperature': 0,
                    'temperature_inc': 0.2,
                    'response_format': "verbose_json"
                }

                start_time = time.time()
                system.power_start("hearing_bench_run")
                response = requests.post(f"{self.url}/inference", files=files, data=data)
                power = system.power_stop("hearing_bench_run")
                total_time = time.time() - start_time
                response_json = response.json()
                if (response_json.get("error")):
                    print(f"Error: {response_json.get('error')} on {file}")
                    continue
                result = HearingBenchmarkResult(response.json(), total_time, power)
                results.append(result)

                self.logger.update_row(model.name, {
                    "status": f"{count + 1}",
                    "total input seconds": round(sum(r.input_seconds for r in results), 2),
                    "total transcribe time": round(sum(r.transcribe_time for r in results), 2),
                    "avg speedup": f"{round(sum(r.speedup for r in results) / len(results), 2)}x",
                    "avg speedup/watt": f"{round(sum(r.speedup_watt for r in results) / len(results), 2)}x"
                })

                count += 1

        pass

    def __del__(self):
        self._kill_server()

    def _start_server(self, model, ngl = 9999, recompile = False, attempt = 0):
        if (attempt > 3):
            raise Exception("Failed to start llamafile server")

        llamafile = os.path.join(model.dir, model.filename)

        if model.type == "hearing":
            cmd_str = " ".join([
                llamafile,
                f"--port {PORT}",
                ">&2"
            ])
        else:
            cmd_str = " ".join([
                llamafile,
                "-c 4096",
                "--nobrowser",
                "--port",
                str(PORT),
                "--recompile" if recompile else "",
                f"-ngl {str(ngl)}" if ngl != 0 else "",
                ">&2"
            ])

        try:
            stdout_lines = []
            stderr_lines = []
            stop_event = threading.Event()
            stop_reading_event = threading.Event()  # Event to stop reading entirely
            proc = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
            # proc = await asyncio.create_subprocess_shell(cmd_str,
            #                                        stdout=subprocess.PIPE,
            #                                        stderr=subprocess.PIPE)
            self.pid = proc.pid

            print(f"Started llamafile server with pid: {self.pid}\ncommand string: {cmd_str}")

            # Start threads to read both stdout and stderr
            stderr_thread = threading.Thread(target=read_stderr, args=(proc.stderr, stop_event, stderr_lines, stop_reading_event))
            stdout_thread = threading.Thread(target=read_stdout, args=(proc.stdout, stop_event, stdout_lines))
            stderr_thread.start()
            stdout_thread.start()

            # Wait until the stop_event is set
            while not stop_event.is_set():
                pass

            # Handle the situation depending on the collected stderr and stdout
            for line in stderr_lines:
                if "GGML_ASSERT" in line:
                    kill(self.pid)
                    self._start_server(model, ngl, recompile=True, attempt=attempt + 1)

        except Exception as e:
            print(e)
            kill(self.pid)

    def _kill_server(self):
        if (self.pid):
            kill(self.pid)