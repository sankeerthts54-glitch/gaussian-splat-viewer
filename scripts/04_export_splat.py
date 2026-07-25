"""
Script 04: Export Trained Gaussian Splat to Web Viewer Format
=============================================================
Finds the latest nerfstudio checkpoint for a scene, exports it to .ply,
then converts to .ksplat (compact binary format for the web viewer).

Usage (inside WSL2, conda activate gsplat):
    python scripts/04_export_splat.py --scene my_scene
    python scripts/04_export_splat.py --scene my_scene --checkpoint path/to/config.yml

What this does:
    1. Finds the most recent nerfstudio training run for the scene
    2. Uses `ns-export gaussian-splat` to write a .ply file
    3. Converts .ply → .ksplat using the GaussianSplats3D converter
       (.ksplat is a compact binary format: sorted by distance, SH compressed,
        ~3x smaller than raw .ply — faster to download in the browser)
    4. Copies the .ksplat to viewer/splats/ so the web viewer can load it

File format notes:
    .ply  - Standard polygon format; each Gaussian is one "vertex" with
            position (xyz), opacity, SH coefficients, and covariance as properties.
            Human-readable header but binary body. ~15-50 MB for a typical scene.
    
    .ksplat - Kenji Tawa's compact splat format. Pre-sorted by distance from
              scene center (speeds up web rendering). Fixed-size records.
              Typically ~5-15 MB for a typical scene.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


# ─── Helpers ─────────────────────────────────────────────────────────────────

def find_latest_config(output_dir: Path) -> Path:
    """
    Find the most recent nerfstudio config.yml for a scene.
    nerfstudio writes: outputs/{scene}/splatfacto/{timestamp}/config.yml
    """
    splatfacto_dir = output_dir / "splatfacto"
    if not splatfacto_dir.exists():
        return None
    
    # Find all config.yml files, pick the most recently modified
    configs = sorted(splatfacto_dir.rglob("config.yml"), key=lambda p: p.stat().st_mtime)
    if not configs:
        return None
    
    return configs[-1]  # most recent


def export_ply(config_path: Path, export_dir: Path, scene_name: str) -> Path:
    """Use nerfstudio's ns-export to write a .ply file."""
    export_dir.mkdir(parents=True, exist_ok=True)
    safe_name = scene_name.replace("/", "_")
    ply_path = export_dir / f"{safe_name}.ply"
    
    print(f"\n  Exporting .ply from nerfstudio checkpoint...")
    print(f"  Config: {config_path}")
    print(f"  Output: {ply_path}")
    
    cmd = [
        "ns-export", "gaussian-splat",
        "--load-config", str(config_path),
        "--output-dir", str(export_dir),
    ]
    
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("❌ ns-export failed.")
        print("   Make sure nerfstudio is installed and the training completed successfully.")
        sys.exit(1)
    
    # nerfstudio writes splat.ply by default — rename to scene name
    default_out = export_dir / "splat.ply"
    if default_out.exists() and not ply_path.exists():
        default_out.rename(ply_path)
    
    if not ply_path.exists():
        # Try the default name
        ply_path = export_dir / "splat.ply"
    
    if not ply_path.exists():
        print(f"❌ Could not find exported .ply at {ply_path}")
        sys.exit(1)
    
    size_mb = ply_path.stat().st_size / (1024 * 1024)
    print(f"  ✅ .ply exported: {size_mb:.1f} MB")
    return ply_path


