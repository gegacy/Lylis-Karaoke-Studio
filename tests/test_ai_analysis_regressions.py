import os

import pytest

from core.ai.lyric_analysis_service import LyricAnalysisService


def test_analysis_rejects_missing_and_empty_sources(tmp_path):
    with pytest.raises(FileNotFoundError):
        LyricAnalysisService.transcribe(str(tmp_path / "missing.wav"))
    empty = tmp_path / "empty.wav"
    empty.write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        LyricAnalysisService.transcribe(str(empty))


def test_analysis_normalizes_provider_output_without_invalid_times(tmp_path, monkeypatch):
    audio = tmp_path / "Nhạc (demo).wav"
    audio.write_bytes(b"audio")

    class FakeProvider:
        @staticmethod
        def transcribe(path, language="vi"):
            assert os.path.samefile(path, audio)
            return [{
                "text": "Xin chào",
                "start": None,
                "end": None,
                "words": [{"word": "Xin", "start": None, "end": None}],
            }]

    monkeypatch.setattr("core.ai.faster_whisper_service.FasterWhisperService", FakeProvider)
    result = LyricAnalysisService.transcribe(str(audio))
    assert len(result["lines"]) == 1
    line = result["lines"][0]
    assert line["text"] == "Xin chào"
    assert line["end"] > line["start"]
    assert line["words"][0]["end"] > line["words"][0]["start"]
