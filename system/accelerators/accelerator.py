import abc
import collections
import threading
import time
from typing import List


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
        if hasattr(self, 'thread') and self.thread:
            self.thread.join()