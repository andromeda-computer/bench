from abc import ABC, abstractmethod


HOST = "127.0.0.1"

class Benchmark:

    def __init__(self):
        pass


class Runtime(ABC):

    def __init__(self, name, url):
        self.name = name
        self.url = url

    @abstractmethod
    def download(self):
        pass

    @abstractmethod
    def run(self):
        pass

class DockerRuntime(Runtime):

    def __init__(self, name, url):
        super().__init__(name, url)

    def download(self):
        # run docker pull on self.url
        pass

    def run(self):
        pass

class LlamafileRuntime(Runtime):

    def __init__(self, name, url):
        super().__init__(name, url)

    def download(self):

        pass

    def run(self):
        # how to handle different model types (llama.cpp, whisper.cpp, etc.)
        # is actually whisperfile runtime? need an input/output top level thing?
        # pattern for that

        # but will also want to handle ngl offloading, number of layers, etc
        pass