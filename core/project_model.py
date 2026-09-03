"""
Lylis Karaoke Studio - Project Model & Persistence
"""
import json
import uuid
import copy
import math
from typing import Dict, Any, Optional

class ProjectModel:
    def __init__(self, title: str = "Chiếc nón ba tầm", aspect_ratio: str = "16:9", duration: float = 42.0):
        self.id = str(uuid.uuid4())
        self.title = title
        self.aspect_ratio = aspect_ratio  # "9:16" | "16:9" | "1:1"
        self.duration = duration
        self.fps = 30
        self.width = 1920
        self.height = 1080
        
        # Style configuration
        self.style = {
            "font_family": "Montserrat",
            "font_size": 32,
            "is_bold": True,
            "is_italic": False,
            "layout_mode": "left_right",  # "left_right" | "center"
            "pos_y_percent": 74,
            "stroke_width": 4,
            "active_color": "#00d2ff",
            "active_color_end": "#145cff",
            "base_color": "#ffffff",
            "stroke_color": "#000000",
            "portrait_focus_y": 25,
            "uppercase_lyrics": False
        }
        
        # Elements toggles
        self.elements = {
            "visualizer": False,
            "visualizer_mode": "Bar Spectrum (Cột sóng đứng)",
            "pointer": True,
            "pointer_icon": "🎤",
            "pointer_icons": {
                "male": "👨",
                "female": "👩",
                "both": "🎤"
            },
            "watermark": False
        }

        self.effects = {
            "brightness": 0,
            "contrast": 0,
            "saturation": 0,
            "blur": 0,
            "particles": False,
            "particle_type": "Golden Sparkles ✨",
            "vignette_percent": 20,
            "enable_glow": True,
            "glow_radius": 8,
            "color_tint": "None (Original)"
        }
        self.transitions = {"start": None, "end": None}
        self.overlay_objects = []
        self.audio_settings = {
            "pitch_semitones": 0,
            "speed": 1.0,
            "vocal_cut": False
        }
        
        # Media assets
        self.bg_path: Optional[str] = None
        self.audio_path: Optional[str] = None
        self.album_audio_paths = []
        self.album_active_track_id: Optional[str] = None
        self.raw_lrc_text: str = ""
        self.language = "vi"
        self.custom_templates = []
        # Normalized imported media and timeline clips. Existing path fields
        # remain for compatibility with the current renderer.
        self.project_version = 2
        self.media_assets = {}
        self.timeline_clips = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "aspect_ratio": self.aspect_ratio,
            "duration": self.duration,
            "fps": self.fps,
            "style": self.style,
            "elements": self.elements,
            "effects": self.effects,
            "transitions": self.transitions,
            "overlay_objects": self.overlay_objects,
            "audio_settings": self.audio_settings,
            "bg_path": self.bg_path,
            "audio_path": self.audio_path,
            "album_audio_paths": copy.deepcopy(self.album_audio_paths),
            "album_active_track_id": self.album_active_track_id,
            "raw_lrc_text": self.raw_lrc_text,
            "language": self.language,
            "custom_templates": copy.deepcopy(self.custom_templates),
            "project_version": self.project_version,
            "media_assets": copy.deepcopy(self.media_assets),
            "timeline_clips": copy.deepcopy(self.timeline_clips),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectModel":
        if not isinstance(data, dict):
            raise ValueError("Project data must be a JSON object.")

        def mapping(value):
            return copy.deepcopy(value) if isinstance(value, dict) else {}

        def sequence(value):
            return copy.deepcopy(value) if isinstance(value, list) else []

        def finite_number(value, default, minimum, maximum, integer=False):
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                parsed = float(default)
            if not math.isfinite(parsed):
                parsed = float(default)
            parsed = max(float(minimum), min(float(maximum), parsed))
            return int(round(parsed)) if integer else parsed

        try:
            duration = float(data.get("duration", 42.0))
        except (TypeError, ValueError):
            duration = 42.0
        if not math.isfinite(duration) or duration <= 0.0:
            duration = 42.0

        aspect_ratio = str(data.get("aspect_ratio", "16:9"))
        try:
            aspect_width, aspect_height = (float(part.strip()) for part in aspect_ratio.split(":", 1))
            if not (0.0 < aspect_width <= 1000.0 and 0.0 < aspect_height <= 1000.0):
                aspect_ratio = "16:9"
        except (TypeError, ValueError):
            aspect_ratio = "16:9"

        p = cls(
            title=str(data.get("title") or "Untitled Project"),
            aspect_ratio=aspect_ratio,
            duration=duration
        )
        p.id = str(data.get("id") or uuid.uuid4())
        try:
            p.fps = max(1, min(240, int(data.get("fps", 30))))
        except (TypeError, ValueError):
            p.fps = 30
        p.style.update(mapping(data.get("style")))
        p.elements.update(mapping(data.get("elements")))
        p.effects.update(mapping(data.get("effects")))
        p.transitions.update(mapping(data.get("transitions")))
        p.overlay_objects = [item for item in sequence(data.get("overlay_objects")) if isinstance(item, dict)]
        p.audio_settings.update(mapping(data.get("audio_settings")))
        p.style["font_size"] = finite_number(p.style.get("font_size"), 32, 8, 300, integer=True)
        p.style["stroke_width"] = finite_number(p.style.get("stroke_width"), 4, 0, 30)
        p.style["portrait_focus_y"] = finite_number(p.style.get("portrait_focus_y"), 25, 0, 100)
        p.style["pos_y_top"] = finite_number(p.style.get("pos_y_top"), 66, 0, 100)
        p.style["pos_y_bottom"] = finite_number(p.style.get("pos_y_bottom"), 78, 0, 100)
        singers = []
        for singer in sequence(p.style.get("custom_singers")):
            if not isinstance(singer, dict):
                continue
            normalized_singer = copy.deepcopy(singer)
            normalized_singer["name"] = str(singer.get("name") or f"Singer {len(singers) + 1}")
            normalized_singer["color"] = str(singer.get("color") or "#f59e0b")
            singers.append(normalized_singer)
        p.style["custom_singers"] = singers
        normalized_tracks = []
        for index, track in enumerate(sequence(p.style.get("album_tracks"))):
            if isinstance(track, dict):
                item = copy.deepcopy(track)
                item['id'] = str(item.get('id') or f'track_{index + 1:04d}')
                item['title'] = str(item.get('title') or item.get('name') or f'Track {index + 1:02d}')
                item['artist'] = str(item.get('artist') or '')
                item['audioSrc'] = str(item.get('audioSrc') or '')
                item['duration'] = finite_number(item.get('duration'), 0, 0, 86400)
                item['lyrics'] = item.get('lyrics') if isinstance(item.get('lyrics'), (list, str)) else []
                item['lyricTiming'] = item.get('lyricTiming') if isinstance(item.get('lyricTiming'), list) else []
            else:
                title = str(track).strip()
                if not title:
                    continue
                item = {'id': f'track_{index + 1:04d}', 'title': title, 'artist': '', 'audioSrc': '', 'cover': '', 'duration': 0, 'lyrics': [], 'lyricTiming': []}
            normalized_tracks.append(item)
        p.style["album_tracks"] = normalized_tracks
        for key in ("brightness", "contrast", "saturation"):
            p.effects[key] = finite_number(p.effects.get(key), 0, -50, 50, integer=True)
        p.effects["blur"] = finite_number(p.effects.get("blur"), 0, 0, 30, integer=True)
        p.effects["vignette_percent"] = finite_number(p.effects.get("vignette_percent"), 20, 0, 100, integer=True)
        p.effects["glow_radius"] = finite_number(p.effects.get("glow_radius"), 8, 0, 30, integer=True)
        p.audio_settings["pitch_semitones"] = finite_number(
            p.audio_settings.get("pitch_semitones"), 0, -6, 6, integer=True
        )
        p.audio_settings["speed"] = finite_number(p.audio_settings.get("speed"), 1.0, 0.5, 1.5)
        p.audio_settings["vocal_cut"] = bool(p.audio_settings.get("vocal_cut", False))
        p.bg_path = data.get("bg_path") if isinstance(data.get("bg_path"), str) else None
        p.audio_path = data.get("audio_path") if isinstance(data.get("audio_path"), str) else None
        p.album_audio_paths = [path for path in sequence(data.get("album_audio_paths")) if isinstance(path, str)]
        active_id = data.get("album_active_track_id")
        p.album_active_track_id = str(active_id) if active_id else None
        p.raw_lrc_text = str(data.get("raw_lrc_text") or "")
        p.language = data.get("language") if data.get("language") in {"vi", "en"} else "vi"
        p.custom_templates = [item for item in sequence(data.get("custom_templates")) if isinstance(item, dict)]
        try:
            p.project_version = max(1, int(data.get("project_version", 1)))
        except (TypeError, ValueError):
            p.project_version = 1
        p.media_assets = {}
        for asset_id, asset in mapping(data.get("media_assets")).items():
            if not isinstance(asset, dict):
                continue
            normalized = copy.deepcopy(asset)
            normalized["id"] = str(normalized.get("id") or asset_id)
            normalized["type"] = str(normalized.get("type") or "image")
            normalized["name"] = str(normalized.get("name") or normalized.get("filename") or normalized["id"])
            normalized["src"] = str(normalized.get("src") or normalized.get("filepath") or "")
            p.media_assets[normalized["id"]] = normalized
        p.timeline_clips = []
        for clip in sequence(data.get("timeline_clips")):
            if not isinstance(clip, dict):
                continue
            normalized = copy.deepcopy(clip)
            normalized["id"] = str(normalized.get("id") or uuid.uuid4())
            normalized["assetId"] = str(normalized.get("assetId") or "")
            if not normalized["assetId"]:
                legacy_src = str(normalized.get("src") or normalized.get("filepath") or "")
                if legacy_src:
                    existing = next((item for item in p.media_assets.values() if item.get("src") == legacy_src), None)
                    if existing is None:
                        legacy_id = f"legacy_{uuid.uuid5(uuid.NAMESPACE_URL, legacy_src)}"
                        existing = {
                            "id": legacy_id,
                            "name": str(normalized.get("filename") or legacy_src.rsplit("/", 1)[-1]),
                            "type": str(normalized.get("type") or "image"),
                            "src": legacy_src,
                        }
                        p.media_assets[legacy_id] = existing
                    normalized["assetId"] = existing["id"]
            normalized["trackId"] = str(normalized.get("trackId") or "")
            normalized["startTime"] = finite_number(normalized.get("startTime"), 0, 0, 86400)
            normalized["sourceStart"] = finite_number(normalized.get("sourceStart"), 0, 0, 86400)
            normalized["duration"] = finite_number(normalized.get("duration"), 0, 0, 86400)
            if normalized["duration"] > 0 and normalized["assetId"]:
                p.timeline_clips.append(normalized)
        return p

    def save_to_file(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filepath: str) -> "ProjectModel":
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
