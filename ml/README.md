# Traffic Prediction & Congestion Intelligence

This folder contains the machine-learning components of the AI Traffic Signal Optimization system.

The ML pipeline is responsible for analyzing traffic-state data, estimating congestion, predicting short-term queue length, and providing the prediction input used by the adaptive signal controller.

---

## 1. Role of the ML Module

The ML module forms the prediction layer of the system:

```text
Traffic State
     ↓
Feature Engineering
     ↓
Congestion Estimation
     ↓
Random Forest Regression
     ↓
Predicted Queue
     ↓
AI Signal Controller
```

The prediction target is the approximate queue length expected around **30 seconds ahead**.

---

## 2. Main Components

### `traffic_prediction.py`

Contains the main machine-learning workflow, including:

* Dataset loading and preparation
* Exploratory data analysis
* Traffic feature analysis
* Model training
* Model evaluation
* Hyperparameter tuning
* Feature-importance analysis
* Final model selection
* Model export

The evaluated models include:

* Linear Regression
* Random Forest
* Gradient Boosting
* Tuned Random Forest
* XGBoost

---

### `feature_engineering.py`

Builds the traffic features used by the final Random Forest model.

The deployed model uses the following 11 features:

| Feature            | Description                                  |
| ------------------ | -------------------------------------------- |
| `vehicles`         | Current number of vehicles                   |
| `queue_length`     | Current number of halting/queued vehicles    |
| `average_speed`    | Current average speed                        |
| `count_trend`      | Change in vehicle count                      |
| `queue_trend`      | Change in queue length                       |
| `speed_trend`      | Change in average speed                      |
| `avg_count_20s`    | Average vehicle count over the recent window |
| `avg_queue_20s`    | Average queue length over the recent window  |
| `avg_speed_20s`    | Average speed over the recent window         |
| `congestion_score` | Interpretable congestion score               |
| `is_green`         | Whether the approach currently has green     |

The prediction pipeline uses four traffic readings at 5-second intervals, corresponding to approximately **20 seconds of recent traffic history**.

---

### `traffic_prediction_rf.pkl`

This is the exported Random Forest regression model used during deployment.

The model is loaded using `joblib` and its stored `feature_names_in_` attribute is used to preserve the trained feature order.

The model is used by the SUMO/TraCI controller to predict future queue length from live simulation traffic-state data.

---

### `congestion_score.py`

Implements an interpretable rule-based congestion score.

The score combines:

* Queue length
* Vehicle count
* Average speed

with the following weighting:

```text
Queue length       → 45%
Vehicle count      → 30%
Average speed      → 25%
```

The score is normalized to the range **0–1** and classified as:

```text
LOW
MEDIUM
HIGH
```

A higher congestion score indicates more severe traffic conditions.

---

## 3. Model Development

The training workflow uses traffic observations from the developed traffic scenarios.

The ML pipeline performs:

```text
Data Loading
    ↓
Data Cleaning
    ↓
EDA
    ↓
Feature Engineering
    ↓
Temporal Train/Test Split
    ↓
Model Training
    ↓
Model Evaluation
    ↓
Model Comparison
    ↓
Final Model Selection
    ↓
Model Export
```

The final Random Forest model was selected based on its performance across the evaluated regression models and its ability to capture nonlinear relationships between traffic-state features and future queue length.

---

## 4. Model Evaluation

The model-development experiments evaluate regression models using:

* Mean Absolute Error (MAE)
* Root Mean Squared Error (RMSE)
* R² score

The reported Random Forest evaluation in the model-development workflow achieved:

```text
R²   = 0.7709
RMSE = 1.9457
```

Further queue-group error analysis was also performed to examine prediction behavior under different traffic conditions.

---

## 5. Prediction Concept

The model receives recent traffic-state information and predicts the future queue:

```text
Current traffic
      +
Recent traffic trend
      +
20-second averages
      +
Congestion score
      +
Signal state
      ↓
Random Forest
      ↓
Predicted queue (~30 seconds)
```

The predicted queue is then supplied to the signal-control module.

---

## 6. Example Prediction

Example traffic state:

```text
Vehicles          : 12
Current queue     : 7
Average speed     : 4.5 m/s
Count trend       : +2
Queue trend       : +1
Speed trend       : -0.8
20s avg vehicles  : 10.5
20s avg queue     : 6.0
20s avg speed     : 5.2
Congestion score  : 0.70
Signal green      : 1
```

The model produces a predicted future queue, which can then be used to determine whether additional green time may be beneficial.

---

## 7. Requirements

Install the required Python packages:

```bash
pip install pandas numpy matplotlib seaborn scikit-learn joblib
```

---

## 8. Important Model Compatibility Note

The exported model should be loaded using:

```python
import joblib

model = joblib.load("traffic_prediction_rf.pkl")
```

The deployment code should use the exact feature order stored in:

```python
model.feature_names_in_
```

This prevents feature-order mismatches between training and inference.

---

## 9. Integration with SUMO

The ML module does not independently control the traffic light.

Instead:

```text
SUMO / TraCI
      ↓
Current traffic state
      ↓
Feature engineering
      ↓
RF prediction
      ↓
AI signal controller
```

The prediction is therefore one component of the larger traffic-signal optimization system.

---

## 10. Folder Structure

```text
ml/
│
├── README.md
├── traffic_prediction.py
├── feature_engineering.py
├── congestion_score.py
├── traffic_prediction_rf.pkl
│
└── data/
    ├── training_data.csv
    └── test_data.csv
```

---

## 11. Output

The ML module provides:

* Current traffic features
* Congestion score
* Congestion level
* Predicted queue length
* Traffic trend information
* Trained Random Forest model

These outputs are consumed by the signal-control and simulation modules.

