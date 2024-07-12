from dataclasses import dataclass
import numpy as np
import psutil
import requests
from rich.console import Console
from rich.layout import Layout
from threading import Event

import os.path
from concurrent.futures import ThreadPoolExecutor

from typing import Callable, List, TypedDict

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

@dataclass
class Column:
    name: str
    display: bool
    compute: Callable[[List], float]
    format: Callable[[float], str] = lambda x: f"{round(x, 2)}"


def calculate_percentile(results, percentile, selector):
    values = [selector(r) for r in results]
    return np.percentile(values, percentile)

def create_percentile_columns(attribute_name, selector, display=False):
    return [
        Column(f"p1 {attribute_name}", display, 
               lambda results: calculate_percentile(results, 1, selector),
               lambda x: f"[green]{round(x)}ms[/green]"),
        
        Column(f"p25 {attribute_name}", display, 
               lambda results: calculate_percentile(results, 25, selector),
               lambda x: f"[green]{round(x)}ms[/green]"),
        
        Column(f"p50 {attribute_name}", display, 
               lambda results: calculate_percentile(results, 50, selector),
               lambda x: f"[green]{round(x)}ms[/green]"),
        
        Column(f"p75 {attribute_name}", display, 
               lambda results: calculate_percentile(results, 75, selector),
               lambda x: f"[green]{round(x)}ms[/green]"),
        
        Column(f"p99 {attribute_name}", display, 
               lambda results: calculate_percentile(results, 99, selector),
               lambda x: f"[green]{round(x)}ms[/green]"),
    ]

class FileSpec(TypedDict):
    url: str
    dest_dir: str
    filename: str

# make this nicer to support different kinds of downloaders
def url_downloader(files: List[FileSpec], workers: int = 10):
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
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for file in to_download:
                dest_path = os.path.join(file['dest_dir'], file['filename'])
                task_id = progress.add_task("download", filename=file['filename'], start=False)
                pool.submit(copy_url, task_id, file['url'], dest_path)