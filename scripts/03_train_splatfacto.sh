#!/usr/bin/env bash
# Script 03: Train 3D Gaussian Splat with nerfstudio splatfacto
# =============================================================
# Usage (inside WSL2, conda activate gsplat):
#   bash scripts/03_train_splatfacto.sh my_scene
#   bash scripts/03_train_splatfacto.sh my_scene --max-num-iterations 50000
#
# What splatfacto is doing:
#   1. Reads your COLMAP output (cameras + sparse point cloud)
#   2. Initializes one 3D Gaussian per sparse point
#   3. Every iteration: renders from a training camera, computes L1+SSIM loss
#      against the real photo, backpropagates gradients through the differentiable
#      rasterizer to update Gaussian positions, covariances, opacities, and SH coefficients
#   4. Densification (every 100 iterations until iter 15k):
#      - Gaussians with high positional gradient → split into 2 smaller Gaussians
#      - Gaussians with high screen-space size → clone them
#      - Gaussians with opacity < threshold → pruned
#   5. At the end: writes a checkpoint + exports a .ply file
#
# RTX 4060 (8GB VRAM) notes:
#   - 30k iterations on a 100-150 image scene: ~30-40 minutes
#   - If you hit OOM: add --pipeline.model.max-num-gaussians 500000
#   - Watch VRAM: nvidia-smi in a second terminal during training

set -e  # exit on any error

# ── CUDA paths (required by gsplat's JIT CUDA compilation) ───────────────────
export CUDA_HOME=/usr/local/cuda-12.1
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:/usr/local/cuda-12.1/lib64/stubs:$LD_LIBRARY_PATH
export MAX_JOBS=4   # limit parallel compile jobs to avoid OOM during first-run CUDA build
# ─────────────────────────────────────────────────────────────────────────────


SCENE_NAME="${1}"
if [ -z "$SCENE_NAME" ]; then
    echo "❌ Usage: bash scripts/03_train_splatfacto.sh <scene_name> [extra ns-train args]"
    echo "   Example: bash scripts/03_train_splatfacto.sh shoe"
    exit 1
fi

# Shift scene name so $@ contains only extra args
shift

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data/$SCENE_NAME"
OUTPUT_DIR="$PROJECT_ROOT/outputs/$SCENE_NAME"

# Determine data format (blender synthetic / COLMAP / nerfstudio-data)
if [ -f "$DATA_DIR/transforms_train.json" ]; then
    DATAPARSER="blender-data"
    echo "  Format:    blender-data (Synthetic / NeRF Blender dataset)"
elif [ -f "$DATA_DIR/transforms.json" ]; then
    DATAPARSER="nerfstudio-data"
    echo "  Format:    nerfstudio-data (Pre-processed sample)"
elif [ -d "$DATA_DIR/sparse/0" ]; then
    DATAPARSER="colmap"
    echo "  Format:    COLMAP sparse reconstruction"
else
    echo "❌ Valid dataset not found at: $DATA_DIR"
    echo "   Expected 'transforms_train.json', 'transforms.json', or 'sparse/0/' directory."
    echo "   Run script 02 or download a sample dataset first."
    exit 1
fi

echo ""
echo "============================================================"
echo "  3DGS Training — Scene: '$SCENE_NAME'"
echo "  nerfstudio splatfacto"
echo "============================================================"
echo "  Data:      $DATA_DIR"
echo "  Output:    $OUTPUT_DIR"
echo "  VRAM:      RTX 4060 (8GB)"
echo ""
echo "  Key hyperparameters:"
echo "    --max-num-iterations 30000"
echo "    densify-until-iter: 15000"
echo "    densify-grad-threshold: 0.0002"
echo ""
echo "  Monitor training:"
echo "    tensorboard --logdir $OUTPUT_DIR"
echo "    (open http://localhost:6006 in browser)"
echo ""
echo "  Press Ctrl+C to stop early (checkpoint is saved every 2000 iters)"
echo "============================================================"
echo ""

# nerfstudio requires the dataparser subcommand at the END of the command
ns-train splatfacto \
    --data "$DATA_DIR" \
    --output-dir "$OUTPUT_DIR" \
    --vis viewer \
    --max-num-iterations 30000 \
    --steps-per-save 2000 \
    --steps-per-eval-image 500 \
    --pipeline.model.num-downscales 0 \
    --pipeline.model.resolution-schedule 250 \
    --pipeline.model.densify-grad-thresh 0.0002 \
    --pipeline.model.cull-alpha-thresh 0.005 \
    --pipeline.model.background-color black \
    "$@" \
    $DATAPARSER
    # ↑ Any extra args you pass go here


echo ""
echo "============================================================"
echo "  ✅ Training complete!"
echo ""
echo "  Next: export to .ksplat for the web viewer:"
echo "    python scripts/04_export_splat.py --scene $SCENE_NAME"
echo "============================================================"
