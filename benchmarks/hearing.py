

class HearingBenchmarkResult():

    # TODO json really should be an adapter in the runtime instead.
    def __init__(self, json, time, power):
        self.text = json['text']
        self.input_seconds = json['duration']
        self.transcribe_time = time
        self.speedup = self.input_seconds / self.transcribe_time
        self.speedup_watt = self.speedup / power[2]