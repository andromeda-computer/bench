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

from bench.benchmarks.model import Model
from bench.config import RUN_STORE_DIR
from bench.logger import logger
from bench.datasets.dataset import CreationDataset, FileDataset, PromptDataset
from bench.runtimes.runtime import Runtime
from bench.system.system import system
from .benchmark_test import BenchmarkResult, BenchmarkTest


class Benchmark(abc.ABC):

    def __init__(self, name, cfg, runtimes: List[Runtime], benchmarker_name, **kwargs):
        # TODO set up proper logging for each benchmark
        print(f"Preparing {name} benchmark...")

        self.name = name
        self.benchmarker_name = benchmarker_name
        self.runtimes = runtimes
        self.models = [] 
        # tests could be a dict from tag: test 
        self.tests = []
        self.datasets = {}

        variants = set()

        logger.info(f"Preparing models for {name}")
        for model_cfg in cfg['models']:
            model = Model(model_cfg)
            self.models.append(model)

            # TODO allow for multiple runtimes on the same model
            model_runtime = self.runtimes.get(model_cfg.get("runtime", None), None) 

            if not model_runtime:
                logger.warning(f"Runtime: {model_cfg.get('runtime')} not supported")
                continue

            if model_cfg.get('variants'):
                for variant in model_cfg['variants']:
                    variants.update(variant.keys())
                    self.tests.append(BenchmarkTest(model, model_runtime, variant))
            else:
                self.tests.append(BenchmarkTest(model, model_runtime))

        # get variant keys and add to column

        self.columns = ["status", "model", "quant"] + list(variants) + ["elapsed time", "avg watts"] + self._benchmark_columns()
        self.rows = {}

        # TODO redo this. it could just use the state from benchmark directly?
        self.bench_logger = BenchmarkLogger(self.columns, self.name.capitalize())


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

    @abc.abstractmethod
    def _compute_results(self):
        pass

    @abc.abstractmethod
    def _benchmark_columns(self):
        pass

    @abc.abstractmethod
    def _update_display(self, tag, data):
        pass

    def update_row(self, tag: str, data: List[BenchmarkResult]):
        self.rows[tag] = self._compute_results(data)
        self._update_display(tag, self.rows[tag])

    def benchmark(self):
        update_thread = threading.Thread(target=self.bench_logger.start_live_updates)
        update_thread.start()

        total_count = sum([len(dataset.data) for _, dataset in self.datasets.items()])

        for test in self.tests:
            logger.info(f"Benchmarking {test.model.name} with {test.runtime.name} runtime...")
            self.bench_logger.add_row(test.tag, {
                "status": f"[blue]starting[/blue]",  
                "model": test.model.name,
                "quant": test.model.quant,
                **(test.variant or {})
            })
            started = test.start_runtime()

            if not started:
                self.bench_logger.update_row(test.tag, {
                    "status": f"[red]failed[/red]",  
                })
                logger.info(f"Failed to start runtime: {test.runtime.name}")
                continue
            
            count = 0

            for _, dataset in self.datasets.items():
                for test_item in dataset.data:
                    count += 1
                    self.bench_logger.update_row(test.tag, {
                        "status": f"[{count}/{total_count}]"
                    })

                    test.run(test_item)
                    self.update_row(test.tag, test.results)

            self.bench_logger.update_row(test.tag, {
                "status": f"[green]success[/green]"
            })

            test.stop_runtime()
            time.sleep(1)


        # sleep to make sure all the rows updated. this should happen on update instead, but shrug
        time.sleep(1)
        # TODO only write to file if asked to
        # actually use a config file to determine sqlite, s3 or local file or whatever..
        # self.bench_logger.write_table(self.benchmarker_name)
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