"""
Lylis Karaoke Studio - Cache & Temporary File Management Engine
Features:
- Automated Cache Cleanup on Startup & Shutdown
- Temporary Audio Stems & Video Render Artifacts Removal
- Memory & Disk Space Reclaim Tracker
- Manual 1-Click Cache Purge
"""
import os
import shutil
import tempfile
import time
from typing import Dict, Any, List

class CacheManager:
    CACHE_DIRS = [
        os.path.join(tempfile.gettempdir(), "lylis_audio"),
        os.path.join(tempfile.gettempdir(), "lylis_render"),
        os.path.join(tempfile.gettempdir(), "lylis_whisper"),
    ]

    @classmethod
    def get_cache_paths(cls) -> List[str]:
        """Returns all directories and temp file locations used by the application."""
        paths = list(cls.CACHE_DIRS)
        return [p for p in paths if os.path.exists(p)]

    @classmethod
    def get_cache_size(cls) -> int:
        """Calculates total bytes occupied by temporary cache files."""
        total_bytes = 0
        for directory in cls.CACHE_DIRS:
            if os.path.exists(directory):
                for root, _, files in os.walk(directory):
                    for f in files:
                        fp = os.path.join(root, f)
                        try:
                            total_bytes += os.path.getsize(fp)
                        except OSError:
                            pass
        # Also check temp files in system temp matching lylis prefix
        temp_dir = tempfile.gettempdir()
        try:
            for f in os.listdir(temp_dir):
                if f.startswith(("lylis_", "tmp_audio_", "tmp_stem_")):
                    fp = os.path.join(temp_dir, f)
                    try:
                        total_bytes += os.path.getsize(fp)
                    except OSError:
                        pass
        except OSError:
            pass
        return total_bytes

    @classmethod
    def clear_cache(cls) -> Dict[str, Any]:
        """
        Removes temporary cached audio, video render clips, and temp chunks.
        Returns a summary dictionary with files removed and freed bytes.
        """
        initial_size = cls.get_cache_size()
        removed_count = 0

        for directory in cls.CACHE_DIRS:
            if os.path.exists(directory):
                try:
                    for filename in os.listdir(directory):
                        file_path = os.path.join(directory, filename)
                        try:
                            if os.path.isfile(file_path) or os.path.islink(file_path):
                                os.unlink(file_path)
                                removed_count += 1
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                                removed_count += 1
                        except Exception:
                            pass
                except Exception:
                    pass

        # Clean system temp folder matching application prefix
        temp_dir = tempfile.gettempdir()
        try:
            for f in os.listdir(temp_dir):
                if f.startswith(("lylis_", "tmp_audio_", "tmp_stem_")):
                    fp = os.path.join(temp_dir, f)
                    try:
                        if os.path.isfile(fp):
                            os.remove(fp)
                            removed_count += 1
                        elif os.path.isdir(fp):
                            shutil.rmtree(fp)
                            removed_count += 1
                    except Exception:
                        pass
        except OSError:
            pass

        final_size = cls.get_cache_size()
        freed_bytes = max(0, initial_size - final_size)
        return {
            "files_removed": removed_count,
            "bytes_freed": freed_bytes,
            "mb_freed": round(freed_bytes / (1024 * 1024), 2)
        }

    @classmethod
    def auto_clean_on_start(cls, max_age_hours: float = 6.0):
        """Removes stale cache files older than max_age_hours on startup."""
        now = time.time()
        max_age_secs = max_age_hours * 3600

        for directory in cls.CACHE_DIRS:
            if os.path.exists(directory):
                try:
                    for filename in os.listdir(directory):
                        file_path = os.path.join(directory, filename)
                        try:
                            if os.path.isfile(file_path):
                                if now - os.path.getmtime(file_path) > max_age_secs:
                                    os.remove(file_path)
                        except Exception:
                            pass
                except Exception:
                    pass
