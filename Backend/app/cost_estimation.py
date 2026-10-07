# Rule-based prototype cost estimation for ClaimSightAI.
# These are illustrative ranges only — NOT real insurance quotations.
#
# WEIGHTING MODEL (equal authority):
#   YOLO weight   = 0.50
#   OpenAI weight = 0.50
#
# Neither model is the sole authority. Both contribute equally to the
# combined damage type selection and combined confidence score used for
# cost estimation. OpenAI never directly sets a rupee amount.

# ── Weights ───────────────────────────────────────────────────────────────
YOLO_WEIGHT   = 0.50
OPENAI_WEIGHT = 0.50

# ── OpenAI severity → cost multiplier ────────────────────────────────────
# Applied only when OpenAI is available and damage is present.
SEVERITY_MODIFIERS = {
    "minor":    0.90,
    "moderate": 1.00,
    "severe":   1.20,
}

# Maps YOLO label variants to the canonical COST_TABLE key.
# Keep in sync with _DAMAGE_LABEL_ALIASES in ai_openai.py.
LABEL_ALIASES = {
    "tire_flat":   "flat tire",
    "lamp_broken": "broken lamp",
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
    "Combined 50/50 YOLO + OpenAI Vision estimate using detected damage type "
    "and combined AI confidence. "
    "Actual repair costs may vary based on vehicle model, parts, labour, "
    "location, and repair shop."
)


def _normalize(label) -> str:
    """Lowercase, strip, apply LABEL_ALIASES. Returns '' for None/empty."""
    if not label:
        return ""
    key = label.strip().lower()
    return LABEL_ALIASES.get(key, key)


