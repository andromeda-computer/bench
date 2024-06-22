
import json
import time
import uuid
from bench import logger
from bench.benchmarks.creation import CreationBenchmarkResult
from bench.models.model import Model
from bench.runtimes.runtime import Runtime
import websocket
import urllib.request
import urllib.parse

BASE_REQ = {
    "3": {
        "inputs": {
            "seed": 108202181225256,
            "steps": 20,
            "cfg": 8,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1,
            "model": [
                "4",
                0
            ],
            "positive": [
                "6",
                0
            ],
            "negative": [
                "7",
                0
            ],
            "latent_image": [
                "5",
                0
            ]
        },
        "class_type": "KSampler"
    },
    "4": {
        "inputs": {
            "ckpt_name": "sd_xl_base_1.0.safetensors"
        },
        "class_type": "CheckpointLoaderSimple"
    },
    "5": {
        "inputs": {
            "width": 512,
            "height": 512,
            "batch_size": 1
        },
        "class_type": "EmptyLatentImage"
    },
    "6": {
        "inputs": {
            "text": "beautiful scenery nature glass bottle landscape, , purple galaxy bottle,",
            "clip": [
                "4",
                1
            ]
        },
        "class_type": "CLIPTextEncode"
    },
    "7": {
        "inputs": {
            "text": "text, watermark",
            "clip": [
                "4",
                1
            ]
        },
        "class_type": "CLIPTextEncode"
    },
    "8": {
        "inputs": {
            "samples": [
                "3",
                0
            ],
            "vae": [
                "4",
                2
            ]
        },
        "class_type": "VAEDecode"
    },
    "9": {
        "inputs": {
            "filename_prefix": "ComfyUI",
            "images": [
                "8",
                0
            ]
        },
        "class_type": "SaveImage"
    }
}

class ComfyRuntime(Runtime):

    def __init__(self, cfg):
        super().__init__(cfg)
        self.pid = None

        self.server_address = "localhost:8188"
        self.client_id = str(uuid.uuid4())

        self.ws = websocket.WebSocket()
        self.ws.connect("ws://{}/ws?clientId={}".format(self.server_address, self.client_id))

    def _download(self):
        pass

    def _start(self, model: Model):
        return True

    def _stop(self):
        return True

    def benchmark(self, model: Model, data):
        if (model.type == "creation"):
            return self._benchmark_creation(model, data)
        else:
            logger.warning(f"Model type: {model.type} not supported for comfy runtime")
            return None
    
    def _benchmark_creation(self, model: Model, data):
        req = BASE_REQ.copy()

        req['4']['inputs']['ckpt_name'] = model.filename
        req['3']['inputs']['steps'] = model.steps
        req['3']['inputs']['scheduler'] = model.scheduler
        req['3']['inputs']['cfg'] = model.cfg_scale
        req['5']['inputs']['width'] = model.resolution
        req['5']['inputs']['height'] = model.resolution
        req['6']['inputs']['text'] = data['prompt']
        req['7']['inputs']['text'] = data['negative']

        prompt_id = self._queue_prompt(req)['prompt_id']
        start = time.time()
        k_sampler_started = None
        k_sampler_sec_elapsed = []
        while True:
            out = self.ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                # print(message)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        break #Execution is done
                    if data['node'] == '3':
                        k_sampler_started = time.time()
                if message['type'] == 'progress' and message['data']['node'] == "3":
                    data = message['data']
                    now = time.time()
                    k_sampler_sec_elapsed.append(now - k_sampler_started)
                    k_sampler_started = now
            else:
                continue #previews are binary data

        total_time = time.time() - start
        return CreationBenchmarkResult(total_time, k_sampler_sec_elapsed)

    def _queue_prompt(self,prompt):
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req =  urllib.request.Request("http://{}/prompt".format(self.server_address), data=data)
        return json.loads(urllib.request.urlopen(req).read())