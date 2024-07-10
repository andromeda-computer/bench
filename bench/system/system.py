import shutil
from typing import List
import cpuinfo
import psutil
import platform
import time
from pynvml import *
from bench.system.rocml import *

# TODO this instead of rich? https://github.com/FedericoCeratto/dashing
from rich.console import Console
from rich.table import Table

from bench.system.accelerators.amd import AMDAccelerator
from bench.system.accelerators.apple import *
from bench.logger import logger
from bench.system.accelerators.nvidia import NvidiaAccelerator
    
class System():

    def __init__(self):
        self.power_monitor = {}

        self.uname = platform.uname()
        self.architecture = platform.machine()
        self.cpu_name = cpuinfo.get_cpu_info()['brand_raw']
        self.cpu_phys_cores = psutil.cpu_count(logical=False)
        self.cpu_total_cores = psutil.cpu_count(logical=True)
        self.ram = psutil.virtual_memory().total / 1024 / 1024 / 1024
        self.accelerators = []

        self._init_nvidia()
        self._init_amd()
        self._init_apple()

        if len(self.accelerators) > 1:
            raise SystemExit("Error: Only a single accelerator device is currently supported")
        
    def _init_apple(self):
        if self.uname.system == "Darwin" and 'arm' in self.architecture.lower():
            self.accelerators.append(AppleAccelerator())

    def _init_amd(self):
        if shutil.which("rocm-smi") and os.path.exists("/sys/module/amdgpu/initstate"):
            try:
                smi_initialize()
                device_count = smi_get_device_count()

                for device in range(device_count):
                    self.accelerators.append(AMDAccelerator(device))
            except Exception as e:
                logger.info(f"Error initializing AMD devices: {e}")
    
    def _init_nvidia(self):
        try:
            nvmlInit()
            device_count = nvmlDeviceGetCount()

            for i in range(device_count):
                self.accelerators.append(NvidiaAccelerator(i))

        except Exception as e:
            logger.info(f"Error initializing Nvidia devices: {e}")

    def print_sys_info(self):
        console = Console()
        panels = []
        cpu_panel = Panel.fit(
            f'\n[b]Operating System: {self.uname.system}[/b]\n'
            f'[b]Processor: {self.cpu_name} ({self.architecture})[/b]\n'
            f'[b]Physical cores:[/b] {self.cpu_phys_cores}\n'
            f'[b]Total cores:[/b] {self.cpu_total_cores}\n'
            f'[b]Usable RAM:[/b] {self.ram:.2f}GB',
            title="Basic System Info",
            border_style="white",
            height=9
        )

        panels.append(cpu_panel)
        for device in self.accelerators:
            panels.append(device.get_panel())

        table = Table.grid()
        table.add_row(*panels)
        # layout.split_row(*panels)

        console.print(table)
        
    def get_accelerator_info_string(self):
        if len(self.accelerators) == 0:
            return "No accelerators found"
        
        return self.accelerators[0].get_basic_info_string()
    
    def power_start(self, name):
        if (len(self.accelerators) == 0):
            # TODO we should have a more robust way of handling this
            raise Exception("No accelerators found")

        # TODO support multiple devices
        self.accelerators[0].start_power_monitor(name)
        return time.time()

    def power_stop(self, name):
        if (len(self.accelerators) == 0):
            # TODO we should have a more robust way of handling this (just use cpu)
            # should imply # GPU layers is 0 for sure.
            raise Exception("No accelerators found") 

        # TODO instead of always picking index 0, we should have a way to specify the device
        # probably by prompting the user which GPU's to use, and how to use them. 
        samples = self.accelerators[0].end_power_monitor(name)
        avg_watts = sum([sample.watts for sample in samples]) / len(samples)

        return (avg_watts, samples, time.time())


system = System()