def combine_damage_assessment(img) -> dict:
    """
    Combine YOLO and OpenAI damage assessments with equal 50/50 weighting.

    YOLO weight   = 0.50  (YOLO_WEIGHT)
    OpenAI weight = 0.50  (OPENAI_WEIGHT)

    Decision logic
    ──────────────
    Case 1 — Both available, same damage type after normalisation:
        combined_damage_type = that type
        combined_confidence  = (yolo_conf * 0.50) + (openai_conf * 0.50)

    Case 2 — Both available, different damage types:
        Each type gets its weighted score.
        The type with the higher weighted score wins.
        combined_confidence = winning weighted score.

    Case 3 — Only YOLO available (OpenAI unavailable/no damage):
        combined_damage_type = YOLO type
        combined_confidence  = yolo_conf * 0.50
        (OpenAI contributes 0 — its 50% slot is empty)

    Case 4 — Only OpenAI available (YOLO detected nothing / unknown):
        combined_damage_type = OpenAI type
        combined_confidence  = openai_conf * 0.50

    Case 5 — Neither has a valid damage type:
        combined_damage_type = None  → triggers unknown_damage_type path

    Returns dict with:
        combined_damage_type  : str | None
        combined_confidence   : float
        yolo_weight           : float  (always YOLO_WEIGHT)
        openai_weight         : float  (always OPENAI_WEIGHT)
        combination_note      : str    (human-readable explanation)
    """
    yolo_type = _normalize(getattr(img, "damage_type", None))
    yolo_conf = float(getattr(img, "confidence", 0.0) or 0.0)

    openai_ok   = bool(getattr(img, "openai_available", False))
    openai_dmg  = bool(getattr(img, "openai_damage_present", False))
    openai_type = _normalize(getattr(img, "openai_damage_type", None))
    openai_conf = float(getattr(img, "openai_confidence", 0.0) or 0.0)

    # OpenAI only contributes when it is available AND reports damage present
    openai_active = openai_ok and openai_dmg and bool(openai_type) and openai_type not in ("none", "unknown")

    yolo_active = bool(yolo_type) and yolo_type not in ("none", "unknown")

    # ── Case 5: nothing usable ────────────────────────────────────────────
    if not yolo_active and not openai_active:
        return {
            "combined_damage_type": None,
            "combined_confidence":  0.0,
            "yolo_weight":          YOLO_WEIGHT,
            "openai_weight":        OPENAI_WEIGHT,
            "combination_note":     "Neither YOLO nor OpenAI produced a usable damage type.",
        }

    # ── Case 3: YOLO only ─────────────────────────────────────────────────
    if yolo_active and not openai_active:
        combined_conf = round(yolo_conf * YOLO_WEIGHT, 4)
        note = (
            f"YOLO only (OpenAI unavailable or no damage). "
            f"YOLO: {yolo_type} @ {yolo_conf:.4f} × {YOLO_WEIGHT} = {combined_conf:.4f}."
        )
        return {
            "combined_damage_type": yolo_type,
            "combined_confidence":  combined_conf,
            "yolo_weight":          YOLO_WEIGHT,
            "openai_weight":        OPENAI_WEIGHT,
            "combination_note":     note,
        }

    # ── Case 4: OpenAI only ───────────────────────────────────────────────
    if openai_active and not yolo_active:
        combined_conf = round(openai_conf * OPENAI_WEIGHT, 4)
        note = (
            f"OpenAI only (YOLO had no valid detection). "
            f"OpenAI: {openai_type} @ {openai_conf:.4f} × {OPENAI_WEIGHT} = {combined_conf:.4f}."
        )
        return {
            "combined_damage_type": openai_type,
            "combined_confidence":  combined_conf,
            "yolo_weight":          YOLO_WEIGHT,
            "openai_weight":        OPENAI_WEIGHT,
            "combination_note":     note,
        }

    # ── Both active ───────────────────────────────────────────────────────
    yolo_score   = round(yolo_conf   * YOLO_WEIGHT,   4)
    openai_score = round(openai_conf * OPENAI_WEIGHT, 4)

    # Case 1: same type after normalisation
    if yolo_type == openai_type:
        combined_conf = round(yolo_score + openai_score, 4)
        note = (
            f"Agreement: both identified '{yolo_type}'. "
            f"({yolo_conf:.4f} × {YOLO_WEIGHT}) + ({openai_conf:.4f} × {OPENAI_WEIGHT}) "
            f"= {combined_conf:.4f}."
        )
        return {
            "combined_damage_type": yolo_type,
            "combined_confidence":  combined_conf,
            "yolo_weight":          YOLO_WEIGHT,
            "openai_weight":        OPENAI_WEIGHT,
            "combination_note":     note,
        }

    # Case 2: different types — higher weighted score wins
    if yolo_score >= openai_score:
        winner, winner_score, loser = yolo_type, yolo_score, openai_type
    else:
        winner, winner_score, loser = openai_type, openai_score, yolo_type

    note = (
        f"Disagreement: YOLO='{yolo_type}' (score {yolo_score:.4f}), "
        f"OpenAI='{openai_type}' (score {openai_score:.4f}). "
        f"'{winner}' wins with higher weighted score {winner_score:.4f}."
    )
    return {
        "combined_damage_type": winner,
        "combined_confidence":  winner_score,
        "yolo_weight":          YOLO_WEIGHT,
        "openai_weight":        OPENAI_WEIGHT,
        "combination_note":     note,
    }


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
    key = LABEL_ALIASES.get(key, key)   # normalize YOLO label → COST_TABLE key
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

    low  = entry["min"]
    high = entry["max"]

    conf = confidence if confidence is not None else 0.5
    conf = max(0.0, min(1.0, conf))

    estimated_min     = low
    estimated_max     = high
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


def _openai_severity_modifier(img):
    """
    Return (factor, reason) based on OpenAI severity field.

    YOLO weight   = 0.50
    OpenAI weight = 0.50

    The severity modifier is only applied when OpenAI is available and
    reports damage. It scales the combined estimate — it never sets a
    rupee amount directly.
    Returns (1.0, None) when OpenAI is unavailable or damage_present is False.
    """
    if not getattr(img, "openai_available", False):
        return 1.0, None

    if not getattr(img, "openai_damage_present", False):
        return 1.0, None

    severity = (getattr(img, "openai_severity", None) or "").strip().lower()
    factor   = SEVERITY_MODIFIERS.get(severity, 1.0)

    agrees = getattr(img, "openai_agrees_with_yolo", None)
    if agrees is False:
        # Disagreement: apply modifier conservatively (cap upward at 1.0)
        factor = min(factor, 1.0)
        reason = (
            f"OpenAI disagrees with YOLO; conservative severity modifier applied "
            f"(severity={severity or 'unknown'}). "
            f"YOLO weight={YOLO_WEIGHT}, OpenAI weight={OPENAI_WEIGHT}."
        )
    else:
        reason = (
            f"OpenAI severity modifier applied (severity={severity or 'unknown'}). "
            f"YOLO weight={YOLO_WEIGHT}, OpenAI weight={OPENAI_WEIGHT}."
        )

    return factor, reason


