import base64
import json
import os
import subprocess
import threading
import time

from jinja2 import Template
import requests
from config import PORT, Model
from runtimes.runtime import Runtime
from utils import kill
from sys_info import system

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
        print("decoded from stdout", line.decode())

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
        count = 0
        results = []
        for _, dataset in datasets.items():
            print("Dataset:", dataset.name)
            # open the prompts.json file
            prompts_file = os.path.join(dataset.dir, "prompts.json")
            with open(prompts_file, "r") as f:
                prompts = json.load(f)
            
            for prompt in prompts:
                print("count:", count)
                # print("Prompt:", prompt)
                data = self._build_llamacpp_request(model, prompt)

                system.power_start("bench_run")
                response = requests.post(f"{self.url}/completion", json=data)
                system.power_stop("bench_run")
                jsonResponse = response.json()
                count += 1
                # print(jsonResponse['content'])
                # print(jsonResponse['timings']['prompt_per_second'], jsonResponse['timings']['predicted_per_second'])

        return results

    def _benchmark_vision(self, model, datasets):
        count = 0

        results = []
        for _, dataset in datasets.items():
            print("Dataset:", dataset.name)
            for file in os.listdir(dataset.dir):
                print(file, count)
                image = os.path.join(dataset.dir, file)
                data = self._build_llamacpp_request(model, "describe this image in detail", image)

                system.power_start("bench_run")
                response = requests.post(f"{self.url}/completion", json=data)
                system.power_stop("bench_run")
                jsonResponse = response.json()
                count += 1
                # print(jsonResponse['content'])
                # print(jsonResponse['timings']['prompt_per_second'], jsonResponse['timings']['predicted_per_second'])

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
        for _, dataset in datasets.items():
            print("Dataset:", dataset.name)
            for file in os.listdir(dataset.dir):
                print("count:", count, file)
                audio = os.path.join(dataset.dir, file)
                files = {
                    'file': (file, open(audio, 'rb'))
                }
                data = {
                    'temperature': 0,
                    'temperature_inc': 0.2
                    'response_format': "json"
                }

                response = requests.post(f"{self.url}/inference", files=files, data=data)
                jsonResponse = response.json()
                print(jsonResponse)
                count += 1

                # print(jsonResponse)
                # print(jsonResponse['content'])
                # print(jsonResponse['timings']['prompt_per_second'], jsonResponse['timings']['predicted_per_second'])

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