# cv/tracking/tracker.py
import pandas as pd
def track_vehicles(video_path, model, classes, tracker="bytetrack.yaml", conf=0.35):
    
    # Runs detection + persistent ID tracking on a video.
    # Returns a generator of per-frame results (same as ultralytics .track()).
    
    return model.track(
        source=video_path,
        classes=list(classes.keys()),
        conf=conf,
        tracker=tracker,
        persist=True,
        stream=True,
        verbose=False
    )

def result_to_dataframe(result, frame_number):
    """
    Converts one Ultralytics tracking result into
    a DataFrame suitable for ROI and traffic processing.
    """

 # Converts each YOLO/ByteTrack result into this DataFrame format.  

    rows = []

    if result.boxes is None or result.boxes.id is None:
        return pd.DataFrame(
            columns=[
                "track_id",
                "class",
                "center_x",
                "center_y",
                "frame"
            ]
        )

    boxes = result.boxes

    track_ids = boxes.id.cpu().numpy()
    classes = boxes.cls.cpu().numpy()
    xyxy = boxes.xyxy.cpu().numpy()

    for track_id, cls, box in zip(
        track_ids,
        classes,
        xyxy
    ):
        x1, y1, x2, y2 = box

        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        rows.append({
            "track_id": int(track_id),
            "class": int(cls),
            "center_x": float(center_x),
            "center_y": float(center_y),
            "frame": frame_number
        })

    return pd.DataFrame(rows)
