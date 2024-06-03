import cpuinfo
import psutil
import platform
from pynvml import *

def log_sys_info():
    uname = platform.uname()
    print(f"System: {uname.system}")
    print(f"Processor: {cpuinfo.get_cpu_info()['brand_raw']}")
    print("Physical cores:", psutil.cpu_count(logical=False))
    print("Total cores:", psutil.cpu_count(logical=True))

    nvmlInit()
    print(f"Driver Version: {nvmlSystemGetDriverVersion()}")
    deviceCount = nvmlDeviceGetCount()
    for i in range(deviceCount):
        handle = nvmlDeviceGetHandleByIndex(i)
        memory = nvmlDeviceGetMemoryInfo(handle)
        memTotal = memory.total / 1024 / 1024
        memFree = memory.free / 1024 / 1024
        memUsed = memory.used / 1024 / 1024
        print(f"Device {i}: {nvmlDeviceGetName(handle)} ({memTotal}MB)")