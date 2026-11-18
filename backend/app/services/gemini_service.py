"""
GeminiService — the only module that talks to the Gemini API.

The API key is read from the backend .env (GEMINI_API_KEY) and is never
exposed to the frontend.

Reliability (fixes "503 UNAVAILABLE: This model is currently experiencing high
demand" and 429 quota errors):
- A chain of models is tried in order: GEMINI_MODEL first, then
  GEMINI_FALLBACK_MODELS. Each model has its own free-tier quota, so when one
  is overloaded or rate-limited the next one answers.
- Overloaded / rate-limited models are put on a short cool-down so the next
  requests skip them immediately instead of waiting for another failure.
- Identical requests (same prompt + same image) are answered from a cache for
  up to an hour, so repeated clicks do not spend quota.
- Large images are downscaled before upload (fewer input tokens, faster calls).
- Invalid key / bad request errors are reported clearly and not retried.
"""

import io
import json
import logging
import re
import threading
import time
from functools import lru_cache

from app.config import get_settings
from app.services.resilience import MemoCache, make_key

logger = logging.getLogger("satquery.gemini")

DEFAULT_FALLBACK_MODELS = "gemini-3.5-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite,gemini-2.5-flash"
REQUEST_TIMEOUT_S = 60          # per model attempt
TOTAL_BUDGET_S = 150            # whole fallback chain
MAX_IMAGE_SIDE = 1600           # px; larger uploads are downscaled before sending
RESPONSE_TTL_S = 60 * 60

_RESPONSE_CACHE = MemoCache(max_items=200)
_cooldown_until: dict[str, float] = {}
_retired_models: set[str] = set()
_state_lock = threading.Lock()


ANALYSIS_PROMPT = """You are a remote sensing analyst AI. Analyze this satellite/aerial image.

Respond ONLY with valid JSON (no markdown fences, no commentary) in this exact shape:
{
  "summary": "2-4 sentence plain-language summary of what the image shows",
  "land_cover": {
    "vegetation": <0-100 or null if you cannot estimate reliably>,
    "water": <0-100 or null>,
    "built_up": <0-100 or null>,
    "bare_land": <0-100 or null>
  },
  "observations": ["short factual observation", "..."],
  "confidence": <0.0-1.0, your confidence in this analysis>
}

Rules:
- If you cannot reliably estimate land-cover percentages, set them to null rather than guessing.
- Only include observations that are visually grounded in the image.
- Do not fabricate precise numbers you cannot support.
"""

ASK_SYSTEM_PROMPT = """You are SatQuery AI, a remote sensing assistant. Answer questions about the
provided satellite/aerial image accurately and concisely, in plain language a
non-expert can follow. If something can't be determined from the image, say so
directly instead of guessing. Keep answers focused and under 150 words unless
the question needs more detail."""

CHANGE_PROMPT = """You are a remote sensing analyst AI comparing two satellite images of the same
location taken at different times (Image A = earlier, Image B = later).

Respond ONLY with valid JSON (no markdown fences, no commentary) in this exact shape:
{
  "summary": "2-4 sentence plain-language summary of what changed",
  "changed_regions": ["short description of a changed area", "..."],
  "confidence": <0.0-1.0>
}

Only describe changes you can actually see between the two images. Do not
fabricate a numeric change percentage — that is computed separately by the
image-processing pipeline, not by you."""


class GeminiUnavailableError(Exception):
    """Raised when Gemini is not configured, or no model could answer."""


@lru_cache(maxsize=2)
def _client_for(api_key: str):
    from google import genai
    from google.genai import types

    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            timeout=REQUEST_TIMEOUT_S * 1000,
            retry_options=types.HttpRetryOptions(attempts=1),  # we handle retries ourselves
        ),
    )


def _retry_delay_seconds(exc: Exception, default: float) -> float:
    """Read Google's suggested retryDelay (e.g. '17s') from a 429 response."""
    match = re.search(r"retry(?:Delay| in)['\"]?[:\s]*['\"]?(\d+(?:\.\d+)?)s", str(exc))
    return min(float(match.group(1)), 300.0) if match else default


