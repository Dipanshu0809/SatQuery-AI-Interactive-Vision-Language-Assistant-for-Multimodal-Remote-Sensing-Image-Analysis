"""
AI Map Copilot — converts a natural-language map instruction into a
structured, VALIDATED command. Gemini (when configured) proposes the
command as JSON; this module then validates it against a strict allowlist
before it's ever returned to the frontend. The frontend executes the
command (toggling a layer, panning the map) — Gemini never touches the
map or any code path directly, and nothing here executes arbitrary code,
SQL, or shell commands.
"""

import json
import logging
import re  # noqa: F401

from app.config import get_settings  # noqa: F401
from app.services.gemini_service import GeminiService, GeminiUnavailableError

logger = logging.getLogger("satquery.map_copilot")

ALLOWED_ACTIONS = {"show_layer", "hide_layer", "zoom_to", "analyze_location", "unknown"}
ALLOWED_LAYERS = {"active_fires", "weather", "vegetation", "water"}

# Small built-in gazetteer so "zoom to Mumbai" works without a paid geocoding
# API. Intentionally short — expand as needed.
KNOWN_LOCATIONS = {
    "mumbai": (19.076, 72.8777),
    "delhi": (28.6139, 77.209),
    "amritsar": (31.634, 74.8723),
    "bangalore": (12.9716, 77.5946),
    "new york": (40.7128, -74.006),
    "los angeles": (34.0522, -118.2437),
    "london": (51.5072, -0.1276),
    "sydney": (-33.8688, 151.2093),
    "cairo": (30.0444, 31.2357),
    "sao paulo": (-23.5505, -46.6333),
    "tokyo": (35.6762, 139.6503),
}

COPILOT_PROMPT = """You control a map through structured commands only. Given the user's
instruction, respond ONLY with JSON (no markdown, no commentary) in this exact shape:
{
  "action": "show_layer" | "hide_layer" | "zoom_to" | "analyze_location" | "unknown",
  "layer": "active_fires" | "weather" | "vegetation" | "water" | null,
  "location": "<place name mentioned by the user, or null>",
  "explanation": "<one short sentence of what you're doing>"
}
Use "unknown" if the instruction doesn't map cleanly to one of these actions."""


def _validate(command: dict) -> dict:
    action = command.get("action")
    if action not in ALLOWED_ACTIONS:
        action = "unknown"

    layer = command.get("layer")
    if layer not in ALLOWED_LAYERS:
        layer = None

    location_name = (command.get("location") or "").strip().lower()
    coords = KNOWN_LOCATIONS.get(location_name)
    if coords is None and location_name:
        # "Mumbai, India" -> "mumbai"
        coords = next((c for name, c in KNOWN_LOCATIONS.items() if name in location_name), None)

    return {
        "action": action,
        "layer": layer,
        "location_name": command.get("location"),
        "latitude": coords[0] if coords else None,
        "longitude": coords[1] if coords else None,
        "explanation": command.get("explanation", ""),
    }


LAYER_WORDS = {
    "active_fires": ("fire", "wildfire", "burn", "hotspot"),
    "weather": ("weather", "temperature", "rain", "wind", "cloud"),
    "vegetation": ("vegetation", "ndvi", "green", "forest", "crop", "plant"),
    "water": ("water", "ndwi", "flood", "river", "lake"),
}


def _rule_based_command(text: str) -> dict:
    """Keyword parser used when Gemini is busy, so simple commands keep working."""
    t = text.lower()
    layer = next((name for name, words in LAYER_WORDS.items() if any(w in t for w in words)), None)
    place = next((name for name in KNOWN_LOCATIONS if name in t), None)
    if layer and any(w in t for w in ("hide", "remove", "turn off", "disable")):
        action = "hide_layer"
    elif any(w in t for w in ("analy", "investigat", "what is happening", "what's happening", "report")) and place:
        action = "analyze_location"
    elif layer:
        action = "show_layer"
    elif place:
        action = "zoom_to"
    else:
        action = "unknown"
    explanation = {
        "show_layer": f"Showing the {(layer or '').replace('_', ' ')} layer" + (f" around {place.title()}" if place else "") + ".",
        "hide_layer": f"Hiding the {(layer or '').replace('_', ' ')} layer.",
        "zoom_to": f"Zooming to {place.title() if place else ''}.",
        "analyze_location": f"Analyzing {place.title() if place else ''} with live evidence.",
        "unknown": "Try e.g. 'show fires near Delhi' or 'zoom to Mumbai' (AI parsing is busy right now).",
    }[action]
    return {"action": action, "layer": layer, "location": place.title() if place else None,
            "explanation": explanation + " (quick parser - Gemini was busy)"}


def parse_command(text: str) -> dict:
    try:
        gemini = GeminiService()
        raw = gemini.generate_text([COPILOT_PROMPT, f"User instruction: {text}"])
        parsed = GeminiService._parse_json(raw)
    except GeminiUnavailableError as e:
        logger.warning("Gemini unavailable for Map Copilot, using rule-based parser: %s", e)
        parsed = _rule_based_command(text)
    command = _validate(parsed)
    # If the user named a place we know but Gemini left it out, keep the coordinates.
    if command["latitude"] is None:
        place = next((name for name in KNOWN_LOCATIONS if name in text.lower()), None)
        if place and command["action"] in ("zoom_to", "analyze_location", "show_layer"):
            command.update(location_name=command["location_name"] or place.title(),
                           latitude=KNOWN_LOCATIONS[place][0], longitude=KNOWN_LOCATIONS[place][1])
    return {**command, "is_demo": False}
