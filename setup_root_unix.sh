#!/bin/bash
set -e

echo "=== Starting Root Setup ==="
export DEBIAN_FRONTEND=noninteractive

echo "1. Installing system dependencies (ffmpeg, colmap, nodejs, npm)..."
apt-get update
apt-get install -y wget bzip2 ca-certificates git build-essential colmap ffmpeg nodejs npm

echo "2. Installing CUDA Toolkit 12.1..."
wget -q https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
dpkg -i cuda-keyring_1.1-1_all.deb
apt-get update
apt-get install -y cuda-toolkit-12-1

echo "3. Installing KSplat converter globally..."
npm install -g @mkkellogg/gaussian-splats-3d

echo "=== Root Setup Complete ==="
