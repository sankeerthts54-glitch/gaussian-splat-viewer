"""
Script 02: COLMAP Structure-from-Motion Pipeline
==================================================
Automates the full COLMAP pipeline: feature extraction → matching → sparse
reconstruction. Validates output quality and prints a clear summary.

Usage (inside WSL2, conda activate gsplat):
    python scripts/02_run_colmap.py --scene my_scene
    python scripts/02_run_colmap.py --scene my_scene --matcher sequential  # for video frames

What's happening (explained):
    Stage 1 — Feature Extraction:
        COLMAP detects SIFT keypoints in every image. SIFT finds corners, blobs,
        and edges that are distinctive and reproducible across viewpoints.
        Output: keypoints stored in database.db

    Stage 2 — Feature Matching:
        COLMAP compares features across image pairs to find correspondences
        (the same real-world point appearing in two photos).
        - exhaustive_matcher: all N*(N-1)/2 pairs — best quality, slow for N>200
        - sequential_matcher: assumes images are in capture order (good for video)
        Output: matches stored in database.db

    Stage 3 — Sparse Reconstruction (Mapper):
        Incremental Structure-from-Motion:
        1. Find the best initial image pair (maximum inlier matches)
        2. Triangulate their shared points into 3D
        3. Incrementally register new cameras (PnP + RANSAC)
        4. Add new 3D points from new cameras
        5. Run bundle adjustment periodically to refine everything
        Output: sparse/0/ with cameras.bin, images.bin, points3D.bin
"""

import argparse
import struct
import subprocess
import sys
from pathlib import Path


# ─── COLMAP command helpers ───────────────────────────────────────────────────

def run_colmap(args: list[str], step_name: str) -> None:
    """Run a COLMAP command and raise on failure."""
    print(f"\n{'─'*60}")
    print(f"  COLMAP Stage: {step_name}")
    print(f"  Command: colmap {' '.join(args[:3])}...")
    print(f"{'─'*60}")
    
    cmd = ["colmap"] + args
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print(f"\n❌ COLMAP failed at stage: {step_name}")
        print("   Common causes:")
        print("   - Too few images / too little overlap")
        print("   - Blurry or featureless images (run 01_extract_frames.py first)")
        print("   - COLMAP not installed (sudo apt-get install colmap)")
        sys.exit(1)
    
    print(f"  ✅ {step_name} complete.")


# ─── Result parsing and validation ───────────────────────────────────────────

def read_colmap_binary_header(path: Path) -> dict:
    """
    Read basic stats from COLMAP binary files (images.bin, points3D.bin).
    
    COLMAP binary format: starts with uint64 count, then struct entries.
    We only read the count (first 8 bytes) to avoid parsing the full format.
    """
    if not path.exists():
        return {"exists": False}
    
    with open(path, "rb") as f:
        count_bytes = f.read(8)
        if len(count_bytes) < 8:
            return {"exists": True, "count": 0}
        count = struct.unpack("<Q", count_bytes)[0]
    
    return {"exists": True, "count": count}


def count_sparse_points(points3d_path: Path) -> int:
    """Count the number of 3D points in a COLMAP points3D.bin file."""
    result = read_colmap_binary_header(points3d_path)
    return result.get("count", 0)


def count_registered_images(images_path: Path) -> int:
    """Count the number of registered cameras in images.bin."""
    result = read_colmap_binary_header(images_path)
    return result.get("count", 0)


