# SUMO Traffic Simulation & Adaptive Signal Control

This folder contains the SUMO simulation environment, TraCI integration, traffic-signal controller, and Traditional-vs-AI evaluation for the AI Traffic Signal Optimization project.

---

## 1. Role of the SUMO Module

The SUMO module provides the simulation and control environment used to test the proposed traffic-signal optimization system.

The complete control pipeline is:

```text
SUMO Traffic Simulation
        ↓
TraCI
        ↓
Current Traffic State
        ↓
Congestion Score
        ↓
RF Queue Prediction
        ↓
AI Signal Controller
        ↓
Green Extension
        ↓
SUMO
```

The AI controller is compared against a traditional fixed-time signal.

---

## 2. Traffic Signal Sequence

The traffic-light system uses a predefined 12-phase sequence.

```text
Phase 0  → NS main green
Phase 1  → NS yellow
Phase 2  → All-red
Phase 3  → NS protected right
Phase 4  → NS right yellow
Phase 5  → All-red

Phase 6  → EW main green
Phase 7  → EW yellow
Phase 8  → All-red
Phase 9  → EW protected right
Phase 10 → EW right yellow
Phase 11 → All-red

Then the sequence repeats.
```

The AI controller does **not** replace this sequence.

The AI can only modify the duration of the currently active main-green phase.

It does not directly jump between phases.

---

## 3. Approach Configuration

The simulated intersection contains four incoming approaches:

```text
North → N_in
South → S_in
East  → E_in
West  → W_in
```

Main green phases:

```text
North/South → Phase 0
East/West   → Phase 6
```

---

## 4. Main Files

### `scenario_F.sumocfg`

SUMO configuration file for Scenario F.

It defines the simulation configuration and simulation duration.

---

### `scenario_F_traditional_vs_ai.py`

Main experiment script.

It performs:

1. Traditional fixed-time simulation
2. AI-controlled simulation
3. Traffic-state collection
4. Congestion calculation
5. RF queue prediction
6. AI signal decisions
7. Tripinfo analysis
8. Traditional-vs-AI comparison

The experiment uses the same Scenario F traffic demand for both controllers.

---

### `ai_signal_controller.py`

Contains the adaptive signal-control logic.

The controller considers:

* Current congestion
* Current queue
* Predicted queue
* Phase elapsed time
* Fairness constraints
* Green-duration constraints

The controller can return actions such as:

```text
KEEP_PHASE
EXTEND_GREEN
```

Direct phase switching is disabled for the final experimental design so that the programmed sequence remains unchanged.

---

### `congestion_score.py`

Provides the rule-based congestion score used by both the prediction and control pipeline.

The score is based on:

```text
45% → Queue length
30% → Vehicle count
25% → Average speed
```

and produces a score between 0 and 1 with:

```text
LOW
MEDIUM
HIGH
```

---

### `traci_test.py`

TraCI integration/testing script.

It connects Python to SUMO, reads traffic-state information from the simulated intersection, performs prediction/control processing, and verifies the complete simulation-control pipeline.

---

## 5. AI Safety Constraints

The controller uses explicit safety constraints.

### Minimum green

```text
MIN_GREEN = 10 seconds
```

The AI does not attempt to modify the phase before the minimum green duration.

### Maximum green

```text
MAX_GREEN = 45 seconds
```

This limits the total duration of a main-green phase.

### Maximum AI extension

```text
MAX_EXTENSION = 10 seconds
```

The AI can add at most 10 seconds to a main-green phase.

### Fairness

A fairness limit is used to prevent one traffic direction from continuously receiving preference.

### Phase-sequence preservation

The AI does not directly switch:

```text
NS → EW
```

or:

```text
EW → NS
```

The existing SUMO sequence remains responsible for phase transitions.

---

## 6. AI Decision Process

At each traffic-reading interval:

```text
1. Read traffic state
        ↓
2. Calculate congestion
        ↓
3. Update traffic history
        ↓
4. Predict future queue using RF
        ↓
5. Calculate traffic demand
        ↓
6. Evaluate safety constraints
        ↓
7. KEEP or EXTEND
        ↓
8. Continue programmed signal sequence
```

Traffic information is sampled approximately every **5 seconds**.

The RF model uses four readings, giving approximately **20 seconds of recent traffic history**.

---

## 7. Green Extension Logic

The AI does not directly replace the phase program.

When the AI requests an extension, the controller:

```text
Current phase
      ↓
Check safety constraints
      ↓
Calculate allowed extension
      ↓
Modify remaining phase duration
      ↓
SUMO continues existing sequence
```

The implementation accounts for the fact that the TraCI phase-duration command operates on the remaining duration of the current phase.

---

## 8. Traditional Controller

The traditional controller provides the baseline.

Characteristics:

```text
Fixed programmed timings
No traffic adaptation
No RF prediction
No congestion-based extension
No AI decision making
```

It therefore represents the conventional signal-control condition against which the AI controller is evaluated.

---

## 9. Scenario Set

The project contains multiple traffic-demand scenarios designed to represent different traffic conditions.

