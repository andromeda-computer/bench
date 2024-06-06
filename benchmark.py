import yaml
from config import CONFIG_FILE, FileDataset, Model, PromptDataset
from runtimes.docker import DockerRuntime
from runtimes.llamafile import LlamafileRuntime
from sys_info import system

class Benchmark():

    def __init__(self, name, cfg):
        # TODO set up proper logging for each benchmark

        self.name = name
        self.models = {}
        self.datasets = {}

        for model in cfg['models']:
            name = model['name']
            self.models[name] = Model(model)

        for dataset in cfg['datasets']:
            name = dataset['name']
            if dataset['type'] == "file":
                self.datasets[name] = FileDataset(self.name, dataset)
            elif dataset['type'] == "prompt":
                self.datasets[name] = PromptDataset(self.name, dataset)
            else:
                print(f"Dataset type: {dataset['type']} not supported")
                continue

        # TODO init runtimes and call them directly in benchmark instead

        print(f"Benchmark {self.name} has {len(self.models)} models and {len(self.datasets)} datasets")

    def download(self):
        for _, model in self.models.items():
            model.download()

        for _, dataset in self.datasets.items():
            dataset.download()

    def benchmark(self):
        for _, model in self.models.items():
            runtime = None
            if model.runtime == "llamafile":
                runtime = LlamafileRuntime()
            elif model.runtime == "docker":
                runtime = DockerRuntime()
            else:
                print(f"Runtime: {model.runtime} not supported")
                continue

            runtime.benchmark(model, self.datasets)

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
        print("Downloading benchmarks...")
        self.download_benchmarks()

        print("Gathering System Info...")
        system.print_sys_info()

        print("Benchmarking...")
        # await self.benchmark_language()
        # await self.benchmark_vision()
        self.benchmark_hearing()

    def benchmark_vision(self):
        self.benchmarks['vision'].benchmark()

    def benchmark_hearing(self):
        self.benchmarks['hearing'].benchmark()

    def benchmark_language(self):
        self.benchmarks['language'].benchmark()


benchmarker = Benchmarker()