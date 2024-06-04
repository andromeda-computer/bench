import cpuinfo
import psutil
import platform
from pynvml import *

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

def log_sys_info():
    uname = platform.uname()
    print(f"System: {uname.system}")
    print(f"Processor: {cpuinfo.get_cpu_info()['brand_raw']}")
    print("Physical cores:", psutil.cpu_count(logical=False))
    print("Total cores:", psutil.cpu_count(logical=True))

    nvmlInit()
    deviceCount = nvmlDeviceGetCount()
    print("\n-------- GPU INFO --------")
    print(f"Driver Version: {nvmlSystemGetDriverVersion()}\n")
    for i in range(deviceCount):
        handle = nvmlDeviceGetHandleByIndex(i)
        memory = nvmlDeviceGetMemoryInfo(handle)
        arch = nvmlDeviceGetArchitecture(handle)
        memTotal = memory.total / 1024 / 1024
        memFree = memory.free / 1024 / 1024
        memUsed = memory.used / 1024 / 1024
        print(f"Device {i}: {nvmlDeviceGetName(handle)} ({memTotal}MB)")
        print(f"CUDA Cores: {nvmlDeviceGetNumGpuCores(handle)}")
        print(f"CUDA Compute Capability: {nvmlDeviceGetCudaComputeCapability(handle)}")
        print(f"Memory Bus Width: {nvmlDeviceGetMemoryBusWidth(handle)}bit")
        print(f"Architecture: {get_nvidia_arch(arch)}\n")
    print("--------------------------\n")
