
# ============================================================
# scenario_F_traditional_vs_ai.py
#
# Scenario F:
# Traditional Fixed-Time vs Enhanced AI Traffic Signal
#
# CONTROLLER 1:
#   Traditional fixed-time signal
#
# CONTROLLER 2:
#   Enhanced AI signal
#   - Current traffic state
#   - Congestion score
#   - RF predicted queue
#   - Safety constraints
#
# IMPORTANT:
#   Both controllers use the SAME programmed signal sequence.
#
# Traditional:
#   Never modifies phase duration.
#
# AI:
#   Can ONLY extend the currently active MAIN GREEN phase.
#   It never directly jumps from NS -> EW or EW -> NS.
#
# ============================================================


import os
import warnings
import xml.etree.ElementTree as ET
from collections import deque

import joblib
import pandas as pd
import traci

from congestion_score import compute_congestion_score
from ai_signal_controller import decide_signal_action

from sklearn.exceptions import InconsistentVersionWarning


# ============================================================
# WARNINGS
# ============================================================

warnings.filterwarnings(
    "ignore",
    category=InconsistentVersionWarning
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = r"D:\01 ICT CAPSTONE\Newsumofiles"

SUMO_CONFIG = os.path.join(
    BASE_DIR,
    "scenario_F.sumocfg"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "traffic_prediction_rf.pkl"
)

TL_ID = "J001"


# ============================================================
# SIMULATION SETTINGS
# ============================================================

SIMULATION_DURATION = 180.0

READING_INTERVAL = 5.0

LOOKBACK_WINDOW = 4


# ============================================================
# SUMO GUI SETTINGS
# ============================================================

# Use SUMO-GUI so the intersection can be visually observed.
SUMO_BINARY = "sumo-gui"

# --start automatically starts the GUI simulation.
SUMO_GUI_START = True

# Small real-time delay so the simulation can be observed.
# Set to 0 for maximum simulation speed.
SUMO_DELAY_MS = 20


# ============================================================
# SIGNAL PHASE CONFIGURATION
# ============================================================

NS_MAIN_PHASE = 0
EW_MAIN_PHASE = 6

MAIN_PHASES = {
    NS_MAIN_PHASE,
    EW_MAIN_PHASE
}


# Your locked 12-phase sequence:
#
# 0  = NS main green
# 1  = NS yellow
# 2  = all-red
# 3  = NS protected right
# 4  = NS right yellow
# 5  = all-red
#
# 6  = EW main green
# 7  = EW yellow
# 8  = all-red
# 9  = EW protected right
# 10 = EW right yellow
# 11 = all-red
#
# Then repeat.

PHASE_GROUP = {
    0: "NS",
    1: "NS",
    2: "NS",
    3: "NS",
    4: "NS",
    5: "NS",
    6: "EW",
    7: "EW",
    8: "EW",
    9: "EW",
    10: "EW",
    11: "EW"
}


# ============================================================
# APPROACH / EDGE CONFIGURATION
# ============================================================

APPROACH_EDGES = {
    "north": "N_in",
    "south": "S_in",
    "east": "E_in",
    "west": "W_in"
}


GREEN_PHASE_FOR_APPROACH = {
    "north": NS_MAIN_PHASE,
    "south": NS_MAIN_PHASE,
    "east": EW_MAIN_PHASE,
    "west": EW_MAIN_PHASE
}


# ============================================================
# AI SAFETY PARAMETERS
# ============================================================

MIN_GREEN = 10.0

MAX_GREEN = 45.0

MAX_EXTENSION = 10.0

BASE_GREEN = 30.0

FAIRNESS_LIMIT = 60.0


# ============================================================
# CONTROLLER NAMES
# ============================================================

TRADITIONAL = "TRADITIONAL"

AI = "AI"


# ============================================================
# CHECK REQUIRED FILES
# ============================================================

if not os.path.exists(SUMO_CONFIG):

    raise FileNotFoundError(
        f"\nSUMO configuration file not found:\n"
        f"{SUMO_CONFIG}"
    )


if not os.path.exists(MODEL_PATH):

    raise FileNotFoundError(
        f"\nRF model file not found:\n"
        f"{MODEL_PATH}"
    )


# ============================================================
# LOAD RF MODEL
# ============================================================

print("\nLoading RF traffic prediction model...")

model = joblib.load(
    MODEL_PATH
)

print(
    "RF model loaded successfully."
)


# ------------------------------------------------------------
# Read feature names directly from the trained model.
# This guarantees that prediction uses the same feature order
# used during model training.
# ------------------------------------------------------------

MODEL_FEATURE_NAMES = list(
    model.feature_names_in_
)


print(
    "\nRF model feature order:"
)


for feature in MODEL_FEATURE_NAMES:

    print(
        f"  - {feature}"
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def read_approach_state(edge_id):
    """
    Read current traffic state from SUMO.

    Returns:
        vehicles
        queue_length
        average_speed
    """

    vehicles = (
        traci.edge.getLastStepVehicleNumber(
            edge_id
        )
    )

    queue_length = (
        traci.edge.getLastStepHaltingNumber(
            edge_id
        )
    )

    average_speed = (
        traci.edge.getLastStepMeanSpeed(
            edge_id
        )
    )

    return {
        "vehicles": int(
            vehicles
        ),

        "queue_length": int(
            queue_length
        ),

        "average_speed": float(
            average_speed
        )
    }


# ============================================================
# RF FEATURE ENGINEERING
# ============================================================

def build_model_features(
    history,
    current_phase,
    approach
):
    """
    Build the exact 11 features expected by the RF model.
    """

    # Need four readings = 20 seconds of history.
    if len(history) < LOOKBACK_WINDOW:

        return None


    window = list(
        history
    )


    current = window[-1]

    previous = window[-2]


    # --------------------------------------------------------
    # CURRENT STATE
    # --------------------------------------------------------

    vehicles = current[
        "vehicles"
    ]

    queue_length = current[
        "queue_length"
    ]

    average_speed = current[
        "average_speed"
    ]


    # --------------------------------------------------------
    # TRENDS
    # --------------------------------------------------------

    count_trend = (
        current["vehicles"]
        -
        previous["vehicles"]
    )

    queue_trend = (
        current["queue_length"]
        -
        previous["queue_length"]
    )

    speed_trend = (
        current["average_speed"]
        -
        previous["average_speed"]
    )


    # --------------------------------------------------------
    # 20-SECOND AVERAGES
    # --------------------------------------------------------

    avg_count_20s = (
        sum(
            item["vehicles"]
            for item in window
        )
        /
        len(window)
    )

    avg_queue_20s = (
        sum(
            item["queue_length"]
            for item in window
        )
        /
        len(window)
    )

    avg_speed_20s = (
        sum(
            item["average_speed"]
            for item in window
        )
        /
        len(window)
    )


    # --------------------------------------------------------
    # CONGESTION SCORE
    # --------------------------------------------------------

    congestion = (
        compute_congestion_score(
            queue_length,
            vehicles,
            average_speed
        )
    )

    congestion_score = (
        congestion["score"]
    )


    # --------------------------------------------------------
    # IS APPROACH GREEN?
    # --------------------------------------------------------

    is_green = int(
        current_phase
        ==
        GREEN_PHASE_FOR_APPROACH[
            approach
        ]
    )


    # --------------------------------------------------------
    # MODEL FEATURES
    # --------------------------------------------------------

    return {

        "vehicles":
            vehicles,

        "queue_length":
            queue_length,

        "average_speed":
            average_speed,

        "count_trend":
            count_trend,

        "queue_trend":
            queue_trend,

        "speed_trend":
            speed_trend,

        "avg_count_20s":
            round(
                avg_count_20s,
                2
            ),

        "avg_queue_20s":
            round(
                avg_queue_20s,
                2
            ),

        "avg_speed_20s":
            round(
                avg_speed_20s,
                2
            ),

        "congestion_score":
            congestion_score,

        "is_green":
            is_green
    }


# ============================================================
# RF PREDICTION
# ============================================================

def predict_queue(
    history,
    current_phase,
    approach
):
    """
    Predict future queue using the trained RF model.

    Returns:
        float
        None if insufficient history.
    """

    features = (
        build_model_features(
            history,
            current_phase,
            approach
        )
    )


    if features is None:

        return None


    # --------------------------------------------------------
    # IMPORTANT:
    #
    # The RF model was trained with pandas feature names.
    # Therefore use a DataFrame rather than a plain list.
    # --------------------------------------------------------

    input_data = {
        name: features[name]
        for name in MODEL_FEATURE_NAMES
    }


    input_df = pd.DataFrame(
        [input_data],
        columns=MODEL_FEATURE_NAMES
    )


    prediction = (
        model.predict(
            input_df
        )[0]
    )


    # Queue cannot be negative.
    prediction = max(
        0.0,
        float(prediction)
    )


    return prediction


# ============================================================
# PRINT TRAFFIC STATE
# ============================================================

def print_traffic_state(
    sim_time,
    current_phase,
    phase_elapsed,
    states,
    predictions
):
    """
    Print traffic state and RF predictions.
    """

    print(
        "\n"
        +
        "=" * 85
    )


    print(
        f"TIME: {sim_time:.1f}s | "
        f"PHASE: {current_phase} | "
        f"GROUP: "
        f"{PHASE_GROUP.get(current_phase, 'UNKNOWN')} | "
        f"PHASE ELAPSED: {phase_elapsed:.1f}s"
    )


    print(
        "=" * 85
    )


    print(
        f"{'Approach':<10}"
        f"{'Vehicles':<10}"
        f"{'Queue':<10}"
        f"{'Speed':<12}"
        f"{'Cong.':<12}"
        f"{'Prediction':<12}"
    )


    print(
        "-" * 85
    )


    for approach in [
        "north",
        "south",
        "east",
        "west"
    ]:

        state = states[
            approach
        ]


        prediction = predictions.get(
            approach
        )


        if prediction is None:

            prediction_text = "N/A"

        else:

            prediction_text = (
                f"{prediction:.2f}"
            )


        print(
            f"{approach:<10}"
            f"{state['vehicles']:<10}"
            f"{state['queue_length']:<10}"
            f"{state['average_speed']:<12.2f}"
            f"{state['congestion_score']:<12.3f}"
            f"{prediction_text:<12}"
        )


# ============================================================
# APPLY AI ACTION
# ============================================================

def apply_ai_action(
    decision,
    current_phase,
    phase_elapsed,
    current_extension_used
):
    """
    Apply the AI decision safely.

    Allowed:
        KEEP_PHASE
        EXTEND_GREEN

    Not allowed:
        direct phase switching
        shortening current green

    Returns:
        final_action,
        updated_extension_used,
        extension_added,
        reason
    """

    # --------------------------------------------------------
    # READ DECISION
    # --------------------------------------------------------

    if isinstance(
        decision,
        dict
    ):

        action = decision.get(
            "action",
            "KEEP_PHASE"
        )

        reason = decision.get(
            "reason",
            ""
        )

    else:

        action = str(
            decision
        )

        reason = ""


    # --------------------------------------------------------
    # ONLY MAIN GREEN PHASES CAN BE MODIFIED
    # --------------------------------------------------------

    if current_phase not in MAIN_PHASES:

        return (
            "KEEP_PHASE",
            current_extension_used,
            0.0,
            "Non-main phase; programmed sequence continues."
        )


    # --------------------------------------------------------
    # MINIMUM GREEN SAFETY
    # --------------------------------------------------------

    if phase_elapsed < MIN_GREEN:

        return (
            "KEEP_PHASE",
            current_extension_used,
            0.0,
            "Minimum green duration not reached."
        )


    # --------------------------------------------------------
    # KEEP PHASE
    # --------------------------------------------------------

    if action == "KEEP_PHASE":

        return (
            "KEEP_PHASE",
            current_extension_used,
            0.0,
            reason
        )


    # --------------------------------------------------------
    # EXTEND GREEN
    # --------------------------------------------------------

    if action == "EXTEND_GREEN":

        # How much AI extension capacity remains?
        remaining_extension = (
            MAX_EXTENSION
            -
            current_extension_used
        )


        # How much total green capacity remains?
        remaining_allowed_green = (
            MAX_GREEN
            -
            phase_elapsed
        )


        # One decision adds at most 5 seconds.
        extension = min(
            5.0,
            remaining_extension,
            remaining_allowed_green
        )


        if extension <= 0.0:

            return (
                "KEEP_PHASE",
                current_extension_used,
                0.0,
                "No safe extension remains."
            )


        # ----------------------------------------------------
        # NEW TOTAL EXTENSION
        # ----------------------------------------------------

        new_extension_total = (
            current_extension_used
            +
            extension
        )


        # ----------------------------------------------------
        # DESIRED TOTAL GREEN
        #
        # Normally:
        #
        # BASE_GREEN + total AI extension
        #
        # The second term also protects against a situation
        # where the phase is already close to MAX_GREEN.
        # ----------------------------------------------------

        intended_total_green = max(
            BASE_GREEN
            +
            new_extension_total,

            phase_elapsed
            +
            extension
        )


        intended_total_green = min(
            intended_total_green,
            MAX_GREEN
        )


        # ----------------------------------------------------
        # SUMO IMPORTANT RULE
        #
        # setPhaseDuration() modifies the REMAINING duration
        # of the current phase.
        #
        # Therefore:
        #
        # remaining duration =
        # desired total duration - elapsed duration
        # ----------------------------------------------------

        remaining_duration = max(
            0.0,
            intended_total_green
            -
            phase_elapsed
        )


        # ----------------------------------------------------
        # GET CURRENT NEXT SWITCH
        # ----------------------------------------------------

        before_switch = (
            traci.trafficlight.getNextSwitch(
                TL_ID
            )
        )


        # ----------------------------------------------------
        # APPLY EXTENSION
        # ----------------------------------------------------

        traci.trafficlight.setPhaseDuration(
            TL_ID,
            remaining_duration
        )


        # ----------------------------------------------------
        # CHECK NEW SWITCH TIME
        # ----------------------------------------------------

        after_switch = (
            traci.trafficlight.getNextSwitch(
                TL_ID
            )
        )


        actual_shift = (
            after_switch
            -
            before_switch
        )


        print(
            "\n  >>> AI EXTENSION"
        )


        print(
            f"      Current phase:"
            f" {current_phase}"
        )


        print(
            f"      Added:"
            f" +{extension:.1f}s"
        )


        print(
            f"      Total extension:"
            f" +{new_extension_total:.1f}s"
        )


        print(
            f"      Intended total green:"
            f" {intended_total_green:.1f}s"
        )


        print(
            f"      Remaining green:"
            f" {remaining_duration:.1f}s"
        )


        print(
            f"      Next switch shifted:"
            f" {actual_shift:.1f}s"
        )


        print(
            f"      Reason:"
            f" {reason}"
        )


        return (
            "EXTEND_GREEN",
            new_extension_total,
            extension,
            reason
        )


    # ========================================================
    # SWITCH_PHASE
    # ========================================================
    #
    # The controller may request this action because of its
    # own decision logic.
    #
    # BUT our experiment explicitly prohibits direct switching.
    #
    # Therefore the request is converted to KEEP_PHASE.
    #
    # SUMO will naturally progress through the programmed
    # sequence.
    # ========================================================

    if action == "SWITCH_PHASE":

        return (
            "KEEP_PHASE",
            current_extension_used,
            0.0,
            "Phase switching disabled; programmed sequence preserved."
        )


    # --------------------------------------------------------
    # UNKNOWN ACTION
    # --------------------------------------------------------

    return (
        "KEEP_PHASE",
        current_extension_used,
        0.0,
        "Unknown AI action."
    )


# ============================================================
# RUN ONE CONTROLLER
# ============================================================

def run_controller(
    controller_name,
    tripinfo_filename
):
    """
    Run one complete SUMO experiment.

    controller_name:
        TRADITIONAL
        AI
    """

    print("\n\n")

    print(
        "#" * 85
    )


    print(
        f"# STARTING CONTROLLER:"
        f" {controller_name}"
    )


    print(
        "#" * 85
    )


    tripinfo_path = os.path.join(
        BASE_DIR,
        tripinfo_filename
    )


    # --------------------------------------------------------
    # Remove old tripinfo file if it exists.
    # This prevents confusion with previous experiments.
    # --------------------------------------------------------

    if os.path.exists(
        tripinfo_path
    ):

        os.remove(
            tripinfo_path
        )


    # --------------------------------------------------------
    # SUMO COMMAND
    # --------------------------------------------------------

    sumo_cmd = [
        SUMO_BINARY,
        "-c",
        SUMO_CONFIG,

        "--start",

        "--tripinfo-output",
        tripinfo_path,

        "--tripinfo-output.write-unfinished",
        "true"
    ]


    # --------------------------------------------------------
    # OPTIONAL GUI DELAY
    # --------------------------------------------------------

    if SUMO_DELAY_MS > 0:

        sumo_cmd.extend(
            [
                "--delay",
                str(SUMO_DELAY_MS)
            ]
        )


    # --------------------------------------------------------
    # START SUMO
    # --------------------------------------------------------

    print(
        "\nStarting SUMO-GUI..."
    )


    traci.start(
        sumo_cmd
    )


    print(
        f"TraCI connected:"
        f" {controller_name}"
    )


    # ========================================================
    # INITIAL PHASE
    # ========================================================

    last_phase = (
        traci.trafficlight.getPhase(
            TL_ID
        )
    )


    phase_start_time = (
        traci.simulation.getTime()
    )


    current_extension_used = 0.0


    # ========================================================
    # FAIRNESS TIMERS
    # ========================================================

    last_ns_served_time = 0.0

    last_ew_served_time = 0.0


    # ========================================================
    # TRAFFIC HISTORY
    # ========================================================

    traffic_history = {

        "north":
            deque(
                maxlen=LOOKBACK_WINDOW
            ),

        "south":
            deque(
                maxlen=LOOKBACK_WINDOW
            ),

        "east":
            deque(
                maxlen=LOOKBACK_WINDOW
            ),

        "west":
            deque(
                maxlen=LOOKBACK_WINDOW
            )
    }


    # ========================================================
    # STATISTICS
    # ========================================================

    stats = {

        "ai_extensions":
            0,

        "total_extension_seconds":
            0.0,

        "ai_keep":
            0,

        "ai_end_green":
            0,

        "phase_changes":
            0,

        "total_vehicles_seen":
            0,

        "queue_sum":
            0.0,

        "queue_samples":
            0,

        "speed_sum":
            0.0,

        "speed_samples":
            0
    }


    # ========================================================
    # NEXT TRAFFIC READING
    # ========================================================

    next_reading_time = 0.0


    try:

        # ====================================================
        # MAIN SIMULATION LOOP
        # ====================================================

        while (
            traci.simulation.getTime()
            <
            SIMULATION_DURATION
        ):

            # ------------------------------------------------
            # ADVANCE SUMO
            # ------------------------------------------------

            traci.simulationStep()


            # ------------------------------------------------
            # CURRENT SIMULATION TIME
            # ------------------------------------------------

            sim_time = (
                traci.simulation.getTime()
            )


            # ------------------------------------------------
            # CURRENT SIGNAL PHASE
            # ------------------------------------------------

            current_phase = (
                traci.trafficlight.getPhase(
                    TL_ID
                )
            )


            # =================================================
            # PHASE CHANGE
            # =================================================

            if current_phase != last_phase:

                stats[
                    "phase_changes"
                ] += 1


                phase_start_time = (
                    sim_time
                )


                # Every new phase starts with zero AI
                # extension for that phase.

                current_extension_used = 0.0


                last_phase = current_phase


            # =================================================
            # PHASE ELAPSED
            # =================================================

            phase_elapsed = (
                sim_time
                -
                phase_start_time
            )


            # =================================================
            # FAIRNESS TIMERS
            # =================================================

            if current_phase == NS_MAIN_PHASE:

                last_ns_served_time = (
                    sim_time
                )


            if current_phase == EW_MAIN_PHASE:

                last_ew_served_time = (
                    sim_time
                )


            time_since_ns_served = (
                sim_time
                -
                last_ns_served_time
            )


            time_since_ew_served = (
                sim_time
                -
                last_ew_served_time
            )


            # =================================================
            # READ TRAFFIC EVERY 5 SECONDS
            # =================================================

            if (
                sim_time + 1e-6
                >=
                next_reading_time
            ):

                next_reading_time += (
                    READING_INTERVAL
                )


                # =================================================
                # READ ALL APPROACHES
                # =================================================

                states = {}


                for approach, edge in (
                    APPROACH_EDGES.items()
                ):

                    states[
                        approach
                    ] = (
                        read_approach_state(
                            edge
                        )
                    )


                # =================================================
                # CALCULATE CONGESTION
                # =================================================

                for approach in states:

                    data = states[
                        approach
                    ]


                    congestion = (
                        compute_congestion_score(
                            data[
                                "queue_length"
                            ],

                            data[
                                "vehicles"
                            ],

                            data[
                                "average_speed"
                            ]
                        )
                    )


                    data[
                        "congestion_score"
                    ] = (
                        congestion[
                            "score"
                        ]
                    )


                    data[
                        "congestion_level"
                    ] = (
                        congestion[
                            "level"
                        ]
                    )


                # =================================================
                # STATISTICS
                # =================================================

                for approach in states:

                    data = states[
                        approach
                    ]


                    stats[
                        "total_vehicles_seen"
                    ] += (
                        data[
                            "vehicles"
                        ]
                    )


                    stats[
                        "queue_sum"
                    ] += (
                        data[
                            "queue_length"
                        ]
                    )


                    stats[
                        "queue_samples"
                    ] += 1


                    stats[
                        "speed_sum"
                    ] += (
                        data[
                            "average_speed"
                        ]
                    )


                    stats[
                        "speed_samples"
                    ] += 1


                # =================================================
                # TRADITIONAL CONTROLLER
                # =================================================

                if (
                    controller_name
                    ==
                    TRADITIONAL
                ):

                    print_traffic_state(
                        sim_time,
                        current_phase,
                        phase_elapsed,
                        states,
                        {}
                    )


                    print(
                        "\n  CONTROLLER:"
                        " TRADITIONAL FIXED-TIME"
                    )


                    print(
                        "  Action:"
                        " NO ADAPTATION"
                    )


                    print(
                        "  Signal follows"
                        " programmed SUMO timings."
                    )


                    print(
                        f"  Current phase duration:"
                        f" "
                        f"{traci.trafficlight.getPhaseDuration(TL_ID):.1f}s"
                    )


                # =================================================
                # AI CONTROLLER
                # =================================================

                else:

                    # =================================================
                    # UPDATE HISTORY
                    # =================================================

                    for approach in states:

                        data = states[
                            approach
                        ]


                        traffic_history[
                            approach
                        ].append(
                            {
                                "vehicles":
                                    data[
                                        "vehicles"
                                    ],

                                "queue_length":
                                    data[
                                        "queue_length"
                                    ],

                                "average_speed":
                                    data[
                                        "average_speed"
                                    ]
                            }
                        )


                    # =================================================
                    # RF PREDICTIONS
                    # =================================================

                    predictions = {}


                    for approach in states:

                        predictions[
                            approach
                        ] = predict_queue(

                            traffic_history[
                                approach
                            ],

                            current_phase,

                            approach
                        )


                    # =================================================
                    # PRINT STATE
                    # =================================================

                    print_traffic_state(
                        sim_time,
                        current_phase,
                        phase_elapsed,
                        states,
                        predictions
                    )


                    # =================================================
                    # BUILD AI INPUT
                    # =================================================
                    #
                    # IMPORTANT:
                    #
                    # ai_signal_controller expects:
                    #
                    # traffic_state["approaches"]
                    #
                    # =================================================

                    ai_input = {
                        "approaches": {}
                    }


                    for approach in states:

                        data = states[
                            approach
                        ]


                        prediction = (
                            predictions[
                                approach
                            ]
                        )


                        # ------------------------------------------------
                        # During the first 20 seconds the RF model has
                        # insufficient history.
                        #
                        # Current queue is used as a safe fallback.
                        # ------------------------------------------------

                        if prediction is None:

                            prediction = float(
                                data[
                                    "queue_length"
                                ]
                            )


                        ai_input[
                            "approaches"
                        ][
                            approach
                        ] = {

                            "vehicles":
                                data[
                                    "vehicles"
                                ],

                            "queue_length":
                                data[
                                    "queue_length"
                                ],

                            "average_speed":
                                data[
                                    "average_speed"
                                ],

                            "congestion_score":
                                data[
                                    "congestion_score"
                                ],

                            "predicted_queue":
                                float(
                                    prediction
                                ),

                            "is_green":
                                (
                                    current_phase
                                    ==
                                    GREEN_PHASE_FOR_APPROACH[
                                        approach
                                    ]
                                )
                        }


                    # =================================================
                    # CONTROLLER CONTEXT
                    # =================================================

                    ai_input[
                        "current_phase"
                    ] = (
                        current_phase
                    )


                    ai_input[
                        "phase_group"
                    ] = (
                        PHASE_GROUP.get(
                            current_phase,
                            "UNKNOWN"
                        )
                    )


                    ai_input[
                        "phase_elapsed"
                    ] = (
                        phase_elapsed
                    )


                    # =================================================
                    # AI DECISION
                    # =================================================

                    print(
                        "\n  AI SIGNAL DECISION"
                    )


                    # -------------------------------------------------
                    # AI ONLY ACTS ON MAIN GREEN
                    # -------------------------------------------------

                    if (
                        current_phase
                        in
                        MAIN_PHASES
                    ):

                        try:

                            # ------------------------------------------------
                            # Your ai_signal_controller uses four inputs.
                            # ------------------------------------------------

                            decision = (
                                decide_signal_action(
                                    ai_input,
                                    phase_elapsed,
                                    time_since_ns_served,
                                    time_since_ew_served
                                )
                            )


                            # ------------------------------------------------
                            # SAFELY APPLY DECISION
                            # ------------------------------------------------

                            (
                                final_action,
                                updated_extension,
                                extension_added,
                                reason
                            ) = (
                                apply_ai_action(
                                    decision,
                                    current_phase,
                                    phase_elapsed,
                                    current_extension_used
                                )
                            )


                            current_extension_used = (
                                updated_extension
                            )


                            # =================================================
                            # UPDATE AI STATISTICS
                            # =================================================

                            if (
                                final_action
                                ==
                                "EXTEND_GREEN"
                            ):

                                stats[
                                    "ai_extensions"
                                ] += 1


                                stats[
                                    "total_extension_seconds"
                                ] += (
                                    extension_added
                                )


                            elif (
                                final_action
                                ==
                                "KEEP_PHASE"
                            ):

                                stats[
                                    "ai_keep"
                                ] += 1


                            elif (
                                final_action
                                ==
                                "END_GREEN"
                            ):

                                stats[
                                    "ai_end_green"
                                ] += 1


                            # =================================================
                            # PRINT DECISION
                            # =================================================

                            print(
                                f"  Final action:"
                                f" {final_action}"
                            )


                            if reason:

                                print(
                                    f"  Reason:"
                                    f" {reason}"
                                )


                        except Exception as e:

                            # ------------------------------------------------
                            # IMPORTANT:
                            #
                            # Any controller error must NOT change the
                            # signal sequence.
                            # ------------------------------------------------

                            print(
                                "\n  AI CONTROLLER ERROR:"
                            )


                            print(
                                f"  "
                                f"{type(e).__name__}: "
                                f"{e}"
                            )


                            print(
                                "  SAFETY FALLBACK:"
                                " KEEP_PHASE"
                            )


                            stats[
                                "ai_keep"
                            ] += 1


                    else:

                        # ------------------------------------------------
                        # Yellow / all-red / protected-right phases:
                        #
                        # AI does nothing.
                        #
                        # SUMO follows the existing programmed sequence.
                        # ------------------------------------------------

                        print(
                            "  Action:"
                            " KEEP_PHASE"
                        )


                        print(
                            "  Reason:"
                            " non-main phase."
                        )


                        print(
                            "  Existing signal sequence"
                            " continues normally."
                        )


    finally:

        # ========================================================
        # CLOSE TRACI
        # ========================================================

        if traci.isLoaded():

            traci.close()


        print(
            f"TraCI closed:"
            f" {controller_name}"
        )


    print("\n")

    print(
        "#" * 85
    )


    print(
        f"# {controller_name}"
        f" SIMULATION FINISHED"
    )


    print(
        "#" * 85
    )


    return stats


# ============================================================
# READ TRIPINFO
# ============================================================

def analyze_tripinfo(
    tripinfo_path
):
    """
    Read SUMO tripinfo XML.

    Calculates:
        total vehicles
        completed vehicles
        unfinished vehicles
        average waiting time
        average duration
        average speed
        total waiting counts
    """

    if not os.path.exists(
        tripinfo_path
    ):

        print(
            "\nWARNING:"
        )


        print(
            f"Tripinfo file not found:"
            f"\n{tripinfo_path}"
        )


        return None


    try:

        tree = ET.parse(
            tripinfo_path
        )


        root = tree.getroot()


        trips = root.findall(
            "tripinfo"
        )


        # --------------------------------------------------------
        # No vehicles
        # --------------------------------------------------------

        if not trips:

            return {

                "vehicles":
                    0,

                "completed":
                    0,

                "unfinished":
                    0,

                "avg_waiting":
                    0.0,

                "avg_duration":
                    0.0,

                "avg_speed":
                    0.0,

                "total_stops":
                    0.0
            }


        waiting_times = []

        durations = []

        speeds = []

        stops = []


        completed = 0


        # ========================================================
        # READ EACH VEHICLE
        # ========================================================

        for trip in trips:

            waiting = float(
                trip.get(
                    "waitingTime",
                    0
                )
            )


            duration = float(
                trip.get(
                    "duration",
                    0
                )
            )


            route_length = float(
                trip.get(
                    "routeLength",
                    0
                )
            )


            # ------------------------------------------------
            # WAITING
            # ------------------------------------------------

            waiting_times.append(
                waiting
            )


            # ------------------------------------------------
            # DURATION
            # ------------------------------------------------

            durations.append(
                duration
            )


            # ------------------------------------------------
            # SPEED = DISTANCE / TIME
            # ------------------------------------------------

            if duration > 0:

                speed = (
                    route_length
                    /
                    duration
                )


                speeds.append(
                    speed
                )


            # ------------------------------------------------
            # WAITING COUNT
            # ------------------------------------------------

            stops.append(
                float(
                    trip.get(
                        "waitingCount",
                        0
                    )
                )
            )


            # ------------------------------------------------
            # COMPLETION
            #
            # SUMO unfinished vehicles have arrival < 0.
            # ------------------------------------------------

            arrival = float(
                trip.get(
                    "arrival",
                    -1
                )
            )


            if arrival >= 0:

                completed += 1


        # ========================================================
        # RETURN
        # ========================================================

        return {

            "vehicles":
                len(trips),

            "completed":
                completed,

            "unfinished":
                (
                    len(trips)
                    -
                    completed
                ),

            "avg_waiting":
                (
                    sum(waiting_times)
                    /
                    len(waiting_times)
                ),

            "avg_duration":
                (
                    sum(durations)
                    /
                    len(durations)
                ),

            "avg_speed":
                (
                    sum(speeds)
                    /
                    len(speeds)
                    if speeds
                    else 0.0
                ),

            "total_stops":
                sum(stops)
        }


    except Exception as e:

        print(
            "\nERROR reading tripinfo:"
        )


        print(
            f"{type(e).__name__}: {e}"
        )


        return None


# ============================================================
# IMPROVEMENT CALCULATION
# ============================================================

def calculate_improvement(
    traditional,
    ai
):
    """
    For lower-is-better metrics:

        improvement =
        (traditional - ai)
        / traditional * 100

    Positive value means AI reduced the metric.

    Used for:
        waiting time
        queue
        travel time
        stops
    """

    if traditional == 0:

        return None


    return (
        (
            traditional
            -
            ai
        )
        /
        traditional
    ) * 100.0


# ============================================================
# MAIN COMPARISON
# ============================================================

def main():

    print("\n")

    print(
        "=" * 100
    )


    print(
        "SCENARIO F"
    )


    print(
        "TRADITIONAL FIXED-TIME"
        " VS ENHANCED AI"
    )


    print(
        "=" * 100
    )


    # ========================================================
    # RUN 1 — TRADITIONAL
    # ========================================================

    traditional_stats = (
        run_controller(
            TRADITIONAL,
            "scenario_F_traditional_tripinfo.xml"
        )
    )


    # ========================================================
    # RUN 2 — AI
    # ========================================================

    ai_stats = (
        run_controller(
            AI,
            "scenario_F_ai_tripinfo.xml"
        )
    )


    # ========================================================
    # READ TRIPINFO
    # ========================================================

    traditional_tripinfo = (
        analyze_tripinfo(
            os.path.join(
                BASE_DIR,
                "scenario_F_traditional_tripinfo.xml"
            )
        )
    )


    ai_tripinfo = (
        analyze_tripinfo(
            os.path.join(
                BASE_DIR,
                "scenario_F_ai_tripinfo.xml"
            )
        )
    )


    # ========================================================
    # VALIDATE
    # ========================================================

    if (
        traditional_tripinfo is None
        or
        ai_tripinfo is None
    ):

        print(
            "\nComparison could not be completed."
        )


        return


    # ========================================================
    # QUEUE STATISTICS
    # ========================================================

    if (
        traditional_stats[
            "queue_samples"
        ]
        >
        0
    ):

        traditional_avg_queue = (
            traditional_stats[
                "queue_sum"
            ]
            /
            traditional_stats[
                "queue_samples"
            ]
        )

    else:

        traditional_avg_queue = 0.0


    if (
        ai_stats[
            "queue_samples"
        ]
        >
        0
    ):

        ai_avg_queue = (
            ai_stats[
                "queue_sum"
            ]
            /
            ai_stats[
                "queue_samples"
            ]
        )

    else:

        ai_avg_queue = 0.0


    # ========================================================
    # SPEED STATISTICS
    # ========================================================

    if (
        traditional_stats[
            "speed_samples"
        ]
        >
        0
    ):

        traditional_avg_speed = (
            traditional_stats[
                "speed_sum"
            ]
            /
            traditional_stats[
                "speed_samples"
            ]
        )

    else:

        traditional_avg_speed = 0.0


    if (
        ai_stats[
            "speed_samples"
        ]
        >
        0
    ):

        ai_avg_speed = (
            ai_stats[
                "speed_sum"
            ]
            /
            ai_stats[
                "speed_samples"
            ]
        )

    else:

        ai_avg_speed = 0.0


    # ========================================================
    # IMPROVEMENTS
    # ========================================================

    waiting_improvement = (
        calculate_improvement(
            traditional_tripinfo[
                "avg_waiting"
            ],

            ai_tripinfo[
                "avg_waiting"
            ]
        )
    )


    queue_improvement = (
        calculate_improvement(
            traditional_avg_queue,
            ai_avg_queue
        )
    )


    travel_improvement = (
        calculate_improvement(
            traditional_tripinfo[
                "avg_duration"
            ],

            ai_tripinfo[
                "avg_duration"
            ]
        )
    )


    # --------------------------------------------------------
    # Higher speed = better
    # --------------------------------------------------------

    if traditional_avg_speed != 0:

        speed_improvement = (

            (
                ai_avg_speed
                -
                traditional_avg_speed
            )
            /
            traditional_avg_speed

        ) * 100.0

    else:

        speed_improvement = None


    # ========================================================
    # COMPLETED VEHICLES
    # ========================================================

    completed_vehicle_change = (
        calculate_improvement(
            traditional_tripinfo[
                "completed"
            ],

            ai_tripinfo[
                "completed"
            ]
        )
    )


    # ========================================================
    # TOTAL STOPS
    # ========================================================

    stop_improvement = (
        calculate_improvement(
            traditional_tripinfo[
                "total_stops"
            ],

            ai_tripinfo[
                "total_stops"
            ]
        )
    )


    # ========================================================
    # FINAL RESULTS
    # ========================================================

    print("\n\n")

    print(
        "=" * 100
    )


    print(
        "SCENARIO F — FINAL COMPARISON"
    )


    print(
        "=" * 100
    )


    print(
        f"\n{'Metric':<32}"
        f"{'Traditional':<20}"
        f"{'Enhanced AI':<20}"
        f"{'Change':<15}"
    )


    print(
        "-" * 100
    )


    # ========================================================
    # METRIC PRINTER
    # ========================================================

    def print_metric(
        name,
        traditional_value,
        ai_value,
        improvement
    ):

        if improvement is None:

            change_text = "N/A"

        else:

            change_text = (
                f"{improvement:+.2f}%"
            )


        print(
            f"{name:<32}"
            f"{traditional_value:<20.3f}"
            f"{ai_value:<20.3f}"
            f"{change_text:<15}"
        )


    # ========================================================
    # WAITING TIME
    # ========================================================

    print_metric(
        "Average waiting time (s)",

        traditional_tripinfo[
            "avg_waiting"
        ],

        ai_tripinfo[
            "avg_waiting"
        ],

        waiting_improvement
    )


    # ========================================================
    # QUEUE
    # ========================================================

    print_metric(
        "Average queue length",

        traditional_avg_queue,

        ai_avg_queue,

        queue_improvement
    )


    # ========================================================
    # TRAVEL TIME
    # ========================================================

    print_metric(
        "Average travel time (s)",

        traditional_tripinfo[
            "avg_duration"
        ],

        ai_tripinfo[
            "avg_duration"
        ],

        travel_improvement
    )


    # ========================================================
    # SPEED
    # ========================================================

    print_metric(
        "Average speed (m/s)",

        traditional_avg_speed,

        ai_avg_speed,

        speed_improvement
    )


    # ========================================================
    # COMPLETED VEHICLES
    # ========================================================

    print_metric(
        "Completed vehicles",

        traditional_tripinfo[
            "completed"
        ],

        ai_tripinfo[
            "completed"
        ],

        completed_vehicle_change
    )


    # ========================================================
    # TOTAL STOPS
    # ========================================================

    print_metric(
        "Total stops",

        traditional_tripinfo[
            "total_stops"
        ],

        ai_tripinfo[
            "total_stops"
        ],

        stop_improvement
    )


    # ========================================================
    # VEHICLE ACCOUNTING
    # ========================================================

    print("\n")


    print(
        "=" * 90
    )


    print(
        "VEHICLE ACCOUNTING"
    )


    print(
        "=" * 90
    )


    print(
        f"Traditional total:"
        f" {traditional_tripinfo['vehicles']}"
    )


    print(
        f"Traditional completed:"
        f" {traditional_tripinfo['completed']}"
    )


    print(
        f"Traditional unfinished:"
        f" {traditional_tripinfo['unfinished']}"
    )


    print()


    print(
        f"AI total:"
        f" {ai_tripinfo['vehicles']}"
    )


    print(
        f"AI completed:"
        f" {ai_tripinfo['completed']}"
    )


    print(
        f"AI unfinished:"
        f" {ai_tripinfo['unfinished']}"
    )


    # ========================================================
    # AI STATISTICS
    # ========================================================

    print("\n")


    print(
        "=" * 90
    )


    print(
        "AI CONTROLLER STATISTICS"
    )


    print(
        "=" * 90
    )


    print(
        f"AI green extensions:"
        f" {ai_stats['ai_extensions']}"
    )


    print(
        f"Total extension seconds:"
        f" {ai_stats['total_extension_seconds']:.1f}s"
    )


    print(
        f"AI KEEP_PHASE decisions:"
        f" {ai_stats['ai_keep']}"
    )


    print(
        f"AI END_GREEN decisions:"
        f" {ai_stats['ai_end_green']}"
    )


    print(
        f"Total phase changes:"
        f" {ai_stats['phase_changes']}"
    )


    # ========================================================
    # EXPERIMENT DESIGN
    # ========================================================

    print("\n")


    print(
        "=" * 90
    )


    print(
        "EXPERIMENT DESIGN"
    )


    print(
        "=" * 90
    )


    print(
        "Traditional:"
        " fixed-time signal with no traffic adaptation."
    )


    print(
        "Enhanced AI:"
        " current traffic + congestion score"
        " + RF queue prediction."
    )


    print(
        "Both controllers:"
        " same Scenario F traffic demand."
    )


    print(
        "Both controllers:"
        " same programmed phase sequence."
    )


    print(
        "AI:"
        " may only extend the active main green."
    )


    print(
        "AI:"
        " does not directly jump between phases."
    )


    print(
        "AI:"
        " does not shorten an active green."
    )


    print(
        "SUMO:"
        " launched using SUMO-GUI for visual verification."
    )


    print(
        "=" * 90
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()

