"""Shared timing helpers for preview and offline media rendering."""
import math


def looping_frame_index(
    current_time: float,
    fps: float,
    duration: float = 0.0,
    frame_count: float = 0.0,
) -> int:
    """Return a stable source-frame index, looping finite background videos."""
    safe_fps = float(fps) if math.isfinite(float(fps)) and float(fps) > 0 else 30.0
    safe_time = max(0.0, float(current_time))
    safe_duration = float(duration)
    if math.isfinite(safe_duration) and safe_duration > 0:
        safe_time %= safe_duration

    index = max(0, int(safe_time * safe_fps))
    safe_count = float(frame_count)
    if math.isfinite(safe_count) and safe_count > 0:
        index %= max(1, int(safe_count))
    return index
