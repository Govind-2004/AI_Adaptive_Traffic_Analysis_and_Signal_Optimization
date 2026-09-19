def count_vehicles(df):
    # Per-frame total and per-class unique vehicle counts
    frame_counts = df.groupby("frame")["track_id"].nunique().reset_index(name="vehicle_count")
    class_frame_counts = (
        df.groupby(["frame", "class"])["track_id"].nunique()
        .reset_index(name="count")
        .pivot(index="frame", columns="class", values="count")
        .fillna(0).reset_index()
    )
    return frame_counts, class_frame_counts

def class_distribution(df):
    # Overall unique vehicle count per class
    return df.groupby("class")["track_id"].nunique().reset_index(name="vehicle_count")