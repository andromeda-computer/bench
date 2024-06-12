import time
from pynvml import *
from rich.panel import Panel

from system.accelerators.accelerator import Accelerator

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