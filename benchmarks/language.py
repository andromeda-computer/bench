from logger import logger

class LanguageBenchmarkResult:

    def __init__(self, prompt, json, response, ttft):
        timings = json['timings']

        self.prompt = prompt
        self.t_prompt_eval = timings['prompt_ms']
        self.t_generation = timings['predicted_ms']
        self.t_total = self.t_prompt_eval + self.t_generation
        self.n_prompt_tokens = timings['prompt_n']
        self.n_generated_tokens = timings['predicted_n']
        self.prompt_tps = timings['prompt_per_second']
        self.generated_tps = timings['predicted_per_second']
        self.response = response
        self.ttft = ttft
        # self.power_raw = power

        # self.avg_watts = sum(sample.watts for sample in power) / len(power)

        # # TODO improve this calculation by using the timings we got back from the 
        # # response, in addition to the direct power sample data.
        # self.prompt_tps_watt = self.prompt_tps / self.avg_watts
        # self.generated_tps_watt = self.generated_tps / self.avg_watts