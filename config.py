import abc
import json
import os

import requests

from utils import url_downloader

CONFIG_FILE = "config.yaml"
DATASET_STORE_DIR = ".datasets"
MODEL_STORE_DIR = ".models"
PORT = 8314

class Dataset(abc.ABC):

    def __init__(self, suite, dataset):
        self.suite = suite
        self.dataset = dataset

        self.name = dataset['name']
        self.url = dataset['url']
        self.source = dataset['source']

        self.dir = os.path.join(DATASET_STORE_DIR, suite, self.name)

    def download(self):
        os.makedirs(self.dir, exist_ok=True)

        if self.source == "hf-api":
            self._download_hf_api()
        elif self.source == "andromeda":
            self._download_andromeda()
        else:
            print(f"Source: {self.source} not supported")

    @abc.abstractmethod
    def _download_hf_api(self):
        pass

    @abc.abstractmethod
    def _download_andromeda(self):
        pass

class PromptDataset(Dataset):

    def _download_hf_api(self):
        prompt_file = os.path.join(self.dir, "prompts.json")
        if os.path.exists(prompt_file):
            return

        key = self.dataset['key']

        response = requests.get(self.url)
        jsonResponse = response.json()

        prompts = []
        for row in jsonResponse['rows']:
            prompts.append(row['row'][key])
        
        # write a json file of the array of prompts
        with open(os.path.join(self.dir, "prompts.json"), "w") as f:
            f.write(json.dumps(prompts))

    def _download_andromeda(self):
        return super()._download_andromeda()

class FileDataset(Dataset):

    def _download_hf_api(self):
        key = self.dataset['key']

        response = requests.get(self.url)
        json = response.json()

        for i, row in enumerate(json['rows']):
            url = row['row'][key]
            ext = url.split('.')[-1]
            filename = f"{i}.{ext}"
            if (os.path.exists(os.path.join(self.dir, filename))):
                continue

            url_downloader([{ "url": url, "dest_dir": self.dir, "filename": filename }])

    def _download_andromeda(self):
        response = requests.get(f"{self.url}/metadata.json")
        metadata = response.json()

        for row in metadata:
            url = f"{self.url}/{row}"
            filename = row
            if (os.path.exists(os.path.join(self.dir, filename))):
                continue
            
            url_downloader([{ "url": url, "dest_dir": self.dir, "filename": filename }])

# TODO make this a base class, and then create a subclass for each type of model
class Model():

    def __init__(self, cfg):
        self.name = cfg['name']
        self.type = cfg['type']
        self.runtime = cfg['runtime']
        self.url = cfg['url']
        self.filename = cfg['url'].split("/")[-1]
        self.prompt_template = cfg.get('prompt_template')
        self.stop = cfg.get('stop')
        self.dir = os.path.join(MODEL_STORE_DIR, self.type)

    def download(self):

        if self.runtime == "llamafile":
            self._download_llamafile()
        elif self.runtime == "docker":
            self._download_docker()
        else:
            print(f"Runtime: {self.runtime} not supported")

    def _download_llamafile(self):
        os.makedirs(self.dir, exist_ok=True)

        llamafile = os.path.join(self.dir, self.filename)

        if (os.path.exists(llamafile)):
            return

        url_downloader([{ "url": self.url, "dest_dir": self.dir, "filename": self.filename }])

        os.chmod(llamafile, 0o755)

    def _download_docker(self):
        pass

# TODO TIME TO FIRST BYTE OF RESPONSE