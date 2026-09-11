# AI-Traffic — Data Contracts

**Status:** Locked as of [fill in date] — all 4 team members have reviewed and agreed.
**Change protocol:** If any field needs to change, post in the team group chat *before* changing code. Do not silently modify these shapes — every downstream module depends on them exactly as written.

This document defines the three JSON interfaces that connect the four project modules. Each module owner should keep a copy of the relevant contract(s) as a reference (e.g. a `sample_*.json` file) inside their own module folder.

```
Video → [CV Module] → CV→ML Contract → [ML Module] → ML→Backend Contract → [Backend] → Backend→Frontend Contract → [Frontend]
```

---

## 1. CV → ML Contract

**Produced by:** CV Pipeline module (Member 1)
**Consumed by:** ML & Optimization module (Member 2), and the Backend ingest endpoint

```json
{
  "junction_id": "J001",
  "timestamp": "2026-09-09T15:00:00",
  "north": {
    "vehicles": 42,
    "cars": 30,
    "buses": 2,
    "trucks": 4,
    "motorcycles": 6,
    "average_speed": 11.5,
    "queue_length": 82
  },
  "south": {
    "vehicles": 31,
    "average_speed": 14.2,
    "queue_length": 57
  },
  "east": {
    "vehicles": 12,
    "average_speed": 24.1,
    "queue_length": 18
  },
  "west": {
    "vehicles": 17,
    "average_speed": 21.3,
    "queue_length": 23
  }
}
```

**Field notes:**
- `junction_id` — fixed as `"J001"` for this single-intersection MVP.
- `timestamp` — ISO 8601 format, one reading emitted per analysis interval.
- Each approach (`north`/`south`/`east`/`west`) must include at minimum `vehicles`, `average_speed`, `queue_length`. Per-class breakdown (`cars`, `buses`, `trucks`, `motorcycles`) is included where available but not strictly required by downstream consumers.
- `average_speed` is approximate (per spec, exact speed is not required).
- `queue_length` unit should be documented by the CV team once finalized (e.g. meters, or vehicle count) — note it here once decided: **[TBD by M1]**.

---

## 2. ML → Backend Contract

**Produced by:** ML & Optimization module (Member 2), after prediction + optimization + safety layer
**Consumed by:** Backend module (Member 3)

```json
{
  "junction_id": "J001",
  "action": "EXTEND_GREEN",
  "phase": "NS_GREEN",
  "duration": 8,
  "reason": "High north-south traffic demand"
}
```

**Field notes:**
- `action` — one of `"KEEP_PHASE"`, `"EXTEND_GREEN"`, `"SWITCH_PHASE"`. This value is always the *safety-layer-approved* action, never the raw model output.
- `phase` — the current/target signal phase, e.g. `"NS_GREEN"`, `"EW_GREEN"`.
- `duration` — seconds, only meaningful for `EXTEND_GREEN` (can be `0` or omitted for other actions — decide and note here: **[TBD by M2]**).
- `reason` — short human-readable string, shown directly on the dashboard's AI Recommendation panel. Keep it concise (this is user-facing text).

---

## 3. Backend → Frontend Contract

**Produced by:** Backend module (Member 3), pushed live via WebSocket
**Consumed by:** Frontend Dashboard module (Member 4)

```json
{
  "traffic": {
    "vehicles": 102,
    "queue_length": 180,
    "average_speed": 13.2,
    "congestion": "HIGH"
  },
  "signal": {
    "phase": "NS_GREEN",
    "remaining_seconds": 27
  },
  "ai": {
    "action": "EXTEND_GREEN",
    "duration": 8,
    "reason": "High traffic demand"
  }
}
```

**Field notes:**
- `traffic.congestion` — one of `"LOW"`, `"MEDIUM"`, `"HIGH"`, computed by the congestion-scoring formula (Section 7 of the spec).
- `traffic.vehicles` / `queue_length` / `average_speed` — aggregated across all four approaches (or per-approach, if the dashboard needs to show a per-lane breakdown — decide and note here: **[TBD by M3 + M4]**).
- `signal.remaining_seconds` — countdown shown on the dashboard's signal status panel.
- `ai` object — directly mirrors the relevant fields from the ML → Backend contract above, passed through by the backend.

---

## Sign-off checklist

Each member should confirm they can produce/consume their relevant contract(s) exactly as written above.

- [ ] M1 (CV) — confirms all CV→ML fields can be computed by the CV pipeline
- [ ] M2 (ML) — confirms CV→ML fields are sufficient as prediction/optimizer input, and ML→Backend fields are sufficient output
- [ ] M3 (Backend) — confirms ML→Backend and Backend→Frontend contracts are implementable in the API/DB schema
- [ ] M4 (Frontend) — confirms Backend→Frontend fields are sufficient to build all dashboard panels

Any `[TBD]` items above should be resolved and this document updated before Sprint 1 tasks begin in earnest.
