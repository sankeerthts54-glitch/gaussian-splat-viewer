"""
Script 01: Frame Extraction
============================
Extracts frames from a phone video at a configurable rate.
Also runs blur detection to flag frames that will hurt COLMAP.

Usage (inside WSL2, conda activate gsplat):
    python scripts/01_extract_frames.py --video /mnt/c/Users/sanke/.../video.mp4 --scene my_scene
    python scripts/01_extract_frames.py --video /mnt/c/Users/sanke/.../video.mp4 --scene my_scene --fps 2
    python scripts/01_extract_frames.py --photos /mnt/c/Users/sanke/.../photos/ --scene my_scene

Output:
    data/{scene_name}/input/   <- COLMAP-ready frames

What's happening:
    - ffmpeg extracts frames at the specified FPS (default: auto-calculated for ~150 frames)
    - Each frame is scored with a Laplacian variance (blur score):
        high score (>100) = sharp, good for SfM
        low score (<50)   = blurry, will hurt matching — automatically removed
    - The script prints a summary: total frames, removed for blur, final count
"""

import argparse
import subprocess
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np


# ─── Constants ───────────────────────────────────────────────────────────────

TARGET_FRAMES = 150       # Ideal number of frames for COLMAP
BLUR_THRESHOLD = 80.0     # Laplacian variance below this = too blurry
MIN_FRAMES = 50           # Warn if we end up with fewer than this
MAX_FRAMES = 300          # Warn if we end up with more (slows COLMAP a lot)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_video_duration(video_path: Path) -> float:
    """Return video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    return float(result.stdout.strip())


def compute_blur_score(image_path: Path) -> float:
    """
    Compute sharpness of an image using Laplacian variance.
    
    How it works:
        The Laplacian operator detects edges by computing the second derivative
        of intensity. A sharp image has strong edges → high variance.
        A blurry image has weak edges → low variance.
    
    Returns:
        float: Higher = sharper. Scores < BLUR_THRESHOLD are considered blurry.
    """
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0.0
    return float(cv2.Laplacian(img, cv2.CV_64F).var())


def extract_frames_from_video(video_path: Path, output_dir: Path, fps: float) -> list[Path]:
    """Use ffmpeg to extract frames at the given FPS."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pattern = output_dir / "frame_%05d.jpg"
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"fps={fps}",
        "-q:v", "2",          # JPEG quality 2 = near-lossless (scale 2-31)
        "-loglevel", "warning",
        str(pattern)
    ]
    
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError("ffmpeg frame extraction failed. Check the video path.")
    
    return sorted(output_dir.glob("frame_*.jpg"))


