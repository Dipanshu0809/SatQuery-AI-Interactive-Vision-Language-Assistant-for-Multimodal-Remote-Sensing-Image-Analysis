"""
Vegetation Intelligence service.

IMPORTANT — SCIENTIFIC HONESTY NOTE:
True NDVI (Normalized Difference Vegetation Index) is calculated from
Near-Infrared and Red reflectance bands: (NIR - Red) / (NIR + Red).
Regular JPG/PNG/TIFF photos uploaded by users only contain visible RGB
channels — there is no NIR band to compute real NDVI from.

This module instead computes ExG (Excess Green Index), a well-established
RGB-only vegetation proxy: ExG = 2*G - R - B, normalized to 0-1. It
correlates with vegetation presence but is NOT NDVI and should never be
labeled or displayed as NDVI. The UI must show it as "RGB Vegetation
Index (proxy)" with this explanation visible.

For real NDVI, multispectral imagery (e.g. Sentinel-2 bands 4 and 8) would
need to be sourced from a provider like Copernicus Data Space — that
integration is not implemented in this module.
"""

import numpy as np


def compute_exg_index(rgb_array: np.ndarray) -> dict:
    """Compute the Excess Green vegetation proxy index for an RGB image.

    Returns a dict with the per-pixel index array (as a normalized heatmap-
    ready array), the mean index value, and a qualitative zone breakdown.
    """
    arr = rgb_array.astype(np.float32) / 255.0
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    exg = 2 * g - r - b  # range roughly -2..2
    exg_norm = np.clip((exg + 1) / 2, 0, 1)  # normalize to 0..1

    mean_index = float(np.mean(exg_norm))

    healthy = float(np.mean(exg_norm > 0.65)) * 100
    moderate = float(np.mean((exg_norm > 0.5) & (exg_norm <= 0.65))) * 100
    low = float(np.mean((exg_norm > 0.4) & (exg_norm <= 0.5))) * 100
    bare = float(np.mean(exg_norm <= 0.4)) * 100

    return {
        "index_array": exg_norm,
        "mean_index": round(mean_index, 3),
        "zones": {
            "healthy": round(healthy, 1),
            "moderate": round(moderate, 1),
            "low": round(low, 1),
            "bare_or_none": round(bare, 1),
        },
    }


def index_to_heatmap_rgb(index_array: np.ndarray) -> np.ndarray:
    """Map a 0..1 vegetation index array to an RGB heatmap (brown -> green)."""
    import cv2

    scaled = (index_array * 255).astype(np.uint8)
    colored = cv2.applyColorMap(scaled, cv2.COLORMAP_SUMMER)
    return cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
