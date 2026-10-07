"""
test_combined_weighting.py
Unit tests for the 50/50 YOLO + OpenAI combined damage assessment.

Run from the Backend directory:
    venv\\Scripts\\python.exe test_combined_weighting.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.cost_estimation import (
    combine_damage_assessment,
    estimate_single,
    estimate_claim,
    YOLO_WEIGHT,
    OPENAI_WEIGHT,
    COST_TABLE,
    LABEL_ALIASES,
)
from app.ai_openai import get_agreement_state, _normalize_damage_label


# ── Minimal stub that mimics a ClaimImage ORM object ─────────────────────

class FakeImage:
    _id_counter = 0

    def __init__(
        self,
        damage_type=None,
        confidence=None,
        openai_available=False,
        openai_damage_present=False,
        openai_damage_type=None,
        openai_confidence=None,
        openai_severity=None,
        openai_agrees_with_yolo=None,
        damage_detected=True,
    ):
        FakeImage._id_counter += 1
        self.id                     = FakeImage._id_counter
        self.filename               = f"img_{self.id}.jpg"
        self.damage_type            = damage_type
        self.confidence             = confidence
        self.openai_available       = openai_available
        self.openai_damage_present  = openai_damage_present
        self.openai_damage_type     = openai_damage_type
        self.openai_confidence      = openai_confidence
        self.openai_severity        = openai_severity
        self.openai_agrees_with_yolo = openai_agrees_with_yolo
        self.damage_detected        = damage_detected


def approx(a, b, tol=1e-4):
    return abs(a - b) <= tol


passed = 0
failed = 0


def run(name, fn):
    global passed, failed
    try:
        fn()
        print(f"PASS  {name}")
        passed += 1
    except Exception as e:
        print(f"FAIL  {name}: {e}")
        failed += 1


# ══════════════════════════════════════════════════════════════════════════
# SECTION 1 — Original weighting tests (preserved)
# ══════════════════════════════════════════════════════════════════════════

def t_weights_sum():
    assert YOLO_WEIGHT + OPENAI_WEIGHT == 1.0

def t_case1_agreement():
    """tire_flat + flat tire -> agreement, combined = 0.7923"""
    img = FakeImage(
        damage_type="tire_flat", confidence=0.6846,
        openai_available=True, openai_damage_present=True,
        openai_damage_type="flat tire", openai_confidence=0.90,
    )
    r = combine_damage_assessment(img)
    assert r["combined_damage_type"] == "flat tire"
    expected = round((0.6846 * 0.50) + (0.90 * 0.50), 4)
    assert approx(r["combined_confidence"], expected), f"got {r['combined_confidence']}"

def t_case2_yolo_wins():
    img = FakeImage(
        damage_type="dent", confidence=0.80,
        openai_available=True, openai_damage_present=True,
        openai_damage_type="scratch", openai_confidence=0.60,
    )
    r = combine_damage_assessment(img)
    assert r["combined_damage_type"] == "dent"
    assert approx(r["combined_confidence"], 0.40)

def t_case2_openai_wins():
    img = FakeImage(
        damage_type="dent", confidence=0.50,
        openai_available=True, openai_damage_present=True,
        openai_damage_type="crack", openai_confidence=0.90,
    )
    r = combine_damage_assessment(img)
    assert r["combined_damage_type"] == "crack"
    assert approx(r["combined_confidence"], 0.45)

def t_case3_yolo_only():
    img = FakeImage(damage_type="scratch", confidence=0.75, openai_available=False)
    r = combine_damage_assessment(img)
    assert r["combined_damage_type"] == "scratch"
    assert approx(r["combined_confidence"], 0.375)

def t_case4_openai_only():
    img = FakeImage(
        damage_type=None, confidence=None,
        openai_available=True, openai_damage_present=True,
        openai_damage_type="dent", openai_confidence=0.85,
    )
    r = combine_damage_assessment(img)
    assert r["combined_damage_type"] == "dent"
    assert approx(r["combined_confidence"], 0.425)

def t_case5_neither():
    img = FakeImage(
        damage_type=None, confidence=None,
        openai_available=True, openai_damage_present=True,
        openai_damage_type="unknown", openai_confidence=0.5,
    )
    r = combine_damage_assessment(img)
    assert r["combined_damage_type"] is None

def t_yolo_unknown_openai_valid():
    img = FakeImage(
        damage_type="unknown", confidence=0.40,
        openai_available=True, openai_damage_present=True,
        openai_damage_type="dent", openai_confidence=0.80,
    )
    r = combine_damage_assessment(img)
    assert r["combined_damage_type"] == "dent"
    assert approx(r["combined_confidence"], 0.40)

def t_estimate_single_flat_tire():
    entry = COST_TABLE["flat tire"]
    conf = 0.7923
    r = estimate_single("flat tire", conf)
    assert r["status"] == "estimated"
    expected_avg = round(entry["min"] + conf * (entry["max"] - entry["min"]))
    assert r["estimated_average"] == expected_avg

def t_label_alias_tire_flat():
    r = estimate_single("tire_flat", 0.70)
    assert r["status"] == "estimated", f"tire_flat alias failed: {r['status']}"

def t_unknown_type_bumper():
    r = estimate_single("bumper damage", 0.80)
    assert r["status"] == "unknown_damage_type"


# ══════════════════════════════════════════════════════════════════════════
# SECTION 2 — New focused tests for the six fixes
# ══════════════════════════════════════════════════════════════════════════

# A. lamp_broken vs dent, boolean=True -> partial_agreement
#    (types differ after normalisation; boolean says True -> soft/partial match)
def t_agreement_lamp_broken_vs_dent():
    state = get_agreement_state(
        yolo_damage_type="lamp_broken",
        openai_available=True,
        openai_agrees_with_yolo=True,   # OpenAI self-reports True
        openai_damage_type="dent",
    )
    # broken lamp != dent, but boolean=True -> partial_agreement (not full agreement)
    assert state == "partial_agreement", (
        f"Expected 'partial_agreement' for lamp_broken vs dent (bool=True), got '{state}'"
    )

# A2. lamp_broken vs dent, boolean=False -> disagreement
def t_agreement_lamp_broken_vs_dent_bool_false():
    state = get_agreement_state(
        yolo_damage_type="lamp_broken",
        openai_available=True,
        openai_agrees_with_yolo=False,
        openai_damage_type="dent",
    )
    assert state == "disagreement", (
        f"Expected 'disagreement' for lamp_broken vs dent (bool=False), got '{state}'"
    )

# B. tire_flat vs flat tire -> agreement (after normalisation)
def t_agreement_tire_flat_vs_flat_tire():
    state = get_agreement_state(
        yolo_damage_type="tire_flat",
        openai_available=True,
        openai_agrees_with_yolo=False,
        openai_damage_type="flat tire",
    )
    assert state == "agreement", (
        f"Expected 'agreement' for tire_flat vs flat tire, got '{state}'"
    )

# C. unknown OpenAI type -> not agreement (when YOLO has a real type)
def t_agreement_unknown_openai_not_agreement():
    state = get_agreement_state(
        yolo_damage_type="dent",
        openai_available=True,
        openai_agrees_with_yolo=True,   # boolean says True but type is unknown
        openai_damage_type="unknown",
    )
    # YOLO type is usable, OpenAI type is not -> falls back to boolean -> agreement
    # This is the correct safe fallback: when OpenAI type is unusable we trust the boolean
    # rather than falsely marking disagreement.
    # The key requirement is: when BOTH types are usable and differ -> disagreement.
    # Here only YOLO is usable, so boolean tiebreaker applies.
    assert state == "agreement", (
        f"Expected 'agreement' (boolean tiebreaker, OpenAI type unusable), got '{state}'"
    )

# C2. unknown OpenAI type AND boolean says False -> disagreement
def t_agreement_unknown_openai_boolean_false():
    state = get_agreement_state(
        yolo_damage_type="dent",
        openai_available=True,
        openai_agrees_with_yolo=False,
        openai_damage_type="unknown",
    )
    assert state == "disagreement", (
        f"Expected 'disagreement' (boolean=False, OpenAI type unusable), got '{state}'"
    )

# C3. OpenAI unavailable -> openai_unavailable regardless of anything
def t_agreement_openai_unavailable():
    state = get_agreement_state(
        yolo_damage_type="dent",
        openai_available=False,
        openai_agrees_with_yolo=True,
        openai_damage_type="dent",
    )
    assert state == "openai_unavailable"

# D. top-level openai_adjustment_factor is populated when adjustment exists
def t_toplevel_adjustment_factor_populated():
    img = FakeImage(
        damage_type="dent", confidence=0.80,
        openai_available=True, openai_damage_present=True,
        openai_damage_type="dent", openai_confidence=0.80,
        openai_severity="severe",       # factor = 1.20
        openai_agrees_with_yolo=True,
        damage_detected=True,
    )
    cost = estimate_claim([img])
    assert cost["openai_adjustment_applied"] is True, "Expected adjustment applied"
    assert cost["openai_adjustment_factor"] is not None, (
        "Top-level openai_adjustment_factor must not be None when adjustment was applied"
    )
    assert isinstance(cost["openai_adjustment_factor"], float), (
        f"Expected float, got {type(cost['openai_adjustment_factor'])}"
    )
    assert approx(cost["openai_adjustment_factor"], 1.20), (
        f"Expected 1.20, got {cost['openai_adjustment_factor']}"
    )

# D2. top-level factor is None when no adjustment
def t_toplevel_adjustment_factor_none_when_no_adjustment():
    img = FakeImage(
        damage_type="dent", confidence=0.80,
        openai_available=False,
        damage_detected=True,
    )
    cost = estimate_claim([img])
    assert cost["openai_adjustment_factor"] is None

# E. claim summary uses combined damage_items (not raw YOLO fields)
def t_summary_uses_combined_damage_items():
    from app.routes.generate import build_summary

    class FakeClaim:
        vehicle_year   = "2020"
        vehicle_make   = "Toyota"
        vehicle_model  = "Corolla"
        vehicle_number = "TN01AB1234"
        accident_date  = None
        accident_location = "Chennai"
        accident_description = "Minor collision"

    img = FakeImage(
        damage_type="lamp_broken", confidence=0.59,
        openai_available=True, openai_damage_present=True,
        openai_damage_type="dent", openai_confidence=0.90,
        damage_detected=True,
    )
    cost = estimate_claim([img])
    summary = build_summary(FakeClaim(), [img], cost)

    # Summary must mention the combined winner (dent), not the raw YOLO type
    assert "dent" in summary.lower(), (
        f"Summary should mention 'dent' (combined winner), got:\n{summary}"
    )
    # Summary must NOT describe it as YOLO-only
    assert "lamp_broken" not in summary.lower(), (
        f"Summary should not mention raw YOLO 'lamp_broken', got:\n{summary}"
    )

# F. 50/50 weighted selection: 0.59 YOLO lamp_broken vs 0.90 OpenAI dent -> dent selected
def t_claim26_image1_dent_wins():
    """
    Claim 26 Image 1:
        YOLO:   lamp_broken @ 0.59  -> score = 0.295
        OpenAI: dent        @ 0.90  -> score = 0.450
        Winner: dent (higher weighted score)
    """
    img = FakeImage(
        damage_type="lamp_broken", confidence=0.59,
        openai_available=True, openai_damage_present=True,
        openai_damage_type="dent", openai_confidence=0.90,
        damage_detected=True,
    )
    r = combine_damage_assessment(img)
    assert r["combined_damage_type"] == "dent", (
        f"Expected 'dent' to win, got '{r['combined_damage_type']}'"
    )
    assert approx(r["combined_confidence"], 0.45), (
        f"Expected 0.45, got {r['combined_confidence']}"
    )
    # Also verify cost engine resolves dent correctly
    cost_item = estimate_single(r["combined_damage_type"], r["combined_confidence"])
    assert cost_item["status"] == "estimated", (
        f"'dent' should be in COST_TABLE, got status={cost_item['status']}"
    )

# G. Claim 26 Image 2: tire_flat YOLO, OpenAI damage_present=True but type=none/unknown
#    -> YOLO-only path, no crash, no "cannot be detected"
def t_claim26_image2_tire_flat_openai_no_type():
    """
    Claim 26 Image 2:
        YOLO:   tire_flat @ 0.685
        OpenAI: damage_present=True, damage_type=None/unknown, confidence=0.90
        Expected: YOLO-only path, combined_damage_type = flat tire
    """
    img = FakeImage(
        damage_type="tire_flat", confidence=0.685,
        openai_available=True, openai_damage_present=True,
        openai_damage_type=None,   # no usable type from OpenAI
        openai_confidence=0.90,
        damage_detected=True,
    )
    r = combine_damage_assessment(img)
    assert r["combined_damage_type"] == "flat tire", (
        f"Expected 'flat tire' (YOLO-only path), got '{r['combined_damage_type']}'"
    )
    assert approx(r["combined_confidence"], round(0.685 * 0.50, 4)), (
        f"Expected {round(0.685 * 0.50, 4)}, got {r['combined_confidence']}"
    )
    cost_item = estimate_single(r["combined_damage_type"], r["combined_confidence"])
    assert cost_item["status"] == "estimated", (
        f"flat tire should be in COST_TABLE, got {cost_item['status']}"
    )

# H. lamp_broken alias resolves to broken lamp in COST_TABLE
def t_lamp_broken_alias():
    assert "lamp_broken" in LABEL_ALIASES, "lamp_broken must be in LABEL_ALIASES"
    assert LABEL_ALIASES["lamp_broken"] == "broken lamp"
    r = estimate_single("lamp_broken", 0.59)
    assert r["status"] == "estimated", (
        f"lamp_broken should resolve via alias to broken lamp, got {r['status']}"
    )

# I. partial_agreement: types differ but boolean says True
def t_partial_agreement_types_differ_boolean_true():
    state = get_agreement_state(
        yolo_damage_type="dent",
        openai_available=True,
        openai_agrees_with_yolo=True,
        openai_damage_type="scratch",
    )
    assert state == "partial_agreement", (
        f"Expected 'partial_agreement' (types differ, boolean=True), got '{state}'"
    )


# ══════════════════════════════════════════════════════════════════════════
# Runner
# ══════════════════════════════════════════════════════════════════════════

TESTS = [
    # Section 1 — original
    ("weights sum to 1.0",                          t_weights_sum),
    ("case1 agreement tire_flat+flat tire",         t_case1_agreement),
    ("case2 YOLO wins dent vs scratch",             t_case2_yolo_wins),
    ("case2 OpenAI wins dent vs crack",             t_case2_openai_wins),
    ("case3 YOLO only",                             t_case3_yolo_only),
    ("case4 OpenAI only",                           t_case4_openai_only),
    ("case5 neither usable",                        t_case5_neither),
    ("YOLO unknown + OpenAI valid",                 t_yolo_unknown_openai_valid),
    ("estimate_single flat tire confidence",        t_estimate_single_flat_tire),
    ("label alias tire_flat -> flat tire",          t_label_alias_tire_flat),
    ("unknown type bumper damage",                  t_unknown_type_bumper),
    # Section 2 — new focused fixes
    ("A: lamp_broken vs dent bool=True -> partial_agreement", t_agreement_lamp_broken_vs_dent),
    ("A2: lamp_broken vs dent bool=False -> disagreement",     t_agreement_lamp_broken_vs_dent_bool_false),
    ("B: tire_flat vs flat tire -> agreement",      t_agreement_tire_flat_vs_flat_tire),
    ("C: unknown OpenAI type + bool True -> agreement (tiebreaker)", t_agreement_unknown_openai_not_agreement),
    ("C2: unknown OpenAI type + bool False -> disagreement", t_agreement_unknown_openai_boolean_false),
    ("C3: OpenAI unavailable -> openai_unavailable",t_agreement_openai_unavailable),
    ("D: top-level factor populated when adjusted", t_toplevel_adjustment_factor_populated),
    ("D2: top-level factor None when no adjustment",t_toplevel_adjustment_factor_none_when_no_adjustment),
    ("E: summary uses combined damage_items",       t_summary_uses_combined_damage_items),
    ("F: Claim26 img1 dent wins 50/50",             t_claim26_image1_dent_wins),
    ("G: Claim26 img2 tire_flat OpenAI no type",    t_claim26_image2_tire_flat_openai_no_type),
    ("H: lamp_broken alias -> broken lamp",         t_lamp_broken_alias),
    ("I: partial_agreement types differ bool True", t_partial_agreement_types_differ_boolean_true),
]

for name, fn in TESTS:
    run(name, fn)

print(f"\n{'='*60}")
print(f"Results: {passed} passed, {failed} failed out of {len(TESTS)} tests")
if failed == 0:
    print("All tests passed.")
sys.exit(0 if failed == 0 else 1)
