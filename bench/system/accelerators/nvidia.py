from pynvml import *
from rich.panel import Panel

from bench.system.accelerators.accelerator import Accelerator

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
        
        self.prev_sample = None
        
        super().__init__()

    def get_panel(self):
        return Panel.fit(
            # f'[b]Device Handle: {}[/b]\n'
            f'[b]Device: {self.name}[/b]\n'
            f'[b]Memory:[/b] {self.memTotal}MB\n'
            f'[b]CUDA Cores:[/b] {self.cudaCores}\n'
            f'[b]CUDA Compute Capability:[/b] {self.cudaCapability}\n'
            f'[b]Memory Bus Width:[/b] {self.memBusWidth}bit\n'
            f'[b]Power Limit ([green]curr[/green]/min/max):[/b] ([green]{self.currPwrLimit}W[/green]/{self.pwrLimitMinMax[0]/1000}W/{self.pwrLimitMinMax[1]/1000}W)\n'
            f'[b]Architecture:[/b] {self.architecture}',
            title="NVIDIA Device Info",
            border_style="Green",
            height=9
        )

    def _get_power_usage(self):
        return nvmlDeviceGetPowerUsage(self.handle) / 1000
    
    def get_basic_info_string(self):
        return f"{self.name.replace(' ', '-')}:{round(self.memTotal / 1024)}GB:{self.currPwrLimit}W"