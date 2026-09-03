"""
Lylis Karaoke Studio - High-Performance Audio Engine
Playback Controller, Waveform Generation, Beat Detection, and Real-Time FFT Spectrum Visualizer
"""
import os
import time
import math
import shutil
import subprocess
import tempfile
import numpy as np
import pygame

class AudioEngine:
    def __init__(self):
        # Initialize pygame audio mixer with low latency buffer
        self.mixer_ready = False
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self.mixer_ready = True
        except Exception as e:
            print(f"[AudioEngine] Mixer init warning: {e}")

        self.current_file = None
        self.source_file = None
        self.audio_settings = {"pitch_semitones": 0, "speed": 1.0, "vocal_cut": False}
        self._effects_temp_dir = None
        self.duration = 0.0
        self.is_playing = False
        self.start_wall_time = 0.0
        self.pause_offset = 0.0
        self.volume = 1.0
        self.loop = False
        
        # Waveform & FFT Spectrum data
        self.raw_samples = None
        self.sample_rate = 44100
        self.waveform_peaks = []
        self.fft_bands = [0.0] * 42

    def load_audio(self, filepath: str, preserve_source: bool = False) -> bool:
        if not os.path.exists(filepath):
            return False

        try:
            self.stop()
            if self.mixer_ready:
                pygame.mixer.music.load(filepath)
            self.current_file = filepath
            if not preserve_source:
                self.source_file = filepath
                self.audio_settings = {"pitch_semitones": 0, "speed": 1.0, "vocal_cut": False}
            
            # Extract duration and waveform peaks
            self._extract_audio_features(filepath)
            self.pause_offset = 0.0
            return True
        except Exception as e:
            print(f"[AudioEngine] Failed to load audio: {e}")
            return False

    def apply_audio_settings(self, pitch_semitones: int = 0, speed: float = 1.0, vocal_cut: bool = False) -> bool:
        """Create a temporary preview mix using FFmpeg and load it for playback."""
        if not self.source_file or not os.path.exists(self.source_file):
            return False
        pitch_semitones = max(-6, min(6, int(pitch_semitones)))
        speed = max(0.5, min(1.5, float(speed)))
        settings = {
            "pitch_semitones": pitch_semitones,
            "speed": speed,
            "vocal_cut": bool(vocal_cut),
        }
        if settings == self.audio_settings:
            return True
        if settings == {"pitch_semitones": 0, "speed": 1.0, "vocal_cut": False}:
            self.audio_settings = settings
            return self.load_audio(self.source_file, preserve_source=True)

        try:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            if self._effects_temp_dir:
                shutil.rmtree(self._effects_temp_dir, ignore_errors=True)
            self._effects_temp_dir = tempfile.mkdtemp(prefix="lylis_audio_")
            output_path = os.path.join(self._effects_temp_dir, "preview.wav")
            filters = []
            if vocal_cut:
                filters.append("pan=stereo|c0=c0-c1|c1=c1-c0")
            if pitch_semitones:
                factor = 2.0 ** (pitch_semitones / 12.0)
                filters.append(
                    f"asetrate={int(self.sample_rate)}*{factor:.8f},"
                    f"aresample={int(self.sample_rate)},atempo={1.0/factor:.8f}"
                )
            if abs(speed - 1.0) > 1e-6:
                filters.append(f"atempo={speed:.6f}")
            cmd = [ffmpeg, "-y", "-i", self.source_file]
            if filters:
                cmd += ["-af", ",".join(filters)]
            cmd += ["-vn", "-acodec", "pcm_s16le", output_path]
            sub_kwargs = {}
            if os.name == "nt":
                sub_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **sub_kwargs)
            if result.returncode != 0 or not os.path.exists(output_path):
                return False
            self.audio_settings = settings
            return self.load_audio(output_path, preserve_source=True)
        except Exception as exc:
            print(f"[AudioEngine] Audio effect error: {exc}")
            return False

    def _extract_audio_features(self, filepath: str):
        """Extracts audio duration, 1000-point waveform peaks, and sample buffer."""
        try:
            import soundfile as sf
            data, sr = sf.read(filepath)
            self.sample_rate = sr
            
            # Convert to mono if stereo
            if len(data.shape) > 1:
                mono = np.mean(data, axis=1)
            else:
                mono = data
                
            self.raw_samples = mono
            self.duration = float(len(mono)) / float(sr)
            
            # Downsample to 1000 normalized peaks
            num_peaks = 1000
            chunk_size = max(1, len(mono) // num_peaks)
            peaks = []
            for i in range(num_peaks):
                chunk = mono[i * chunk_size : (i + 1) * chunk_size]
                if len(chunk) > 0:
                    peaks.append(float(np.max(np.abs(chunk))))
                else:
                    peaks.append(0.0)
                    
            max_val = max(peaks) if peaks and max(peaks) > 0 else 1.0
            self.waveform_peaks = [p / max_val for p in peaks]
        except Exception:
            # Fallback estimation
            try:
                sound = pygame.mixer.Sound(filepath)
                self.duration = sound.get_length()
            except Exception:
                self.duration = 45.0
            # Synthetic waveform
            self.waveform_peaks = [abs(math.sin(i * 0.1) * math.cos(i * 0.04)) for i in range(1000)]

    def play(self):
        if not self.current_file:
            return

        try:
            if not self.is_playing:
                if self.duration > 0 and self.pause_offset >= self.duration:
                    self.pause_offset = 0.0
                if self.mixer_ready:
                    pygame.mixer.music.play(start=self.pause_offset)
                self.start_wall_time = time.time()
                self.is_playing = True
        except Exception as e:
            print(f"[AudioEngine] Play error: {e}")

    def pause(self):
        if self.is_playing:
            elapsed = time.time() - self.start_wall_time
            self.pause_offset = min(self.duration, self.pause_offset + elapsed) if self.duration > 0 else (self.pause_offset + elapsed)
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            self.is_playing = False

    def stop(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.is_playing = False
        self.pause_offset = 0.0

    def seek(self, target_seconds: float):
        target_seconds = max(0.0, min(self.duration, target_seconds)) if self.duration > 0 else max(0.0, target_seconds)
        was_playing = self.is_playing
        self.pause_offset = target_seconds
        
        if was_playing:
            try:
                pygame.mixer.music.play(start=target_seconds)
                self.start_wall_time = time.time()
            except Exception as e:
                print(f"[AudioEngine] Seek play error: {e}")
        else:
            self.start_wall_time = time.time()

    def set_volume(self, vol: float):
        self.volume = max(0.0, min(1.0, vol))
        try:
            pygame.mixer.music.set_volume(self.volume)
        except Exception:
            pass

    def close(self):
        self.unload()
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
        except Exception:
            pass

    def unload(self):
        """Release the active track and reset playback-derived state."""
        self.stop()
        self.current_file = None
        self.source_file = None
        self.duration = 0.0
        self.raw_samples = None
        self.waveform_peaks = []
        self.fft_bands = [0.0] * 42
        self.audio_settings = {"pitch_semitones": 0, "speed": 1.0, "vocal_cut": False}
        if self._effects_temp_dir:
            shutil.rmtree(self._effects_temp_dir, ignore_errors=True)
            self._effects_temp_dir = None

    def get_current_time(self) -> float:
        if self.is_playing:
            elapsed = time.time() - self.start_wall_time
            curr = self.pause_offset + elapsed
            if self.duration > 0 and curr >= self.duration:
                if self.loop:
                    self.seek(0.0)
                    return 0.0
                else:
                    try:
                        pygame.mixer.music.stop()
                    except Exception:
                        pass
                    self.is_playing = False
                    self.pause_offset = self.duration
                    return self.duration
            return curr
        return self.pause_offset

    def get_spectrum_bands(self, num_bands: int = 42) -> list:
        """Calculates dynamic FFT frequency bins for real-time visualizer."""
        curr_t = self.get_current_time()
        
        if self.raw_samples is not None and self.is_playing:
            center_idx = int(curr_t * self.sample_rate)
            win_size = 1024
            half = win_size // 2
            start = max(0, center_idx - half)
            end = min(len(self.raw_samples), center_idx + half)
            
            chunk = self.raw_samples[start:end]
            if len(chunk) == win_size:
                # Apply Hanning window & FFT
                windowed = chunk * np.hanning(win_size)
                fft_vals = np.abs(np.fft.rfft(windowed))[:num_bands]
                # Log compression
                bands = [float(np.log1p(v * 20.0)) for v in fft_vals]
                max_b = max(bands) if bands and max(bands) > 0 else 1.0
                return [min(1.0, b / max_b) for b in bands]
                
        # Aesthetic procedural fallback
        bands = []
        for i in range(num_bands):
            t = curr_t * 6.0 + i * 0.35
            h_val = abs(math.sin(t) * math.cos(t * 0.7)) * 0.8 + 0.2
            bands.append(h_val if self.is_playing else 0.08)
        return bands
