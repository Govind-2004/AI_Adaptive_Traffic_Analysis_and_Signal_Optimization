# ============================================================
# comparison_test.py
#
# BASELINE vs ENHANCED AI TRAFFIC SIGNAL CONTROLLER
#
# Baseline:
#   - Current traffic measurements only
#   - NO congestion score
#   - NO RF prediction
#
# Enhanced:
#   - Current traffic measurements
#   - Congestion score
#   - RF queue prediction (~30s)
#
# Both:
#   - Same Scenario F
#   - Same 180s duration
#   - Same signal phase sequence
#   - Same safety constraints
#   - Same fairness constraints
#
# Output:
#   comparison_results.csv
# ============================================================


import os
import csv
import warnings
from collections import defaultdict, deque

import joblib
import traci

from congestion_score import compute_congestion_score


# ============================================================
# SUPPRESS SKLEARN VERSION WARNING
# ============================================================

from sklearn.exceptions import InconsistentVersionWarning

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

OUTPUT_CSV = os.path.join(
    BASE_DIR,
    "comparison_results.csv"
)

TL_ID = "J001"

SIMULATION_DURATION = 180

READING_INTERVAL = 5

LOOKBACK_WINDOW = 4


# ============================================================
# SIGNAL CONFIGURATION
# ============================================================

NS_MAIN_PHASE = 0
EW_MAIN_PHASE = 6

MAIN_PHASES = {
    NS_MAIN_PHASE,
    EW_MAIN_PHASE
}


# Locked sequence:
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
# The controller NEVER directly jumps 0 -> 6
# or 6 -> 0.


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
# APPROACH CONFIGURATION
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


NS_APPROACHES = [
    "north",
    "south"
]

EW_APPROACHES = [
    "east",
    "west"
]


# ============================================================
# SAFETY PARAMETERS
# ============================================================

MIN_GREEN = 10

MAX_GREEN = 45

MAX_EXTENSION = 10

FAIRNESS_LIMIT = 60

BASE_GREEN = 30


# ============================================================
# LOAD RF MODEL
# ============================================================

print("\nLoading RF prediction model...")

model = joblib.load(MODEL_PATH)

MODEL_FEATURE_NAMES = list(
    model.feature_names_in_
)

print("RF model loaded successfully.")

print("\nModel features:")

for feature in MODEL_FEATURE_NAMES:
    print(" -", feature)

print()


# ============================================================
# READ TRAFFIC FROM SUMO
# ============================================================

def read_approach_state(edge_id):

    vehicles = traci.edge.getLastStepVehicleNumber(
        edge_id
    )

    queue_length = traci.edge.getLastStepHaltingNumber(
        edge_id
    )

    average_speed = traci.edge.getLastStepMeanSpeed(
        edge_id
    )

    return {
        "vehicles": int(vehicles),
        "queue": int(queue_length),
        "speed": float(average_speed)
    }


# ============================================================
# BUILD CURRENT TRAFFIC STATE
# ============================================================

def get_current_states(current_phase):

    states = {}

    for approach, edge in APPROACH_EDGES.items():

        data = read_approach_state(edge)

        congestion = compute_congestion_score(
            data["queue"],
            data["vehicles"],
            data["speed"]
        )

        states[approach] = {

            "vehicles":
                data["vehicles"],

            "queue":
                data["queue"],

            "speed":
                data["speed"],

            "congestion_score":
                congestion["score"],

            "congestion_level":
                congestion["level"],

            "green":
                current_phase
                == GREEN_PHASE_FOR_APPROACH[
                    approach
                ]
        }

    return states


# ============================================================
# TRAFFIC HISTORY FOR RF
# ============================================================

def create_history():

    return {

        "north":
            deque(maxlen=LOOKBACK_WINDOW),

        "south":
            deque(maxlen=LOOKBACK_WINDOW),

        "east":
            deque(maxlen=LOOKBACK_WINDOW),

        "west":
            deque(maxlen=LOOKBACK_WINDOW)
    }


# ============================================================
# BUILD RF FEATURES
# ============================================================

def build_model_features(
    history,
    approach,
    current_phase
):

    data_history = history[approach]

    if len(data_history) < LOOKBACK_WINDOW:

        return None

    window = list(data_history)

    current = window[-1]

    previous = window[-2]


    # --------------------------------------------------------
    # Current state
    # --------------------------------------------------------

    vehicles = current["vehicles"]

    queue_length = current["queue"]

    average_speed = current["speed"]


    # --------------------------------------------------------
    # Trends
    # --------------------------------------------------------

    count_trend = (
        current["vehicles"]
        - previous["vehicles"]
    )

    queue_trend = (
        current["queue"]
        - previous["queue"]
    )

    speed_trend = (
        current["speed"]
        - previous["speed"]
    )


    # --------------------------------------------------------
    # 20 second averages
    # --------------------------------------------------------

    avg_count_20s = (
        sum(
            item["vehicles"]
            for item in window
        )
        / len(window)
    )

    avg_queue_20s = (
        sum(
            item["queue"]
            for item in window
        )
        / len(window)
    )

    avg_speed_20s = (
        sum(
            item["speed"]
            for item in window
        )
        / len(window)
    )


    # --------------------------------------------------------
    # Congestion score
    # --------------------------------------------------------

    congestion = compute_congestion_score(
        queue_length,
        vehicles,
        average_speed
    )

    congestion_score = congestion["score"]


    # --------------------------------------------------------
    # Signal state
    # --------------------------------------------------------

    is_green = int(
        current_phase
        == GREEN_PHASE_FOR_APPROACH[
            approach
        ]
    )


    # --------------------------------------------------------
    # Exact RF features
    # --------------------------------------------------------

    features = {

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


    return features


# ============================================================
# PREDICT FUTURE QUEUE
# ============================================================

def predict_queue(
    history,
    approach,
    current_phase
):

    features = build_model_features(
        history,
        approach,
        current_phase
    )

    if features is None:

        return None


    input_vector = [

        features[name]

        for name
        in MODEL_FEATURE_NAMES
    ]


    prediction = model.predict(
        [input_vector]
    )[0]


    prediction = max(
        0.0,
        float(prediction)
    )


    return prediction


# ============================================================
# GET GROUP QUEUE
# ============================================================

def get_group_queue(
    states,
    approaches
):

    return max(
        states[a]["queue"]
        for a in approaches
    )


# ============================================================
# BASELINE CONTROLLER
#
# Uses ONLY current queue.
#
# No:
#   congestion score
#   RF prediction
# ============================================================

def baseline_decision(
    current_phase,
    phase_elapsed,
    states,
    time_since_ns_served,
    time_since_ew_served
):

    # --------------------------------------------------------
    # Only main green phases can be controlled
    # --------------------------------------------------------

    if current_phase not in MAIN_PHASES:

        return (
            "KEEP_PHASE",
            "Non-main phase."
        )


    # --------------------------------------------------------
    # Maximum green
    # --------------------------------------------------------

    if phase_elapsed >= MAX_GREEN:

        return (
            "SWITCH_PHASE",
            "Maximum green reached."
        )


    # --------------------------------------------------------
    # Fairness
    # --------------------------------------------------------

    if (
        current_phase == NS_MAIN_PHASE
        and
        time_since_ew_served
        >= FAIRNESS_LIMIT
    ):

        return (
            "SWITCH_PHASE",
            "EW fairness limit reached."
        )


    if (
        current_phase == EW_MAIN_PHASE
        and
        time_since_ns_served
        >= FAIRNESS_LIMIT
    ):

        return (
            "SWITCH_PHASE",
            "NS fairness limit reached."
        )


    # --------------------------------------------------------
    # Minimum green
    # --------------------------------------------------------

    if phase_elapsed < MIN_GREEN:

        return (
            "KEEP_PHASE",
            "Minimum green not reached."
        )


    # --------------------------------------------------------
    # Current queue demand
    # --------------------------------------------------------

    ns_queue = get_group_queue(
        states,
        NS_APPROACHES
    )

    ew_queue = get_group_queue(
        states,
        EW_APPROACHES
    )


    # --------------------------------------------------------
    # Current group
    # --------------------------------------------------------

    if current_phase == NS_MAIN_PHASE:

        current_queue = ns_queue

        opposing_queue = ew_queue

    else:

        current_queue = ew_queue

        opposing_queue = ns_queue


    # --------------------------------------------------------
    # Reactive decision
    #
    # Uses only CURRENT queue.
    # --------------------------------------------------------

    if opposing_queue > current_queue + 2:

        return (
            "SWITCH_PHASE",
            "Opposing queue is higher."
        )


    if current_queue >= opposing_queue + 2:

        return (
            "EXTEND_GREEN",
            "Current queue is higher."
        )


    return (
        "KEEP_PHASE",
        "Current queues are sufficiently balanced."
    )


# ============================================================
# ENHANCED CONTROLLER
#
# Uses:
#   congestion score
#   predicted queue
# ============================================================

def calculate_enhanced_demand(
    states,
    predicted_queues,
    approaches
):

    congestion_values = []

    current_queues = []

    predicted_values = []


    for approach in approaches:

        state = states[approach]

        congestion_values.append(
            state["congestion_score"]
        )

        current_queues.append(
            state["queue"]
        )


        prediction = predicted_queues.get(
            approach
        )


        if prediction is None:

            prediction = state["queue"]


        predicted_values.append(
            prediction
        )


    max_congestion = max(
        congestion_values
    )

    max_current_queue = max(
        current_queues
    )

    max_predicted_queue = max(
        predicted_values
    )


    normalized_current_queue = min(
        max_current_queue / 20.0,
        1.0
    )

    normalized_predicted_queue = min(
        max_predicted_queue / 20.0,
        1.0
    )


    demand = (

        0.50 * max_congestion

        +

        0.20
        * normalized_current_queue

        +

        0.30
        * normalized_predicted_queue
    )


    return demand


def enhanced_decision(
    current_phase,
    phase_elapsed,
    states,
    predicted_queues,
    time_since_ns_served,
    time_since_ew_served
):

    # --------------------------------------------------------
    # Only main green phases
    # --------------------------------------------------------

    if current_phase not in MAIN_PHASES:

        return (
            "KEEP_PHASE",
            "Non-main phase."
        )


    # --------------------------------------------------------
    # Maximum green
    # --------------------------------------------------------

    if phase_elapsed >= MAX_GREEN:

        return (
            "SWITCH_PHASE",
            "Maximum green reached."
        )


    # --------------------------------------------------------
    # Fairness
    # --------------------------------------------------------

    if (
        current_phase == NS_MAIN_PHASE
        and
        time_since_ew_served
        >= FAIRNESS_LIMIT
    ):

        return (
            "SWITCH_PHASE",
            "EW fairness limit reached."
        )


    if (
        current_phase == EW_MAIN_PHASE
        and
        time_since_ns_served
        >= FAIRNESS_LIMIT
    ):

        return (
            "SWITCH_PHASE",
            "NS fairness limit reached."
        )


    # --------------------------------------------------------
    # Minimum green
    # --------------------------------------------------------

    if phase_elapsed < MIN_GREEN:

        return (
            "KEEP_PHASE",
            "Minimum green not reached."
        )


    # --------------------------------------------------------
    # Calculate predictive demand
    # --------------------------------------------------------

    ns_demand = calculate_enhanced_demand(
        states,
        predicted_queues,
        NS_APPROACHES
    )

    ew_demand = calculate_enhanced_demand(
        states,
        predicted_queues,
        EW_APPROACHES
    )


    # --------------------------------------------------------
    # Current group
    # --------------------------------------------------------

    if current_phase == NS_MAIN_PHASE:

        current_demand = ns_demand

        opposing_demand = ew_demand

    else:

        current_demand = ew_demand

        opposing_demand = ns_demand


    # --------------------------------------------------------
    # Decision
    # --------------------------------------------------------

    if opposing_demand >= current_demand + 0.10:

        return (
            "SWITCH_PHASE",
            (
                f"Opposing demand higher "
                f"({opposing_demand:.3f} "
                f"vs "
                f"{current_demand:.3f})."
            )
        )


    if current_demand >= opposing_demand + 0.10:

        return (
            "EXTEND_GREEN",
            (
                f"Current demand higher "
                f"({current_demand:.3f} "
                f"vs "
                f"{opposing_demand:.3f})."
            )
        )


    return (
        "KEEP_PHASE",
        "Predictive demand is sufficiently balanced."
    )


# ============================================================
# APPLY ACTION
# ============================================================

def apply_action(
    action,
    current_phase,
    phase_elapsed,
    extension_used
):

    # --------------------------------------------------------
    # KEEP
    # --------------------------------------------------------

    if action == "KEEP_PHASE":

        return (
            "KEEP_PHASE",
            extension_used
        )


    # --------------------------------------------------------
    # SWITCH
    #
    # We NEVER call setPhase().
    #
    # This preserves:
    #
    # 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6
    #
    # 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 0
    # --------------------------------------------------------

    if action == "SWITCH_PHASE":

        if current_phase in MAIN_PHASES:

            if phase_elapsed < MIN_GREEN:

                return (
                    "KEEP_PHASE",
                    extension_used
                )


            traci.trafficlight.setPhaseDuration(
                TL_ID,
                0
            )

            return (
                "SWITCH_PHASE",
                extension_used
            )


    # --------------------------------------------------------
    # EXTEND
    # --------------------------------------------------------

    if action == "EXTEND_GREEN":

        remaining_extension = (
            MAX_EXTENSION
            - extension_used
        )


        remaining_green = (
            MAX_GREEN
            - phase_elapsed
        )


        extension = min(
            5,
            remaining_extension,
            remaining_green
        )


        if extension <= 0:

            return (
                "KEEP_PHASE",
                extension_used
            )


        new_extension_total = (
            extension_used
            + extension
        )


        new_duration = (
            BASE_GREEN
            + new_extension_total
        )


        traci.trafficlight.setPhaseDuration(
            TL_ID,
            new_duration
        )


        return (
            "EXTEND_GREEN",
            new_extension_total
        )


    return (
        "KEEP_PHASE",
        extension_used
    )


# ============================================================
# METRICS TRACKING
# ============================================================

class MetricsTracker:

    def __init__(self):

        self.vehicle_first_seen = {}

        self.vehicle_last_speed = {}

        self.vehicle_was_stopped = {}

        self.vehicle_stops = defaultdict(int)

        self.vehicle_waiting = {}

        self.vehicle_travel_time = {}

        self.completed_vehicles = set()

        self.total_speed_samples = 0

        self.speed_sum = 0.0

        self.queue_sum = 0.0

        self.queue_samples = 0

        self.waiting_sum = 0.0

        self.travel_time_sum = 0.0

        self.stop_count = 0

        self.total_vehicles_seen = set()


        # Signal action counts

        self.keep_count = 0

        self.extend_count = 0

        self.switch_count = 0

        self.phase_switches = 0


        self.phase_change_count = 0


        self.previous_phase = None


    # --------------------------------------------------------
    # Observe vehicles
    # --------------------------------------------------------

    def observe_vehicles(self, step):

        vehicle_ids = traci.vehicle.getIDList()


        for veh_id in vehicle_ids:

            self.total_vehicles_seen.add(
                veh_id
            )


            # --------------------------------------------
            # First observation
            # --------------------------------------------

            if veh_id not in self.vehicle_first_seen:

                self.vehicle_first_seen[
                    veh_id
                ] = step

                self.vehicle_was_stopped[
                    veh_id
                ] = False


            # --------------------------------------------
            # Speed
            # --------------------------------------------

            speed = traci.vehicle.getSpeed(
                veh_id
            )

            self.vehicle_last_speed[
                veh_id
            ] = speed


            self.speed_sum += speed

            self.total_speed_samples += 1


            # --------------------------------------------
            # Stop-event detection
            #
            # We count a stop when a vehicle transitions
            # from moving to near-zero speed.
            # --------------------------------------------

            stopped_now = (
                speed < 0.1
            )


            was_stopped = (
                self.vehicle_was_stopped.get(
                    veh_id,
                    False
                )
            )


            if (
                stopped_now
                and not was_stopped
            ):

                self.vehicle_stops[
                    veh_id
                ] += 1

                self.stop_count += 1


            self.vehicle_was_stopped[
                veh_id
            ] = stopped_now


            # --------------------------------------------
            # Accumulated waiting time
            # --------------------------------------------

            try:

                waiting = (
                    traci.vehicle
                    .getAccumulatedWaitingTime(
                        veh_id
                    )
                )

                self.vehicle_waiting[
                    veh_id
                ] = waiting

            except Exception:

                pass


    # --------------------------------------------------------
    # Observe queue
    # --------------------------------------------------------

    def observe_queue(
        self,
        states
    ):

        total_queue = sum(
            states[a]["queue"]
            for a in APPROACH_EDGES
        )


        self.queue_sum += (
            total_queue
        )

        self.queue_samples += 1


    # --------------------------------------------------------
    # Detect phase changes
    # --------------------------------------------------------

    def observe_phase(
        self,
        current_phase
    ):

        if (
            self.previous_phase
            is not None
            and
            current_phase
            != self.previous_phase
        ):

            self.phase_change_count += 1


        self.previous_phase = (
            current_phase
        )


    # --------------------------------------------------------
    # Record controller action
    # --------------------------------------------------------

    def record_action(
        self,
        action
    ):

        if action == "KEEP_PHASE":

            self.keep_count += 1

        elif action == "EXTEND_GREEN":

            self.extend_count += 1

        elif action == "SWITCH_PHASE":

            self.switch_count += 1

            self.phase_switches += 1


    # --------------------------------------------------------
    # Record arrived vehicles
    # --------------------------------------------------------

    def record_arrivals(
        self,
        step
    ):

        arrived_ids = (
            traci.simulation
            .getArrivedIDList()
        )


        for veh_id in arrived_ids:

            self.completed_vehicles.add(
                veh_id
            )


            # --------------------------------------------
            # Travel time
            # --------------------------------------------

            if veh_id in self.vehicle_first_seen:

                travel_time = (
                    step
                    -
                    self.vehicle_first_seen[
                        veh_id
                    ]
                )

                self.vehicle_travel_time[
                    veh_id
                ] = travel_time

                self.travel_time_sum += (
                    travel_time
                )


            # --------------------------------------------
            # Waiting time
            # --------------------------------------------

            if veh_id in self.vehicle_waiting:

                self.waiting_sum += (
                    self.vehicle_waiting[
                        veh_id
                    ]
                )


    # --------------------------------------------------------
    # Finalize vehicles still inside simulation
    # --------------------------------------------------------

    def finalize_active_vehicles(
        self,
        final_step
    ):

        for veh_id in self.vehicle_first_seen:

            if (
                veh_id
                not in self.completed_vehicles
            ):

                travel_time = (
                    final_step
                    -
                    self.vehicle_first_seen[
                        veh_id
                    ]
                )

                self.travel_time_sum += (
                    travel_time
                )


                if veh_id in self.vehicle_waiting:

                    self.waiting_sum += (
                        self.vehicle_waiting[
                            veh_id
                        ]
                    )


    # --------------------------------------------------------
    # Produce metrics
    # --------------------------------------------------------

    def get_metrics(self):

        completed = len(
            self.completed_vehicles
        )


        if self.speed_sum > 0:

            average_speed = (
                self.speed_sum
                /
                self.total_speed_samples
            )

        else:

            average_speed = 0.0


        if self.queue_samples > 0:

            average_queue = (
                self.queue_sum
                /
                self.queue_samples
            )

        else:

            average_queue = 0.0


        if completed > 0:

            average_waiting = (
                self.waiting_sum
                /
                completed
            )

        else:

            average_waiting = 0.0


        total_vehicles_for_travel = (
            len(self.vehicle_first_seen)
        )


        if total_vehicles_for_travel > 0:

            average_travel_time = (
                self.travel_time_sum
                /
                total_vehicles_for_travel
            )

        else:

            average_travel_time = 0.0


        return {

            "average_waiting_time_s":
                round(
                    average_waiting,
                    3
                ),

            "average_queue_length":
                round(
                    average_queue,
                    3
                ),

            "average_travel_time_s":
                round(
                    average_travel_time,
                    3
                ),

            "throughput":
                completed,

            "average_speed_m_s":
                round(
                    average_speed,
                    3
                ),

            "total_stops":
                self.stop_count,

            "keep_phase":
                self.keep_count,

            "extend_green":
                self.extend_count,

            "switch_phase":
                self.switch_count,

            "phase_switches":
                self.phase_switches,

            "total_vehicles_seen":
                len(
                    self.total_vehicles_seen
                )
        }


# ============================================================
# RUN ONE EXPERIMENT
# ============================================================

def run_experiment(
    experiment_name,
    enhanced
):

    print("\n\n")

    print(
        "=" * 80
    )

    print(
        f"STARTING EXPERIMENT: {experiment_name}"
    )

    print(
        "=" * 80
    )


    if enhanced:

        print(
            "Mode: ENHANCED AI"
        )

        print(
            "  Congestion score: ENABLED"
        )

        print(
            "  RF prediction:     ENABLED"
        )

    else:

        print(
            "Mode: BASELINE AI"
        )

        print(
            "  Congestion score: DISABLED"
        )

        print(
            "  RF prediction:     DISABLED"
        )


    print()


    # --------------------------------------------------------
    # Fresh history for each experiment
    # --------------------------------------------------------

    traffic_history = create_history()


    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    metrics = MetricsTracker()


    # --------------------------------------------------------
    # Start SUMO
    # --------------------------------------------------------

    sumo_cmd = [
        "sumo-gui",
        "-c",
        SUMO_CONFIG
    ]


    print(
        "Starting SUMO..."
    )


    traci.start(
        sumo_cmd
    )


    print(
        "TraCI connected."
    )


    # --------------------------------------------------------
    # Timing variables
    # --------------------------------------------------------

    step = 0


    last_phase = (
        traci.trafficlight.getPhase(
            TL_ID
        )
    )


    phase_start_time = 0

    current_extension_used = 0


    # --------------------------------------------------------
    # Fairness timers
    # --------------------------------------------------------

    last_ns_served_time = 0

    last_ew_served_time = 0


    # --------------------------------------------------------
    # Predicted queues
    # --------------------------------------------------------

    predicted_queues = {

        "north": None,
        "south": None,
        "east": None,
        "west": None
    }


    try:

        # ====================================================
        # FIXED 180 SECOND SIMULATION
        # ====================================================

        while step < SIMULATION_DURATION:

            traci.simulationStep()


            # ------------------------------------------------
            # Current phase
            # ------------------------------------------------

            current_phase = (
                traci.trafficlight
                .getPhase(
                    TL_ID
                )
            )


            # ------------------------------------------------
            # Phase change
            # ------------------------------------------------

            if (
                current_phase
                != last_phase
            ):

                phase_start_time = step

                current_extension_used = 0

                last_phase = current_phase


            # ------------------------------------------------
            # Phase elapsed
            # ------------------------------------------------

            phase_elapsed = (
                step
                -
                phase_start_time
            )


            # ------------------------------------------------
            # Service timers
            # ------------------------------------------------

            if (
                current_phase
                == NS_MAIN_PHASE
            ):

                last_ns_served_time = step


            if (
                current_phase
                == EW_MAIN_PHASE
            ):

                last_ew_served_time = step


            time_since_ns_served = (
                step
                -
                last_ns_served_time
            )


            time_since_ew_served = (
                step
                -
                last_ew_served_time
            )


            # ------------------------------------------------
            # Track vehicles every simulation second
            # ------------------------------------------------

            metrics.observe_vehicles(
                step
            )


            metrics.observe_phase(
                current_phase
            )


            # ------------------------------------------------
            # Record arrived vehicles
            # ------------------------------------------------

            metrics.record_arrivals(
                step
            )


            # =================================================
            # TRAFFIC CONTROL EVERY 5 SECONDS
            # =================================================

            if (
                step
                %
                READING_INTERVAL
                == 0
            ):

                # ---------------------------------------------
                # Read traffic
                # ---------------------------------------------

                current_states = (
                    get_current_states(
                        current_phase
                    )
                )


                # ---------------------------------------------
                # Queue metric
                # ---------------------------------------------

                metrics.observe_queue(
                    current_states
                )


                # ---------------------------------------------
                # Save history
                # ---------------------------------------------

                for approach in APPROACH_EDGES:

                    traffic_history[
                        approach
                    ].append({

                        "vehicles":
                            current_states[
                                approach
                            ]["vehicles"],

                        "queue":
                            current_states[
                                approach
                            ]["queue"],

                        "speed":
                            current_states[
                                approach
                            ]["speed"]
                    })


                # =================================================
                # ENHANCED MODE ONLY:
                # RF PREDICTION
                # =================================================

                if enhanced:

                    for approach in APPROACH_EDGES:

                        predicted_queues[
                            approach
                        ] = predict_queue(

                            traffic_history,

                            approach,

                            current_phase
                        )

                else:

                    # -----------------------------------------
                    # Explicitly disable prediction
                    # -----------------------------------------

                    predicted_queues = {

                        "north": None,
                        "south": None,
                        "east": None,
                        "west": None
                    }


                # =================================================
                # DECIDE SIGNAL ACTION
                # =================================================

                if current_phase in MAIN_PHASES:

                    if enhanced:

                        action, reason = (
                            enhanced_decision(

                                current_phase,

                                phase_elapsed,

                                current_states,

                                predicted_queues,

                                time_since_ns_served,

                                time_since_ew_served
                            )
                        )

                    else:

                        action, reason = (
                            baseline_decision(

                                current_phase,

                                phase_elapsed,

                                current_states,

                                time_since_ns_served,

                                time_since_ew_served
                            )
                        )


                    # -----------------------------------------
                    # Apply action
                    # -----------------------------------------

                    final_action, current_extension_used = (
                        apply_action(

                            action,

                            current_phase,

                            phase_elapsed,

                            current_extension_used
                        )
                    )


                    metrics.record_action(
                        final_action
                    )


                    # -----------------------------------------
                    # Console output
                    # -----------------------------------------

                    print(
                        "\n"
                        + "-" * 75
                    )

                    print(
                        f"{experiment_name} | "
                        f"TIME: {step}s"
                    )

                    print(
                        f"PHASE: {current_phase} "
                        f"({PHASE_GROUP[current_phase]})"
                    )

                    print(
                        f"PHASE ELAPSED: "
                        f"{phase_elapsed}s"
                    )


                    print(
                        f"NS queue: "
                        f"{get_group_queue(states=current_states, approaches=NS_APPROACHES)}"
                    )

                    print(
                        f"EW queue: "
                        f"{get_group_queue(states=current_states, approaches=EW_APPROACHES)}"
                    )


                    if enhanced:

                        ns_pred = max(

                            (
                                predicted_queues[a]
                                if predicted_queues[a]
                                is not None
                                else 0
                            )

                            for a in NS_APPROACHES
                        )


                        ew_pred = max(

                            (
                                predicted_queues[a]
                                if predicted_queues[a]
                                is not None
                                else 0
                            )

                            for a in EW_APPROACHES
                        )


                        print(
                            f"NS predicted queue: "
                            f"{ns_pred:.2f}"
                        )

                        print(
                            f"EW predicted queue: "
                            f"{ew_pred:.2f}"
                        )


                    print(
                        f"Action: "
                        f"{final_action}"
                    )

                    print(
                        f"Reason: "
                        f"{reason}"
                    )


                else:

                    # ------------------------------------------------
                    # Non-main phases cannot be controlled
                    # ------------------------------------------------

                    pass


            step += 1


        # ====================================================
        # FINALIZE METRICS
        # ====================================================

        metrics.finalize_active_vehicles(
            SIMULATION_DURATION
        )


        results = (
            metrics.get_metrics()
        )


        print(
            "\n"
            + "=" * 80
        )

        print(
            f"{experiment_name} FINISHED"
        )

        print(
            "=" * 80
        )


        for key, value in results.items():

            print(
                f"{key}: {value}"
            )


        return results


    finally:

        if traci.isLoaded():

            traci.close()


        print(
            "TraCI connection closed."
        )


# ============================================================
# CALCULATE IMPROVEMENT
# ============================================================

def calculate_improvement(
    baseline,
    enhanced,
    metric
):

    baseline_value = (
        baseline[metric]
    )

    enhanced_value = (
        enhanced[metric]
    )


    # --------------------------------------------------------
    # Higher is better
    # --------------------------------------------------------

    higher_is_better = {

        "throughput",

        "average_speed_m_s"
    }


    if baseline_value == 0:

        return 0.0


    if metric in higher_is_better:

        improvement = (

            (
                enhanced_value
                -
                baseline_value
            )
            /
            baseline_value
        ) * 100

    else:

        improvement = (

            (
                baseline_value
                -
                enhanced_value
            )
            /
            baseline_value
        ) * 100


    return round(
        improvement,
        3
    )


# ============================================================
# SAVE COMPARISON CSV
# ============================================================

def save_comparison_csv(
    baseline,
    enhanced
):

    metrics = [

        "average_waiting_time_s",

        "average_queue_length",

        "average_travel_time_s",

        "throughput",

        "average_speed_m_s",

        "total_stops",

        "keep_phase",

        "extend_green",

        "switch_phase",

        "phase_switches",

        "total_vehicles_seen"
    ]


    with open(
        OUTPUT_CSV,
        "w",
        newline=""
    ) as file:

        writer = csv.writer(
            file
        )


        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        writer.writerow([

            "metric",

            "baseline",

            "enhanced",

            "improvement_percent"
        ])


        # ----------------------------------------------------
        # Data
        # ----------------------------------------------------

        for metric in metrics:

            improvement = (
                calculate_improvement(

                    baseline,

                    enhanced,

                    metric
                )
            )


            writer.writerow([

                metric,

                baseline[metric],

                enhanced[metric],

                improvement
            ])


    print(
        f"\nComparison CSV saved to:\n"
        f"{OUTPUT_CSV}"
    )


# ============================================================
# PRINT FINAL COMPARISON
# ============================================================

def print_final_comparison(
    baseline,
    enhanced
):

    print(
        "\n\n"
        + "=" * 90
    )

    print(
        "FINAL BASELINE vs ENHANCED AI COMPARISON"
    )

    print(
        "=" * 90
    )


    print(

        f"{'Metric':<30}"
        f"{'Baseline':>15}"
        f"{'Enhanced':>15}"
        f"{'Improvement':>18}"
    )


    print(
        "-" * 90
    )


    metrics = [

        (
            "Average waiting time (s)",
            "average_waiting_time_s"
        ),

        (
            "Average queue length",
            "average_queue_length"
        ),

        (
            "Average travel time (s)",
            "average_travel_time_s"
        ),

        (
            "Throughput",
            "throughput"
        ),

        (
            "Average speed (m/s)",
            "average_speed_m_s"
        ),

        (
            "Total stops",
            "total_stops"
        ),

        (
            "KEEP_PHASE",
            "keep_phase"
        ),

        (
            "EXTEND_GREEN",
            "extend_green"
        ),

        (
            "SWITCH_PHASE",
            "switch_phase"
        ),

        (
            "Total phase switches",
            "phase_switches"
        )
    ]


    for label, key in metrics:

        improvement = (
            calculate_improvement(

                baseline,

                enhanced,

                key
            )
        )


        print(

            f"{label:<30}"

            f"{baseline[key]:>15.3f}"

            f"{enhanced[key]:>15.3f}"

            f"{improvement:>17.2f}%"
        )


    print(
        "=" * 90
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n"
        + "#" * 80
    )

    print(
        "# TRAFFIC SIGNAL AI COMPARISON"
    )

    print(
        "# Scenario F"
    )

    print(
        "# Baseline vs Enhanced"
    )

    print(
        "#" * 80
    )


    # ========================================================
    # RUN 1 — BASELINE
    # ========================================================

    baseline_results = run_experiment(

        experiment_name="BASELINE",

        enhanced=False
    )


    # ========================================================
    # RUN 2 — ENHANCED AI
    # ========================================================

    enhanced_results = run_experiment(

        experiment_name="ENHANCED_AI",

        enhanced=True
    )


    # ========================================================
    # FINAL COMPARISON
    # ========================================================

    print_final_comparison(

        baseline_results,

        enhanced_results
    )


    # ========================================================
    # SAVE CSV
    # ========================================================

    save_comparison_csv(

        baseline_results,

        enhanced_results
    )


    print(
        "\nExperiment complete! 🚦"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()