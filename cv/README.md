## Running the CV Pipeline on Kaggle

The video dataset is not stored in this repository (too large for git). 
It's hosted separately on Kaggle and must be attached to your notebook 
as a data source before running.

### 1. Create a new Kaggle notebook
- Go to kaggle.com → Code → New Notebook
- Under Notebook Settings (right sidebar), set **Accelerator** to GPU 
  (T4 x1 or better) — detection runs far slower on CPU.

### 2. Attach the video dataset
- In the right sidebar, click **Add Input**
- Search for and add the dataset: `govindvijay001/ai-traffic-videos`
- This mounts the videos at `/kaggle/input/ai-traffic-videos/` 
  (read-only — you cannot modify files there directly)

### 3. Clone this repository
Run in a notebook cell:
```python
%cd /kaggle/working
!rm -rf AI_Adaptive_Traffic_Analysis_and_Signal_Optimization
!git clone -b feature/cv-yolo-detection https://github.com/Govind-2004/AI_Adaptive_Traffic_Analysis_and_Signal_Optimization.git
```
(Once this branch is merged to `main`, drop the `-b feature/cv-yolo-detection` flag.)

### 4. Copy the videos into the project structure
```python
import os

for root, dirs, files in os.walk("/kaggle/input"):
    for file in files:
        if file.lower().endswith((".mp4", ".avi", ".mov", ".mkv")):
            print(os.path.join(root, file))


%cd /kaggle/working/AI_Adaptive_Traffic_Analysis_and_Signal_Optimization

!mkdir -p cv/videos

!cp /kaggle/input/datasets/govindvijay001/ai-traffic-videos/North.mp4 cv/videos/
!cp /kaggle/input/datasets/govindvijay001/ai-traffic-videos/South.mp4 cv/videos/
!cp /kaggle/input/datasets/govindvijay001/ai-traffic-videos/East.mp4 cv/videos/
!cp /kaggle/input/datasets/govindvijay001/ai-traffic-videos/West.mp4 cv/videos/            
```
If you're using your own videos instead of the provided dataset, upload 
them as a Kaggle private dataset first, then adjust the paths above to 
match your dataset's slug (visible under Add Input once attached).

### 5. Install dependencies
```python
!pip install -q ultralytics
import ultralytics
import cv2
import pandas
import numpy
import torch
```
(OpenCV, pandas, numpy, torch are pre-installed in Kaggle's environment.)

### 6. Run the full pipeline
```python
!python -m cv.src.main_cv
```
This runs detection, tracking, ROI assignment, speed, and queue estimation 
for all four directions, and writes one `traffic_state.json` per direction 
(plus the assembled 4-direction state) to `cv/output/traffic_states/`.

### 7. View the output
```python
import os
output_dir = "cv/output/traffic_states"
for file in sorted(os.listdir(output_dir)):
    print(file)
```

### Notes
- ROI polygons and speed/queue thresholds in `cv/config/` are calibrated 
  for the specific camera angles in the provided dataset. Using different 
  footage will require recalibrating these — see `cv/notebook/` for the 
  calibration process used to derive them.
- Expected runtime: approximately [X] minutes for all four videos on a 
  Kaggle T4 GPU.
