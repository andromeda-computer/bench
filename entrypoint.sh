#!/bin/bash

CHECKPOINTS_DIR="/app/ComfyUI/models/checkpoints"

# Function to download file if it doesn't exist
download_if_not_exists() {
    local url=$1
    local filename=$2
    if [ ! -f "$CHECKPOINTS_DIR/$filename" ]; then
        echo "Downloading $filename..."
        curl -L -o "$CHECKPOINTS_DIR/$filename" "$url" \
             --progress-bar \
             --retry 3 \
             --retry-delay 5 \
             --retry-max-time 60
        echo "Download complete: $filename"
    else
        echo "$filename already exists, skipping download."
    fi
}

# Download checkpoint files
download_if_not_exists "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" "sd_xl_base_1.0.safetensors"
download_if_not_exists "https://huggingface.co/ByteDance/SDXL-Lightning/resolve/main/sdxl_lightning_4step.safetensors" "sdxl_lightning_4step.safetensors"

# Start ComfyUI in the background
python3 /app/ComfyUI/main.py &

# Start an interactive shell
/bin/bash