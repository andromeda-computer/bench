# FROM https://github.com/tlkh/asitop/tree/main/asitop

import os
import re
import subprocess
import threading
import time
import psutil

from rich.panel import Panel

from bench.system.accelerators.accelerator import Accelerator

DATE_FORMAT = "%a %b %d %H:%M:%S %Y %z"

class AppleAccelerator(Accelerator):

    def __init__(self):
        if os.geteuid() != 0:
            print("Error: This script must be run as root on MacOS to gather powermetric")
            sys.exit(1)

        self.soc_info = get_soc_info()
        self.ram_metrics = get_ram_metrics_dict()
        self.name = self.soc_info['name']
        self.p_cores = self.soc_info['p_core_count']
        self.e_cores = self.soc_info['e_core_count']
        self.gpu_cores = self.soc_info['gpu_core_count']
        self.cpu_max_power = self.soc_info['cpu_max_power']
        self.gpu_max_power = self.soc_info['gpu_max_power']
        self.power_limit = self.cpu_max_power + self.gpu_max_power
        self.memory = self.ram_metrics['total_GB']
        self.as_power_metrics = AppleSiliconPowermetrics()

        super().__init__()

    def get_panel(self):
        return Panel.fit(
            f'\n[b]Device: {self.name}[/b]\n'
            f'[b]P Cores:[/b] {self.p_cores}\n'
            f'[b]E Cores:[/b] {self.e_cores}\n'
            f'[b]GPU Cores:[/b] {self.gpu_cores}\n'
            f'[b]Power Limit:[/b] {self.power_limit}W',
            title="Apple Device Info",
            border_style="bright_white",
            height=9
        )

    def _get_power_usage(self):
        # sample the latest reading from system power
        return self.as_power_metrics.get_power_usage()['system_power'] / 1000
    
    def get_basic_info_string(self):
        return f"{self.name.replace(' ', '-')}:{self.memory}GB:{self.power_limit}:{self.p_cores}P:{self.e_cores}E:{self.gpu_cores}GPU"

