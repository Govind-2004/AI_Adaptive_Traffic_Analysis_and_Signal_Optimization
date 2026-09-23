"""
Main Computer Vision Pipeline

Pipeline:
Video
  ↓
YOLO Detection
  ↓
ByteTrack Tracking
  ↓
ROI / Direction Assignment
  ↓
Vehicle Class Resolution
  ↓
Speed Estimation
  ↓
Queue Estimation
  ↓
Traffic State
  ↓
JSON Output
"""

import os
import yaml
import pandas as pd

# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

PROJECT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

CONFIG_PATH = os.path.join(
    PROJECT_DIR,
    "cv",
    "config",
    "intersection_config.yaml"
)


# --------------------------------------------------
# 2. Load configuration
# --------------------------------------------------

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)


# --------------------------------------------------
# 3. Display configuration
# --------------------------------------------------

print("========================================")
print("   AI ADAPTIVE TRAFFIC - CV PIPELINE")
print("========================================")

print(f"Project directory : {PROJECT_DIR}")
print(f"Configuration     : {CONFIG_PATH}")
print(f"Junction ID       : {config['junction_id']}")

print("\nConfigured videos:")

for direction in ["north", "south", "east", "west"]:
    video_name = config[direction]["video"]

    video_path = os.path.join(
        PROJECT_DIR,
        "cv",
        "videos",
        video_name
    )

    print(
        f"{direction.upper():<6} → "
        f"{video_name:<15} "
        f"Exists: {os.path.exists(video_path)}"
    )

    # --------------------------------------------------
# 4. Import CV modules
# --------------------------------------------------

from cv.detection.detector import (
    load_model,
    VEHICLE_CLASSES
)

from cv.tracking.tracker import track_vehicles

# --------------------------------------------------
# 5. Load YOLO model
# --------------------------------------------------

print("\nLoading YOLO model...")

model, device = load_model()

print(f"YOLO model loaded successfully.")
print(f"Device: {device}")
print(f"Vehicle classes: {VEHICLE_CLASSES}")

# --------------------------------------------------
# 6. Test YOLO + ByteTrack on North video
# --------------------------------------------------

print("\nTesting YOLO + ByteTrack on NORTH video...")

north_video = os.path.join(
    PROJECT_DIR,
    "cv",
    "videos",
    config["north"]["video"]
)

results = track_vehicles(
    video_path=north_video,
    model=model,
    classes=VEHICLE_CLASSES,
    tracker="bytetrack.yaml",
    conf=0.35
)

# Get the first processed frame
first_result = next(results)

print("North video processed successfully.")

if first_result.boxes is not None:
    print(
        f"Detections in first frame: "
        f"{len(first_result.boxes)}"
    )
else:
    print("Detections in first frame: 0")


# --------------------------------------------------
# 7. Save annotated frame
# --------------------------------------------------

OUTPUT_DIR = os.path.join(
    PROJECT_DIR,
    "cv",
    "output",
    "detection_test"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

output_path = os.path.join(
    OUTPUT_DIR,
    "north_tracking_test.jpg"
)

first_result.save(filename=output_path)

print(f"Annotated frame saved to: {output_path}")

# --------------------------------------------------
# 8. Convert tracking result to DataFrame
# --------------------------------------------------

from cv.tracking.tracker import result_to_dataframe

tracking_df = result_to_dataframe(
    first_result,
    frame_number=0
)

print("\nTracking DataFrame:")
print(tracking_df)

# --------------------------------------------------
# 9. Apply North ROI
# --------------------------------------------------

from cv.traffic.roi import assign_roi_and_direction

north_roi = config["north"]["roi"]

north_roi_df = assign_roi_and_direction(
    tracking_df,
    roi_points=north_roi,
    direction="north"
)

print("\nNorth ROI DataFrame:")
print(north_roi_df)

print(
    f"\nVehicles inside North ROI: "
    f"{len(north_roi_df)}"
)

# --------------------------------------------------
# 10. Process North video for ROI analysis
# --------------------------------------------------

print("\nProcessing NORTH video for ROI analysis...")

north_results = track_vehicles(
    video_path=north_video,
    model=model,
    classes=VEHICLE_CLASSES,
    tracker="bytetrack.yaml",
    conf=0.35
)

north_tracking_frames = []

for frame_number, result in enumerate(north_results):

    frame_df = result_to_dataframe(
        result,
        frame_number=frame_number
    )

    if not frame_df.empty:
        north_tracking_frames.append(frame_df)

if north_tracking_frames:
    north_tracking_df = pd.concat(
        north_tracking_frames,
        ignore_index=True
    )
else:
    north_tracking_df = pd.DataFrame()

print(
    f"Total tracking observations: "
    f"{len(north_tracking_df)}"
)

print(
    f"Unique vehicles tracked: "
    f"{north_tracking_df['track_id'].nunique()}"
)