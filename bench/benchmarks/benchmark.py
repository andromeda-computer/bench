import abc
import os
import re
import threading
import time
import csv

from typing import List

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

from bench.config import RUN_STORE_DIR
from bench.logger import logger
from bench.datasets.dataset import CreationDataset, FileDataset, PromptDataset
from bench.models.model import Model
from bench.system.system import system

class Benchmark(abc.ABC):

    def __init__(self, name, cfg, runtimes, benchmarker_name, **kwargs):
        # TODO set up proper logging for each benchmark
        print(f"Preparing {name} benchmark...")

        self.name = name
        self.benchmarker_name = benchmarker_name
        self.runtimes = runtimes

        self.models = {}
        self.datasets = {}
        self.results = {}

        logger.info(f"Preparing models for {name}")
        for model in cfg['models']:
            name = model['name']
            if model.get('variants'):
                for variant in model['variants']:
                    self.models[f'{name}-{variant}'] = Model(model, variant)
            else:
                self.models[name] = Model(model)

        logger.info(f"Preparing datasets for {name}")
        for dataset in cfg['datasets']:
            name = dataset['name']
            if dataset['type'] == "file":
                self.datasets[name] = FileDataset(self.name, dataset, **kwargs)
            elif dataset['type'] == "prompt":
                self.datasets[name] = PromptDataset(self.name, dataset, **kwargs)
            elif dataset['type'] == "creation":
                self.datasets[name] = CreationDataset(self.name, dataset, **kwargs)
            else:
                logger.warning(f"Dataset type: {dataset['type']} not supported")
                continue

        logger.info(f"Benchmark {self.name} has {len(self.models)} models and {len(self.datasets)} datasets")

    # TODO set up common columns for all benchmarks
    @abc.abstractmethod
    def _benchmark_columns(self):
        pass

    @abc.abstractmethod
    def _update_row(self, model: Model, results: List):
        pass

    def benchmark(self):
        self.bench_logger = BenchmarkLogger(self._benchmark_columns(), self.name.capitalize())
        update_thread = threading.Thread(target=self.bench_logger.start_live_updates)
        update_thread.start()

        for _, model in self.models.items():
            time.sleep(1)
            runtime = self.runtimes.get(model.runtime, None)

            if not runtime:
                logger.warning(f"Runtime: {model.runtime} not supported")
                continue

            # TODO model.benchmark(runtime, ...??)
            # almost certainly this is the way
            # the model would know what type it is so it can call the right benchmark method
            # with type hints
            # also would support somtehing like resolution much nicer.
            logger.info(f"Benchmarking {model.name} with {model.runtime} runtime...")
            # print(f"Benchmarking {model.name} with {model.runtime} runtime and {model.quant} quant...")
            self.bench_logger.add_row(model.tag, {
                "status": f"[blue]starting[/blue]",  
                "model": model.name,
                "quant": model.quant,
            })
            started = runtime.start(model)

            if not started:
                self.bench_logger.update_row(model.tag, {
                    "status": f"[red]failed[/red]",  
                })
                logger.info(f"Failed to start runtime: {model.runtime}")
                continue

            results = []
            count = 0
            total_count = sum([len(dataset.data) for _, dataset in self.datasets.items()])

            for _, dataset in self.datasets.items():
                for data in dataset.data:
                    count += 1
                    self.bench_logger.update_row(model.tag, {
                        "status": f"[{count}/{total_count}]"
                    })

                    # TODO it might make more sense to calculate tok/sec/watt directly here
                    start_time = system.power_start("individual_bench_run")
                    result = runtime.benchmark(model, data)
                    watts, samples, end_time = system.power_stop("individual_bench_run")
                    total_time = end_time - start_time

                    if result:
                        # TODO a class?
                        results.append({"data": result, "time": total_time, "watts": watts})
                        self._update_row(model, results)
            
            self.results[model.name] = results

            self.bench_logger.update_row(model.name, {
                "status": f"[green]success[/green]"
            })
            runtime.stop()

        # sleep to make sure all the rows updated. this should happen on update instead, but shrug
        time.sleep(1)
        # TODO only write to file if asked to
        self.bench_logger.write_table(self.benchmarker_name)
        self.bench_logger.stop()
        # make sure we are actually stopped before continuing
        time.sleep(2)

def get_benchmark_color(name):
    if name == "language":
        return "bright_cyan"
    elif name == "vision":
        return "bright_blue"
    elif name == "hearing":
        return "bright_magenta"
    elif name == "creation":
        return "bright_yellow"
    else:
        return "blue"

def remove_tags(input_string):
    # Pattern to match any text within square brackets and the square brackets themselves
    pattern = r'\[.*?\]'
    # Substitute the matched pattern with an empty string
    cleaned_string = re.sub(pattern, '', f"{input_string}")
    return cleaned_string

class BenchmarkLogger():
    def __init__(self, columns, title: str):
        self.columns = columns
        self.title = title
        self.rows = {}
        self.console = Console()
        self.lock = threading.Lock()
        self.update_flag = threading.Event()
        self.update_flag.set()
        self.border_color = get_benchmark_color(title.lower())

    def _generate_table(self):
        table = Table(box=None)
        for column in self.columns:
            table.add_column(column)
        for row in self.rows.values():
            table.add_row(*[str(row.get(col, "")) for col in self.columns])
        return Panel.fit(table, title=self.title, border_style=self.border_color)

    def _refresh_table(self, live):
        with self.lock:
            live.update(self._generate_table())

    def add_row(self, row_name, data):
        with self.lock:
            self.rows[row_name] = data

    def update_row(self, row_name, data):
        with self.lock:
            if row_name in self.rows:
                self.rows[row_name].update(data)

    # TODO all of this feels like a hack, surely a better way
    def start_live_updates(self, refresh_rate=4):
        self.live = Live(self._generate_table(), refresh_per_second=refresh_rate)
        self.update_thread = threading.Thread(target=self._run_updates)
        self.update_thread.start()
        with self.live:
            self.update_thread.join()

    def _run_updates(self):
        while self.update_flag.is_set():
            self._refresh_table(self.live)
            time.sleep(0.1)

    def write_table(self, benchmarker_name):
        run_dir = os.path.join(RUN_STORE_DIR, f"{system.get_accelerator_info_string()}:{benchmarker_name}")
        run_path = os.path.join(run_dir, f"{self.title.lower()}.csv")

        os.makedirs(run_dir, exist_ok=True)

        with open(run_path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(self.columns)
            for row in self.rows.values():
                processed_row = [remove_tags(value) for _, value in row.items()]
                writer.writerow(processed_row)

    def stop(self):
        self.update_flag.clear()
        if self.update_thread.is_alive():
            self.update_thread.join()