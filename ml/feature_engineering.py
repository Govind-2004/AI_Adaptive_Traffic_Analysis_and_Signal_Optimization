"""
feature_engineering.py
------------------------
Turns a SEQUENCE of raw traffic_state readings (matching the locked CV->ML contract)
into feature vectors + labels ready for training the prediction model.

WHY this exists as a separate step:
A single traffic_state reading only tells you "what's happening right now" -- it has
no sense of trend or momentum. The prediction model needs to see recent HISTORY to
learn patterns like "queue has been rising steadily -> likely to keep rising."
This module is responsible for turning a list of historical readings into a clean,
fixed-size numeric feature vector the model can actually train on.
"""

from congestion_score import compute_congestion_score

# How many past readings to look back on when building one feature vector.
# 4 readings at a 5-second interval = 20 seconds of history informing each prediction.
LOOKBACK_WINDOW = 4

# How many readings ahead we're trying to predict (the "label").
# e.g., PREDICTION_HORIZON=6 at a 5-second interval = predicting ~30 seconds ahead.
PREDICTION_HORIZON = 6


def extract_features_for_approach(readings, approach_name, current_phase_is_green):
    """
    Given a list of raw traffic_state readings (dicts, oldest first) for ONE approach,
    build a single feature vector representing "the situation right now."

    readings: list of dicts, each like {"vehicles": 42, "queue_length": 82, "average_speed": 11.5}
              must contain at least LOOKBACK_WINDOW entries, most recent last.
    approach_name: e.g. "north" -- used only for labeling, not part of the math.
    current_phase_is_green: bool -- whether this approach currently has a green light.

    Returns: a flat dict of named features (easy to inspect/debug), which can be
             converted to a plain list/array right before feeding into a model.
    """
    if len(readings) < LOOKBACK_WINDOW:
        raise ValueError(
            f"Need at least {LOOKBACK_WINDOW} readings to build features, got {len(readings)}"
        )

    window = readings[-LOOKBACK_WINDOW:]  # most recent LOOKBACK_WINDOW readings
    current = window[-1]
    previous = window[-2]

    # --- Basic current-state features ---
    current_count = current["vehicles"]
    current_queue = current["queue_length"]
    current_speed = current["average_speed"]

    # --- Trend features: how much things changed since the last reading ---
    count_trend = current_count - previous["vehicles"]
    queue_trend = current_queue - previous["queue_length"]
    speed_trend = current_speed - previous["average_speed"]

    # --- Short history features: average over the whole lookback window ---
    avg_count_over_window = sum(r["vehicles"] for r in window) / len(window)
    avg_queue_over_window = sum(r["queue_length"] for r in window) / len(window)

    avg_speed_over_window = sum(
    r["average_speed"] for r in window
) / len(window)

    # --- Reuse the congestion score formula we already built (Sprint 1) ---
    congestion = compute_congestion_score(current_queue, current_count, current_speed)

    # --- Signal context ---
    phase_feature = 1 if current_phase_is_green else 0

    return {
        "approach": approach_name,
        "current_count": current_count,
        "current_queue": current_queue,
        "current_speed": current_speed,
        "count_trend": count_trend,
        "queue_trend": queue_trend,
        "speed_trend": speed_trend,
        "avg_count_over_window": round(avg_count_over_window, 2),
        "avg_queue_over_window": round(avg_queue_over_window, 2),
        "avg_speed_over_window": round(avg_speed_over_window, 2),
        "congestion_score": congestion["score"],
        "is_green": phase_feature,
    }


def feature_dict_to_vector(feature_dict):
    """
    Converts the named feature dict into a plain ordered list of numbers --
    this is the actual shape scikit-learn models expect as input.
    Keeping this as a separate function means we always know EXACTLY which
    feature corresponds to which position, in one single place.
    """
    return [
    feature_dict["current_count"],
    feature_dict["current_queue"],
    feature_dict["current_speed"],
    feature_dict["count_trend"],
    feature_dict["queue_trend"],
    feature_dict["speed_trend"],
    feature_dict["avg_count_over_window"],
    feature_dict["avg_queue_over_window"],
    feature_dict["avg_speed_over_window"],
    feature_dict["congestion_score"],
    feature_dict["is_green"],
    ]

FEATURE_NAMES = [
    "current_count", "current_queue", "current_speed",
    "count_trend", "queue_trend", "speed_trend",
    "avg_count_over_window", "avg_queue_over_window",
    "avg_speed_over_window",
    "congestion_score", "is_green",
]


def build_training_examples(full_reading_history, approach_name, phase_history):
    """
    Slides a window across a FULL historical sequence of readings for one approach,
    producing many (features, label) training pairs -- this is what turns one video's
    worth of data into dozens/hundreds of usable training examples.

    full_reading_history: list of dicts (the whole video's readings for this approach)
    phase_history: list of bools, same length, whether this approach was green at each reading
    Returns: list of (feature_vector, label) tuples, ready for model.fit()
    """
    examples = []
    n = len(full_reading_history)

    # We need LOOKBACK_WINDOW readings before, and PREDICTION_HORIZON readings after,
    # so we slide from index LOOKBACK_WINDOW-1 up to n - PREDICTION_HORIZON - 1.
    for i in range(LOOKBACK_WINDOW - 1, n - PREDICTION_HORIZON):
        window = full_reading_history[: i + 1]  # everything up to and including "now"
        feature_dict = extract_features_for_approach(
            window, approach_name, phase_history[i]
        )
        feature_vector = feature_dict_to_vector(feature_dict)

        # The LABEL: the actual queue_length that occurred PREDICTION_HORIZON steps later.
        label = full_reading_history[i + PREDICTION_HORIZON]["queue_length"]

        examples.append((feature_vector, label))

    return examples


if __name__ == "__main__":
    # ---- Quick synthetic test: simulate a steadily rising queue over 20 readings ----
    synthetic_readings = [
        {"vehicles": 10 + i, "queue_length": 20 + i * 4, "average_speed": max(3.0, 15 - i * 0.5)}
        for i in range(20)
    ]
    synthetic_phase = [True] * 20  # pretend this approach stayed green the whole time

    examples = build_training_examples(synthetic_readings, "north", synthetic_phase)

    print(f"Generated {len(examples)} training examples from {len(synthetic_readings)} readings.\n")
    print("Feature order:", FEATURE_NAMES)
    print("-" * 90)
    for features, label in examples[:5]:
        print(f"Features: {features}  ->  Label (future queue): {label}")
