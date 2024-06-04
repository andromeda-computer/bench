# import os

# import requests

# from config import config
# from utils import url_downloader

# MODEL_STORE = ".models"
# DATASET_STORE = ".datasets"

# class Downloader():

#     def __init__(self):
#         pass

#     def download(self):
#         self.download_models()
#         self.download_datasets()

#     def download_models(self):
#         # make the .models dir
#         if not os.path.exists(MODEL_STORE):
#             os.makedirs(MODEL_STORE)

#         to_download = []
#         # make the appropriate directories for the model types and figure 
#         # out which models need to be downloaded
#         for suite in config.suites:
#             dest_dir = os.path.join(MODEL_STORE, suite)
#             if not os.path.exists(dest_dir):
#                 os.makedirs(dest_dir)

#             # iterate through the models in this suite
#             for model in config.suites[suite]:
#                 if (model['runtime'] != "llamafile"):
#                     # TODO add a verbose flag for logging
#                     # print(f"Runtime: {model['runtime']} not supported")
#                     continue
                
#                 filename = model['url'].split("/")[-1]
#                 if os.path.exists(os.path.join(dest_dir, filename)):
#                     # print(f"{filename} already downloaded")
#                     continue
                    
#                 # print(f"Adding {model['url']} to download list")
#                 to_download.append({"url": model['url'], "dest_dir": dest_dir, "filename": filename})

#         url_downloader(to_download)

#     def download_datasets(self):
#         # make the .datasets dir
#         if not os.path.exists(DATASET_STORE):
#             os.makedirs(DATASET_STORE)
        
#         # make the appropriate directories for the dataset types and figure
#         # out which datasets need to be downloaded
#         for suite in config.datasets:
#             dest_dir = os.path.join(DATASET_STORE, suite)
#             if not os.path.exists(dest_dir):
#                 os.makedirs(dest_dir)

#             # todo iteratre through the dataset in the suite and save the files
#             for dataset in config.datasets[suite]:
#                 dir = os.path.join(dest_dir, dataset['name'])
#                 if not os.path.exists(dir):
#                     os.makedirs(dir)

#                 if (dataset['source'] == "hf-api"):
#                     self._download_hf_api_dataset(dataset, dir)
#                 elif (dataset['source'] == "andromeda"):
#                     self._download_andromeda_dataset(dataset, dir)
#                 else:
#                     raise Exception(f"Unknown dataset source: {dataset['source']}")

#     def _download_hf_api_dataset(self, dataset, dest_dir):


#     def _download_andromeda_dataset(self, dataset, dest_dir):

        

# downloader = Downloader()

# def install_runtimes():
#     pass