def copy_photos(photo_dir: Path, output_dir: Path) -> list[Path]:
    """Copy photos from a directory into the COLMAP input directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extensions = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
    photos = sorted([p for p in photo_dir.iterdir() if p.suffix in extensions])
    
    if not photos:
        raise ValueError(f"No photos found in {photo_dir}")
    
    copied = []
    for i, photo in enumerate(photos):
        dest = output_dir / f"frame_{i:05d}{photo.suffix.lower()}"
        shutil.copy2(photo, dest)
        copied.append(dest)
    
    return copied


def filter_blurry_frames(
    frames: list[Path],
    threshold: float = BLUR_THRESHOLD,
    keep_every_n: int = 1,
) -> tuple[list[Path], list[Path]]:
    """
    Score each frame for blur and remove frames below the threshold.
    Also applies uniform subsampling if keep_every_n > 1.
    
    Returns:
        (kept_frames, removed_frames)
    """
    print(f"\n  Analyzing {len(frames)} frames for blur (threshold={threshold})...")
    
    scored = []
    for frame in frames:
        score = compute_blur_score(frame)
        scored.append((frame, score))
    
    # Remove blurry frames
    kept = [(f, s) for f, s in scored if s >= threshold]
    removed_blur = [(f, s) for f, s in scored if s < threshold]
    
    # Apply subsampling if too many frames remain
    if keep_every_n > 1:
        kept = kept[::keep_every_n]
    
    # Remove the actual blurry files from disk
    for f, s in removed_blur:
        f.unlink()
    
    return [f for f, _ in kept], [f for f, _ in removed_blur]


def auto_fps(duration_seconds: float, target_frames: int = TARGET_FRAMES) -> float:
    """Calculate the FPS needed to extract ~target_frames from a video."""
    fps = target_frames / duration_seconds
    # Clamp: never extract faster than 4fps (redundant frames) or slower than 0.5fps
    fps = max(0.5, min(4.0, fps))
    return round(fps, 2)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extract frames from a video or copy photos for COLMAP.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From video (auto FPS):
  python scripts/01_extract_frames.py --video footage/video.mp4 --scene shoe

  # From video (manual FPS):
  python scripts/01_extract_frames.py --video footage/video.mp4 --scene shoe --fps 2

  # From a folder of photos:
  python scripts/01_extract_frames.py --photos footage/shoe_photos/ --scene shoe
        """
    )
    
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--video",  type=Path, help="Path to input video file")
    source.add_argument("--photos", type=Path, help="Path to folder of photos")
    
    parser.add_argument("--scene",    type=str,   required=True, help="Scene name (used for output folder)")
    parser.add_argument("--fps",      type=float, default=None,  help="Frames per second to extract (default: auto)")
    parser.add_argument("--blur-threshold", type=float, default=BLUR_THRESHOLD,
                        help=f"Laplacian variance threshold for blur removal (default: {BLUR_THRESHOLD})")
    parser.add_argument("--no-blur-filter", action="store_true",
                        help="Skip blur detection (keep all frames)")
    
    args = parser.parse_args()
    
    # ── Output directory ──────────────────────────────────────────────────────
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "data" / args.scene / "input"
    
    if output_dir.exists() and any(output_dir.iterdir()):
        print(f"⚠️  Output directory already has files: {output_dir}")
        answer = input("   Overwrite? [y/N]: ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)
        shutil.rmtree(output_dir)
    
    print(f"\n{'='*60}")
    print(f"  3DGS Frame Extraction — Scene: '{args.scene}'")
    print(f"{'='*60}")
    print(f"  Output: {output_dir}")
    
    # ── Extract or copy frames ────────────────────────────────────────────────
    if args.video:
        if not args.video.exists():
            print(f"\n❌ Video not found: {args.video}")
            sys.exit(1)
        
        print(f"\n  Video: {args.video}")
        duration = get_video_duration(args.video)
        print(f"  Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        
        fps = args.fps or auto_fps(duration)
        expected_frames = int(duration * fps)
        print(f"  Extracting at {fps} fps → ~{expected_frames} frames")
        
        frames = extract_frames_from_video(args.video, output_dir, fps)
        print(f"  ✅ Extracted {len(frames)} frames")
        
    else:  # --photos
        if not args.photos.exists():
            print(f"\n❌ Photo directory not found: {args.photos}")
            sys.exit(1)
        
        print(f"\n  Photos from: {args.photos}")
        frames = copy_photos(args.photos, output_dir)
        print(f"  ✅ Copied {len(frames)} photos")
    
    # ── Blur filtering ────────────────────────────────────────────────────────
    if not args.no_blur_filter:
        kept, removed = filter_blurry_frames(frames, threshold=args.blur_threshold)
        
        print(f"\n  Blur filter results:")
        print(f"    Total frames:   {len(frames)}")
        print(f"    Blurry removed: {len(removed)}")
        print(f"    Sharp kept:     {len(kept)}")
        
        if removed:
            print(f"\n  Removed (top 5 blurriest):")
            for f, s in sorted([(f, compute_blur_score(f)) for f in [r for r, _ in [(r, 0) for r in removed[:5]]]], key=lambda x: x[1]):
                print(f"    {f.name}: blur_score={s:.1f}")
        
        final_count = len(kept)
    else:
        print("\n  ⚠️  Blur filtering skipped.")
        final_count = len(frames)
    
    # ── Quality warnings ──────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print(f"  Final frame count: {final_count}")
    
    if final_count < MIN_FRAMES:
        print(f"\n  ⚠️  WARNING: Only {final_count} frames. COLMAP may struggle.")
        print(f"     Recommendation: Shoot more footage or lower --fps to keep more frames.")
        print(f"     If using --blur-threshold, try lowering it (current: {args.blur_threshold}).")
    elif final_count > MAX_FRAMES:
        print(f"\n  ⚠️  NOTE: {final_count} frames is quite a lot.")
        print(f"     COLMAP exhaustive matching scales as O(N²) — this will be slow.")
        print(f"     Consider re-running with a lower --fps value.")
    else:
        print(f"  ✅ Frame count looks good for COLMAP.")
    
    print(f"\n  Next step:")
    print(f"    python scripts/02_run_colmap.py --scene {args.scene}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
