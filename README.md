# andromeda-bench

Benchmarks a bunch of AI workloads. Currently:

* LLM (via llamafile/llama.cpp runtime)
* Vision Models (via llamafile/llama.cpp runtime)
* Speech To Text Models (via whisperfile/whisper.cpp runtime)
* Diffusion Models (via ComfyUI)

Collects the following info: TBD write this

## Running

0. not necessary but create a venv and activate it (`python -m venv env && source ./env/bin/activate`)
1. `pip install -r requirements.txt`
2. `python main.py --fast`

## NVIDIA GPU's

make sure cuda is installed. 

on ubuntu 22.04 lts try this

```
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-5

# For older GPUs (or to be safe)
sudo apt-get install -y cuda-drivers

# For newer GPUs (or to be OSS friendly)
# sudo apt-get install -y nvidia-driver-555-open
# or if you hate open source
# sudo apt-get install -y cuda-drivers-555

# because its better than nvidia-smi directly
sudo apt install nvtop

# add to bash rc
export PATH="/usr/local/cuda-12.5/bin:$PATH"

sudo reboot
```

## AMD GPU's

make sure you've installed rocm (details how coming soon)

make sure `libstdc++-12-dev` is installed `sudo apt install libstdc++-12-dev`

## Apple Devices

You shouldn't need to do anything. Just run with `sudo python main.py --fast` instead. If you run without sudo, power metrics from the system cannot be captured. In the future you may optionally not collect power metrics, but for now you must.

## Dockerfile