def convert_ply_to_ksplat(ply_path: Path, ksplat_path: Path) -> None:
    """
    Convert .ply → .ksplat using the GaussianSplats3D Node.js converter.
    
    .ksplat format details:
        - Each Gaussian stored as a fixed-size binary record
        - Pre-sorted by distance from scene center (helps web renderer)
        - SH coefficients truncated to degree 1 (saves space, looks fine for most scenes)
        - Roughly 3x smaller than raw .ply
    
    Requirements: Node.js must be installed in WSL2
        sudo apt-get install nodejs npm
    """
    print(f"\n  Converting .ply → .ksplat...")
    print(f"  Input:  {ply_path}")
    print(f"  Output: {ksplat_path}")
    
    # Check if Node.js is available
    if shutil.which("node") is None:
        print("\n  ⚠️  Node.js not found. Installing...")
        subprocess.run(["sudo", "apt-get", "install", "-y", "nodejs", "npm"], check=True)
    
    # Install the converter if needed (one-time)
    converter_check = subprocess.run(
        ["node", "-e", "require('@mkkellogg/gaussian-splats-3d')"],
        capture_output=True
    )
    if converter_check.returncode != 0:
        print("  Installing gaussian-splats-3d converter locally...")
        subprocess.run(["npm", "install", "@mkkellogg/gaussian-splats-3d"], check=True)
    
    # Run the conversion script
    convert_script = Path(__file__).parent / "utils" / "ply_to_ksplat.mjs"
    
    if not convert_script.exists():
        print(f"❌ Converter script not found: {convert_script}")
        print("   This script should have been created with the repo setup.")
        sys.exit(1)
    
    result = subprocess.run([
        "node", str(convert_script),
        str(ply_path), str(ksplat_path)
    ])
    
    if result.returncode != 0:
        print("❌ .ply → .ksplat conversion failed.")
        print("   Falling back: copy the .ply directly to viewer/splats/")
        print("   Note: The web viewer also supports .ply natively.")
        return False
    
    size_mb = ksplat_path.stat().st_size / (1024 * 1024)
    print(f"  ✅ .ksplat created: {size_mb:.1f} MB")
    return True


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Export a trained nerfstudio splat to .ksplat for the web viewer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument("--scene",      type=str,  required=True, help="Scene name")
    parser.add_argument("--checkpoint", type=Path, default=None,
                        help="Path to nerfstudio config.yml (auto-detected if omitted)")
    parser.add_argument("--no-convert", action="store_true",
                        help="Skip .ksplat conversion (just export .ply)")
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    output_dir   = project_root / "outputs"  / args.scene
    export_dir   = project_root / "exports"  / args.scene
    viewer_splat = project_root / "viewer" / "splats"
    
    viewer_splat.mkdir(parents=True, exist_ok=True)
    
    # ── Find config ────────────────────────────────────────────────────────────
    if args.checkpoint:
        config_path = args.checkpoint
    else:
        config_path = find_latest_config(output_dir)
    
    if config_path is None or not config_path.exists():
        print(f"❌ No nerfstudio config found for scene '{args.scene}'.")
        print(f"   Expected: outputs/{args.scene}/splatfacto/*/config.yml")
        print(f"   Run training first: bash scripts/03_train_splatfacto.sh {args.scene}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"  Splat Export — Scene: '{args.scene}'")
    print(f"{'='*60}")
    
    safe_scene = args.scene.replace("/", "_")
    
    # ── Export .ply ────────────────────────────────────────────────────────────
    ply_path = export_ply(config_path, export_dir, safe_scene)
    
    # ── Convert to .ksplat ─────────────────────────────────────────────────────
    if not args.no_convert:
        ksplat_path = export_dir / f"{safe_scene}.ksplat"
        success = convert_ply_to_ksplat(ply_path, ksplat_path)
        
        if success:
            # Copy to viewer
            dest = viewer_splat / f"{safe_scene}.ksplat"
            shutil.copy2(ksplat_path, dest)
            print(f"\n  ✅ Copied to web viewer: {dest}")
        else:
            # Fallback copy .ply to viewer
            dest = viewer_splat / f"{safe_scene}.ply"
            shutil.copy2(ply_path, dest)
            print(f"\n  ✅ Copied .ply to web viewer (fallback): {dest}")
    else:
        # Copy .ply to viewer
        dest = viewer_splat / f"{safe_scene}.ply"
        shutil.copy2(ply_path, dest)
        print(f"\n  ✅ Copied .ply to web viewer: {dest}")
    
    print(f"\n{'─'*60}")
    print(f"  Next steps:")
    print(f"    1. Open viewer/index.html in your browser to test locally")
    print(f"    2. Update viewer/src/main.js to point to 'splats/{safe_scene}.ksplat'")
    print(f"    3. Push to GitHub to trigger auto-deploy to GitHub Pages")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
