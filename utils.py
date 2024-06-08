import threading
import time
import psutil
import requests
from rich.console import Console
from rich.layout import Layout
from threading import Event
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

import os.path
from concurrent.futures import ThreadPoolExecutor

from typing import List, TypedDict

console = Console()
layout = Layout()

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

progress = Progress(
    TextColumn("[bold blue]{task.fields[filename]}", justify="left"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
    refresh_per_second=5
)


done_event = Event()

def kill(proc_pid):
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

def handle_sigint(signum, frame):
    done_event.set()

def copy_url(task_id: TaskID, url: str, path: str) -> None:
    """Copy data from a url to a local file."""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('Content-Length', 0))
    progress.update(task_id, total=total_size)
    with open(path, "wb") as dest_file:
        progress.start_task(task_id)
        for chunk in response.iter_content(32768):
            dest_file.write(chunk)
            progress.update(task_id, advance=len(chunk))
            if done_event.is_set():
                return

class FileSpec(TypedDict):
    url: str
    dest_dir: str
    filename: str

# make this nicer to support different kinds of downloaders
def url_downloader(files: List[FileSpec]):
    """Download multiple files to the given directory."""

    # if all the files already exist then we can skip downloading
    to_download = []
    for file in files:
        dest_path = os.path.join(file['dest_dir'], file['filename'])
        if not os.path.exists(dest_path):
            os.makedirs(file['dest_dir'], exist_ok=True)
            to_download.append(file)
    
    if len(to_download) == 0:
        return

    with progress:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for file in to_download:
                dest_path = os.path.join(file['dest_dir'], file['filename'])
                task_id = progress.add_task("download", filename=file['filename'], start=False)
                pool.submit(copy_url, task_id, file['url'], dest_path)

# livetablemanager?
class BenchmarkLogger():
    def __init__(self, columns, title):
        self.columns = columns
        self.title = title
        self.rows = {}
        self.console = Console()
        self.lock = threading.Lock()
        self.update_flag = threading.Event()
        self.update_flag.set()

    def _generate_table(self):
        table = Table(box=None)
        for column in self.columns:
            table.add_column(column)
        for row in self.rows.values():
            table.add_row(*[str(row.get(col, "")) for col in self.columns])
        return Panel(table, title=self.title, border_style="blue")

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

    def stop(self):
        self.update_flag.clear()
        if self.update_thread.is_alive():
            self.update_thread.join()