def _classify(exc: Exception) -> tuple[str, float]:
    """Return (kind, cooldown_seconds). kind is one of
    busy | quota | retired | auth | bad_request | network."""
    try:
        from google.genai import errors as genai_errors
    except ImportError:  # pragma: no cover
        genai_errors = None
    if genai_errors is not None and isinstance(exc, genai_errors.APIError):
        code = int(getattr(exc, "code", 0) or 0)
        text = f"{getattr(exc, 'status', '')} {getattr(exc, 'message', '')}".lower()
        if code == 429:
            return "quota", _retry_delay_seconds(exc, 60.0)
        if code == 404 or "not found" in text or "not supported" in text:
            return "retired", 0.0
        if code in (401, 403) or "api key" in text or "permission" in text:
            return "auth", 0.0
        if code == 400:
            return "bad_request", 0.0
        if code >= 500:
            return "busy", 45.0
        return "busy", 20.0
    # Timeouts, connection resets, DNS failures...
    return "network", 15.0


class GeminiService:
    def __init__(self):
        settings = get_settings()
        if not settings.gemini_api_key:
            raise GeminiUnavailableError(
                "GEMINI_API_KEY is not configured. Add it to backend/.env (or the Render environment) and restart the backend."
            )
        try:
            import google.genai  # noqa: F401
        except ImportError as e:
            raise GeminiUnavailableError("google-genai package is not installed (pip install -r requirements.txt).") from e

        self._client = _client_for(settings.gemini_api_key)
        primary = (getattr(settings, "gemini_model", None) or "gemini-3.6-flash").strip()
        fallbacks = getattr(settings, "gemini_fallback_models", None)
        if fallbacks is None:
            fallbacks = DEFAULT_FALLBACK_MODELS
        chain = [primary] + [m.strip() for m in str(fallbacks).split(",") if m.strip()]
        self._models = list(dict.fromkeys(chain))  # de-duplicate, keep order
        self._model = primary
        self.last_model_used: str | None = None

    # ---- internal helpers -------------------------------------------------

    def _ordered_models(self) -> list[str]:
        """Models not retired; ones on cool-down go to the back of the queue."""
        now = time.time()
        with _state_lock:
            alive = [m for m in self._models if m not in _retired_models]
            ready = [m for m in alive if _cooldown_until.get(m, 0) <= now]
            cooling = sorted((m for m in alive if m not in ready), key=lambda m: _cooldown_until.get(m, 0))
        return ready + cooling

    def _generate(self, parts: list, timeout_s: int = REQUEST_TIMEOUT_S, cache_ttl: float = RESPONSE_TTL_S) -> str:
        cache_key = make_key("gemini", [self._part_fingerprint(p) for p in parts])
        cached = _RESPONSE_CACHE.get(cache_key) if cache_ttl > 0 else None
        if cached is not None:
            self.last_model_used = "cache"
            return cached

        started = time.time()
        failures: list[str] = []
        kinds: set[str] = set()
        for model in self._ordered_models():
            if time.time() - started > TOTAL_BUDGET_S:
                break
            try:
                response = self._client.models.generate_content(model=model, contents=parts)
                text = getattr(response, "text", None)
                if not text:
                    # Usually a safety block or an empty candidate; another model may answer.
                    failures.append(f"{model}: empty response")
                    kinds.add("empty")
                    continue
            except Exception as e:  # noqa: BLE001
                kind, cooldown = _classify(e)
                kinds.add(kind)
                failures.append(f"{model}: {kind} ({str(e)[:160]})")
                if kind == "auth":
                    raise GeminiUnavailableError(
                        "Gemini rejected the API key (invalid, expired or not enabled). "
                        "Create a new key at https://aistudio.google.com/apikey and update GEMINI_API_KEY."
                    ) from e
                if kind == "bad_request":
                    raise GeminiUnavailableError(f"Gemini could not process this request: {getattr(e, 'message', str(e))[:300]}") from e
                with _state_lock:
                    if kind == "retired":
                        _retired_models.add(model)
                    elif cooldown:
                        _cooldown_until[model] = time.time() + cooldown
                logger.warning("Gemini model %s failed (%s); trying the next model", model, kind)
                time.sleep(0.4)
                continue

            if model != self._model:
                logger.info("Gemini answered with fallback model %s", model)
            self.last_model_used = model
            if cache_ttl > 0:
                _RESPONSE_CACHE.set(cache_key, text, cache_ttl)
            return text

        logger.error("All Gemini models failed: %s", " | ".join(failures) or "no models configured")
        if kinds and kinds <= {"quota"}:
            raise GeminiUnavailableError(
                "Gemini free-tier quota is used up on every configured model. Wait a minute (per-minute limit) "
                "or until tomorrow (daily limit), or set a different GEMINI_API_KEY."
            )
        if kinds == {"empty"}:
            raise GeminiUnavailableError("Gemini returned an empty answer (the request may have been blocked by its safety filter).")
        raise GeminiUnavailableError(
            "Gemini AI is temporarily overloaded (high demand on Google's side) and every fallback model was busy. "
            "Please try again in a minute."
        )

    @staticmethod
    def _part_fingerprint(part):
        if isinstance(part, str):
            return part
        inline = getattr(part, "inline_data", None)
        if inline is not None and getattr(inline, "data", None) is not None:
            return {"mime": inline.mime_type, "bytes": make_key(inline.data)}
        return repr(part)

    @staticmethod
    def _parse_json(text: str) -> dict:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        # Some models wrap the JSON in prose: take the outermost {...} block.
        start, end = cleaned.find("{"), cleaned.rfind("}")
        try:
            if start != -1 and end > start:
                return json.loads(cleaned[start:end + 1])
            raise json.JSONDecodeError("no object", cleaned, 0)
        except json.JSONDecodeError as e:
            raise GeminiUnavailableError(
                "Gemini returned a response that could not be parsed as JSON."
            ) from e

    @staticmethod
    def _shrink(image_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
        """Downscale very large images: fewer tokens, faster uploads, same insight."""
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(image_bytes))
            if max(img.size) <= MAX_IMAGE_SIDE and len(image_bytes) <= 4 * 1024 * 1024:
                return image_bytes, mime_type
            img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
            return buf.getvalue(), "image/jpeg"
        except Exception:  # noqa: BLE001 - send the original if Pillow cannot read it
            return image_bytes, mime_type

    @classmethod
    def _image_part(cls, image_bytes: bytes, mime_type: str):
        from google.genai import types

        data, mime = cls._shrink(image_bytes, mime_type or "image/png")
        return types.Part.from_bytes(data=data, mime_type=mime)

    # ---- public API ---------------------------------------------------

    def analyze_image(self, image_bytes: bytes, mime_type: str) -> dict:
        """Analyze a single image; returns dict matching AnalysisResponse fields."""
        parts = [self._image_part(image_bytes, mime_type), ANALYSIS_PROMPT]
        text = self._generate(parts)
        data = self._parse_json(text)
        return {
            "summary": data.get("summary", ""),
            "land_cover": data.get("land_cover"),
            "observations": data.get("observations", []),
            "confidence": data.get("confidence"),
        }

    def ask_about_image(
        self, image_bytes: bytes, mime_type: str, question: str, history: list[dict] | None = None
    ) -> str:
        """Ask a free-form question about an image, with optional prior turns."""
        parts: list = [ASK_SYSTEM_PROMPT, self._image_part(image_bytes, mime_type)]
        if history:
            transcript = "\n".join(f"{h['role']}: {h['content']}" for h in history)
            parts.append(f"Conversation so far:\n{transcript}")
        parts.append(f"Question: {question}")
        return self._generate(parts, cache_ttl=10 * 60).strip()

    def summarize_changes(
        self, image_a_bytes: bytes, mime_a: str, image_b_bytes: bytes, mime_b: str
    ) -> dict:
        """Compare two images; returns dict with summary/changed_regions/confidence."""
        parts = [
            "Image A (earlier):",
            self._image_part(image_a_bytes, mime_a),
            "Image B (later):",
            self._image_part(image_b_bytes, mime_b),
            CHANGE_PROMPT,
        ]
        text = self._generate(parts)
        data = self._parse_json(text)
        return {
            "summary": data.get("summary", ""),
            "changed_regions": data.get("changed_regions", []),
            "confidence": data.get("confidence"),
        }

    def generate_text(self, prompt_parts: list[str]) -> str:
        """General-purpose text generation for structured-output use cases
        (Map Copilot commands, Earth Analyst / Mission Mode reasoning over
        retrieved evidence). Public wrapper around _generate."""
        return self._generate(prompt_parts).strip()

    def generate_report_summary(self, analysis_context: dict) -> str:
        """Produce a short narrative conclusion for a PDF report."""
        prompt = (
            "Write a concise 3-5 sentence professional conclusion for a remote "
            "sensing analysis report, based on this data (JSON):\n"
            f"{json.dumps(analysis_context)}\n"
            "Write plain prose, no markdown, no headers."
        )
        return self._generate([prompt]).strip()
