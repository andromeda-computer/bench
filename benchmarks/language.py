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