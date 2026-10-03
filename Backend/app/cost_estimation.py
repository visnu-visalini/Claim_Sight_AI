# Rule-based prototype cost estimation for ClaimSightAI.
# These are illustrative ranges only — NOT real insurance quotations.

# OpenAI severity → cost multiplier (applied on top of YOLO baseline)
SEVERITY_MODIFIERS = {
    "minor":    0.90,
    "moderate": 1.00,
    "severe":   1.20,
}

COST_TABLE = {
    "dent":          {"min": 3000,  "max": 8000},
    "scratch":       {"min": 2000,  "max": 6000},
    "crack":         {"min": 4000,  "max": 12000},
    "glass shatter": {"min": 8000,  "max": 25000},
    "broken lamp":   {"min": 5000,  "max": 15000},
    "flat tire":     {"min": 2000,  "max": 6000},
}

ESTIMATION_METHOD = (
    "Rule-based prototype estimate using detected damage type and AI confidence. "
    "Actual repair costs may vary based on vehicle model, parts, labour, "
    "location, and repair shop."
)


def estimate_single(damage_type, confidence):
    """
    Return cost estimate for one detected damage.

    confidence adjusts the estimate within the range:
      - low confidence  → closer to min
      - high confidence → closer to max

    Returns a dict with min, max, average, and status.
    """
    if not damage_type:
        return None

    key = damage_type.strip().lower()
    entry = COST_TABLE.get(key)

    if entry is None:
        # Unknown damage type — do not invent a price
        return {
            "damage_type": damage_type,
            "confidence": confidence,
            "estimated_min": None,
            "estimated_max": None,
            "estimated_average": None,
            "status": "unknown_damage_type",
            "note": (
                f"Damage type '{damage_type}' is not in the estimation table. "
                "Manual assessment required."
            ),
        }

    low = entry["min"]
    high = entry["max"]

    # Scale within range using confidence (default 0.5 if missing)
    conf = confidence if confidence is not None else 0.5
    conf = max(0.0, min(1.0, conf))          # clamp to [0, 1]

    estimated_min = low
    estimated_max = high
    estimated_average = round(low + conf * (high - low))

    return {
        "damage_type": damage_type,
        "confidence": confidence,
        "estimated_min": estimated_min,
        "estimated_max": estimated_max,
        "estimated_average": estimated_average,
        "status": "estimated",
        "note": None,
    }


def _openai_modifier(img):
    """
    Return (factor, reason) based on OpenAI fields on a ClaimImage.
    Returns (1.0, None) when OpenAI is unavailable or damage_present is False.
    Never invents a price — only scales the YOLO baseline.
    """
    if not getattr(img, "openai_available", False):
        return 1.0, None

    if not getattr(img, "openai_damage_present", False):
        return 1.0, None

    severity = (getattr(img, "openai_severity", None) or "").strip().lower()
    factor = SEVERITY_MODIFIERS.get(severity, 1.0)

    agrees = getattr(img, "openai_agrees_with_yolo", None)
    if agrees is False:
        # Disagreement: apply modifier conservatively (cap at 1.0 upward)
        factor = min(factor, 1.0)
        reason = f"OpenAI disagrees with YOLO; conservative modifier applied (severity={severity or 'unknown'})"
    else:
        reason = f"OpenAI severity modifier applied (severity={severity or 'unknown'})"

    return factor, reason


def estimate_claim(images):
    """
    Given a list of ClaimImage ORM objects, compute the full claim estimate.

    Only images where damage_detected=True are included.
    Each image contributes one damage item (the best detection already stored).
    Returns a structured dict ready to be serialised as JSON.
    """
    damage_items = []
    total_min = 0
    total_max = 0
    total_average = 0
    has_unknown = False
    any_openai_adjustment = False

    for img in images:
        if not img.damage_detected:
            continue

        item = estimate_single(img.damage_type, img.confidence)

        if item is None:
            continue

        item["image_id"] = img.id
        item["filename"] = img.filename

        # --- OpenAI modifier (only touches estimated values, not COST_TABLE) ---
        factor, reason = _openai_modifier(img)
        openai_adjusted = factor != 1.0 or reason is not None

        if openai_adjusted and item["status"] == "estimated":
            item["estimated_min"]     = round(item["estimated_min"]     * factor)
            item["estimated_max"]     = round(item["estimated_max"]     * factor)
            item["estimated_average"] = round(item["estimated_average"] * factor)
            # Ensure logical ordering after scaling
            if item["estimated_min"] > item["estimated_max"]:
                item["estimated_min"], item["estimated_max"] = (
                    item["estimated_max"], item["estimated_min"]
                )
            any_openai_adjustment = True

        item["openai_adjustment_applied"] = openai_adjusted and item["status"] == "estimated"
        item["openai_adjustment_factor"]  = factor if item["openai_adjustment_applied"] else None
        item["openai_adjustment_reason"]  = reason if item["openai_adjustment_applied"] else None
        # ----------------------------------------------------------------------

        damage_items.append(item)

        if item["status"] == "estimated":
            total_min     += item["estimated_min"]
            total_max     += item["estimated_max"]
            total_average += item["estimated_average"]
        else:
            has_unknown = True

    if not damage_items:
        return {
            "has_damage": False,
            "damage_items": [],
            "total_estimated_min": 0,
            "total_estimated_max": 0,
            "total_estimated_average": 0,
            "has_unknown_damage": False,
            "estimation_method": ESTIMATION_METHOD,
            "openai_adjustment_applied": False,
            "openai_adjustment_factor": None,
            "openai_adjustment_reason": None,
        }

    return {
        "has_damage": True,
        "damage_items": damage_items,
        "total_estimated_min": total_min,
        "total_estimated_max": total_max,
        "total_estimated_average": total_average,
        "has_unknown_damage": has_unknown,
        "estimation_method": ESTIMATION_METHOD,
        "openai_adjustment_applied": any_openai_adjustment,
        "openai_adjustment_factor": None,   # per-item; see damage_items
        "openai_adjustment_reason": None,   # per-item; see damage_items
    }
