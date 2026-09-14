"""
congestion_score.py
--------------------
Computes an interpretable congestion score (0-1) and classification (LOW/MEDIUM/HIGH)
for a single approach, based on the spec's Section 7 requirements.

This is deliberately simple and rule-based (not ML) so it stays explainable and acts
as a reliable fallback even if the prediction model underperforms.
"""

# ---- Reference ranges used for normalization ----
# These define what counts as "0% congested" and "100% congested" for each metric.
# TUNE THESE once you have real traffic_state data from the CV pipeline (Sprint 2) --
# right now they're reasonable starting guesses for a moderately busy urban intersection.

REFERENCE_RANGES = {
    "queue_length": {"min": 0, "max": 100},      # meters (or vehicle count, once M1 confirms unit)
    "vehicle_count": {"min": 0, "max": 60},        # vehicles observed in the approach
    "average_speed": {"min": 0, "max": 15},        # m/s -- note: LOWER speed = MORE congestion
}

# ---- Weights: how much each factor contributes to the final score ----
# Must sum to 1.0. These are a reasonable starting point -- tune after testing on real data.
# NOTE: dropped waiting_time -- it's not in our locked data_contracts.md (CV->ML only sends
# vehicles/queue_length/average_speed), and adding it would mean extra work for the CV module
# for a formula that already works well with 3 factors. Re-weighted to compensate.
WEIGHTS = {
    "queue_length": 0.45,
    "vehicle_count": 0.30,
    "average_speed": 0.25,   # applied as (1 - normalized speed), since slower = worse
}


def normalize(value, metric_name):
    """Scale a raw value to 0-1 based on the reference range for that metric."""
    r = REFERENCE_RANGES[metric_name]
    if r["max"] == r["min"]:
        return 0.0
    normalized = (value - r["min"]) / (r["max"] - r["min"])
    return max(0.0, min(1.0, normalized))  # clip to [0, 1] in case real data exceeds the assumed range


def compute_congestion_score(queue_length, vehicle_count, average_speed):
    """
    Returns a dict with the raw score (0-1) and the LOW/MEDIUM/HIGH classification,
    plus each normalized component so you can explain WHY the score came out this way.

    Inputs match the locked CV->ML data contract exactly: queue_length, vehicle_count
    (from 'vehicles'), average_speed -- no extra fields required from the CV module.
    """
    norm_queue = normalize(queue_length, "queue_length")
    norm_count = normalize(vehicle_count, "vehicle_count")
    norm_speed = normalize(average_speed, "average_speed")

    # Speed is inverted: a HIGH speed means LOW congestion contribution
    speed_congestion_component = 1 - norm_speed

    score = (
        WEIGHTS["queue_length"] * norm_queue
        + WEIGHTS["vehicle_count"] * norm_count
        + WEIGHTS["average_speed"] * speed_congestion_component
    )
    score = round(score, 3)

    # Classification thresholds -- tune these after testing on real data
    if score < 0.35:
        level = "LOW"
    elif score < 0.65:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return {
        "score": score,
        "level": level,
        "components": {
            "queue_length_normalized": round(norm_queue, 3),
            "vehicle_count_normalized": round(norm_count, 3),
            "speed_congestion_normalized": round(speed_congestion_component, 3),
        },
    }


if __name__ == "__main__":
    # ---- Quick test on synthetic data, matching the spec's example JSON (Section 5) ----
    test_cases = [
        {"name": "North (from spec example)", "queue_length": 82, "vehicle_count": 42, "average_speed": 11.5 / 3.6},
        {"name": "South (from spec example)", "queue_length": 57, "vehicle_count": 31, "average_speed": 14.2 / 3.6},
        {"name": "East (from spec example)",  "queue_length": 18, "vehicle_count": 12, "average_speed": 24.1 / 3.6},
        {"name": "West (from spec example)",  "queue_length": 23, "vehicle_count": 17, "average_speed": 21.3 / 3.6},
        {"name": "Empty road (sanity check)", "queue_length": 0,  "vehicle_count": 0,  "average_speed": 15},
        {"name": "Gridlock (sanity check)",   "queue_length": 100,"vehicle_count": 60, "average_speed": 0},
    ]

    print(f"{'Approach':<28} {'Score':<8} {'Level':<8}")
    print("-" * 45)
    for case in test_cases:
        result = compute_congestion_score(
            case["queue_length"], case["vehicle_count"], case["average_speed"]
        )
        print(f"{case['name']:<28} {result['score']:<8} {result['level']:<8}")
