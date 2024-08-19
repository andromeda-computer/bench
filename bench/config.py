import os

ANDROMEDA_BENCH_VERSION="0.0.2"

CONFIG_FILE = "config.yaml"
BASE_STORE_DIR = ".store"
DATASET_STORE_DIR = os.path.join(BASE_STORE_DIR, "datasets")
RUNTIME_STORE_DIR = os.path.join(BASE_STORE_DIR, "runtimes")
MODEL_STORE_DIR = os.path.join(BASE_STORE_DIR, "models")
RUN_STORE_DIR = os.path.join(BASE_STORE_DIR, "runs")
PORT = 8314
HOST = "localhost"

def update_store_dirs(base_dir):
    global BASE_STORE_DIR, DATASET_STORE_DIR, RUNTIME_STORE_DIR, MODEL_STORE_DIR, RUN_STORE_DIR
    BASE_STORE_DIR = base_dir
    DATASET_STORE_DIR = os.path.join(BASE_STORE_DIR, "datasets")
    RUNTIME_STORE_DIR = os.path.join(BASE_STORE_DIR, "runtimes")
    MODEL_STORE_DIR = os.path.join(BASE_STORE_DIR, "models")
    RUN_STORE_DIR = os.path.join(BASE_STORE_DIR, "runs")