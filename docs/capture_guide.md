# 📸 Scene Capture Guide

Everything you need to know to shoot footage that produces a clean 3D reconstruction.
Read this fully before you pick up your phone. Bad footage = wasted GPU hours.

---

## What Makes a Good Scene?

### ✅ Pick scenes with:

- **Diffuse, matte surfaces** — wood, fabric, clay, painted surfaces, most food
- **Rich texture** — patterns, text, scratches, grain (anything a camera can find "keypoints" in)
- **Stable, consistent lighting** — overcast daylight through a window is ideal; no harsh shadows
- **Static content** — nothing moves while you're shooting

**Great beginner subjects:**
- A sneaker or boot placed on a table
- A small potted succulent or plant
- A cluttered desk corner (keyboard, mug, headphones)
- A decorative object (sculpture, figurine, trophy)
- A bookshelf section

### ❌ Avoid:

| Surface type | Why it breaks reconstruction |
|---|---|
| **Mirrors / chrome / glass** | SfM sees different content from every angle — features can't be matched |
| **Blank white/black walls** | Zero texture → zero keypoints → zero matches |
| **Wet or shiny surfaces** | Specular highlights change with viewpoint, confusing the matcher |
| **Moving elements** | People, pets, fans, curtains — any motion violates the static-scene assumption |
| **Transparency** | The camera sees through the object; depth is ambiguous |
| **Very dark scenes** | Low light → noisy images → blurry keypoints → failed matches |

---

## Shooting Pattern — Object (Recommended for Your First Scene)

This pattern gives COLMAP enough overlapping views to register every camera.

```
Top-down view of shooting orbit:

        [High ring: 4-5 shots at ~45° above equator]

  →  →  →  →  →  →  →  →  →  →  →  →  →
  ↑  [Equatorial ring: 8-10 shots at eye level]  ↓
  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←  ←

        [Low ring: 4-5 shots at ~20° below equator]

        + 1-2 overhead shots looking straight down
```

**Total: ~20-30 photos, or 1-2 minutes of slow orbit video**

### If shooting photos (recommended for your first attempt):
1. Place object on a flat surface with a **textured background** (a tablecloth, newspaper, or patterned mat — not a plain white desk)
2. Shoot your equatorial ring first: take a photo, step ~30° around, repeat
3. Then tilt down for the high ring, same rotation pattern
4. Then tilt up for the low ring
5. Don't zoom — only move yourself
6. Each photo should share **~60-70% of content** with the previous one

### If shooting video (also works):
- Set your phone to **1080p 30fps** (not 4K — the extra resolution doesn't help and creates huge files)
- Walk slowly and continuously around the object (~15-20 seconds per full orbit)
- Do 3 orbits: low, equatorial, high
- Keep the object in frame and roughly centered
- No sudden movements — steady, smooth, slow
- No zoom

---

## Camera Settings

| Setting | Recommendation |
|---|---|
| **Focus** | Lock to manual/AF-locked on the object. Tap-to-lock on iPhone/Android |
| **Exposure** | Lock exposure (same tap gesture). Inconsistent exposure creates different-brightness images that confuse the photometric part of training |
| **Stabilization** | EIS/OIS on — reduces blur |
| **Resolution** | 1080p is ideal (4K creates unnecessarily large files; 720p sometimes lacks detail) |
| **Shutter** | Avoid motion blur: 1/100s or faster. In low light, raise ISO instead of slowing shutter |

---

## Lighting

**Best:** Overcast daylight from a window (soft, even, no harsh shadows)
**Good:** Indoor ceiling light, well-lit room
**Acceptable:** Lamp light on one side (shadows will appear in the splat but it still works)
**Bad:** Direct sunlight (over-exposed regions, hard shadows)
**Terrible:** Nighttime phone camera with flash (flash changes with camera angle — your images will have wildly different lighting)

---

## Before You Start Shooting — Checklist

```
[ ] Object is placed on a TEXTURED surface (not blank white)
[ ] Room/area has consistent lighting — no windows in direct sun
[ ] Phone storage has at least 2GB free
[ ] Phone is charged or plugged in
[ ] Phone focus and exposure are LOCKED on the object
[ ] No people, pets, or moving elements in the scene
[ ] You've walked the orbit once without shooting to plan your path
```

---

## Common Mistakes and How to Spot Them

### Mistake 1: Too little overlap
**Symptom:** COLMAP registers < 70% of your images; sparse point cloud has gaps
**Prevention:** Slow down. If in doubt, take more photos. 40-50 photos is not too many.

### Mistake 2: Motion blur
**Symptom:** `check_colmap.py` flags many blurry frames; reconstruction is soft
**Prevention:** Hold still for 0.5 seconds at each photo position. Lock shutter speed if possible.

### Mistake 3: Inconsistent lighting
**Symptom:** Training loss plateaus early; reconstruction has banding or ghosting
**Prevention:** Lock exposure. Keep curtains/windows consistent (all open or all closed).

### Mistake 4: Shooting too close
**Symptom:** Only the center of the object is reconstructed; edges are missing
**Prevention:** Keep the whole object in frame with some margin. Back up if you can't see the full object.

### Mistake 5: Circular motion only, no height variation
**Symptom:** Top and bottom of object are blurry/missing; visible "disk" of coverage
**Prevention:** Always shoot at least 3 height levels (low, equatorial, high).

---

## After Shooting

1. Transfer your video/photos to your Windows machine
2. Put the video at: `C:\Users\sanke\OneDrive\Desktop\Blend\raw_footage\{scene_name}.mp4`
   (or photos at: `C:\Users\sanke\OneDrive\Desktop\Blend\raw_footage\{scene_name}\`)
3. Run the frame extraction script (see main README)

---

## Example Scene Setup

Here's a recommended first scene to reconstruct — simple enough to succeed on your first run:

**Subject:** A lace-up shoe or boot  
**Background:** A bath towel or patterned tablecloth spread on a table  
**Lighting:** Near a window on a cloudy day  
**Shooting time:** 3 slow orbits, ~2 minutes total video  
**Expected result:** Clean reconstruction of the shoe with visible texture and lace detail
