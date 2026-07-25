# 🌌 3D Gaussian Splatting — End-to-End Portfolio Pipeline

> **Real-world scene reconstruction using photogrammetry + neural rendering, viewable live in the browser.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-black?style=for-the-badge&logo=vercel)](https://gaussian-splat-viewer-kmk1.vercel.app/)

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python)](https://python.org)
[![CUDA](https://img.shields.io/badge/CUDA-11.8+-76B900?style=flat&logo=nvidia)](https://developer.nvidia.com/cuda-toolkit)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

<!-- DEMO GIF — replace with your recorded demo -->
<!-- ![Demo](docs/assets/demo.gif) -->

---

## What This Is

A full pipeline from a 2-minute phone video to an interactive 3D scene you can share as a URL.

```
Phone video  →  Frame extraction  →  COLMAP SfM  →  3DGS Training  →  Web Viewer
   (2 min)         (01_extract)       (02_colmap)    (nerfstudio)     (three.js)
```

The scene is represented as **millions of tiny 3D Gaussian "splats"** — not triangles, not voxels. Each splat has a position, shape (covariance ellipsoid), opacity, and view-dependent color (spherical harmonics). Rendering works by projecting them to 2D and alpha-compositing them, which is fast enough for real-time interactive viewing in a browser.

---

## Pipeline Stages

### 1. Data Capture
Short phone video (1-3 min) orbiting around a subject. See [capture guide](docs/capture_guide.md) for exact shooting patterns and common mistakes.

### 2. Frame Extraction
```bash
python scripts/01_extract_frames.py \
  --video path/to/video.mp4 \
  --scene my_scene \
  --fps 2
```
Extracts frames, runs blur detection, outputs to `data/my_scene/input/`.

### 3. COLMAP Structure-from-Motion
```bash
python scripts/02_run_colmap.py --scene my_scene
```
Runs COLMAP feature extraction → matching → sparse reconstruction. Validates pose quality automatically.

### 4. 3DGS Training (nerfstudio)
```bash
bash scripts/03_train_splatfacto.sh my_scene
```
~30-40 minutes on RTX 4060. Outputs trained scene checkpoint.

### 5. Export + Web Viewer
```bash
python scripts/04_export_splat.py --scene my_scene
```
Exports to `.ksplat`, serves from `viewer/`. Deploy to GitHub Pages with one push.

---

## Results

| Scene | Gaussians | Train Time | PSNR |
|---|---|---|---|
| — | — | — | — |

*(Will be filled after first training run)*

---

## How Gaussian Splatting Works

3DGS represents a scene as a collection of 3D Gaussians — think of them as semi-transparent, color-tinted ellipsoids floating in space. The training loop:

1. **Initialize** from the SfM sparse point cloud (each 3D point becomes one Gaussian)
2. **Render** by projecting each Gaussian to the camera plane, sorting front-to-back by depth, and alpha-compositing
3. **Optimize** via gradient descent — the loss is the difference between the rendered image and the real photo
4. **Densify** — Gaussians covering large areas split into smaller ones; transparent Gaussians get pruned

The key insight: because this renderer is differentiable, you can backpropagate through the entire rendering operation and learn both the position/shape and the color of every Gaussian simultaneously.

---

## Stretch Goal: Object Selection & Removal

Click on any part of the scene to select and hide the Gaussians in that region. This demonstrates that the scene is a set of *addressable 3D primitives*, not just pixels — a key architectural property of 3DGS.

---

## What I'd Do Differently at Scale

- **COLMAP bottleneck**: For > 1000 images, exhaustive matching is O(N²). Use hierarchical matching or vocabulary tree matching instead.
- **Streaming large scenes**: A 500k-Gaussian scene is 50+ MB. At scale, use progressive loading with level-of-detail tiers.
- **Training stability**: The original 3DGS densification heuristic is empirical and can fail on thin structures. Newer methods (2DGS, Scaffold-GS) address this with better geometry priors.
- **Editable representations**: Storing Gaussians in a structured format (e.g., by object segment) from the start enables downstream editing without expensive re-training.

---

## Setup

See [docs/wsl2_setup.md](docs/wsl2_setup.md) for the full environment setup guide (Windows + WSL2 + CUDA).

**Quick install (inside WSL2 Ubuntu):**
```bash
git clone https://github.com/your-username/gaussian-splat-portfolio
cd gaussian-splat-portfolio
pip install -r requirements.txt
```

---

## Repo Structure

```
├── scripts/               # Pipeline automation scripts
│   ├── 01_extract_frames.py
│   ├── 02_run_colmap.py
│   ├── 03_train_splatfacto.sh
│   ├── 04_export_splat.py
│   └── utils/
│       ├── check_colmap.py
│       └── fps_advisor.py
├── viewer/                # Static web viewer (deployable to GitHub Pages)
│   ├── index.html
│   └── src/
├── docs/                  # Guides and explainers
│   ├── capture_guide.md
│   └── wsl2_setup.md
├── data/                  # Input frames (git-ignored)
├── outputs/               # Training outputs (git-ignored)
├── exports/               # .ksplat exports (git LFS or CDN)
└── notebooks/             # Kaggle/Colab alternative pipeline
```

---

## License

MIT — use this freely for learning and portfolio purposes.
