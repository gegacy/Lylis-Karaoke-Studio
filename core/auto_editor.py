"""Deterministic one-click editing helpers used by the Auto Edit command."""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

from core.lrc_engine import LrcEngine, LyricLine, WordSyllable


def _plain_lyrics(raw_text: str) -> List[str]:
    """Return usable lyric lines from plain text while ignoring metadata."""
    result = []
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and "]" in line:
            # A timestamped line is handled by LrcEngine instead.
            continue
        result.append(line)
    return result


def _timed_plain_lines(raw_text: str, duration: float) -> List[LyricLine]:
    texts = _plain_lyrics(raw_text)
    if not texts:
        return []
    usable_duration = max(float(duration), len(texts) * 1.5)
    step = usable_duration / len(texts)
    lines: List[LyricLine] = []
    for index, text in enumerate(texts):
        start = index * step
        end = min(usable_duration, start + step * 0.94)
        words = text.split()
        word_step = max(0.05, (end - start) / max(1, len(words)))
        syllables = [
            WordSyllable(word + (" " if pos < len(words) - 1 else ""), start + pos * word_step,
                         start + (pos + 1) * word_step)
            for pos, word in enumerate(words)
        ]
        lines.append(LyricLine(start, end, syllables, raw_text=text))
    return lines


def detect_beat_times(peaks: Sequence[float], duration: float) -> List[float]:
    """Find strong, separated waveform peaks suitable for lyric snapping."""
    if not peaks or duration <= 0 or len(peaks) < 3:
        return []
    threshold = max(0.55, sum(float(value) for value in peaks) / len(peaks) * 1.35)
    min_gap = max(0.18, min(0.5, duration / 24.0))
    beats: List[float] = []
    for index in range(1, len(peaks) - 1):
        value = float(peaks[index])
        if value < threshold or value < float(peaks[index - 1]) or value < float(peaks[index + 1]):
            continue
        timestamp = index / (len(peaks) - 1) * duration
        if not beats or timestamp - beats[-1] >= min_gap:
            beats.append(timestamp)
        elif beats and value > float(peaks[max(0, min(len(peaks) - 1, int(round(beats[-1] / max(0.001, duration) * (len(peaks) - 1)))))]):
            beats[-1] = timestamp
    return beats


def snap_lines_to_beats(lines: Iterable[LyricLine], beats: Sequence[float], tolerance: float = 0.18) -> List[LyricLine]:
    """Snap starts to nearby beats while preserving lyric order and durations."""
    result = list(lines)
    if not result or not beats:
        return result
    previous = -0.01
    for line in result:
        nearest = min(beats, key=lambda beat: abs(float(beat) - line.line_start))
        if abs(nearest - line.line_start) <= tolerance and nearest > previous + 0.05:
            shift = nearest - line.line_start
            line.line_start = nearest
            line.line_end = max(nearest + 0.1, line.line_end + shift)
            for word in line.words:
                word.start_time += shift
                word.end_time += shift
        previous = line.line_start
    for index in range(len(result) - 1):
        target_end = min(result[index].line_end, result[index + 1].line_start)
        result[index].line_end = max(result[index].line_start + 0.1, target_end)
        if result[index].words:
            result[index].words[-1].end_time = result[index].line_end
    return result


def prepare_auto_edit(
    raw_text: str,
    duration: float,
    waveform_peaks: Sequence[float] | None = None,
) -> Tuple[List[LyricLine], str]:
    """Parse or time plain lyrics, normalize them, and optionally beat-snap them."""
    lines = LrcEngine.parse(raw_text)
    if not lines:
        lines = _timed_plain_lines(raw_text, duration)
    if not lines:
        return [], ""

    lines.sort(key=lambda line: line.line_start)
    for index, line in enumerate(lines):
        if index + 1 < len(lines):
            line.line_end = min(line.line_end, lines[index + 1].line_start)
        line.line_end = max(line.line_start + 0.1, line.line_end)

    beats = detect_beat_times(waveform_peaks or [], duration)
    lines = snap_lines_to_beats(lines, beats)
    return lines, LrcEngine.export_lrc(lines)
