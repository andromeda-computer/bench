class LanguageBenchmarkResult:

    def __init__(self, prompt, json, power):
        timings = json['timings']

        self.prompt = prompt
        self.t_prompt_eval = timings['prompt_ms']
        self.t_generation = timings['predicted_ms']
        self.t_total = self.t_prompt_eval + self.t_generation
        self.n_prompt_tokens = timings['prompt_n']
        self.n_generated_tokens = timings['predicted_n']
        self.prompt_tps = timings['prompt_per_second']
        self.generated_tps = timings['predicted_per_second']
        self.response = json['content']
        self.power_raw = power

        # TODO improve this calculation by monitoring continously in python
        # then can more accurately get the start/stop times and calculate. 
        # Can be done at the ms level probably?
        # TODO we should be able to skip this and not use it at all.
        if power[2] == 0:
            print("WARNING: Power is 0, setting prompt_tps_watt and generated_tps_watt to 0. Power readings will be inaccurate")
            # print("RAW POWER READING", power, self.prompt, self.response)
            self.prompt_tps_watt = 0
            self.generated_tps_watt = 0
        else:
            self.prompt_tps_watt = self.prompt_tps / power[2]
            self.generated_tps_watt = self.generated_tps / power[2]