class AppleSiliconPowermetrics:
    def __init__(self):
        self.ane_power = 0
        self.cpu_power = 0
        self.gpu_power = 0
        self.system_power = 0

        print("You will need to put your password in to get power usage for Apple devices")
        self.process = subprocess.Popen(["sudo", "powermetrics", "-i", "10", "--samplers", "cpu_power"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.thread = threading.Thread(target=self.read_output, daemon=True)
        self.thread.start()

        self.last_update = time.time()

    def read_output(self):
        while True:
            output = self.process.stdout.readline()
            if output == '' and self.process.poll() is not None:
                break
            if output:
                self.parse_output(str(output))

    def parse_output(self, output):
        if "Sampled system activity" in output:
            self.last_update = time.time()
            return

        match = re.search(r'\d+(?=\smW)', output)

        if match:
            milliwatts = int(match.group())
            if "Combined Power" in output:
                self.system_power = milliwatts
            elif "CPU Power" in output:
                self.cpu_power = milliwatts
            elif "GPU Power" in output:
                self.gpu_power = milliwatts
            elif "ANE Power" in output:
                self.ane_power = milliwatts
    
    def get_power_usage(self):
        return {
            "ane_power": self.ane_power,
            "cpu_power": self.cpu_power,
            "gpu_power": self.gpu_power,
            "system_power": self.system_power,
            "last_update": self.last_update
        }

def convert_to_GB(value):
    return round(value/1024/1024/1024, 1)

def get_ram_metrics_dict():
    ram_metrics = psutil.virtual_memory()
    swap_metrics = psutil.swap_memory()
    total_GB = convert_to_GB(ram_metrics.total)
    free_GB = convert_to_GB(ram_metrics.available)
    used_GB = convert_to_GB(ram_metrics.total-ram_metrics.available)
    swap_total_GB = convert_to_GB(swap_metrics.total)
    swap_used_GB = convert_to_GB(swap_metrics.used)
    swap_free_GB = convert_to_GB(swap_metrics.total-swap_metrics.used)
    if swap_total_GB > 0:
        swap_free_percent = int(100-(swap_free_GB/swap_total_GB*100))
    else:
        swap_free_percent = None
    ram_metrics_dict = {
        "total_GB": round(total_GB, 1),
        "free_GB": round(free_GB, 1),
        "used_GB": round(used_GB, 1),
        "free_percent": int(100-(ram_metrics.available/ram_metrics.total*100)),
        "swap_total_GB": swap_total_GB,
        "swap_used_GB": swap_used_GB,
        "swap_free_GB": swap_free_GB,
        "swap_free_percent": swap_free_percent,
    }
    return ram_metrics_dict


def get_cpu_info():
    cpu_info = os.popen('sysctl -a | grep machdep.cpu').read()
    cpu_info_lines = cpu_info.split("\n")
    data_fields = ["machdep.cpu.brand_string", "machdep.cpu.core_count"]
    cpu_info_dict = {}
    for l in cpu_info_lines:
        for h in data_fields:
            if h in l:
                value = l.split(":")[1].strip()
                cpu_info_dict[h] = value
    return cpu_info_dict


def get_core_counts():
    cores_info = os.popen('sysctl -a | grep hw.perflevel').read()
    cores_info_lines = cores_info.split("\n")
    data_fields = ["hw.perflevel0.logicalcpu", "hw.perflevel1.logicalcpu"]
    cores_info_dict = {}
    for l in cores_info_lines:
        for h in data_fields:
            if h in l:
                value = int(l.split(":")[1].strip())
                cores_info_dict[h] = value
    return cores_info_dict


def get_gpu_cores():
    try:
        cores = os.popen(
            "system_profiler -detailLevel basic SPDisplaysDataType | grep 'Total Number of Cores'").read()
        cores = int(cores.split(": ")[-1])
    except:
        cores = "?"
    return cores


def get_soc_info():
    cpu_info_dict = get_cpu_info()
    core_counts_dict = get_core_counts()
    try:
        e_core_count = core_counts_dict["hw.perflevel1.logicalcpu"]
        p_core_count = core_counts_dict["hw.perflevel0.logicalcpu"]
    except:
        e_core_count = "?"
        p_core_count = "?"
    soc_info = {
        "name": cpu_info_dict["machdep.cpu.brand_string"],
        "core_count": int(cpu_info_dict["machdep.cpu.core_count"]),
        "cpu_max_power": None,
        "gpu_max_power": None,
        "cpu_max_bw": None,
        "gpu_max_bw": None,
        "e_core_count": e_core_count,
        "p_core_count": p_core_count,
        "gpu_core_count": get_gpu_cores()
    }
    # TDP (power)
    if soc_info["name"] == "Apple M1 Max":
        soc_info["cpu_max_power"] = 30
        soc_info["gpu_max_power"] = 60
    elif soc_info["name"] == "Apple M1 Pro":
        soc_info["cpu_max_power"] = 30
        soc_info["gpu_max_power"] = 30
    elif soc_info["name"] == "Apple M1":
        soc_info["cpu_max_power"] = 20
        soc_info["gpu_max_power"] = 20
    elif soc_info["name"] == "Apple M1 Ultra":
        soc_info["cpu_max_power"] = 60
        soc_info["gpu_max_power"] = 120
    elif soc_info["name"] == "Apple M2":
        soc_info["cpu_max_power"] = 25
        soc_info["gpu_max_power"] = 15
    else:
        soc_info["cpu_max_power"] = 20
        soc_info["gpu_max_power"] = 20
    # bandwidth
    if soc_info["name"] == "Apple M1 Max":
        soc_info["cpu_max_bw"] = 250
        soc_info["gpu_max_bw"] = 400
    elif soc_info["name"] == "Apple M1 Pro":
        soc_info["cpu_max_bw"] = 200
        soc_info["gpu_max_bw"] = 200
    elif soc_info["name"] == "Apple M1":
        soc_info["cpu_max_bw"] = 70
        soc_info["gpu_max_bw"] = 70
    elif soc_info["name"] == "Apple M1 Ultra":
        soc_info["cpu_max_bw"] = 500
        soc_info["gpu_max_bw"] = 800
    elif soc_info["name"] == "Apple M2":
        soc_info["cpu_max_bw"] = 100
        soc_info["gpu_max_bw"] = 100
    else:
        soc_info["cpu_max_bw"] = 70
        soc_info["gpu_max_bw"] = 70
    return soc_info
