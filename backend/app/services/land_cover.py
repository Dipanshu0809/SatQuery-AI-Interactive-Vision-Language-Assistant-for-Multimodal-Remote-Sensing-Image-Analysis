"""
Lightweight, replaceable land-cover estimation pipeline.

This is a color-heuristic baseline (HSV thresholding via OpenCV), used as
a fallback/demonstration CV pipeline and NOT a trained deep-learning
classifier. It's intentionally simple so it can be swapped for a real
pretrained segmentation model (e.g. a U-Net trained on Sentinel-2 /
EuroSAT-style data) without changing the calling code's interface.
"""

import cv2
import numpy as np


def estimate_land_cover(rgb_array: np.ndarray) -> dict:
    """Estimate rough land-cover percentages from an RGB image using HSV
    color thresholds. Returns percentages that sum to ~100.

    This is a heuristic, not a calibrated classifier — treat it as a
    demonstration CV pipeline, not ground truth.
    """
    hsv = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    total = rgb_array.shape[0] * rgb_array.shape[1]

    vegetation_mask = (h >= 30) & (h <= 95) & (s >= 40)
    water_mask = (h >= 95) & (h <= 135) & (s >= 30) & (v >= 30)
    built_up_mask = (s < 40) & (v >= 90)
    bare_mask = (h >= 5) & (h <= 30) & (s >= 15) & (s < 120)

    vegetation_pct = float(np.sum(vegetation_mask)) / total * 100
    water_pct = float(np.sum(water_mask)) / total * 100
    built_up_pct = float(np.sum(built_up_mask)) / total * 100
    bare_pct = float(np.sum(bare_mask)) / total * 100

    raw_total = vegetation_pct + water_pct + built_up_pct + bare_pct
    if raw_total > 0:
        # Normalize to ~100 while keeping "unclassified" implicit remainder small
        scale = min(100 / raw_total, 1.0) if raw_total > 100 else 1.0
        vegetation_pct *= scale
        water_pct *= scale
        built_up_pct *= scale
        bare_pct *= scale

    return {
        "vegetation": round(vegetation_pct, 1),
        "water": round(water_pct, 1),
        "built_up": round(built_up_pct, 1),
        "bare_land": round(bare_pct, 1),
    }
