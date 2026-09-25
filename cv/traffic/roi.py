import cv2
import numpy as np


def assign_roi_and_direction(df, roi_points, direction):
    """
    Filters tracking data to vehicles inside the road ROI
    and assigns the physical approach direction configured
    for the camera.
    """

    roi_polygon = np.array(roi_points, dtype=np.int32)

    df = df.copy()

    df["in_roi"] = df.apply(
        lambda row: cv2.pointPolygonTest(
            roi_polygon,
            (float(row["center_x"]), float(row["center_y"])),
            False
        ) >= 0,
        axis=1
    )

    df["direction"] = direction

    return df[df["in_roi"]].copy()


def resolve_vehicle_class(df):
    """
    Assigns each track_id its most frequently detected
    vehicle class to reduce class-label flickering.
    """

    track_class = (
        df.groupby("track_id")["class"]
        .agg(lambda x: x.value_counts().idxmax())
    )

    df = df.copy()
    df["resolved_class"] = df["track_id"].map(track_class)

    return df