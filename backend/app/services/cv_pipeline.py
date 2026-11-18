"""Computer-vision baseline pipeline for SatQuery AI.

This module intentionally uses OpenCV/NumPy only, so the project works on a
fresh machine without downloading model weights. It provides reproducible
image statistics, scene complexity, candidate object regions, and a visual
overlay. These are CV measurements/heuristics, not ground-truth semantic
labels. A learned model can be plugged into this interface later.
"""

import io
import cv2
import numpy as np
from PIL import Image


def analyze_scene(rgb: np.ndarray) -> dict:
    """Run a deterministic CV analysis on an RGB image."""
    h, w = rgb.shape[:2]
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # Edges / texture are useful scene-level CV signals.
    edges = cv2.Canny(gray, 70, 160)
    edge_density = float(np.mean(edges > 0) * 100)
    contrast = float(np.std(gray))
    brightness = float(np.mean(gray))

    # Candidate regions: contours around visually distinctive areas.
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    candidate = ((sat > 70) & (val > 45)).astype(np.uint8) * 255
    kernel = np.ones((5, 5), np.uint8)
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_OPEN, kernel)
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(candidate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = max(64, int(h * w * 0.001))
    regions = []
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:20]:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        x, y, bw, bh = cv2.boundingRect(contour)
        regions.append({
            "x": int(x), "y": int(y), "width": int(bw), "height": int(bh),
            "area_pct": round(area / (h * w) * 100, 2),
        })

    # A conservative, non-semantic scene profile.
    if edge_density < 4:
        scene = "low-detail / open terrain"
    elif edge_density < 10:
        scene = "mixed terrain / moderate structure"
    else:
        scene = "high-detail / structured scene"

    overlay = rgb.copy()
    for i, r in enumerate(regions[:12], start=1):
        cv2.rectangle(overlay, (r["x"], r["y"]), (r["x"] + r["width"], r["y"] + r["height"]), (255, 80, 40), 2)
        cv2.putText(overlay, f"R{i}", (r["x"], max(16, r["y"] - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 80, 40), 1, cv2.LINE_AA)
    blended = cv2.addWeighted(rgb, 0.68, overlay, 0.32, 0)
    buf = io.BytesIO()
    Image.fromarray(blended).save(buf, format="PNG")

    return {
        "image_width": w,
        "image_height": h,
        "brightness": round(brightness, 1),
        "contrast": round(contrast, 1),
        "edge_density_pct": round(edge_density, 2),
        "candidate_regions": regions,
        "candidate_count": len(regions),
        "scene_profile": scene,
        "method": "OpenCV scene analysis baseline",
        "overlay_bytes": buf.getvalue(),
    }
