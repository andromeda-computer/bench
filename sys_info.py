import cpuinfo
import psutil
import platform
from pynvml import *
import time

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
        self.memory = nvmlDeviceGetMemoryInfo(self.handle)
        self.arch = nvmlDeviceGetArchitecture(self.handle)
        self.currPwrLimit = nvmlDeviceGetPowerManagementLimit(self.handle) / 1000
        self.pwrLimitMinMax = nvmlDeviceGetPowerManagementLimitConstraints(self.handle)
        self.memTotal = self.memory.total / 1024 / 1024
        self.memBusWidth = nvmlDeviceGetMemoryBusWidth(self.handle)
        self.cudaCapability = nvmlDeviceGetCudaComputeCapability(self.handle)
        self.cudaCores = nvmlDeviceGetNumGpuCores(self.handle)
        self.architecture = get_nvidia_arch(self.arch)

    def print(self):
        print(f"Device: {nvmlDeviceGetName(self.handle)} ({self.memTotal}MB)")
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

        self._init_nvidia()
    
    def _init_nvidia(self):
        nvmlInit()
        self.nvidia_device_count = nvmlDeviceGetCount()
        self.nvidia_driver_version = nvmlSystemGetDriverVersion()
        self.nvidia_devices = []
        for i in range(self.nvidia_device_count):
            self.nvidia_devices.append(NvidiaDevice(i))

    def print_sys_info(self):
        print(f"System: {self.uname.system}")
        print(f"Processor: {self.cpu_name}")
        print("Physical cores:", self.cpu_phys_cores)
        print("Total cores:", self.cpu_total_cores)
        print("\n-------- GPU INFO --------")
        print(f"# NVIDIA Devices: {self.nvidia_device_count}")
        print(f"Driver Version: {self.nvidia_driver_version}\n")
        for device in self.nvidia_devices:
            device.print()
        print("--------------------------")
    
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