"""
Lylis Karaoke Studio - Faster-Whisper AI Audio Transcription
Generates word-level timestamps (word, start_time, end_time)
"""
import os
import math
import sys
from typing import List, Dict, Any

class FasterWhisperService:
    _model = None
    _model_error = ""

    @classmethod
    def get_model(cls, model_size: str = "base"):
        if cls._model is None:
            try:
                # Windows without Developer Mode cannot create Hugging Face
                # cache symlinks; disable only the noisy warning.
                os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
                from faster_whisper import WhisperModel
                # CPU float32 / int8 execution for universal local compatibility
                cls._model = WhisperModel(model_size, device="cpu", compute_type="int8")
            except Exception as e:
                cls._model_error = str(e)
                print(f"[FasterWhisper] Model loading notice: {e}", file=sys.stderr)
                return None
        return cls._model

    @classmethod
    def transcribe(cls, audio_path: str, language: str = "vi") -> List[Dict[str, Any]]:
        """
        Transcribes audio file into structured lines with word timestamps.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        model = cls.get_model()
        if model is None:
            detail = f": {cls._model_error}" if cls._model_error else ""
            raise RuntimeError(f"faster-whisper model could not be loaded{detail}")
        try:
                segments, info = model.transcribe(
                    audio_path,
                    language=language,
                    word_timestamps=True,
                    beam_size=5
                )

                lines = []
                for seg in segments:
                    words = []
                    if hasattr(seg, 'words') and seg.words:
                        for w in seg.words:
                            word_start = _number(w.start, seg.start)
                            word_end = _number(w.end, max(word_start + 0.02, seg.end))
                            words.append({
                                'word': w.word.strip(),
                                'start': word_start,
                                'end': max(word_start + 0.02, word_end)
                            })
                    else:
                        # Split words evenly
                        seg_words = seg.text.strip().split()
                        dur = max(0.1, (seg.end - seg.start) / max(1, len(seg_words)))
                        for idx, w in enumerate(seg_words):
                            words.append({
                                'word': w,
                                'start': float(seg.start + idx * dur),
                                'end': float(seg.start + (idx + 1) * dur)
                            })

                    lines.append({
                        'text': seg.text.strip(),
                        'start': _number(seg.start, 0.0),
                        'end': max(_number(seg.start, 0.0) + 0.05, _number(seg.end, _number(seg.start, 0.0) + 0.05)),
                        'words': words
                    })
                return lines
        except Exception as e:
            raise RuntimeError(f"faster-whisper transcription failed: {e}") from e


def _number(value, fallback):
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else float(fallback)
    except (TypeError, ValueError):
        return float(fallback)
