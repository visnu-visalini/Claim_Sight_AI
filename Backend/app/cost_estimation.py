# Rule-based prototype cost estimation for ClaimSightAI.
# These are illustrative ranges only — NOT real insurance quotations.

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

    for img in images:
        if not img.damage_detected:
            continue

        item = estimate_single(img.damage_type, img.confidence)

        if item is None:
            continue

        item["image_id"] = img.id
        item["filename"] = img.filename
        damage_items.append(item)

        if item["status"] == "estimated":
            total_min += item["estimated_min"]
            total_max += item["estimated_max"]
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
        }

    return {
        "has_damage": True,
        "damage_items": damage_items,
        "total_estimated_min": total_min,
        "total_estimated_max": total_max,
        "total_estimated_average": total_average,
        "has_unknown_damage": has_unknown,
        "estimation_method": ESTIMATION_METHOD,
    }
