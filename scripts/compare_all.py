"""
compare_all.py
----------------
Runs the fixed-vs-adaptive comparison across all 5 scenarios (A-E) at once
and prints one consolidated results table -- this is the table you'll use
directly in your review/report.

Expects tripinfo files already generated, named exactly:
    fixed_A_tripinfo.xml   adaptive_A_tripinfo.xml
    fixed_B_tripinfo.xml   adaptive_B_tripinfo.xml
    ... etc for C, D, E

USAGE:
    python compare_all.py
"""

import xml.etree.ElementTree as ET
import os

SCENARIOS = {
    "A": "Low traffic",
    "B": "Balanced",
    "C": "Heavy N-S",
    "D": "Heavy E-W",
    "E": "Sudden surge",
}


def analyze(tripinfo_path):
    if not os.path.exists(tripinfo_path):
        return None
    tree = ET.parse(tripinfo_path)
    trips = tree.findall("tripinfo")
    if not trips:
        return {"count": 0, "avg_waiting": 0, "avg_duration": 0}
    waiting_times = [float(t.get("waitingTime")) for t in trips]
    durations = [float(t.get("duration")) for t in trips]
    return {
        "count": len(trips),
        "avg_waiting": sum(waiting_times) / len(waiting_times),
        "avg_duration": sum(durations) / len(durations),
    }


def pct_change(fixed_val, adaptive_val, lower_is_better=True):
    if fixed_val == 0:
        return "N/A"
    change = (fixed_val - adaptive_val) / fixed_val * 100
    if not lower_is_better:
        change = -change
    return f"{change:+.1f}%"


def main():
    print(f"\n{'Scenario':<10}{'Condition':<15}{'Waiting':<12}{'Travel':<12}{'Throughput':<15}")
    print("-" * 65)

    for letter, name in SCENARIOS.items():
        fixed_path = f"fixed_{letter}_tripinfo.xml"
        adaptive_path = f"adaptive_{letter}_tripinfo.xml"

        fixed = analyze(fixed_path)
        adaptive = analyze(adaptive_path)

        if fixed is None or adaptive is None:
            print(f"{letter:<10}{name:<15}{'-- missing files --':<40}")
            continue

        wait_change = pct_change(fixed["avg_waiting"], adaptive["avg_waiting"])
        travel_change = pct_change(fixed["avg_duration"], adaptive["avg_duration"])
        throughput_change = f"{fixed['count']} -> {adaptive['count']}"

        print(f"{letter:<10}{name:<15}{wait_change:<12}{travel_change:<12}{throughput_change:<15}")

    print()


if __name__ == "__main__":
    main()