### Scenario A — Low Traffic

Approximate demand:

```text
120 vehicles/hour/approach
```

Purpose:

```text
Low-demand baseline condition
```

---

### Scenario B — Balanced Traffic

Approximate demand:

```text
400 vehicles/hour/approach
```

Purpose:

```text
Balanced traffic condition
```

---

### Scenario C — Heavy North/South Traffic

Approximate demand:

```text
North/South ≈ 700 vehicles/hour
East/West    ≈ 120 vehicles/hour
```

Purpose:

```text
Directional congestion toward North/South
```

---

### Scenario D — Heavy East/West Traffic

Approximate demand:

```text
East/West    ≈ 700 vehicles/hour
North/South  ≈ 120 vehicles/hour
```

Purpose:

```text
Directional congestion toward East/West
```

---

### Scenario E — Traffic Surge

The scenario begins under a more balanced condition and subsequently introduces a stronger North-direction traffic demand.

Purpose:

```text
Evaluate the controller under changing traffic demand.
```

---

### Scenario F — Integrated AI Evaluation

Scenario F combines the developed traffic-state, ML prediction, and adaptive-control components.

The primary comparison is:

```text
Traditional Fixed-Time
        VS
Enhanced AI Controller
```

---

## 10. Scenario F Experiment

The Scenario F experiment runs two independent simulations using the same traffic demand:

```text
                    Scenario F
                       │
             ┌─────────┴─────────┐
             ↓                   ↓
      Traditional              AI
      Fixed-Time               Controller
             │                   │
             ↓                   ↓
       Tripinfo XML          Tripinfo XML
             │                   │
             └─────────┬─────────┘
                       ↓
                 Metric Comparison
```

---

## 11. Current Scenario F Result

A 180-second Scenario F run produced the following observed results:

| Metric               | Traditional | Enhanced AI |       Change |
| -------------------- | ----------: | ----------: | -----------: |
| Average waiting time |    17.519 s |    13.667 s | 21.99% lower |
| Average queue length |       0.669 |       0.520 | 22.22% lower |
| Average travel time  |    53.519 s |    48.741 s |  8.93% lower |
| Average speed        |  11.158 m/s |  11.648 m/s | 4.39% higher |
| Completed vehicles   |          27 |          27 |    No change |
| Waiting-count events |          19 |          13 | 31.58% lower |

During this run:

```text
AI green extensions        : 2
Total extension time      : 10 seconds
Completed vehicles        : 27 / 27
```

These values represent one 180-second Scenario F run and should be treated as an experimental observation rather than a multi-run statistical benchmark.

---

## 12. Running the Simulation

Make sure SUMO and TraCI are installed and available in the system environment.

Example Python dependencies:

```bash
pip install traci sumolib pandas joblib scikit-learn
```

Run the experiment:

```bash
python scenario_F_traditional_vs_ai.py
```

The experiment launches SUMO-GUI and performs the Traditional and AI runs sequentially.

---

## 13. Expected Output

The terminal displays information similar to:

```text
TIME: 70.0s
PHASE: 6
GROUP: EW

north   vehicles=1  queue=1  ...
south   vehicles=0  queue=0  ...
east    vehicles=1  queue=1  ...
west    vehicles=1  queue=1  ...

AI SIGNAL DECISION
Final action: KEEP_PHASE
```

When the AI determines that additional green time is appropriate:

```text
AI EXTENSION

Current phase: 6
Added: +5.0s
Total extension: +5.0s
Intended total green: ...
Remaining green: ...
Next switch shifted: ...
```

---

## 14. Output Files

The experiment generates SUMO trip-information files:

```text
scenario_F_traditional_tripinfo.xml
scenario_F_ai_tripinfo.xml
```

These files are used to calculate:

* Average waiting time
* Average travel time
* Average speed
* Completed vehicles
* Unfinished vehicles
* Waiting-count events

---

## 15. Repository Structure

```text
sumo/
│
├── README.md
│
├── scenario_F.sumocfg
├── scenario_F.net.xml
├── scenario_F.rou.xml
│
├── scenario_F_traditional_vs_ai.py
├── ai_signal_controller.py
├── traci_test.py
├── congestion_score.py
│
├── scenario_F_traditional_tripinfo.xml
└── scenario_F_ai_tripinfo.xml
```

Additional SUMO network, route, connection, and signal files required by the scenarios should also be stored in this folder.

---

## 16. Relationship with the ML Module

The SUMO module consumes the ML prediction model from the ML module:

```text
SUMO
 ↓
Traffic state
 ↓
Feature engineering
 ↓
Random Forest model
 ↓
Predicted queue
 ↓
AI signal controller
 ↓
SUMO signal timing
```

This creates the closed-loop simulation used to evaluate the proposed system.

---

## 17. Project Objective

The purpose of this module is to demonstrate that traffic-signal timing can be adapted using observed and predicted traffic conditions while preserving the predefined signal sequence and enforcing explicit safety constraints.

The SUMO environment provides a controlled platform for comparing the proposed AI-based controller with a traditional fixed-time baseline.

