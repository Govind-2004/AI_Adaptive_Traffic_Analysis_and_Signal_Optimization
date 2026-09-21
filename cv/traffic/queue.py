import pandas as pd


def detect_queued_vehicles(
    df,
    speed_threshold,
    min_queue_duration,
    fps,
    max_frame_gap=5
):
    """
    Identifies vehicles that remain below a configured
    pixel-speed threshold for at least the minimum queue duration.
    """

    required_columns = {"track_id", "frame", "pixel_speed"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if fps <= 0:
        raise ValueError("fps must be greater than 0")

    if speed_threshold < 0:
        raise ValueError("speed_threshold cannot be negative")

    if min_queue_duration < 0:
        raise ValueError("min_queue_duration cannot be negative")

    df = df.copy()
    df = df.sort_values(["track_id", "frame"]).reset_index(drop=True)

    df["frame_gap"] = df.groupby("track_id")["frame"].diff()

    df["is_slow"] = df["pixel_speed"] <= speed_threshold

    df["run_break"] = (
        (~df["is_slow"]) |
        (df["frame_gap"] > max_frame_gap) |
        (df["frame_gap"].isna())
    )

    df["run_id"] = (
        df.groupby("track_id")["run_break"]
        .cumsum()
    )

    slow_df = df[df["is_slow"]].copy()

    if slow_df.empty:
        return pd.DataFrame(
            columns=[
                "track_id",
                "run_id",
                "start_frame",
                "end_frame",
                "observations",
                "duration_seconds"
            ]
        )

    queue_runs = (
        slow_df
        .groupby(["track_id", "run_id"])
        .agg(
            start_frame=("frame", "min"),
            end_frame=("frame", "max"),
            observations=("frame", "count")
        )
        .reset_index()
    )

    queue_runs["duration_seconds"] = (
        (queue_runs["end_frame"] -
         queue_runs["start_frame"]) / fps
    )

    queue_runs = queue_runs[
        queue_runs["duration_seconds"] >= min_queue_duration
    ].copy()

    return queue_runs


def estimate_queue_length(df_queued):
    """
    Estimates queue length as the number of unique vehicles
    identified as persistent slow/queued vehicles.
    """

    if df_queued.empty:
        return 0

    return int(df_queued["track_id"].nunique())