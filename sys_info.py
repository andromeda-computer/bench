import cpuinfo
import psutil
import platform
from pynvml import *
import time

from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table

def get_nvidia_arch(arch_num):
    if arch_num == 2:
        return "Kepler"
    elif arch_num == 3:
        return "Maxwell"
    elif arch_num == 4:
        return "Pascal"
    elif arch_num == 5:
        return "Volta"
    elif arch_num == 6:
        return "Turing"
    elif arch_num == 7:
        return "Ampere"
    elif arch_num == 8:
        return "Ada"
    elif arch_num == 9:
        return "Hopper"

class NvidiaDevice():

    def __init__(self, index):
        self.handle = nvmlDeviceGetHandleByIndex(index)
        self.name = nvmlDeviceGetName(self.handle)
        self.memory = nvmlDeviceGetMemoryInfo(self.handle)
        self.arch = nvmlDeviceGetArchitecture(self.handle)
        self.currPwrLimit = nvmlDeviceGetPowerManagementLimit(self.handle) / 1000
        self.pwrLimitMinMax = nvmlDeviceGetPowerManagementLimitConstraints(self.handle)
        self.memTotal = self.memory.total / 1024 / 1024
        self.memBusWidth = nvmlDeviceGetMemoryBusWidth(self.handle)
        self.cudaCapability = nvmlDeviceGetCudaComputeCapability(self.handle)
        self.cudaCores = nvmlDeviceGetNumGpuCores(self.handle)
        self.architecture = get_nvidia_arch(self.arch)

    def get_panel(self):
        return Panel.fit(
            # f'[b]Device Handle: {}[/b]\n'
            f'[b]Device: {self.name}[/b]\n'
            f'[b]Memory:[/b] {self.memTotal}MB\n'
            f'[b]CUDA Cores:[/b] {self.cudaCores}\n'
            f'[b]CUDA Compute Capability:[/b] {self.cudaCapability}\n'
            f'[b]Memory Bus Width:[/b] {self.memBusWidth}bit\n'
            f'[b]Power Limit (curr/min/max):[/b] ({self.currPwrLimit}W/{self.pwrLimitMinMax[0]/1000}W/{self.pwrLimitMinMax[1]/1000}W)\n'
            f'[b]Architecture:[/b] {self.architecture}',
            title="Nvidia Device Info",
            border_style="Green"
        )

    def print(self):
        print(f"Device: {self.name} ({self.memTotal}MB)")
        print(f"CUDA Cores: {self.cudaCores}")
        print(f"CUDA Compute Capability: {self.cudaCapability}")
        print(f"Memory Bus Width: {self.memBusWidth}bit")
        print(f"Power Limit (curr/min/max): ({self.currPwrLimit}W/{self.pwrLimitMinMax[0]/1000}W/{self.pwrLimitMinMax[1]/1000}W)")
        print(f"Architecture: {self.architecture}")
    
class System():

    def __init__(self):
        self.power_monitor = {}

        self.uname = platform.uname()
        self.cpu_name = cpuinfo.get_cpu_info()['brand_raw']
        self.cpu_phys_cores = psutil.cpu_count(logical=False)
        self.cpu_total_cores = psutil.cpu_count(logical=True)
        self.ram = psutil.virtual_memory().total / 1024 / 1024 / 1024

        self._init_nvidia()
    
    def _init_nvidia(self):
        nvmlInit()
        self.nvidia_device_count = nvmlDeviceGetCount()
        self.nvidia_driver_version = nvmlSystemGetDriverVersion()
        self.nvidia_devices = []
        for i in range(self.nvidia_device_count):
            self.nvidia_devices.append(NvidiaDevice(i))

    def print_sys_info(self):
        console = Console()
        panels = []
        cpu_panel = Panel.fit(
            f'\n[b]Operating System: {self.uname.system}[/b]\n'
            f'[b]Processor: {self.cpu_name}[/b]\n'
            f'[b]Physical cores:[/b] {self.cpu_phys_cores}\n'
            f'[b]Total cores:[/b] {self.cpu_total_cores}\n'
            f'[b]Usable RAM:[/b] {self.ram:.2f}GB',
            title="Basic System Info",
            border_style="bright_blue",
            height=9
        )

        panels.append(cpu_panel)
        for device in self.nvidia_devices:
            panels.append(device.get_panel())

        table = Table.grid()
        table.add_row(*panels)
        # layout.split_row(*panels)

        console.print(table)
        
    
    def power_start(self, name):
        if name in self.power_monitor:
            raise Exception(f"Power monitor {name} already started")

        # TODO be robust for multiple devices
        start = time.time()
        self.power_monitor[name] = {"mJ": nvmlDeviceGetTotalEnergyConsumption(self.nvidia_devices[0].handle), "time": start}
        return self.power_monitor[name]

    def power_stop(self, name):
        if name in self.power_monitor:
            stopTime = time.time()
            startTime = self.power_monitor[name]['time']
            startMJ = self.power_monitor[name]['mJ']
            stopMJ = nvmlDeviceGetTotalEnergyConsumption(self.nvidia_devices[0].handle)

            totalMJ = stopMJ - startMJ
            totalJoules = totalMJ / 1000
            totalTime = stopTime - startTime
            totalWatts = totalJoules / totalTime
            totalMilliwatts = totalMJ / totalTime

            del self.power_monitor[name]
            return (totalJoules, totalTime, totalWatts, totalMilliwatts)
        else:
            raise Exception(f"Power monitor {name} not started")


system = System()