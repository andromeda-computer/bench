import yaml

CONFIG_FILE = "config.yaml"

class ConfigModel():

    def __init__(self):
        pass

class Config():

    def __init__(self):
        with open(CONFIG_FILE, 'r') as cfg_file:
            self.raw = yaml.safe_load(cfg_file)
            self.suites = self.raw['suites']
            self.runtimes = self.raw['runtimes']
            self.datasets = self.raw['datasets']

config = Config()