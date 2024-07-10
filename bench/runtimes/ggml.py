import abc
import base64
import json
import os
import subprocess
import threading
import time
from jinja2 import Template
import requests

from bench.benchmarks.hearing import HearingBenchmarkResult
from bench.benchmarks.language import LanguageBenchmarkResult
from bench.benchmarks.model import Model
from bench.config import HOST, PORT
from bench.runtimes.runtime import Runtime
from bench.utils import kill, url_downloader
from bench.logger import logger

def read_stderr(pipe, stop_event, stderr_lines, stop_reading_event):
    while not stop_reading_event.is_set():
        line = pipe.readline()
        if not line:
            break
        decoded_line = line.decode()
        logger.debug(decoded_line)
        stderr_lines.append(decoded_line)
        if "CUDA error: no kernel image is available for execution on the device" in decoded_line:
            # logger.info("need to recompile!", decoded_line)
            stop_event.set()
        if "compile_nvidia" in decoded_line:
            pass
            # logger.info("compiling for nvidia", decoded_line)
        if "cudaMalloc failed: out of memory" in decoded_line:
            # logger.info("cudaMalloc failed: out of memory", decoded_line)
            stop_event.set()
        if "server listening" in decoded_line:
            stop_event.set()

def read_stdout(pipe, stop_event, stderr_lines):
    while not stop_event.is_set():
        line = pipe.readline()
        decoded_line = line.decode()
        # logger.debug(decoded_line)


class ExecutableGGMLRuntime(Runtime, abc.ABC):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.pid = None

    def _download(self):
        self.executable = self._download_executable_ggml_runtime()

    def _start(self, model: Model):
        return self._start_server(model)
    
    def _stop(self):
        self._stop_server()

    def _download_executable_ggml_runtime(self):
        version = self.cfg.get("version", None)
        url = self.cfg.get('url', None)

        if not url:
            logger.error(f"URL required in config.yaml for self: {self.name}")
            return

        if not version:
            logger.error(f"Version required in config.yaml for self: {self.name}")
            return

        filename = f"{self.name}-{version}"
        executable = os.path.join(self.dir, filename)

        url_downloader([{ "url": url, "dest_dir": self.dir, "filename": filename }])

        # make it executable now
        os.chmod(executable, 0o775)

        return executable

    def _start_server(self, model: Model, ngl = 9999, recompile = False, attempt = 0):
        if (attempt > 3):
            raise Exception("Failed to start llamafile server for model {model.name} after 3 attempts. Exiting.")

        if model.type == "hearing":
            cmd_str = " ".join([
                self.executable,
                f"-m {model.path}",
                f"--port {PORT}",
                f"--host {HOST}",
                f"--convert",
                ">&2"
            ])
        else:
            cmd_str = " ".join([
                self.executable,
                f"-m {model.path}",
                f"--mmproj {model.projector_path}" if model.projector_path else "",
                "-c 4096",
                "--nobrowser",
                f"--host {HOST}",
                f"--port {PORT}",
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
            self.pid = proc.pid

            logger.info(f"Started llamafile server with pid: {self.pid}\ncommand string: {cmd_str}")

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
                if "CUDA error: no kernel image is available for execution on the device" in line:
                    kill(self.pid)
                    self._start_server(model, ngl, recompile=True, attempt=attempt + 1)
                elif "cudaMalloc failed: out of memory" in line:
                    kill(self.pid)
                    return False

            self.url = f"http://{HOST}:{PORT}"
            return True

        except Exception as e:
            logger.error(e)
            kill(self.pid)

    def _stop_server(self):
        if hasattr(self, 'pid') and self.pid:
            kill(self.pid)
            self.pid = None

    def __del__(self):
        self._stop_server()

class LlamafileRuntime(ExecutableGGMLRuntime):
    
        def benchmark(self, model: Model, data, config = None):
            req_data = {}

            # TODO call the same function just with image
            if model.type == "vision":
                req_data = self._build_llamacpp_request(model, data, data.path)
            elif model.type == "language":
                req_data = self._build_llamacpp_request(model, data)
            else:
                logger.warning(f"Benchmark type: {model.type} not supported for llamafile runtime")
                return None

            t_start = time.perf_counter()
            response = requests.post(f"{self.url}/completion", json=req_data)

            result = self._decode_llamacpp_streaming_response(response, t_start)

            return result

        def _decode_llamacpp_streaming_response(self, response, t_start):
            ttft = None
            completed_response = None

            data = b''
            message = ""
            for chunk in response:
                for line in chunk.splitlines(keepends=True):
                    data += line
                if data.endswith((b"\r\r", b"\n\n", b"\r\n\r\n")):
                    rows = [l for l in data.decode().split("\n") if l.strip()]
                    for row in rows:
                        json_data = json.loads(row[6:])
                        if not ttft:
                            ttft = (time.perf_counter() - t_start) * 1000
                        if json_data.get('timings'):
                            completed_response = json_data
                        message += json_data.get('content', "")
                    data = b''

            if not completed_response:
                logger.error("No completion response received")
                return None

            return LanguageBenchmarkResult(data, completed_response, message, ttft)

        def _build_llamacpp_request(self, model, prompt, image = None, stream = True):
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
            data['stream'] = stream
            return data

class WhisperfileRuntime(ExecutableGGMLRuntime):

        def benchmark(self, model: Model, data, config = None):
            if (model.type == "hearing"):
                # TODO this really doesnt make sense as a wrapper, 
                # need to return without thinking or having to program in
                return self._benchmark_hearing(model, data)
            else:
                logger.warning(f"Benchmark type: {model.type} not supported for whisperfile runtime")

        def _benchmark_hearing(self, model: Model, data):
            files = {
                'file': (data.name, open(data.path, 'rb'))
            }
            req_data = {
                'temperature': 0,
                'temperature_inc': 0.2,
                'response_format': "verbose_json"
            }

            response = requests.post(f"{self.url}/inference", files=files, data=req_data)
            response_json = response.json()
            # TODO handle errors
            # if (response_json.get("error")):
            #     logger.warning(f"Error: {response_json.get('error')} on {file}")

            result = HearingBenchmarkResult(response_json)

            return result