#!/usr/bin/env bash
# Script 00: Download Sample Dataset
# =============================================================
# Usage (inside WSL2, conda activate gsplat):
#   bash scripts/00_download_sample.sh
#
# This script uses nerfstudio's built-in downloader to get a high-quality,
# pre-processed dataset (the "lego" scene). This guarantees a successful 
# first run so you can test the training and web viewer pipeline without
# worrying about camera capture issues.

set -e

echo ""
echo "============================================================"
echo "  Downloading Sample Dataset ('dozer')"
echo "============================================================"
echo ""

# Download the nerfstudio 'dozer' dataset
ns-download-data nerfstudio --capture-name dozer

echo ""
echo "============================================================"
echo "  ✅ Download complete!"
echo "  Data is located at: data/nerfstudio/dozer"
echo ""
echo "  Next step (Train the Splat):"
echo "    bash scripts/03_train_splatfacto.sh nerfstudio/dozer"
echo "============================================================"
