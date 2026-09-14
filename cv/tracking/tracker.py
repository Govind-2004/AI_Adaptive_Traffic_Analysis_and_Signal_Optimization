# cv/tracking/tracker.py

def track_vehicles(video_path, model, classes, tracker="bytetrack.yaml", conf=0.35):
    """
    Runs detection + persistent ID tracking on a video.
    Returns a generator of per-frame results (same as ultralytics .track()).
    """
    return model.track(
        source=video_path,
        classes=list(classes.keys()),
        conf=conf,
        tracker=tracker,
        persist=True,
        stream=True,
        verbose=False
    )
