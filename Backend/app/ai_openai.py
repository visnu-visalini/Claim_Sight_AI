"""
ai_openai.py — OpenAI Vision second-opinion module for ClaimSightAI.

Provides analyze_damage_with_openai(image_path, yolo_detections).

YOLO remains the primary detector. This module adds an independent
second opinion only. It never replaces YOLO results.

The API key is loaded exclusively from the OPENAI_API_KEY environment
variable (populated from .env via python-dotenv in run.py / __init__.py).
The key is never logged, printed, or returned in any response.
"""

import os
import base64
import json
import logging

logger = logging.getLogger(__name__)

# ── Safe fallback returned on any failure ─────────────────────────────────

_FALLBACK = {
    "available":           False,
    "error":               "OpenAI analysis unavailable",
    "damage_present":      None,
    "damage_type":         None,
    "severity":            None,
    "affected_part":       None,
    "visual_assessment":   None,
    "confidence":          None,
    "agrees_with_yolo":    None,
}

# ── Model ─────────────────────────────────────────────────────────────────

_MODEL = "gpt-4o-mini"   # vision-capable, cost-efficient

# ── System prompt ─────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a vehicle damage assessment assistant for an insurance claim system. "
    "Analyze the provided vehicle image and give an independent second opinion on "
    "any visible damage. "
    "Do not invent damage that is not visually supported by the image. "
    "Do not provide a final insurance payout decision. "
    "Do not provide a precise repair price. "
    "Base your assessment solely on what is visible in the image."
)

# ── JSON schema for structured output ────────────────────────────────────

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "damage_present": {
            "type": "boolean",
            "description": "True if visible vehicle damage is present in the image."
        },
        "damage_type": {
            "type": "string",
            "description": (
                "Primary damage type visible (e.g. dent, scratch, crack, "
                "glass shatter, broken lamp, flat tire). "
                "Use 'unknown' if the type cannot be determined. "
                "Use 'none' if no damage is present."
            )
        },
        "severity": {
            "type": "string",
            "enum": ["minor", "moderate", "severe", "unknown", "none"],
            "description": "Severity of the damage. Use 'none' if no damage is present."
        },
        "affected_part": {
            "type": "string",
            "description": (
                "Vehicle part most affected (e.g. front bumper, rear door, "
                "windshield, headlight). Use 'none' if no damage is present."
            )
        },
        "visual_assessment": {
            "type": "string",
            "description": (
                "A concise 1-3 sentence description of what is visually observed "
                "in the image regarding vehicle condition and damage."
            )
        },
        "confidence": {
            "type": "number",
            "description": "Confidence in this assessment, between 0.0 and 1.0."
        },
        "agrees_with_yolo": {
            "type": "boolean",
            "description": (
                "True if this assessment broadly agrees with the YOLO detection "
                "result provided in the prompt context."
            )
        }
    },
    "required": [
        "damage_present",
        "damage_type",
        "severity",
        "affected_part",
        "visual_assessment",
        "confidence",
        "agrees_with_yolo"
    ],
    "additionalProperties": False
}


def _encode_image(image_path: str) -> str:
    """Read image from disk and return a base64-encoded data URI."""
    ext = image_path.rsplit(".", 1)[-1].lower()
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _build_yolo_context(yolo_detections: list) -> str:
    """Format YOLO detections as a readable context string for the prompt."""
    if not yolo_detections:
        return "YOLO detected no damage in this image."

    lines = ["YOLO damage detection results:"]
    for i, d in enumerate(yolo_detections, 1):
        dtype = d.get("damage_type", "unknown")
        conf  = d.get("confidence", 0.0)
        lines.append(f"  {i}. {dtype} (confidence: {round(conf * 100)}%)")
    return "\n".join(lines)


def _clamp_confidence(value) -> float:
    """Ensure confidence is a float in [0.0, 1.0]."""
    try:
        v = float(value)
        return max(0.0, min(1.0, v))
    except (TypeError, ValueError):
        return 0.5


def analyze_damage_with_openai(image_path: str, yolo_detections: list) -> dict:
    """
    Send the image to OpenAI Vision for an independent damage assessment.

    Parameters
    ----------
    image_path      : absolute path to the saved image file on disk
    yolo_detections : list of dicts returned by detect_damage()

    Returns
    -------
    dict with keys:
        available, damage_present, damage_type, severity,
        affected_part, visual_assessment, confidence, agrees_with_yolo
    On any failure, returns _FALLBACK (available=False) so the upload
    workflow continues uninterrupted.
    """

    # ── 1. Check API key ──────────────────────────────────────────────────
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "YOUR_KEY_HERE":
        logger.warning("OPENAI_API_KEY is not configured — skipping OpenAI analysis.")
        return dict(_FALLBACK)

    # ── 2. Encode image ───────────────────────────────────────────────────
    try:
        image_data_uri = _encode_image(image_path)
    except Exception as exc:
        logger.error("OpenAI: failed to encode image '%s': %s", image_path, exc)
        return dict(_FALLBACK)

    # ── 3. Build prompt ───────────────────────────────────────────────────
    yolo_context = _build_yolo_context(yolo_detections)

    user_text = (
        f"{yolo_context}\n\n"
        "Please independently inspect the vehicle image above and provide your "
        "own damage assessment as a second opinion. "
        "Respond with a JSON object matching the required schema exactly."
    )

    # ── 4. Call OpenAI ────────────────────────────────────────────────────
    try:
        from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=_MODEL,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "damage_assessment",
                    "strict": True,
                    "schema": _RESPONSE_SCHEMA,
                }
            },
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_uri, "detail": "high"},
                        },
                        {"type": "text", "text": user_text},
                    ],
                },
            ],
            max_tokens=512,
            timeout=30,
        )

    except APIConnectionError:
        logger.error("OpenAI: connection error — network unreachable.")
        return dict(_FALLBACK)
    except APITimeoutError:
        logger.error("OpenAI: request timed out.")
        return dict(_FALLBACK)
    except RateLimitError:
        logger.error("OpenAI: rate limit reached.")
        return dict(_FALLBACK)
    except Exception as exc:
        logger.error("OpenAI: unexpected API error: %s", type(exc).__name__)
        return dict(_FALLBACK)

    # ── 5. Parse response ─────────────────────────────────────────────────
    try:
        raw_content = response.choices[0].message.content
        parsed = json.loads(raw_content)
    except Exception as exc:
        logger.error("OpenAI: failed to parse response JSON: %s", exc)
        return dict(_FALLBACK)

    # ── 6. Validate and sanitise fields ───────────────────────────────────
    valid_severities = {"minor", "moderate", "severe", "unknown", "none"}

    try:
        result = {
            "available":         True,
            "error":             None,
            "damage_present":    bool(parsed.get("damage_present", False)),
            "damage_type":       str(parsed.get("damage_type", "unknown"))[:100],
            "severity":          (
                parsed.get("severity", "unknown")
                if parsed.get("severity") in valid_severities
                else "unknown"
            ),
            "affected_part":     str(parsed.get("affected_part", "unknown"))[:100],
            "visual_assessment": str(parsed.get("visual_assessment", ""))[:1000],
            "confidence":        _clamp_confidence(parsed.get("confidence", 0.5)),
            "agrees_with_yolo":  bool(parsed.get("agrees_with_yolo", False)),
        }
    except Exception as exc:
        logger.error("OpenAI: failed to sanitise parsed response: %s", exc)
        return dict(_FALLBACK)

    return result
