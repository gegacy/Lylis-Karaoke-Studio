"""
Lylis Karaoke Studio - AI & Acoustic Voice Gender Detector (Nam & Nữ)
Analyzes Fundamental Frequency (F0), Spectral Centroid, and Harmonic Pitch to detect Male vs Female vocals.
"""
import numpy as np
from typing import List, Dict, Tuple
from core.lrc_engine import LyricLine

class VoiceGenderDetector:
    @staticmethod
    def estimate_f0(audio_chunk: np.ndarray, sample_rate: int) -> float:
        """
        Estimates the fundamental frequency (F0 in Hz) using autocorrelation.
        Human voice range: 70 Hz to 450 Hz.
        """
        if len(audio_chunk) < sample_rate * 0.05:  # Need at least 50ms
            return 0.0

        # Remove DC offset & apply Hanning window
        chunk = audio_chunk - np.mean(audio_chunk)
        window = np.hanning(len(chunk))
        windowed = chunk * window

        # Autocorrelation via FFT
        n = len(windowed)
        n_fft = 2 ** int(np.ceil(np.log2(2 * n - 1)))
        fft_data = np.fft.rfft(windowed, n_fft)
        corr = np.fft.irfft(fft_data * np.conj(fft_data))
        corr = corr[:n]

        # Normalized autocorrelation
        if corr[0] <= 0:
            return 0.0
        norm_corr = corr / corr[0]

        # Pitch search range: 75 Hz (min pitch) to 420 Hz (max pitch)
        min_lag = int(sample_rate / 420.0)
        max_lag = int(sample_rate / 75.0)

        if max_lag >= len(norm_corr):
            max_lag = len(norm_corr) - 1
        if min_lag >= max_lag:
            return 0.0

        # Find peak in the candidate lag range
        search_region = norm_corr[min_lag:max_lag]
        if len(search_region) == 0:
            return 0.0

        peak_idx = np.argmax(search_region)
        peak_val = search_region[peak_idx]

        # Voiced threshold
        if peak_val > 0.35:
            lag = min_lag + peak_idx
            # Parabolic interpolation for sub-sample precision
            if 0 < peak_idx < len(search_region) - 1:
                alpha = search_region[peak_idx - 1]
                beta = search_region[peak_idx]
                gamma = search_region[peak_idx + 1]
                delta = 0.5 * (alpha - gamma) / (alpha - 2 * beta + gamma + 1e-9)
                lag += delta
            return float(sample_rate / lag)
        return 0.0

    @staticmethod
    def compute_spectral_centroid(audio_chunk: np.ndarray, sample_rate: int) -> float:
        """Computes the brightness / spectral centroid of the audio chunk."""
        if len(audio_chunk) < 512:
            return 0.0
        fft_vals = np.abs(np.fft.rfft(audio_chunk * np.hanning(len(audio_chunk))))
        freqs = np.fft.rfftfreq(len(audio_chunk), 1.0 / sample_rate)
        sum_fft = np.sum(fft_vals)
        if sum_fft == 0:
            return 0.0
        return float(np.sum(freqs * fft_vals) / sum_fft)

    @classmethod
    def detect_line_gender(
        cls, 
        raw_samples: np.ndarray, 
        sample_rate: int, 
        start_sec: float, 
        end_sec: float,
        text_hint: str = ""
    ) -> Tuple[str, float]:
        """
        Classifies voice gender for a specific time range.
        Returns: ("male" | "female" | "both", confidence [0.0 - 1.0])
        """
        # 1. Check explicit text hints first (e.g. '(Nam)', '(Nữ)', '(Song ca)', 'Anh', 'Em')
        text_lower = text_hint.lower().strip()
        if "(nam)" in text_lower or "[nam]" in text_lower or text_lower.startswith("nam:"):
            return "male", 0.95
        if "(nữ)" in text_lower or "[nữ]" in text_lower or text_lower.startswith("nữ:") or "(nu)" in text_lower:
            return "female", 0.95
        if "(song ca)" in text_lower or "[song ca]" in text_lower or "(cả hai)" in text_lower:
            return "both", 0.95

        # 2. Extract audio samples for the line
        if raw_samples is None or sample_rate <= 0 or len(raw_samples) == 0:
            # Fallback to linguistic heuristics
            if text_lower.startswith("anh ") or " chàng " in text_lower:
                return "male", 0.75
            elif text_lower.startswith("em ") or " nàng " in text_lower:
                return "female", 0.75
            return "both", 0.5

        start_idx = max(0, int(start_sec * sample_rate))
        end_idx = min(len(raw_samples), int(end_sec * sample_rate))
        
        if end_idx <= start_idx + 1024:
            return "both", 0.5

        chunk = raw_samples[start_idx:end_idx]
        
        # Frame analysis (100ms window, 50ms hop)
        frame_len = int(sample_rate * 0.1)
        hop_len = int(sample_rate * 0.05)
        
        pitches = []
        centroids = []
        
        for i in range(0, len(chunk) - frame_len, hop_len):
            frame = chunk[i : i + frame_len]
            rms = np.sqrt(np.mean(frame ** 2))
            if rms > 0.01:  # Non-silent frame
                f0 = cls.estimate_f0(frame, sample_rate)
                if 80.0 <= f0 <= 400.0:
                    pitches.append(f0)
                    centroids.append(cls.compute_spectral_centroid(frame, sample_rate))

        if len(pitches) == 0:
            # Fallback based on text heuristics
            if text_lower.startswith("anh ") or " chàng " in text_lower:
                return "male", 0.7
            elif text_lower.startswith("em ") or " nàng " in text_lower:
                return "female", 0.7
            return "both", 0.5

        median_f0 = float(np.median(pitches))
        median_centroid = float(np.median(centroids)) if centroids else 1800.0
        
        # Classification thresholds:
        # Male pitch: 85 - 165 Hz (median < 168 Hz)
        # Female pitch: 170 - 320 Hz (median >= 168 Hz)
        if median_f0 < 165.0:
            conf = min(0.98, max(0.65, (170.0 - median_f0) / 70.0 + 0.5))
            return "male", conf
        elif median_f0 >= 175.0:
            conf = min(0.98, max(0.65, (median_f0 - 170.0) / 90.0 + 0.5))
            return "female", conf
        else:
            # Boundary range (165 - 175 Hz): use spectral centroid
            if median_centroid > 2200.0:
                return "female", 0.65
            else:
                return "male", 0.65

    @classmethod
    def detect_all_lines(
        cls, 
        lines: List[LyricLine], 
        raw_samples: np.ndarray, 
        sample_rate: int
    ) -> List[Dict]:
        """
        Analyzes and detects voice gender for all lyric lines.
        Returns a list of dicts: [{'line_idx': int, 'singer': str, 'confidence': float, 'text': str}]
        """
        results = []
        for idx, line in enumerate(lines):
            singer, conf = cls.detect_line_gender(
                raw_samples,
                sample_rate,
                line.line_start,
                line.line_end,
                line.full_text
            )
            line.singer = singer
            results.append({
                'line_idx': idx,
                'singer': singer,
                'confidence': conf,
                'text': line.full_text
            })
        return results
