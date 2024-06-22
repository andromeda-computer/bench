
import os

from bench import logger
from bench.config import MODEL_STORE_DIR
from bench.utils import url_downloader

class Model():

    def __init__(self, cfg, variant = None):
        self.variant = variant
        self.name = cfg['name']
        self.tag = self.name
        self.type = cfg['type']
        self.runtime = cfg['runtime']
        self.quant = cfg.get('quant', 'unknown')
        self.url = cfg['url']
        self.projector_url = cfg.get('projector_url', None)
        self.filename = cfg['url'].split("/")[-1]
        self.projector_filename = f"{self.name}.mmproj" if self.projector_url else None
        self.prompt_template = cfg.get('prompt_template')
        self.stop = cfg.get('stop')
        self.dir = os.path.join(MODEL_STORE_DIR, self.type)
        self.path = os.path.join(self.dir, self.filename)
        self.projector_path = os.path.join(self.dir, self.projector_filename) if self.projector_url else None

        # TODO this really needs to be broken out into different classes???
        # for comfy runtime
        # TODO should validate that they exist for comfy
        self.steps = cfg.get('steps', None)
        self.scheduler = cfg.get('scheduler', None)
        self.cfg_scale = cfg.get('cfg_scale', None)

        if variant:
            self.resolution = variant.get('resolution', None)
            self.tag = f"{self.name}-{self.resolution}"

        self._download()

    def _download(self):
        if self.runtime == "llamafile" or self.runtime == "whisperfile":
            to_download = [{"url": self.url, "dest_dir": self.dir, "filename": self.filename}]

            if self.projector_url:
                to_download.append({"url": self.projector_url, "dest_dir": self.dir, "filename": self.projector_filename})

            url_downloader(to_download)
        elif self.runtime == "docker":
            self._download_docker()
        elif self.runtime == "comfy":
            self._download_comfy()
        else:
            logger.warning(f"Runtime: {self.runtime} not supported")

    def _download_from_url(self):
        url_downloader([{ "url": self.url, "dest_dir": self.dir, "filename": self.filename }])

    def _download_docker(self):
        pass

    def _download_comfy(self):
        pass