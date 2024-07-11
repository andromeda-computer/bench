import asyncio
import os
import shutil
import time
from typing import List, Dict, TypedDict
import aiohttp

class FileSpec(TypedDict):
    url: str
    dest_dir: str
    filename: str

class AsyncDownloader:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.queue = asyncio.Queue()
            cls._instance.downloads = {}
            cls._instance.max_workers = 5  # Set the maximum number of concurrent workers
            cls._instance.semaphore = asyncio.Semaphore(cls._instance.max_workers)
            cls._instance.progress = {}
            cls._instance.console_lock = asyncio.Lock()
        return cls._instance

    def add_download(self, file_spec: FileSpec):
        dest_path = os.path.join(file_spec['dest_dir'], file_spec['filename'])
        if not os.path.exists(dest_path):
            os.makedirs(file_spec['dest_dir'], exist_ok=True)
            self.queue.put_nowait(file_spec)  # Use put_nowait instead of create_task
        # else:
            # print(f"File already exists: {dest_path}")

    async def _download_file(self, file_spec: FileSpec):
        url = file_spec['url']
        dest_path = os.path.join(file_spec['dest_dir'], file_spec['filename'])
        async with self.semaphore:  # Use semaphore to limit concurrent downloads
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded_size = 0
                        start_time = time.time()
                        with open(dest_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded_size += len(chunk)
                                    await self._update_progress(file_spec['filename'], downloaded_size, total_size, start_time)
                        await self._display_progress()
                        self.downloads[url] = True
                    else:
                        self.downloads[url] = False
    
    async def _update_progress(self, filename: str, downloaded: int, total: int, start_time: float):
        elapsed_time = time.time() - start_time
        speed = downloaded / elapsed_time if elapsed_time > 0 else 0
        percent = (downloaded / total) * 100 if total > 0 else 0
        time_remaining = (total - downloaded) / speed if speed > 0 else 0

        self.progress[filename] = {
            'downloaded': downloaded,
            'total': total,
            'percent': percent,
            'speed': speed,
            'time_remaining': time_remaining
        }

        await self._display_progress()

    async def _display_progress(self):
        async with self.console_lock:
            console_width = shutil.get_terminal_size().columns
            print("\033[2J\033[H", end="")  # Clear screen and move cursor to top-left
            print("Download Progress:")
            for filename, data in self.progress.items():
                progress_bar_width = console_width - 100
                filled_width = int(data['percent'] / 100 * progress_bar_width)
                bar = f"[{'=' * filled_width}{' ' * (progress_bar_width - filled_width)}]"
                print(f"{filename[:40]:<40} {bar} {data['percent']:6.2f}% {data['downloaded']/1024/1024:6.2f}MB/{data['total']/1024/1024:6.2f}MB {data['speed']/1024/1024:6.2f}MB/s ETA: {data['time_remaining']:6.2f}s")

    async def process_queue(self):
        tasks = []
        while not self.queue.empty():
            file_spec = await self.queue.get()
            task = asyncio.create_task(self._download_file(file_spec))
            tasks.append(task)
        await asyncio.gather(*tasks)

    async def wait_for_downloads(self):
        # Wait a short time to allow the queue to be populated
        await asyncio.sleep(0.1)
        await self.process_queue()
        return all(self.downloads.values())

def get_downloader():
    return AsyncDownloader()