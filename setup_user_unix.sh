#!/bin/bash
set -e

echo "=== Starting User Setup ==="

# Set paths explicitly so script can find them
export PATH="/usr/local/cuda-12.1/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH"

echo "1. Installing Miniconda..."
if [ ! -d "$HOME/miniconda" ]; then
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -p $HOME/miniconda
    rm miniconda.sh
fi

export PATH="$HOME/miniconda/bin:$PATH"
conda init bash

echo "2. Creating 'gsplat' conda environment..."
# Accept Conda ToS for automated installations
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main || true
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r || true

# Remove if exists to ensure clean state
conda env remove -n gsplat -y || true
conda create -n gsplat python=3.10 -y

# Activate conda env inside the bash script
source $HOME/miniconda/etc/profile.d/conda.sh
conda activate gsplat

echo "3. Installing PyTorch 2.1.2 for CUDA 12.1..."
pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cu121

echo "4. Installing build tools and project requirements..."
pip install ninja packaging setuptools
cd /mnt/c/Users/sanke/OneDrive/Desktop/Blend
pip install -r requirements.txt

echo "5. Installing nerfstudio..."
pip install nerfstudio

echo "6. Installing tiny-cuda-nn (this takes ~5-10 minutes to compile)..."
pip install git+https://github.com/NVlabs/tiny-cuda-nn/#subdirectory=bindings/torch

echo "=== User Setup Complete ==="
