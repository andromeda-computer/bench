import abc
import collections
import shutil
from typing import List
import cpuinfo
import psutil
import platform
from pynvml import *
from pyrsmi import rocml
import time

# TODO this instead of rich? https://github.com/FedericoCeratto/dashing
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table

from accelerators.apple import *
from logger import logger

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
    
class PowerMonitorSample():

    def __init__(self, watts, time):
        self.watts = watts
        self.time = time

# TODO this power monitoring solution is not very elegant but it works.
# it probably needs to be broken out to the system level as well.
class Accelerator(abc.ABC):

    def __init__(self):
        self.thread = None
        self.power_monitors = {}
        self.latest_samples = collections.deque(maxlen=10)

        # start sampling
        self.thread = threading.Thread(target=self._sample_power_usage)
        self.thread.daemon = True  # set as daemon thread so it exits with the main thread
        self.thread.start()

    def start_power_monitor(self, name):
        if name in self.power_monitors:
            raise Exception(f"Power monitor {name} already started")

        self.power_monitors[name] = []

    def end_power_monitor(self, name) -> List[PowerMonitorSample]:
        if name in self.power_monitors:
            samples = self.power_monitors[name]
            del self.power_monitors[name]

            return samples
        else:
            raise Exception(f"Power monitor {name} not started")

    def _add_power_sample(self, sample: PowerMonitorSample):
        self.latest_samples.append(sample)

        # add the sample to every running power monitor
        for monitor in self.power_monitors:
            self.power_monitors[monitor].append(sample)

    def _sample_power_usage(self):
        while True:
            sample_start = time.time()
            watts = self._get_power_usage()

            # watts could be None if the sample couldn't be taken (or needs a first sample to start)
            if (watts):
                self._add_power_sample(PowerMonitorSample(watts, sample_start))
            time.sleep(0.01)
        
    @abc.abstractmethod
    def get_panel(self):
        pass

    @abc.abstractmethod
    def _get_power_usage(self):
        pass

    def __del__(self):
        if self.thread:
            self.thread.join()

class NvidiaAccelerator(Accelerator):

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

        super().__init__()

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
            border_style="Green",
            height=9
        )

    def _get_power_usage(self):
        latest_power = nvmlDeviceGetTotalEnergyConsumption(self.handle)
        if not hasattr(self, 'start_power'):
            self.start_power = latest_power
            return None

        # get the previous sample time
        prev_sample = self.latest_samples[-1]
        now = time.time()

        joules = (latest_power - self.start_power) / 1000
        watts = joules / (now - prev_sample.time)
        return watts

class AMDAccelerator(Accelerator):

    def __init__(self, index):
        self.index = index
        self.name = rocml.smi_get_device_name(index)
        self.memory = rocml.smi_get_device_memory_total(index) * 1e-9

        super().__init__()

    def get_panel(self):
        return Panel.fit(
            f'[b]Device: {self.name}[/b]\n'
            f'[b]Memory:[/b] {self.memory:.2f}GB',
            title="AMD Device Info",
            border_style="red",
            height=9
        )

    def _get_power_usage(self):
        watts = rocml.smi_get_device_average_power(self.index)
        return watts

class AppleAccelerator(Accelerator):

    def __init__(self):
        self.soc_info = get_soc_info()
        self.name = self.soc_info['name']
        self.p_cores = self.soc_info['p_core_count']
        self.e_cores = self.soc_info['e_core_count']
        self.gpu_cores = self.soc_info['gpu_core_count']
        self.as_power_metrics = AppleSiliconPowermetrics()

        super().__init__()

    def get_panel(self):
        return Panel.fit(
            f'\n[b]Device: {self.name}[/b]\n'
            f'[b]P Cores:[/b] {self.p_cores}\n'
            f'[b]E Cores:[/b] {self.e_cores}\n'
            f'[b]GPU Cores:[/b] {self.gpu_cores}\n',
            title="Apple Device Info",
            border_style="white",
            height=9
        )

    def _get_power_usage(self):
        # sample the latest reading from system power
        return self.as_power_metrics.get_power_usage()['system_power'] / 1000
    
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
        if shutil.which("rocm-smi"):
            try:
                rocml.smi_initialize()
                device_count = rocml.smi_get_device_count()

                for device in range(device_count):
                    self.accelerators.append(AMDAccelerator(device))
            except Exception as e:
                logger.info(f"Error initializing AMD devices: {e}")
    
    def _init_nvidia(self):
        if shutil.which("nvcc"):
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
            border_style="bright_blue",
            height=9
        )

        panels.append(cpu_panel)
        for device in self.accelerators:
            panels.append(device.get_panel())

        table = Table.grid()
        table.add_row(*panels)
        # layout.split_row(*panels)

        console.print(table)
        
    
    def power_start(self, name):
        if (len(self.accelerators) == 0):
            # TODO we should have a more robust way of handling this
            raise Exception("No accelerators found")

        # TODO support multiple devices
        self.accelerators[0].start_power_monitor(name)
        return time.time()

    def power_stop(self, name):
        if (len(self.accelerators) == 0):
            # TODO we should have a more robust way of handling this
            raise Exception("No accelerators found") 

        samples = self.accelerators[0].end_power_monitor(name)
        avg_watts = sum([sample.watts for sample in samples]) / len(samples)

        return (avg_watts, samples, time.time())


system = System()