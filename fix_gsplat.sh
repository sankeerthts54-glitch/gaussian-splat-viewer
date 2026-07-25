#!/bin/bash
set -e

export CUDA_HOME=/usr/local/cuda-12.1
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:/usr/local/cuda-12.1/lib64/stubs:$LD_LIBRARY_PATH

source ~/miniconda/etc/profile.d/conda.sh
conda activate gsplat

echo "CUDA_HOME: $CUDA_HOME"
echo "nvcc version:"
nvcc --version

echo ""
echo "Reinstalling gsplat from source with CUDA support..."
pip install gsplat --no-binary gsplat

echo ""
echo "Done! Testing import..."
python -c "import gsplat; print('gsplat version:', gsplat.__version__)"