def validate_reconstruction(sparse_dir: Path, total_input_images: int) -> None:
    """
    Check reconstruction quality and print a summary report.
    
    Key metrics:
        Registration rate: % of input images that COLMAP could register.
            < 70%  → likely bad; check overlap and image quality
            70-90% → acceptable; some edge images may not register
            > 90%  → good
        
        3D point count: more is better; very scene-dependent.
            < 1000  → sparse; expect blurry reconstruction
            1000-10000 → typical for a small object
            > 10000 → good; rich texture
    """
    recon_dir = sparse_dir / "0"
    
    images_bin    = recon_dir / "images.bin"
    points3d_bin  = recon_dir / "points3D.bin"
    cameras_bin   = recon_dir / "cameras.bin"
    
    print(f"\n{'='*60}")
    print(f"  COLMAP Reconstruction Quality Report")
    print(f"{'='*60}")
    
    if not recon_dir.exists():
        print("  ❌ No reconstruction found at sparse/0/")
        print("     COLMAP mapper may have failed to find an initial pair.")
        print("     Try shooting more images with better overlap.")
        sys.exit(1)
    
    registered_images = count_registered_images(images_bin)
    point_count       = count_sparse_points(points3d_bin)
    
    registration_pct = (registered_images / total_input_images * 100) if total_input_images > 0 else 0
    
    print(f"\n  Input images:      {total_input_images}")
    print(f"  Registered:        {registered_images}  ({registration_pct:.1f}%)")
    print(f"  3D points:         {point_count:,}")
    
    # ── Registration rate assessment ──
    if registration_pct >= 90:
        print(f"\n  ✅ Registration rate: EXCELLENT ({registration_pct:.1f}%)")
    elif registration_pct >= 70:
        print(f"\n  ⚠️  Registration rate: ACCEPTABLE ({registration_pct:.1f}%)")
        print(f"     Some cameras failed to register. Check the missing images —")
        print(f"     they may have low overlap with their neighbors.")
    else:
        print(f"\n  ❌ Registration rate: POOR ({registration_pct:.1f}%)")
        print(f"     Only {registered_images} of {total_input_images} cameras registered.")
        print(f"     Likely causes:")
        print(f"       - Insufficient image overlap (shoot more, slower)")
        print(f"       - Blurry images (re-run 01_extract_frames.py with lower blur threshold)")
        print(f"       - Scene has too little texture (pick a more textured subject)")
        print(f"     Training on this reconstruction may produce poor results.")
    
    # ── Point count assessment ──
    if point_count < 1000:
        print(f"\n  ⚠️  WARNING: Very few 3D points ({point_count:,}).")
        print(f"     The sparse point cloud is thin. Gaussian training initializes from")
        print(f"     these points — a thin cloud → fewer initial Gaussians → blurry start.")
        print(f"     Consider re-shooting with more overlap or better lighting.")
    elif point_count >= 10000:
        print(f"\n  ✅ Point count: GOOD ({point_count:,} points)")
    else:
        print(f"\n  ✅ Point count: OK ({point_count:,} points)")
    
    print(f"\n{'─'*60}")
    print(f"  Sparse reconstruction saved to: {recon_dir}")
    print(f"\n  Next step:")
    print(f"    bash scripts/03_train_splatfacto.sh <scene_name>")
    print(f"{'='*60}\n")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run the full COLMAP Structure-from-Motion pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard object capture (use exhaustive matching):
  python scripts/02_run_colmap.py --scene shoe

  # Video-derived frames in sequential order:
  python scripts/02_run_colmap.py --scene living_room --matcher sequential
        """
    )
    
    parser.add_argument("--scene",   type=str, required=True,
                        help="Scene name (must have data/{scene}/input/ with images)")
    parser.add_argument("--matcher", type=str, default="exhaustive",
                        choices=["exhaustive", "sequential"],
                        help="Matching strategy: exhaustive (default) or sequential (for video)")
    parser.add_argument("--gpu",    action="store_true", default=True,
                        help="Use GPU for feature extraction (default: True)")
    
    args = parser.parse_args()
    
    # ── Paths ─────────────────────────────────────────────────────────────────
    project_root = Path(__file__).parent.parent
    data_dir     = project_root / "data" / args.scene
    input_dir    = data_dir / "input"
    db_path      = data_dir / "database.db"
    sparse_dir   = data_dir / "sparse"
    
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        print(f"   Run 01_extract_frames.py first.")
        sys.exit(1)
    
    image_files = list(input_dir.glob("*.jpg")) + list(input_dir.glob("*.png"))
    total_images = len(image_files)
    
    if total_images < 20:
        print(f"⚠️  Only {total_images} images found. COLMAP needs at least 20-30.")
        print(f"   Recommend: re-shoot with more coverage or lower blur threshold.")
    
    print(f"\n{'='*60}")
    print(f"  COLMAP SfM Pipeline — Scene: '{args.scene}'")
    print(f"{'='*60}")
    print(f"  Input:   {input_dir} ({total_images} images)")
    print(f"  DB:      {db_path}")
    print(f"  Sparse:  {sparse_dir}")
    print(f"  Matcher: {args.matcher}")
    
    sparse_dir.mkdir(parents=True, exist_ok=True)
    
    # ── Stage 1: Feature Extraction ───────────────────────────────────────────
    # What this does: runs SIFT on every image, stores keypoints + descriptors
    # in the SQLite database. SiftGPU uses your RTX 4060 → much faster.
    run_colmap([
        "feature_extractor",
        "--database_path", str(db_path),
        "--image_path",    str(input_dir),
        "--ImageReader.single_camera", "1",   # assume one camera for all images
        "--SiftExtraction.use_gpu", "1" if args.gpu else "0",
        "--SiftExtraction.max_num_features", "8192",  # more features = better matching
    ], "Feature Extraction")
    
    # ── Stage 2: Feature Matching ─────────────────────────────────────────────
    # What this does: find correspondences between image pairs.
    # exhaustive: try all N*(N-1)/2 pairs — O(N²), but highest quality
    # sequential: only match adjacent images — O(N), good for ordered video frames
    if args.matcher == "exhaustive":
        run_colmap([
            "exhaustive_matcher",
            "--database_path", str(db_path),
            "--SiftMatching.use_gpu", "1" if args.gpu else "0",
        ], "Exhaustive Feature Matching")
    else:
        run_colmap([
            "sequential_matcher",
            "--database_path", str(db_path),
            "--SiftMatching.use_gpu", "1" if args.gpu else "0",
            "--SequentialMatching.overlap", "10",   # match each frame with 10 neighbors
            "--SequentialMatching.loop_detection", "1",
        ], "Sequential Feature Matching")
    
    # ── Stage 3: Sparse Reconstruction (Mapper) ───────────────────────────────
    # What this does: incremental SfM
    # 1. Find best initial pair (max inlier matches, good baseline)
    # 2. Triangulate initial 3D points
    # 3. Register cameras one by one using PnP (Perspective-n-Point)
    # 4. Triangulate new points visible from new cameras
    # 5. Bundle adjustment: jointly refine all camera poses + 3D points
    run_colmap([
        "mapper",
        "--database_path", str(db_path),
        "--image_path",    str(input_dir),
        "--output_path",   str(sparse_dir),
        "--Mapper.num_threads", "4",
        "--Mapper.init_min_num_inliers", "50",    # lower = easier to start (helps thin texture)
        "--Mapper.abs_pose_min_num_inliers", "20",
    ], "Sparse Reconstruction (Mapper)")
    
    # ── Validate and report ───────────────────────────────────────────────────
    validate_reconstruction(sparse_dir, total_images)


if __name__ == "__main__":
    main()
