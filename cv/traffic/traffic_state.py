from datetime import datetime, timezone


def build_traffic_state(junction_id, north, south, east, west, timestamp=None):
    """
    Builds the CV → ML traffic-state contract.

    Each approach must contain at least:
        vehicles, average_speed, queue_length
    Per-class vehicle counts are optional.
    """
    required_fields = {"vehicles", "average_speed", "queue_length"}

    for name, block in [
        ("north", north),
        ("south", south),
        ("east", east),
        ("west", west)
    ]:
        if block is None:
            raise ValueError(f"'{name}' direction block cannot be None")

        missing = required_fields - set(block.keys())

        if missing:
            raise ValueError(
                f"'{name}' direction block missing required fields: "
                f"{sorted(missing)}"
            )

    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    return {
        "junction_id": junction_id,
        "timestamp": timestamp,
        "north": north,
        "south": south,
        "east": east,
        "west": west
    }