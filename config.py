import os
import requests
import yaml
from sys_info import system
from utils import url_downloader 

CONFIG_FILE = "config.yaml"
DATASET_STORE_DIR = ".datasets"
MODEL_STORE_DIR = ".models"

class Dataset():

    def __init__(self, suite, dataset):
        self.suite = suite
        self.dataset = dataset

        self.name = dataset['name']
        self.url = dataset['url']
        self.source = dataset['source']

        self.dir = os.path.join(DATASET_STORE_DIR, suite, self.name)

    def download(self):
        os.makedirs(self.dir, exist_ok=True)

        if self.source == "hf-api":
            self._download_hf_api()
        elif self.source == "andromeda":
            self._download_andromeda()
        else:
            print(f"Source: {self.source} not supported")

    def _download_hf_api(self):
        key = self.dataset['key']

        response = requests.get(self.url)
        json = response.json()

        for i, row in enumerate(json['rows']):
            url = row['row'][key]
            ext = url.split('.')[-1]
            filename = f"{i}.{ext}"
            if (os.path.exists(os.path.join(self.dir, filename))):
                continue

            url_downloader([{ "url": url, "dest_dir": self.dir, "filename": filename }])

    def _download_andromeda(self):
        response = requests.get(f"{self.url}/metadata.json")
        metadata = response.json()

        for row in metadata:
            url = f"{self.url}/{row}"
            filename = row
            if (os.path.exists(os.path.join(self.dir, filename))):
                continue
            
            url_downloader([{ "url": url, "dest_dir": self.dir, "filename": filename }])

# TODO make this a base class, and then create a subclass for each type of model
class Model():

    def __init__(self, cfg):
        self.name = cfg['name']
        self.type = cfg['type']
        self.runtime = cfg['runtime']
        self.url = cfg['url']
        self.filename = cfg['url'].split("/")[-1]
        self.dir = os.path.join(MODEL_STORE_DIR, self.type)

    def download(self):

        if self.runtime == "llamafile":
            self._download_llamafile()
        elif self.runtime == "docker":
            self._download_docker()
        else:
            print(f"Runtime: {self.runtime} not supported")

    def _download_llamafile(self):
        os.makedirs(self.dir, exist_ok=True)

        if (os.path.exists(os.path.join(self.dir, self.filename))):
            return

        url_downloader([{ "url": self.url, "dest_dir": self.dir, "filename": self.filename }])

    def _download_docker(self):
        pass

class Benchmark():

    def __init__(self, name, cfg):
        self.name = name
        self.models = {}
        self.datasets = {}

        for model in cfg['models']:
            name = model['name']
            self.models[name] = Model(model)

        for dataset in cfg['datasets']:
            name = dataset['name']
            self.datasets[name] = Dataset(self.name, dataset)

        print(f"Benchmark {self.name} has {len(self.models)} models and {len(self.datasets)} datasets")

    def download(self):
        for _, model in self.models.items():
            model.download()

        for _, dataset in self.datasets.items():
            dataset.download()

class Benchmarker():

    def __init__(self):
        cfg_file = open(CONFIG_FILE, 'r')

        self.cfg = yaml.safe_load(cfg_file)
        self.benchmarks = self._init_benchmarks(self.cfg['benchmarks'])

    def _init_benchmarks(self, cfg):
        benchmarks = {}
        for benchmark, value in cfg.items():
            benchmarks[benchmark] = Benchmark(benchmark, value)

        return benchmarks
    
    def download_benchmarks(self):
        for _, benchmark in self.benchmarks.items():
            benchmark.download()
    
    def benchmark(self):
        self.download_benchmarks()

        system.print_sys_info()

        self.benchmark_vision()
        self.benchmark_hearing()
        pass

    def benchmark_vision(self):
        pass

    def benchmark_hearing(self):
        pass

    def benchmark_language(self):
        pass


benchmarker = Benchmarker()