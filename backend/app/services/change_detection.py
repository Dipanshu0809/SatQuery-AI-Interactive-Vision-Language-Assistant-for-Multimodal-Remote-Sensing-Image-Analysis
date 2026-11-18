"""
Pixel-level change detection pipeline.

Computes an actual, reproducible change percentage and a difference
heatmap from two co-registered images (assumes the two uploads roughly
cover the same extent — no georeferencing/alignment is performed in this
baseline pipeline). This is the ONLY source of the numeric change
percentage shown in the UI; Gemini is used separately for a narrative
summary, never for the number itself.
"""

import io

import cv2
import numpy as np
from PIL import Image


def _resize_to_match(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    h = min(a.shape[0], b.shape[0])
    w = min(a.shape[1], b.shape[1])
    a_r = cv2.resize(a, (w, h))
    b_r = cv2.resize(b, (w, h))
    return a_r, b_r


def compute_change(
    image_a: np.ndarray, image_b: np.ndarray, threshold: int = 30
) -> dict:
    """Compare two RGB numpy arrays.

    Returns:
        change_percentage: float, % of pixels that differ beyond threshold
        heatmap_bytes: PNG bytes of a difference heatmap image
        diff_mask: bool array of changed pixels (for further analysis)
    """
    a, b = _resize_to_match(image_a, image_b)

    gray_a = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    gray_b = cv2.cvtColor(b, cv2.COLOR_RGB2GRAY)

    gray_a = cv2.GaussianBlur(gray_a, (5, 5), 0)
    gray_b = cv2.GaussianBlur(gray_b, (5, 5), 0)

    diff = cv2.absdiff(gray_a, gray_b)
    _, mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

    # Remove small noise
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    changed_pixels = int(np.sum(mask > 0))
    total_pixels = mask.shape[0] * mask.shape[1]
    change_percentage = round((changed_pixels / total_pixels) * 100, 2)

    heatmap_color = cv2.applyColorMap(diff, cv2.COLORMAP_INFERNO)
    heatmap_rgb = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
    heatmap_img = Image.fromarray(heatmap_rgb)
    buf = io.BytesIO()
    heatmap_img.save(buf, format="PNG")

    return {
        "change_percentage": change_percentage,
        "heatmap_bytes": buf.getvalue(),
        "diff_mask": mask > 0,
    }


def region_summary(diff_mask: np.ndarray, grid: int = 3) -> list[str]:
    """Break the image into a grid and report which cells have the most
    change, as a lightweight stand-in for proper region labeling."""
    h, w = diff_mask.shape
    cell_h, cell_w = h // grid, w // grid
    labels = [
        ["top-left", "top-center", "top-right"],
        ["mid-left", "center", "mid-right"],
        ["bottom-left", "bottom-center", "bottom-right"],
    ]
    scores = []
    for i in range(grid):
        for j in range(grid):
            cell = diff_mask[i * cell_h : (i + 1) * cell_h, j * cell_w : (j + 1) * cell_w]
            pct = float(np.sum(cell)) / max(cell.size, 1) * 100
            scores.append((pct, labels[i][j] if i < 3 and j < 3 else f"region-{i}-{j}"))

    scores.sort(reverse=True)
    top = [f"Notable change in the {label} region ({pct:.1f}% of that area)" for pct, label in scores[:3] if pct > 1]
    return top or ["Change is diffuse across the frame with no single dominant region"]
