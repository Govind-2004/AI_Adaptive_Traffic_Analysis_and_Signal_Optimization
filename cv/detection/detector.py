
# YOLO model loading
from ultralytics import YOLO
import torch

def load_model(model_path="yolo11n.pt"):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = YOLO(model_path)
    return model, device

# Vehicle class definitions
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

# Detection function
def detect_vehicles(frame, model, device, conf=0.35):
    results = model(
        frame,
        device=device,
        classes=list(VEHICLE_CLASSES.keys()),
        conf=conf,
        verbose=False
    )
    return results[0]