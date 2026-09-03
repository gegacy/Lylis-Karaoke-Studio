"""Audio-to-timed-lyrics adapter used by the desktop editor.

The UI only consumes this normalized result; provider-specific output stays here.
"""
import os
import math
import logging
from typing import Any, Dict, List


class LyricAnalysisService:
    @staticmethod
    def transcribe(audio_path: str, language: str = "auto", progress=None) -> Dict[str, Any]:
        def stage(name):
            logging.getLogger("lylis.ai_lyrics").info("[AI Lyrics] %s", name)
            if progress:
                progress(name)

        stage("job created")
        if not audio_path or not os.path.isfile(audio_path):
            raise FileNotFoundError("The selected audio file is missing.")
        try:
            if os.path.getsize(audio_path) <= 0:
                raise ValueError("The selected audio file is empty.")
        except OSError as exc:
            raise OSError("The selected audio file cannot be read.") from exc
        stage("source resolved")
        try:
            from core.ai.faster_whisper_service import FasterWhisperService
            provider_language = None if language in ("", "auto") else language
            stage("preparing audio")
            raw_lines = FasterWhisperService.transcribe(audio_path, language=provider_language or "vi")
            stage("transcription response received")
        except ImportError as exc:
            raise RuntimeError("Install optional 'faster-whisper' to analyze uploaded audio.") from exc
        except Exception as exc:
            raise RuntimeError(f"Audio transcription failed: {exc}") from exc

        lines: List[Dict[str, Any]] = []
        for index, raw in enumerate(raw_lines or []):
            text = str(raw.get("text") or "").strip()
            if not text:
                continue
            start = _finite(raw.get("start"), 0.0)
            end = max(start + 0.05, _finite(raw.get("end"), start + 0.05))
            words = []
            for word_index, item in enumerate(raw.get("words") or []):
                word_text = str(item.get("word") or item.get("text") or "").strip()
                if not word_text:
                    continue
                word_start = max(start, _finite(item.get("start"), start))
                word_end = min(end, max(word_start + 0.02, _finite(item.get("end"), word_start + 0.02)))
                words.append({"id": f"word_{index}_{word_index}", "text": word_text, "start": word_start, "end": word_end})
            lines.append({"id": f"line_{index}", "text": text, "start": start, "end": end, "words": words})
        stage(f"normalized {len(lines)} lines")
        return {"language": language if language not in ("", "auto") else "unknown", "lines": lines}


def _finite(value, default):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default
    return value if math.isfinite(value) else default
