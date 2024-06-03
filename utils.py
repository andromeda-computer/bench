import psutil
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.text import Text

from threading import Event
import signal

import os.path
import sys
from concurrent.futures import ThreadPoolExecutor

from functools import partial

from typing import List, TypedDict

from urllib.request import urlopen

console = Console()
layout = Layout()

layout.split(
    Layout(name="header", size=1),
    Layout(ratio=1, name="main"),
    Layout(size=10, name="footer"),
)

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
    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
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
    # progress.console.log(f"Requesting {url}")
    response = urlopen(url)
    # This will break if the response doesn't contain content length
    progress.update(task_id, total=int(response.info()["Content-length"]))
    with open(path, "wb") as dest_file:
        progress.start_task(task_id)
        for data in iter(partial(response.read, 32768), b""):
            dest_file.write(data)
            progress.update(task_id, advance=len(data))
            if done_event.is_set():
                return
    # progress.console.log(f"Downloaded {path}")


class FileSpec(TypedDict):
    url: str
    dest_dir: str
    filename: str

def url_downloader(files: List[FileSpec]):
    """Download multiple files to the given directory."""

    with progress:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for file in files:
                dest_path = os.path.join(file['dest_dir'], file['filename'])
                task_id = progress.add_task("download", filename=file['filename'], start=False)
                pool.submit(copy_url, task_id, file['url'], dest_path)