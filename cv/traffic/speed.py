import numpy as np


def compute_pixel_speed(df, fps, max_frame_gap=5):
    """
    Computes frame-to-frame pixel speed for each tracked vehicle.

    Filters out observations with large frame gaps or invalid time
    intervals.

    Returns the tracking data with speed-related columns,
    restricted to valid observations.
    """

    df = df.copy().sort_values(
        ["track_id", "frame"]
    )

    df["time_seconds"] = df["frame"] / fps

    df["delta_x"] = (
        df.groupby("track_id")["center_x"].diff()
    )

    df["delta_y"] = (
        df.groupby("track_id")["center_y"].diff()
    )

    df["pixel_displacement"] = np.sqrt(
        df["delta_x"] ** 2 +
        df["delta_y"] ** 2
    )

    df["frame_gap"] = (
        df.groupby("track_id")["frame"].diff()
    )

    df["time_delta"] = (
        df.groupby("track_id")["time_seconds"].diff()
    )

    df_valid = df[
        (df["frame_gap"] >= 1) &
        (df["frame_gap"] <= max_frame_gap) &
        (df["time_delta"] > 0)
    ].copy()

    df_valid["pixel_speed"] = (
        df_valid["pixel_displacement"] /
        df_valid["time_delta"]
    )

    return df_valid


def representative_vehicle_speeds(
    df_valid,
    min_observations=10,
    smoothing_window=5
):
    """
    Smooths per-frame pixel speed using a rolling median
    and calculates one representative pixel speed per vehicle.

    Only vehicles with sufficient valid observations are retained.
    """

    df_valid = df_valid.sort_values(
        ["track_id", "frame"]
    ).copy()

    df_valid["smoothed_pixel_speed"] = (
        df_valid
        .groupby("track_id")["pixel_speed"]
        .transform(
            lambda x: x.rolling(
                window=smoothing_window,
                center=True,
                min_periods=1
            ).median()
        )
    )

    vehicle_speed = (
        df_valid
        .groupby("track_id")["smoothed_pixel_speed"]
        .median()
        .rename("representative_pixel_speed")
        .to_frame()
    )

    observations = (
        df_valid
        .groupby("track_id")["pixel_speed"]
        .count()
        .rename("observations")
    )

    vehicle_speed = vehicle_speed.join(
        observations
    )

    return vehicle_speed[
        vehicle_speed["observations"] >= min_observations
    ]