def estimate_claim(images):
    """
    Given a list of ClaimImage ORM objects, compute the full claim estimate.

    YOLO weight   = 0.50
    OpenAI weight = 0.50

    For each damaged image:
      1. combine_damage_assessment() selects the combined_damage_type and
         combined_confidence using equal 50/50 weighting.
      2. estimate_single() looks up the COST_TABLE using combined_damage_type.
      3. combined_confidence drives the position within the cost range.
      4. _openai_severity_modifier() optionally scales the result.

    OpenAI never directly sets a rupee amount — all prices come from COST_TABLE.
    Returns a structured dict ready to be serialised as JSON.
    """
    damage_items      = []
    total_min         = 0
    total_max         = 0
    total_average     = 0
    has_unknown       = False
    any_openai_adjust = False

    for img in images:
        if not img.damage_detected:
            # Also check if OpenAI found damage when YOLO did not
            openai_ok  = bool(getattr(img, "openai_available", False))
            openai_dmg = bool(getattr(img, "openai_damage_present", False))
            if not (openai_ok and openai_dmg):
                continue
            # OpenAI found damage but YOLO did not — still run combination
            # (combine_damage_assessment handles the YOLO-inactive case)

        # ── 50/50 combination ─────────────────────────────────────────────
        combo = combine_damage_assessment(img)
        combined_type = combo["combined_damage_type"]
        combined_conf = combo["combined_confidence"]

        item = estimate_single(combined_type, combined_conf)

        if item is None:
            continue

        item["image_id"] = img.id
        item["filename"] = img.filename

        # Attach combination metadata for API transparency
        item["combined_damage_type"] = combo["combined_damage_type"]
        item["combined_confidence"]  = combo["combined_confidence"]
        item["yolo_weight"]          = combo["yolo_weight"]
        item["openai_weight"]        = combo["openai_weight"]
        item["combination_note"]     = combo["combination_note"]

        # ── OpenAI severity modifier ──────────────────────────────────────
        factor, reason = _openai_severity_modifier(img)
        openai_adjusted = factor != 1.0 or reason is not None

        if openai_adjusted and item["status"] == "estimated":
            item["estimated_min"]     = round(item["estimated_min"]     * factor)
            item["estimated_max"]     = round(item["estimated_max"]     * factor)
            item["estimated_average"] = round(item["estimated_average"] * factor)
            if item["estimated_min"] > item["estimated_max"]:
                item["estimated_min"], item["estimated_max"] = (
                    item["estimated_max"], item["estimated_min"]
                )
            any_openai_adjust = True

        item["openai_adjustment_applied"] = openai_adjusted and item["status"] == "estimated"
        item["openai_adjustment_factor"]  = factor if item["openai_adjustment_applied"] else None
        item["openai_adjustment_reason"]  = reason if item["openai_adjustment_applied"] else None

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
        "openai_adjustment_applied": any_openai_adjust,
        # Aggregate the representative top-level factor from per-item values.
        # Use the first item that actually had an adjustment applied.
        # The per-item detail remains available in damage_items.
        "openai_adjustment_factor": next(
            (item["openai_adjustment_factor"]
             for item in damage_items
             if item.get("openai_adjustment_applied")),
            None,
        ),
        "openai_adjustment_reason": next(
            (item["openai_adjustment_reason"]
             for item in damage_items
             if item.get("openai_adjustment_applied")),
            None,
        ),
    }
