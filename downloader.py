import os

from config import config
from utils import url_downloader

MODEL_STORE = ".models"

def download():
    download_models()
    download_datasets()

def download_models():
    # make the .models dir
    if not os.path.exists(MODEL_STORE):
        os.makedirs(MODEL_STORE)

    to_download = []
    # make the appropriate directories for the model types and figure 
    # out which models need to be downloaded
    for suite in config.suites:
        dest_dir = os.path.join(MODEL_STORE, suite)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        # iterate through the models in this suite
        for model in config.suites[suite]:
            if (model['runtime'] != "llamafile"):
                # TODO add a verbose flag for logging
                # print(f"Runtime: {model['runtime']} not supported")
                continue
            
            filename = model['url'].split("/")[-1]
            if os.path.exists(os.path.join(dest_dir, filename)):
                # print(f"{filename} already downloaded")
                continue
                
            # print(f"Adding {model['url']} to download list")
            to_download.append({"url": model['url'], "dest_dir": dest_dir, "filename": filename})

    url_downloader(to_download)

def download_datasets():
    pass

def install_runtimes():
    pass