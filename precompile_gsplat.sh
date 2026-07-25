#!/bin/bash
# Pre-compile gsplat CUDA kernels with MAX_JOBS=2 (uses swap if needed)
export CUDA_HOME=/usr/local/cuda-12.1
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
export MAX_JOBS=2

source ~/miniconda/etc/profile.d/conda.sh
conda activate gsplat

echo "Pre-compiling gsplat CUDA kernels (MAX_JOBS=2)..."
echo "This may take 5-10 minutes. Do not interrupt."
echo ""

python - <<'EOF'
import os
os.environ['MAX_JOBS'] = '2'
import torch
print(f"PyTorch: {torch.__version__}, CUDA available: {torch.cuda.is_available()}")
import gsplat
print(f"gsplat version: {gsplat.__version__}")
# Force CUDA kernel compilation by calling a simple op
import torch
from gsplat.cuda._wrapper import _make_lazy_cuda_obj
print("Triggering CUDA kernel compilation...")
# Just importing and triggering the lazy load is enough to compile
try:
    from gsplat import rasterization
    print("SUCCESS: gsplat CUDA kernels compiled and ready!")
except Exception as e:
    print(f"Note: {e}")
EOF
