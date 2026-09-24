MIN_GREEN = 10.0
MAX_GREEN = 45.0
MAX_EXTENSION = 10.0
DECISION_THRESHOLD = 0.10

NS_MAIN_PHASE = 0
EW_MAIN_PHASE = 6

NS_APPROACHES = {"north", "south"}
EW_APPROACHES = {"east", "west"}


def get_group_for_approach(approach):
    if approach in NS_APPROACHES:
        return "NS"
    if approach in EW_APPROACHES:
        return "EW"
    raise ValueError(f"Unknown approach: {approach}")


def get_opposing_group(group):
    if group == "NS":
        return "EW"
    if group == "EW":
        return "NS"
    raise ValueError(f"Unknown group: {group}")


def is_main_green_phase(current_phase):
    return current_phase in {NS_MAIN_PHASE, EW_MAIN_PHASE}


def get_current_group(current_phase):
    if current_phase == NS_MAIN_PHASE:
        return "NS"
    if current_phase == EW_MAIN_PHASE:
        return "EW"
    return None


def calculate_group_state(traffic_state):
    approaches = traffic_state["approaches"]

    north = approaches["north"]
    south = approaches["south"]
    east = approaches["east"]
    west = approaches["west"]

    ns_data = [north, south]
    ew_data = [east, west]

    ns_congestion = max(
        data["congestion_score"] for data in ns_data
    )
    ew_congestion = max(
        data["congestion_score"] for data in ew_data
    )

    ns_queue = sum(
        data["queue_length"] for data in ns_data
    )
    ew_queue = sum(
        data["queue_length"] for data in ew_data
    )

    ns_vehicles = sum(
        data["vehicles"] for data in ns_data
    )
    ew_vehicles = sum(
        data["vehicles"] for data in ew_data
    )

    ns_predictions = [
        data.get("predicted_queue")
        for data in ns_data
        if data.get("predicted_queue") is not None
    ]

    ew_predictions = [
        data.get("predicted_queue")
        for data in ew_data
        if data.get("predicted_queue") is not None
    ]

    ns_predicted_queue = (
        sum(ns_predictions) if ns_predictions else None
    )
    ew_predicted_queue = (
        sum(ew_predictions) if ew_predictions else None
    )

    return {
        "NS": {
            "congestion": ns_congestion,
            "queue": ns_queue,
            "vehicles": ns_vehicles,
            "predicted_queue": ns_predicted_queue,
        },
        "EW": {
            "congestion": ew_congestion,
            "queue": ew_queue,
            "vehicles": ew_vehicles,
            "predicted_queue": ew_predicted_queue,
        },
    }


def calculate_demand_score(group_state):
    congestion = group_state["congestion"]
    current_queue = group_state["queue"]
    predicted_queue = group_state["predicted_queue"]

    queue_component = min(current_queue / 20.0, 1.0)

    if predicted_queue is None:
        predicted_component = queue_component
    else:
        predicted_component = min(predicted_queue / 20.0, 1.0)

    demand_score = (
        0.50 * congestion
        + 0.20 * queue_component
        + 0.30 * predicted_component
    )

    return round(demand_score, 3)


def safety_check(
    current_phase,
    phase_elapsed,
    requested_action,
    requested_extension,
):
    if not is_main_green_phase(current_phase):
        return {
            "approved": False,
            "action": "KEEP_PHASE",
            "extension": 0.0,
            "reason": "Current phase is not a main green phase.",
        }

    if phase_elapsed < MIN_GREEN:
        return {
            "approved": False,
            "action": "KEEP_PHASE",
            "extension": 0.0,
            "reason": "Minimum green time has not been reached.",
        }

    if phase_elapsed >= MAX_GREEN:
        return {
            "approved": False,
            "action": "KEEP_PHASE",
            "extension": 0.0,
            "reason": "Maximum green duration reached.",
        }

    if requested_action == "EXTEND_GREEN":
        allowed_extension = min(
            requested_extension,
            MAX_EXTENSION,
            MAX_GREEN - phase_elapsed,
        )

        if allowed_extension <= 0:
            return {
                "approved": False,
                "action": "KEEP_PHASE",
                "extension": 0.0,
                "reason": "No safe extension available.",
            }

        return {
            "approved": True,
            "action": "EXTEND_GREEN",
            "extension": round(allowed_extension, 2),
            "reason": "Extension passed safety checks.",
        }

    return {
        "approved": True,
        "action": "KEEP_PHASE",
        "extension": 0.0,
        "reason": "Maintain current phase.",
    }


