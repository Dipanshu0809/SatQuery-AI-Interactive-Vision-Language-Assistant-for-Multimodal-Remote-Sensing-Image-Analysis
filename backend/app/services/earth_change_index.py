"""
Earth Change Index — SatQuery AI's own composite analytical indicator.

NOT an official scientific or government index. It's a simple, transparent
weighted combination of signals already computed elsewhere in the app
(vegetation-proxy delta, water-proxy delta, built-up delta, nearby fire
activity), scaled into a LOW / MODERATE / HIGH / CRITICAL label. The
methodology is intentionally simple and disclosed in full here so it can
be shown to the user rather than treated as a black box.
"""


def compute_change_index(
    vegetation_delta_pct: float = 0.0,
    water_delta_pct: float = 0.0,
    built_up_delta_pct: float = 0.0,
    nearby_fire_count: int = 0,
) -> dict:
    """All *_delta_pct are absolute percentage-point changes (0-100).
    nearby_fire_count is the number of active fire detections within the
    region of interest, from firms_service.
    """
    veg_score = min(abs(vegetation_delta_pct) / 25, 1.0) * 35
    water_score = min(abs(water_delta_pct) / 25, 1.0) * 20
    built_score = min(abs(built_up_delta_pct) / 25, 1.0) * 25
    fire_score = min(nearby_fire_count / 5, 1.0) * 20

    raw_score = veg_score + water_score + built_score + fire_score  # 0-100

    if raw_score < 20:
        label = "LOW"
    elif raw_score < 45:
        label = "MODERATE"
    elif raw_score < 70:
        label = "HIGH"
    else:
        label = "CRITICAL"

    return {
        "score": round(raw_score, 1),
        "label": label,
        "components": {
            "vegetation": round(veg_score, 1),
            "water": round(water_score, 1),
            "built_up": round(built_score, 1),
            "fire_activity": round(fire_score, 1),
        },
        "methodology": (
            "SatQuery AI analytical index (not an official scientific or "
            "government index). Weighted composite: vegetation-proxy change "
            "35%, water-proxy change 20%, built-up change 25%, nearby active "
            "fire count 20%. Capped and scaled per component before summing."
        ),
    }
