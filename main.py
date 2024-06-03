import os
from jinja2 import Template
import yaml

from benchmark import LanguageBenchmark
from sys_info import log_sys_info
from utils import kill, url_downloader

import subprocess
import time
import requests

from model import PORT
from rich.console import Console

MODEL_STORE = ".models"
CONFIG_FILE = "config.yaml"

log_sys_info()

# TODO this could be done in a class
# load what models we need from the config.yml file
with open(CONFIG_FILE, 'r') as cfg_file:
    config = yaml.safe_load(cfg_file)
    suites = config['suites']
    runtimes = config['runtimes']
 
# make the .models dir
if not os.path.exists(MODEL_STORE):
    os.makedirs(MODEL_STORE)

to_download = []
# make the appropriate directories for the model types and figure 
# out which models need to be downloaded
for suite in suites:
    dest_dir = os.path.join(MODEL_STORE, suite)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # iterate through the models in this suite
    for model in suites[suite]:
        if (model['runtime'] != "llamafile"):
            print(f"Runtime: {model['runtime']} not supported")
            continue
        
        filename = model['url'].split("/")[-1]
        if os.path.exists(os.path.join(dest_dir, filename)):
            print(f"{filename} already downloaded")
            continue
            
        print(f"Adding {model['url']} to download list")
        to_download.append({"url": model['url'], "dest_dir": dest_dir, "filename": filename})

# only download the models if they are not already downloaded
# print(to_download)
url_downloader(to_download)

suite = "language"
language_benchmark = LanguageBenchmark()
print("\nLanguage")
console = Console()

# Define the column names and their widths
columns = [
    ("MODEL", 25),
    ("PARAMS", 7),
    ("# PROMPT TOKENS", 16),
    ("# GENERATED TOKENS", 20),
    ("PROMPT TOK/SEC", 15),
    ("GENERATION TOK/SEC", 20)
]

# Print the header
header = ""
for col_name, col_width in columns:
    header += f"{col_name:<{col_width}}"
console.print(header)

def print_benchmark_row(result):
    row = ""
    row += f"{result['model']:<{columns[0][1]}}"
    row += f"{result['params']:<{columns[1][1]}}"
    row += f"{result['prompt_tokens']:<{columns[2][1]}}"
    row += f"{result['generated_tokens']:<{columns[3][1]}}"
    row += f"{result['prompt_tps']:<{columns[4][1]}}"
    row += f"{result['generated_tps']:<{columns[5][1]}}"
    console.print(row)

# Create model classes
for model in suites[suite]:
    if (model['runtime'] != "llamafile"):
        continue
    if (suite != "language"):
        continue

    filename = model['url'].split("/")[-1]
    dest_dir = os.path.join(MODEL_STORE, suite)
    llamafile = os.path.join(dest_dir, filename)
    # make sure it's executable
    os.chmod(llamafile, os.stat(llamafile).st_mode | 0o111)

    # run the model
    cmd_str = f"{llamafile} --nobrowser --port {PORT} -ngl 9999"
    try: 
        proc = subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)

        # wait for the server to start
        url = f"http://127.0.0.1:{PORT}/health"
        attempt = 1
        while True:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    break
            except requests.exceptions.ConnectionError as e:
                attempt += 1
                time.sleep(5)

        result = language_benchmark.benchmark_model(Template(model['prompt_template']), model['name'])
        # print(f"{result['model']}\t\t{result['params']}\t{result['prompt_tokens']}\t{result['generated_tokens']}\t{result['prompt_tps']}\t{result['generated_tps']}")
        print_benchmark_row(result)

        kill(proc.pid)
    except:
        kill(proc.pid)



# TODO support all suites
# for suite in suites: