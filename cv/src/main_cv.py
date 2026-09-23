# cv/src/main_cv.py

import os
import json
import yaml
import gc
import pandas as pd
import torch

from cv.detection.detector import (
    load_model,
    VEHICLE_CLASSES
)

from cv.tracking.tracker import (
    result_to_dataframe
)

from cv.traffic.roi import (
    assign_roi_and_direction,
    resolve_vehicle_class
)

from cv.traffic.speed import (
    compute_pixel_speed,
    representative_vehicle_speeds
)

from cv.traffic.queue import (
    detect_queued_vehicles,
    estimate_queue_length
)

from cv.traffic.traffic_state import (
    build_traffic_state
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

CONFIG_PATH = os.path.join(
    PROJECT_ROOT,
    "cv",
    "config",
    "intersection_config.yaml"
)

OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    "cv",
    "output"
)

TRAFFIC_STATE_DIR = os.path.join(
    OUTPUT_DIR,
    "traffic_states"
)

os.makedirs(
    TRAFFIC_STATE_DIR,
    exist_ok=True
)


# ============================================================
# CONFIGURATION
# ============================================================

WINDOW_SECONDS = 5

CONFIDENCE_THRESHOLD = 0.35

SPEED_THRESHOLD = 20

MIN_QUEUE_DURATION = 1.0

MAX_FRAME_GAP = 5

MIN_SPEED_OBSERVATIONS = 5

SMOOTHING_WINDOW = 5

TRACKER_CONFIG = "bytetrack.yaml"

directions = [
    "north",
    "south",
    "east",
    "west"
]


# ============================================================
# LOAD CONFIGURATION
# ============================================================

with open(CONFIG_PATH, "r") as file:
    config = yaml.safe_load(file)

junction_id = config["junction_id"]


# ============================================================
# HEADER
# ============================================================

print()
print("========================================")
print("   AI ADAPTIVE TRAFFIC - CV PIPELINE")
print("========================================")

print(
    f"Project directory : {PROJECT_ROOT}"
)

print(
    f"Configuration     : {CONFIG_PATH}"
)

print(
    f"Junction ID       : {junction_id}"
)

print(
    f"Observation window: "
    f"{WINDOW_SECONDS} seconds"
)


# ============================================================
# VIDEO PATHS
# ============================================================

video_paths = {}

print()
print("Configured videos:")

for direction in directions:

    video_name = config[direction]["video"]

    video_path = os.path.join(
        PROJECT_ROOT,
        "cv",
        "videos",
        video_name
    )

    video_paths[direction] = video_path

    exists = os.path.exists(video_path)

    print(
        f"{direction.upper():<6} → "
        f"{video_name:<15} "
        f"Exists: {exists}"
    )

    if not exists:
        raise FileNotFoundError(
            f"Video not found: {video_path}"
        )


# ============================================================
# VIDEO INFORMATION
# ============================================================

print()
print("Reading video information...")

video_info = {}

for direction, video_path in video_paths.items():

    import cv2

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open video: {video_path}"
        )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    frame_count = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    width = int(
        cap.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    )

    height = int(
        cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    )

    duration = (
        frame_count / fps
        if fps > 0
        else 0
    )

    video_info[direction] = {
        "fps": fps,
        "frame_count": frame_count,
        "width": width,
        "height": height,
        "duration": duration
    }

    print(
        f"{direction.upper():<6} → "
        f"{width}x{height} | "
        f"{fps:.2f} FPS | "
        f"{frame_count} frames | "
        f"{duration:.2f}s"
    )

    cap.release()


# ============================================================
# DETERMINE OBSERVATION WINDOWS
# ============================================================

max_duration = max(
    info["duration"]
    for info in video_info.values()
)

num_windows = int(
    (max_duration + WINDOW_SECONDS - 1)
    // WINDOW_SECONDS
)

print()
print(
    f"Total observation windows: "
    f"{num_windows}"
)

print(
    f"Approximate video duration: "
    f"{max_duration:.2f} seconds"
)


# ============================================================
# STORAGE
# ============================================================
#
# We process one camera completely at a time.
#
# Example:
#
# North:
#   0–5
#   5–10
#   ...
#   25–30
#
# Then South, East and West.
#
# This means only ONE YOLO model is loaded at a time.
# ============================================================

window_tracking_data = {
    direction: {}
    for direction in directions
}


# ============================================================
# PROCESS EACH CAMERA COMPLETELY
# ============================================================

for direction in directions:

    print()
    print("=" * 60)
    print(
        f"PROCESSING {direction.upper()} CAMERA"
    )
    print("=" * 60)

    video_path = video_paths[direction]

    fps = video_info[
        direction
    ]["fps"]

    # --------------------------------------------------------
    # LOAD ONLY ONE MODEL
    # --------------------------------------------------------

    print()
    print(
        "Loading YOLO model..."
    )

    model, device = load_model(
        "yolo11n.pt"
    )

    print(
        f"Device: {device}"
    )

    print(
        "Starting continuous "
        "ByteTrack tracking..."
    )

    # --------------------------------------------------------
    # TEMPORARY STORAGE
    # --------------------------------------------------------

    direction_window_frames = {
        window_index: []
        for window_index in range(
            num_windows
        )
    }

    # --------------------------------------------------------
    # PROCESS ENTIRE VIDEO IN ONE TRACK CALL
    # --------------------------------------------------------
    #
    # This is important.
    #
    # We DO NOT call model.track() separately
    # for every 5-second window.
    #
    # Instead:
    #
    # 0s → 30s
    #
    # is one continuous tracking sequence.
    #
    # Therefore ByteTrack can maintain track IDs
    # throughout the entire camera video.
    # --------------------------------------------------------

    results = model.track(
        source=video_path,
        classes=list(
            VEHICLE_CLASSES.keys()
        ),
        conf=CONFIDENCE_THRESHOLD,
        tracker=TRACKER_CONFIG,
        persist=True,
        device=device,
        stream=True,
        verbose=False
    )

    for frame_number, result in enumerate(
        results
    ):

        frame_df = result_to_dataframe(
            result,
            frame_number=frame_number
        )

        if frame_df.empty:
            continue

        # Determine which 5-second window
        # this frame belongs to.

        video_time = (
            frame_number / fps
        )

        window_index = int(
            video_time / WINDOW_SECONDS
        )

        # Protect against final-frame rounding
        if window_index >= num_windows:
            window_index = (
                num_windows - 1
            )

        direction_window_frames[
            window_index
        ].append(
            frame_df
        )

    # --------------------------------------------------------
    # COMBINE FRAMES INTO WINDOWS
    # --------------------------------------------------------

    for window_index in range(
        num_windows
    ):

        frames = (
            direction_window_frames[
                window_index
            ]
        )

        if frames:

            window_df = pd.concat(
                frames,
                ignore_index=True
            )

        else:

            window_df = pd.DataFrame()

        window_tracking_data[
            direction
        ][window_index] = window_df

        if window_df.empty:

            vehicle_count = 0
            observations = 0

        else:

            observations = len(
                window_df
            )

            vehicle_count = int(
                window_df[
                    "track_id"
                ].nunique()
            )

        print(
            f"{direction.upper():<6} | "
            f"Window {window_index + 1} | "
            f"Observations: "
            f"{observations} | "
            f"Vehicles: "
            f"{vehicle_count}"
        )

    # --------------------------------------------------------
    # RELEASE MODEL MEMORY
    # --------------------------------------------------------

    del results
    del model

    gc.collect()

    if device == "cuda":
        torch.cuda.empty_cache()

    print()
    print(
        f"{direction.upper()} camera "
        f"processing completed."
    )


# ============================================================
# PROCESS THE SIX TRAFFIC WINDOWS
# ============================================================

all_traffic_states = []


for window_index in range(
    num_windows
):

    window_start = (
        window_index * WINDOW_SECONDS
    )

    window_end = (
        window_start + WINDOW_SECONDS
    )

    print()
    print("=" * 60)
    print(
        f"WINDOW {window_index + 1}"
    )
    print(
        f"Time: {window_start}s → "
        f"{window_end}s"
    )
    print("=" * 60)


    # ========================================================
    # STEP 1: ROI + CLASS RESOLUTION
    # ========================================================

    print()
    print(
        "Applying ROI and "
        "resolving classes..."
    )

    roi_data = {}

    for direction in directions:

        df = (
            window_tracking_data[
                direction
            ][window_index]
        )

        if df.empty:

            roi_data[direction] = (
                pd.DataFrame()
            )

            print(
                f"{direction.upper():<6} → "
                f"ROI observations: 0 | "
                f"Vehicles: 0"
            )

            continue

        roi_points = config[
            direction
        ]["roi"]

        direction_df = (
            assign_roi_and_direction(
                df,
                roi_points=roi_points,
                direction=direction
            )
        )

        direction_df = (
            resolve_vehicle_class(
                direction_df
            )
        )

        roi_data[
            direction
        ] = direction_df

        vehicle_count = int(
            direction_df[
                "track_id"
            ].nunique()
        )

        print(
            f"{direction.upper():<6} → "
            f"ROI observations: "
            f"{len(direction_df)} | "
            f"Vehicles: "
            f"{vehicle_count}"
        )


    # ========================================================
    # STEP 2: SPEED
    # ========================================================

    print()
    print(
        "Calculating vehicle speeds..."
    )

    speed_data = {}

    for direction in directions:

        df = roi_data[direction]

        if df.empty:

            speed_data[direction] = (
                pd.DataFrame()
            )

            print(
                f"{direction.upper():<6} → "
                f"Speed observations: 0 | "
                f"Vehicles with speed: 0"
            )

            continue

        fps = video_info[
            direction
        ]["fps"]

        speed_df = compute_pixel_speed(
            df,
            fps=fps,
            max_frame_gap=MAX_FRAME_GAP
        )

        speed_data[
            direction
        ] = speed_df

        if speed_df.empty:

            speed_vehicle_count = 0

        else:

            speed_vehicle_count = int(
                speed_df[
                    "track_id"
                ].nunique()
            )

        print(
            f"{direction.upper():<6} → "
            f"Speed observations: "
            f"{len(speed_df)} | "
            f"Vehicles with speed: "
            f"{speed_vehicle_count}"
        )


    # ========================================================
    # STEP 3: QUEUE
    # ========================================================

    print()
    print(
        "Estimating queues..."
    )

    queue_data = {}

    for direction in directions:

        speed_df = (
            speed_data[direction]
        )

        if speed_df.empty:

            queue_data[direction] = (
                pd.DataFrame()
            )

            print(
                f"{direction.upper():<6} → "
                f"Queue runs: 0 | "
                f"Queue length: 0"
            )

            continue

        fps = video_info[
            direction
        ]["fps"]

        queued = (
            detect_queued_vehicles(
                speed_df,
                speed_threshold=(
                    SPEED_THRESHOLD
                ),
                min_queue_duration=(
                    MIN_QUEUE_DURATION
                ),
                fps=fps,
                max_frame_gap=(
                    MAX_FRAME_GAP
                )
            )
        )

        queue_data[
            direction
        ] = queued

        queue_length = (
            estimate_queue_length(
                queued
            )
        )

        print(
            f"{direction.upper():<6} → "
            f"Queue runs: "
            f"{len(queued)} | "
            f"Queue length: "
            f"{queue_length}"
        )


    # ========================================================
    # STEP 4: BUILD DIRECTION BLOCKS
    # ========================================================

    print()
    print(
        "Building traffic state..."
    )

    direction_blocks = {}

    for direction in directions:

        df = roi_data[direction]

        speed_df = speed_data[
            direction
        ]

        queued_df = queue_data[
            direction
        ]


        # ----------------------------------------------------
        # VEHICLE COUNTS
        # ----------------------------------------------------

        if df.empty:

            vehicles = 0
            cars = 0
            buses = 0
            trucks = 0
            motorcycles = 0

        else:

            vehicles = int(
                df[
                    "track_id"
                ].nunique()
            )

            vehicle_classes = (
                df[
                    [
                        "track_id",
                        "resolved_class"
                    ]
                ]
                .drop_duplicates(
                    "track_id"
                )
            )

            class_counts = (
                vehicle_classes[
                    "resolved_class"
                ]
                .value_counts()
                .to_dict()
            )

            cars = int(
                class_counts.get(
                    2,
                    0
                )
            )

            motorcycles = int(
                class_counts.get(
                    3,
                    0
                )
            )

            buses = int(
                class_counts.get(
                    5,
                    0
                )
            )

            trucks = int(
                class_counts.get(
                    7,
                    0
                )
            )


        # ----------------------------------------------------
        # AVERAGE SPEED
        # ----------------------------------------------------

        if speed_df.empty:

            average_speed = None

        else:

            representative_speeds = (
                representative_vehicle_speeds(
                    speed_df,
                    min_observations=(
                        MIN_SPEED_OBSERVATIONS
                    ),
                    smoothing_window=(
                        SMOOTHING_WINDOW
                    )
                )
            )

            if representative_speeds.empty:

                average_speed = None

            else:

                average_speed = round(
                    float(
                        representative_speeds[
                            "representative_pixel_speed"
                        ].mean()
                    ),
                    2
                )


        # ----------------------------------------------------
        # QUEUE LENGTH
        # ----------------------------------------------------

        queue_length = (
            estimate_queue_length(
                queued_df
            )
        )


        # ----------------------------------------------------
        # DIRECTION BLOCK
        # ----------------------------------------------------

        direction_blocks[
            direction
        ] = {

            "vehicles": vehicles,

            "cars": cars,

            "buses": buses,

            "trucks": trucks,

            "motorcycles": motorcycles,

            "average_speed": (
                average_speed
            ),

            "queue_length": (
                queue_length
            )
        }


        print(
            f"{direction.upper():<6} → "
            f"Vehicles: {vehicles} | "
            f"Avg speed: "
            f"{average_speed} px/s | "
            f"Queue: {queue_length}"
        )


    # ========================================================
    # STEP 5: BUILD TRAFFIC STATE
    # ========================================================

    traffic_state = build_traffic_state(
        junction_id=junction_id,

        north=direction_blocks[
            "north"
        ],

        south=direction_blocks[
            "south"
        ],

        east=direction_blocks[
            "east"
        ],

        west=direction_blocks[
            "west"
        ]
    )


    # ========================================================
    # STEP 6: SAVE INDIVIDUAL STATE
    # ========================================================

    state_filename = (
        f"traffic_state_"
        f"{window_index + 1:03d}.json"
    )

    state_path = os.path.join(
        TRAFFIC_STATE_DIR,
        state_filename
    )

    with open(
        state_path,
        "w"
    ) as file:

        json.dump(
            traffic_state,
            file,
            indent=4
        )

    all_traffic_states.append(
        traffic_state
    )

    print()
    print(
        "Traffic state generated:"
    )

    print(
        json.dumps(
            traffic_state,
            indent=4
        )
    )

    print()
    print(
        f"Saved: {state_path}"
    )


# ============================================================
# SAVE COMPLETE SESSION
# ============================================================

summary_path = os.path.join(
    TRAFFIC_STATE_DIR,
    "traffic_states_all.json"
)

with open(
    summary_path,
    "w"
) as file:

    json.dump(
        all_traffic_states,
        file,
        indent=4
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print(
    "========================================"
)

print(
    "       CV PIPELINE COMPLETED"
)

print(
    "========================================"
)

print(
    f"Total windows processed: "
    f"{num_windows}"
)

print(
    f"Window size: "
    f"{WINDOW_SECONDS} seconds"
)

print()
print(
    "Output directory:"
)

print(
    TRAFFIC_STATE_DIR
)

print()
print(
    "Complete session summary:"
)

print(
    summary_path
)

print()
print(
    "The CV module processed the complete "
    "video sequence and generated updated "
    "four-direction traffic states."
)