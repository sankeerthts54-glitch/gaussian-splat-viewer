# WSL2 + CUDA + nerfstudio Setup Guide
# Windows + RTX 4060 (CUDA 13.1, Driver 592.27)

This is your one-time environment setup. Follow each section in order.
Estimated total time: 45-60 minutes (most of it is waiting for downloads).

---

## Step 1 — Install WSL2

Open **PowerShell as Administrator** and run:

```powershell
wsl --install -d Ubuntu-22.04
```

This installs WSL2 with Ubuntu 22.04 LTS. Your machine will prompt you to restart — do it.

After the restart, Ubuntu will launch automatically and ask you to create a username/password.
**Choose something simple** (e.g., your first name, password "1234") — this is just a Linux user, not your Windows account.

**Verify WSL2 is working:**
```powershell
wsl --list --verbose
# Should show Ubuntu-22.04 with VERSION 2
```

---

## Step 2 — Verify CUDA is Visible Inside WSL2

NVIDIA's driver on Windows automatically exposes CUDA to WSL2 — you do NOT need to install a separate CUDA driver in WSL2. Open your Ubuntu terminal and run:

```bash
nvidia-smi
```

You should see your RTX 4060 listed. If not, check that your Windows NVIDIA driver is up to date (it already is — driver 592.27 is recent).

---

## Step 3 — Install the CUDA Toolkit (inside WSL2)

The CUDA *toolkit* (compilers, libraries) is separate from the driver. Install it in WSL2:

```bash
# Add NVIDIA's CUDA repo for Ubuntu 22.04
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update

# Install CUDA Toolkit 12.1 (compatible with PyTorch 2.x and nerfstudio)
sudo apt-get install -y cuda-toolkit-12-1

# Add CUDA to your PATH
echo 'export PATH=/usr/local/cuda-12.1/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

**Verify:**
```bash
nvcc --version
# Should show: Cuda compilation tools, release 12.1
```

---

## Step 4 — Install Python Environment Manager (conda)

We'll use Miniconda to manage the Python environment:

```bash
# Download Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda
echo 'export PATH=$HOME/miniconda/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
conda init bash
source ~/.bashrc
```

**Verify:**
```bash
conda --version
# Should show: conda 24.x.x (or similar)
```

---

## Step 5 — Create the Project Environment

```bash
conda create -n gsplat python=3.10 -y
conda activate gsplat
```

> **Important:** Every time you open a new WSL2 terminal, run `conda activate gsplat` before doing any project work.

---

## Step 6 — Install PyTorch with CUDA 12.1

```bash
pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cu121
```

**Verify GPU is accessible from PyTorch:**
```bash
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
# Expected output:
# True
# NVIDIA GeForce RTX 4060 Laptop GPU
```

If this prints `True`, your environment is correct.

---

## Step 7 — Install nerfstudio

```bash
# Install build dependencies
pip install ninja packaging setuptools

# Install nerfstudio (this takes ~5-10 minutes)
pip install nerfstudio

# Install tiny-cuda-nn (needed for splatfacto, requires compilation — ~10 min)
pip install git+https://github.com/NVlabs/tiny-cuda-nn/#subdirectory=bindings/torch
```

**Verify nerfstudio:**
```bash
ns-train --help
# Should list available training methods including splatfacto
```

---

## Step 8 — Install COLMAP (inside WSL2)

```bash
sudo apt-get install -y colmap
```

**Verify:**
```bash
colmap --version
# Should show: COLMAP 3.x.x
```

> **Note:** The apt version of COLMAP may be slightly older. For the latest features, you can build from source, but the apt version works perfectly for this project.

---

## Step 9 — Install Project Python Dependencies

```bash
# Clone the repo (or navigate to your project directory)
# From WSL2, your Windows files are at /mnt/c/Users/sanke/...
cd /mnt/c/Users/sanke/OneDrive/Desktop/Blend

# Install project dependencies
pip install -r requirements.txt
```

---

## Step 10 — Install ffmpeg (for frame extraction)

```bash
sudo apt-get install -y ffmpeg

# Verify
ffmpeg -version | head -1
# Should show: ffmpeg version 4.x or 5.x or 6.x
```

---

## Accessing Your Windows Files from WSL2

Your Windows `C:\` drive is mounted at `/mnt/c/` inside WSL2.

| Windows Path | WSL2 Path |
|---|---|
| `C:\Users\sanke\OneDrive\Desktop\Blend` | `/mnt/c/Users/sanke/OneDrive/Desktop/Blend` |
| `C:\Videos\my_video.mp4` | `/mnt/c/Videos/my_video.mp4` |

**Pro tip:** You can open your project folder in VS Code with WSL2 integration:
```bash
# Inside WSL2, from your project directory:
code .
```
This opens VS Code on Windows connected to your WSL2 environment — the best of both worlds.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `nvidia-smi` not found in WSL2 | Update Windows NVIDIA driver; restart WSL2 with `wsl --shutdown` then reopen |
| `nvcc` not found | Re-check PATH: `echo $PATH \| grep cuda` |
| `tiny-cuda-nn` compilation fails | Ensure `cuda-toolkit-12-1` is installed and `nvcc --version` shows 12.1 |
| Out of VRAM during training | Reduce image resolution or number of Gaussians (covered in Phase 2 guide) |
| Permission denied on `/mnt/c/...` | WSL2 filesystem permissions issue; run `sudo chmod -R 777 /mnt/c/Users/sanke/OneDrive/Desktop/Blend` |

---

## Environment Summary

After setup, your environment looks like:

```
Windows 11
├── NVIDIA Driver 592.27 (CUDA 13.1 capable)
├── WSL2 (Ubuntu 22.04)
│   ├── CUDA Toolkit 12.1
│   ├── conda environment: gsplat (Python 3.10)
│   │   ├── PyTorch 2.1.2 + CUDA 12.1
│   │   ├── nerfstudio 1.x (splatfacto)
│   │   └── project dependencies
│   ├── COLMAP 3.x
│   └── ffmpeg
└── Project files at /mnt/c/Users/sanke/OneDrive/Desktop/Blend
```

Once this is set up, proceed to the [Capture Guide](capture_guide.md) to shoot your first scene.
