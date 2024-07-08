import abc
import json
import os

import requests

from bench import logger
from bench.config import DATASET_STORE_DIR
from bench.utils import url_downloader


class Dataset(abc.ABC):

    def __init__(self, suite, dataset, **kwargs):
        self.suite = suite
        self.dataset = dataset

        self.name = dataset['name']
        self.url = dataset['url']
        self.source = dataset['source']

        self.dir = os.path.join(DATASET_STORE_DIR, suite, self.name)

        self._download()

        # TODO this feels like a massive hack but it does work
        if kwargs.get("full"):
            len = None
        if kwargs.get("fast"):
            len = 1
        else:
            len = 5
            if suite == "language":
                len = 2

        self.data = self._load(len)

    def _download(self):
        if self.source == "hf-api":
            self._download_hf_api()
        elif self.source == "andromeda":
            self._download_andromeda()
        else:
            logger.warning(f"Source: {self.source} not supported")

    @abc.abstractmethod
    def _load(self, len = None):
        pass

    @abc.abstractmethod
    def _download_hf_api(self):
        pass

    @abc.abstractmethod
    def _download_andromeda(self):
        pass

class CreationDataset(Dataset):

    def _load(self, len = None):
        with open(os.path.join(self.dir, "prompts.json"), "r") as f:
            return json.load(f)[:len]

    def _download_hf_api(self):
        return super()._download_hf_api()

    def _download_andromeda(self):
        url_downloader([{ "url": self.url, "dest_dir": self.dir, "filename": "prompts.json" }])

class PromptDataset(Dataset):

    def _load(self, len = None):
        with open(os.path.join(self.dir, "prompts.json"), "r") as f:
            return json.load(f)[:len]

    def _download_hf_api(self):
        prompt_file = os.path.join(self.dir, "prompts.json")
        if os.path.exists(prompt_file):
            return

        os.makedirs(self.dir, exist_ok=True)

        # TODO url downloader?
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

    def _load(self, len = None):
        data = []
        for f in sorted(os.listdir(self.dir))[:len]:
            data.append(self.DatasetItem(os.path.join(self.dir, f), f))

        return data
    
    class DatasetItem():
        def __init__(self, path, name):
            self.path = path
            self.name = name

    def _download_hf_api(self):
        key = self.dataset['key']

        response = requests.get(self.url)
        json = response.json()

        for i, row in enumerate(json['rows']):
            url = row['row'][key]
            ext = url.split('.')[-1]
            filename = f"{i}.{ext}"

            url_downloader([{ "url": url, "dest_dir": self.dir, "filename": filename }])

    def _download_andromeda(self):
        response = requests.get(f"{self.url}/metadata.json")
        metadata = response.json()

        for row in metadata:
            url = f"{self.url}/{row}"
            filename = row
            
            url_downloader([{ "url": url, "dest_dir": self.dir, "filename": filename }])