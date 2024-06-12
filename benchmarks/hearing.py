class HearingBenchmarkResult():

    # TODO json really should be an adapter in the runtime instead.
    def __init__(self, json):
        self.text = json['text']
        self.input_seconds = json['duration']
        self.transcribe_time = json['transcribe_time'] / 1000
        self.speedup = self.input_seconds / self.transcribe_time