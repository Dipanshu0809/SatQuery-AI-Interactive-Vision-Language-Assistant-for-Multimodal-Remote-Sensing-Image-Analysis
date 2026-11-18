"""
Water Intelligence service.

SCIENTIFIC HONESTY NOTE — same caveat as vegetation_service.py: true NDWI
(Normalized Difference Water Index) needs Green and NIR bands. RGB photos
don't contain NIR. This computes a simple HSV-based water-likelihood proxy
(blue/cyan hue + moderate-to-high saturation), NOT real NDWI, and the UI
must label it "RGB Water Index (proxy)".
"""

import cv2
import numpy as np


def compute_water_index(rgb_array: np.ndarray) -> dict:
    hsv = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[:, :, 0].astype(np.float32), hsv[:, :, 1].astype(np.float32), hsv[:, :, 2].astype(np.float32)

    # Blue/cyan hue range in OpenCV's 0-179 H scale, moderate saturation, not too dark
    water_likelihood = np.zeros_like(h)
    mask = (h >= 95) & (h <= 135) & (s >= 25) & (v >= 25)
    water_likelihood[mask] = 1.0

    coverage_pct = float(np.mean(water_likelihood)) * 100

    return {
        "index_array": water_likelihood,
        "coverage_pct": round(coverage_pct, 1),
    }


def index_to_heatmap_rgb(index_array: np.ndarray) -> np.ndarray:
    scaled = (index_array * 255).astype(np.uint8)
    colored = cv2.applyColorMap(scaled, cv2.COLORMAP_OCEAN)
    return cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