def decide_signal_action(
    traffic_state,
    phase_elapsed,
    time_since_ns_served=None,
    time_since_ew_served=None,
):
    current_phase = traffic_state["current_phase"]
    current_group = get_current_group(current_phase)

    if current_group is None:
        return {
            "action": "KEEP_PHASE",
            "approved": False,
            "reason": "Current phase is not a main green.",
            "safety_reason": "Programmed sequence continues.",
            "current_phase": current_phase,
            "current_group": None,
            "extension": 0.0,
            "NS_demand": None,
            "EW_demand": None,
        }

    groups = calculate_group_state(traffic_state)

    ns_score = calculate_demand_score(groups["NS"])
    ew_score = calculate_demand_score(groups["EW"])

    if current_group == "NS":
        current_score = ns_score
        opposing_score = ew_score
    else:
        current_score = ew_score
        opposing_score = ns_score

    demand_difference = current_score - opposing_score

    if (
        current_score > opposing_score
        and abs(demand_difference) >= DECISION_THRESHOLD
    ):
        requested_action = "EXTEND_GREEN"
        requested_extension = 5.0
        reason = (
            f"Current group demand {current_score:.3f} "
            f"is higher than opposing demand {opposing_score:.3f}."
        )
    elif (
        opposing_score > current_score
        and abs(demand_difference) >= DECISION_THRESHOLD
    ):
        requested_action = "KEEP_PHASE"
        requested_extension = 0.0
        reason = (
            f"Opposing demand {opposing_score:.3f} "
            f"is higher than current demand {current_score:.3f}. "
            f"Programmed sequence is preserved."
        )
    else:
        requested_action = "KEEP_PHASE"
        requested_extension = 0.0
        reason = "Traffic demand is sufficiently balanced."

    safety_result = safety_check(
        current_phase,
        phase_elapsed,
        requested_action,
        requested_extension,
    )

    return {
        "action": safety_result["action"],
        "approved": safety_result["approved"],
        "reason": reason,
        "safety_reason": safety_result["reason"],
        "current_phase": current_phase,
        "current_group": current_group,
        "NS_demand": ns_score,
        "EW_demand": ew_score,
        "demand_difference": round(demand_difference, 3),
        "current_group_score": round(current_score, 3),
        "opposing_group_score": round(opposing_score, 3),
        "extension": safety_result["extension"],
        "phase_elapsed": round(phase_elapsed, 2),
    }


def print_decision(decision):
    print("\n" + "=" * 60)
    print("AI SIGNAL DECISION")
    print("=" * 60)
    print(f"Current phase: {decision['current_phase']}")
    print(f"Current group: {decision['current_group']}")
    print(f"NS demand: {decision.get('NS_demand', 'N/A')}")
    print(f"EW demand: {decision.get('EW_demand', 'N/A')}")
    print(f"Action: {decision['action']}")
    print(f"Extension: {decision.get('extension', 0):.2f}s")
    print(f"Reason: {decision.get('reason', '')}")
    print(f"Safety: {decision.get('safety_reason', '')}")
    print("=" * 60)


if __name__ == "__main__":
    print("AI signal controller loaded successfully.")
    print("Allowed actions: KEEP_PHASE, EXTEND_GREEN")
