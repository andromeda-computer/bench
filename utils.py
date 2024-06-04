import psutil
import requests
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

import tqdm

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

    with progress:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for file in files:
                dest_path = os.path.join(file['dest_dir'], file['filename'])
                task_id = progress.add_task("download", filename=file['filename'], start=False)
                pool.submit(copy_url, task_id, file['url'], dest_path)

# import os
# import requests
# from concurrent.futures import ThreadPoolExecutor
# from typing import TypedDict, List
# from tqdm import tqdm

# class FileSpec(TypedDict):
#     url: str
#     dest_dir: str
#     filename: str

# def copy_url(url: str, path: str, progress_bar: tqdm) -> None:
#     """Copy data from a url to a local file."""
#     response = requests.get(url, stream=True)
#     total_size = int(response.headers.get('Content-Length', 0))
#     progress_bar.total = total_size
#     block_size = 32768

#     with open(path, "wb") as dest_file:
#         for chunk in response.iter_content(block_size):
#             dest_file.write(chunk)
#             progress_bar.update(len(chunk))

# def url_downloader(files: List[FileSpec]):
#     """Download multiple files to the given directory."""

#     with ThreadPoolExecutor(max_workers=4) as pool:
#         progress_bars = []
#         futures = []

#         for file in files:
#             dest_path = os.path.join(file['dest_dir'], file['filename'])
#             progress_bar = tqdm(
#                 unit='B',
#                 unit_scale=True,
#                 unit_divisor=1024,
#                 total=None,
#                 desc=file['filename'],
#                 bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
#             )
#             progress_bars.append(progress_bar)
#             future = pool.submit(copy_url, file['url'], dest_path, progress_bar)
#             futures.append(future)

#         for future in futures:
#             future.result()

#         for progress_bar in progress_bars:
#             progress_bar.close()