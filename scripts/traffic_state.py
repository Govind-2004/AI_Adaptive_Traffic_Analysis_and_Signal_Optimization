import traci

from congestion_score import compute_congestion_score


# ============================================================
# CONFIGURATION
# ============================================================

TRAFFIC_LIGHT_ID = "J001"

APPROACH_EDGES = {
    "north": "N_in",
    "south": "S_in",
    "east": "E_in",
    "west": "W_in",
}

# Current 12-phase signal sequence:
#
# 0  = NS main green
# 1  = NS yellow
# 2  = all red
# 3  = NS protected right
# 4  = NS right yellow
# 5  = all red
# 6  = EW main green
# 7  = EW yellow
# 8  = all red
# 9  = EW protected right
# 10 = EW right yellow
# 11 = all red

GREEN_PHASE_FOR_APPROACH = {
    "north": 0,
    "south": 0,
    "east": 6,
    "west": 6,
}


# ============================================================
# READ TRAFFIC STATE FROM SUMO
# ============================================================

def read_approach_state(edge_id):
    """
    Read the current traffic state for one approach.

    Returns:
        vehicles       -> number of vehicles on the approach
        queue_length   -> number of halted vehicles
        average_speed  -> average vehicle speed in m/s
    """

    vehicles = traci.edge.getLastStepVehicleNumber(edge_id)

    queue_length = traci.edge.getLastStepHaltingNumber(edge_id)

    average_speed = traci.edge.getLastStepMeanSpeed(edge_id)

    return {
        "vehicles": vehicles,
        "queue_length": queue_length,
        "average_speed": average_speed,
    }


# ============================================================
# GET COMPLETE TRAFFIC STATE
# ============================================================

def get_traffic_state():
    """
    Read the current traffic state of all four approaches.

    Also calculates:
        - congestion score
        - congestion level
        - congestion components
        - whether the approach currently has green
    """

    current_phase = traci.trafficlight.getPhase(TRAFFIC_LIGHT_ID)

    approaches = {}

    for approach, edge_id in APPROACH_EDGES.items():

        # ----------------------------------------------------
        # Read raw SUMO traffic data
        # ----------------------------------------------------

        state = read_approach_state(edge_id)

        # ----------------------------------------------------
        # Determine whether this approach currently has green
        # ----------------------------------------------------

        is_green = (
            current_phase == GREEN_PHASE_FOR_APPROACH[approach]
        )

        # ----------------------------------------------------
        # Calculate congestion score
        # ----------------------------------------------------

        congestion = compute_congestion_score(
            queue_length=state["queue_length"],
            vehicle_count=state["vehicles"],
            average_speed=state["average_speed"],
        )

        # ----------------------------------------------------
        # Add everything to approach state
        # ----------------------------------------------------

        approaches[approach] = {
            "vehicles": state["vehicles"],
            "queue_length": state["queue_length"],
            "average_speed": state["average_speed"],
            "is_green": is_green,

            "congestion_score": congestion["score"],
            "congestion_level": congestion["level"],
            "congestion_components": congestion["components"],
        }

    # --------------------------------------------------------
    # Return complete traffic state
    # --------------------------------------------------------

    return {
        "current_phase": current_phase,
        "approaches": approaches,
    }


# ============================================================
# PRINT TRAFFIC STATE
# ============================================================

def print_traffic_state(state):
    """
    Print the traffic state in a readable format.
    """

    print("\n" + "=" * 60)
    print("CURRENT TRAFFIC STATE")
    print("=" * 60)

    print(f"Traffic light: {TRAFFIC_LIGHT_ID}")
    print(f"Current phase: {state['current_phase']}")

    for approach, data in state["approaches"].items():

        print("\n" + "-" * 40)
        print(approach.upper())

        print(f"Vehicles:          {data['vehicles']}")
        print(f"Queue length:      {data['queue_length']}")
        print(f"Average speed:     {data['average_speed']:.2f} m/s")
        print(f"Green:             {data['is_green']}")

        print(
            f"Congestion score:  {data['congestion_score']:.3f}"
        )

        print(
            f"Congestion level:  {data['congestion_level']}"
        )

        print(
            f"Components:        {data['congestion_components']}"
        )

    print("=" * 60)


# ============================================================
# TEST WHEN RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    print("traffic_state.py loaded successfully.")
    print("Connecting to running SUMO/TraCI...")

    try:

        # ----------------------------------------------------
        # Get current traffic state
        # ----------------------------------------------------

        state = get_traffic_state()

        # ----------------------------------------------------
        # Display it
        # ----------------------------------------------------

        print_traffic_state(state)

        print("\nTraffic state extraction successful!")

    except Exception as e:

        print("\nERROR while reading traffic state:")
        print(e)

        print(
            "\nMake sure SUMO is running and "
            "TraCI is connected before executing this test."
        )