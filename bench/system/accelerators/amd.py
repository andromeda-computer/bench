from rich.panel import Panel

from bench.system.accelerators.accelerator import Accelerator
from bench.system.rocml import *

class AMDAccelerator(Accelerator):

    def __init__(self, index):
        self.index = index
        self.name = smi_get_device_name(index)
        self.revision = smi_get_device_revision(index)
        self.memory = smi_get_device_memory_total(index) * 1e-9
        self.power_limit = smi_get_device_power_cap(index)
        super().__init__()

    def get_panel(self):
        return Panel.fit(
            f'\n[b]Device: {self.name}[/b]\n'
            f'[b]Revision: 0x{self.revision:x}[/b]\n'
            f'[b]Memory:[/b] {self.memory:.2f}GB\n'
            f'[b]Power Limit:[/b] {self.power_limit}W',
            title="AMD Device Info",
            border_style="red",
            height=9
        )

    def _get_power_usage(self):
        watts = smi_get_device_average_power(self.index)
        return watts
    
    def get_basic_info_string(self):
        return f"{self.name.replace(' ', '-')}:{self.memory:.2f}GB:{self.power_limit}W"