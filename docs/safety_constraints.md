# AI-Traffic — Signal Safety Constraints

**Status:** Locked as of [fill in date]. These values are used consistently in TWO places:
1. The SUMO fixed-time baseline signal (`intersection.net.xml` / `plain.tll.xml`)
2. The AI safety-constraint layer code (Member 2, Sprint 2 task: "Implement safety constraint layer")

Using the same numbers in both places ensures the fixed-time baseline and the AI-controlled signal are being held to the same safety standard, which is what makes the fixed-vs-adaptive comparison fair and meaningful.

---

## Values

| Constraint | Value | Reasoning |
|---|---|---|
| **Minimum green time** | 10 seconds | Shortest allowable green — anything less doesn't give queued vehicles a fair chance to move through, regardless of what the AI predicts. |
| **Maximum green time** | 45 seconds | Longest allowable green (including any AI extension) — prevents one direction from monopolizing the signal even under high predicted demand. |
| **Baseline fixed green duration** | 30 seconds | The actual green duration used in the FIXED-TIME baseline signal for each direction (a specific, deliberate value within the 10–45s allowed range, not just SUMO's auto-generated default). |
| **Yellow clearance** | 3 seconds | Time for vehicles already committed to entering the intersection to clear it before cross-traffic gets a green light. |
| **All-red clearance** | 2 seconds | Brief window where ALL directions are red, after yellow ends and before the next direction turns green — extra safety margin for any vehicle/pedestrian still in the intersection. |
| **Minimum red time** | 15 seconds | Derived as (other direction's green 30s minus overlap) — no direction should be red for less than this, ensuring a fair minimum cycle structure. |
| **Maximum green extension (AI only)** | +10 seconds | The AI optimizer may extend a green phase by at most 10 seconds beyond its current duration, and never beyond the 45s maximum green cap above. |
| **Fairness rule** | No approach skipped more than 1 full cycle | If an approach hasn't received a green phase in one full cycle, it must be served next, regardless of AI recommendation, to prevent starvation. |

---

## How this applies to SUMO (fixed-time baseline)

A single cycle should look like:

```
NS Green (30s) → NS Yellow (3s) → All-Red (2s) → EW Green (30s) → EW Yellow (3s) → All-Red (2s) → [repeat]
```

Total cycle length: 30 + 3 + 2 + 30 + 3 + 2 = **70 seconds**.

## How this applies to the AI safety layer (built later, Sprint 2)

When the optimizer outputs a decision, the safety layer clips/validates it against these same numbers before it's allowed to execute:
- `EXTEND_GREEN` requests are capped at +10 seconds, and the resulting total green can never exceed 45 seconds.
- `SWITCH_PHASE` cannot occur before the minimum green (10s) has elapsed on the current phase.
- Yellow (3s) and all-red (2s) clearance always play out in full regardless of what the AI wants — these are non-negotiable, always-enforced transitions.
- The fairness rule overrides any AI recommendation that would starve an approach beyond 1 full cycle.
