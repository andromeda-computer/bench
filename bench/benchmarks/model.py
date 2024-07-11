from bench import logger
from bench import config
import os

from bench.downloader import get_downloader

class Model():

    def __init__(self, cfg):
        self.name = cfg['name']
        # self.tag = self.name
        self.runtime = cfg['runtime']
        self.type = cfg['type']
        self.quant = cfg.get('quant', 'unknown')
        self.url = cfg['url']
        self.projector_url = cfg.get('projector_url', None)
        self.filename = cfg['url'].split("/")[-1]
        self.projector_filename = f"{self.name}.mmproj" if self.projector_url else None
        self.prompt_template = cfg.get('prompt_template')
        self.stop = cfg.get('stop')
        self.dir = os.path.join(config.MODEL_STORE_DIR, self.type)
        self.path = os.path.join(self.dir, self.filename)
        self.projector_path = os.path.join(self.dir, self.projector_filename) if self.projector_url else None

        # TODO this really needs to be broken out into different classes???
        # for comfy runtime
        # TODO should validate that they exist for comfy
        self.steps = cfg.get('steps', None)
        self.scheduler = cfg.get('scheduler', None)
        self.cfg_scale = cfg.get('cfg_scale', None)

        # TODO this is part of BenchmarkTest now.
        # if variant:
        #     self.resolution = variant.get('resolution', None)
        #     self.tag = f"{self.name}-{self.resolution}"

        self._download()

    def _download(self):
        runtime_name = self.runtime
        if runtime_name == "llamafile" or runtime_name == "whisperfile":
            downloader = get_downloader()

            downloader.add_download({"url": self.url, "dest_dir": self.dir, "filename": self.filename})
            # to_download = [{"url": self.url, "dest_dir": self.dir, "filename": self.filename}]

            if self.projector_url:
                downloader.add_download({"url": self.projector_url, "dest_dir": self.dir, "filename": self.projector_filename})
                # to_download.append({"url": self.projector_url, "dest_dir": self.dir, "filename": self.projector_filename})

            # url_downloader(to_download)
        elif runtime_name == "docker":
            self._download_docker()
        elif runtime_name == "comfy":
            self._download_comfy()
        else:
            logger.warning(f"Runtime: {runtime_name} not supported")

    def _download_from_url(self):
        get_downloader().add_download({"url": self.url, "dest_dir": self.dir, "filename": self.filename})
        # url_downloader([{ "url": self.url, "dest_dir": self.dir, "filename": self.filename }])

    def _download_docker(self):
        pass

    def _download_comfy(self):
        pass