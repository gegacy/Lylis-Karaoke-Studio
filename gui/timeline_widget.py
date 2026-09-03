"""
Lylis Karaoke Studio - Exact Reference 7-Layer DAW Timeline Sequencer with CapCut Editing Tools
Features:
- CapCut Editing Toolbar: [ ✂ Split (Ctrl+B/S) ] [ 🗑 Delete (Del) ] [ 📋 Duplicate (Ctrl+D) ] [ Copy/Paste ] [ Ripple (Shift+Del) ] [ ⚡ Beats ] [ 🧲 Snap ] [ ＋ Line ]
- 7 DAW Sequencer Tracks:
  - Layer 7: Syllables / Từ từng chữ (Purple Chips with Word Text)
  - Layer 6: Lines / Câu hát phụ (Indigo/Blue Line Bars)
  - Layer 5: Objects / Văn bản & Vật thể (Sky Blue)
  - Layer 4: FX / Hiệu ứng (Pink)
  - Layer 3: Media / Câu hát chính (Orange Track with filename)
  - Layer 2: Media / Hình ảnh & Video (Green Track with Media Clips)
  - Layer 1: Base / Âm thanh Sóng âm (Dark Slate / Blue Waveform)
- Interactive CapCut Trimming (Left/Right Drag Handles with ↔ cursor)
- CapCut Clip Dragging & Moving with Magnetic Snapping to Playhead, Clips & Beats
- CapCut Magnetic Guidelines & Floating Timecode Badges
- CapCut "+" Add Line / Clip at timeline timestamp
- CapCut Box Marquee Selection & Right-Click Context Menu
"""
import copy
import math
import time
import uuid
from typing import List, Optional, Tuple, Set

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QSlider, QFrame, QLabel, QStyle, QMenu
)
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPen, QPolygonF, QPainterPath
)
from PyQt5.QtCore import Qt, QRect, QRectF, QPointF, QPoint, QSize, pyqtSignal
from core.lrc_engine import LyricLine, WordSyllable


class TimelineCanvas(QWidget):
    time_seek_requested = pyqtSignal(float)
    lyrics_modified = pyqtSignal(list)
    media_clips_modified = pyqtSignal(list)
    line_selected = pyqtSignal(int)
    media_asset_dropped = pyqtSignal(object, float)
    media_files_dropped = pyqtSignal(list, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(0)
        self.current_time = 0.0
        self.duration = 45.0
        self.zoom_seconds = 10.0
        self.scroll_offset = 0.0
        self.follow_playhead_enabled = True
        self.playback_active = False
        self.manual_scroll_grace_seconds = 1.75
        self._manual_follow_resume_at = 0.0
        self.lyric_lines: List[LyricLine] = []
        self.waveform_peaks = []
        self.beat_times = []
        self.overlay_objects = []
        self.effects = {}
        self.transitions = {}
        self.media_label = "No background"
        self.audio_label = "No audio"
        self.media_clips = []
        self.media_assets = {}
        
        # Selection states (CapCut unified selection)
        self.selected_type: Optional[str] = None  # 'line' | 'word' | 'media'
        self.selected_line_idx: Optional[int] = None
        self.selected_line_indices: Set[int] = set()
        self.selected_media_clip_idx: Optional[int] = None
        self.selected_word_pos: Optional[Tuple[int, int]] = None  # (line_idx, word_idx)
        self.clipboard_lines = []
        self.clipboard_media = []

        # Line trim & move interaction states
        self.is_trimming_start = False
        self.is_trimming_end = False
        self.trim_line_idx: Optional[int] = None
        self.is_moving_line = False
        self.move_line_idx: Optional[int] = None
        self.move_drag_start_t = 0.0
        self.orig_line_start = 0.0
        self.orig_line_end = 0.0
        self.orig_word_times = []
        self.moving_line_ref = None
        self.orig_selected_clip_data = []

        # Media clip interaction states
        self.is_trimming_media_start = False
        self.is_trimming_media_end = False
        self.is_moving_media = False
        self.trim_media_idx: Optional[int] = None
        self.move_media_idx: Optional[int] = None
        self.move_media_drag_start_t = 0.0
        self.orig_media_start = 0.0
        self.orig_media_dur = 0.0

        # Word syllable interaction states
        self.is_trimming_word_start = False
        self.is_trimming_word_end = False
        self.is_moving_word = False
        self.trim_word_pos: Optional[Tuple[int, int]] = None
        self.move_word_pos: Optional[Tuple[int, int]] = None
        self.move_word_drag_start_t = 0.0
        self.orig_word_start = 0.0
        self.orig_word_end = 0.0

        # Marquee box selection
        self.is_box_selecting = False
        self.box_start_pt: Optional[QPoint] = None
        self.box_curr_pt: Optional[QPoint] = None

        # Playhead dragging & Snapping
        self.is_dragging_playhead = False
        self.snap_enabled = True
        self.beats_enabled = True
        self.snap_guideline_x: Optional[float] = None
        self.drag_tooltip_text: Optional[str] = None
        self.drag_tooltip_x: Optional[float] = None
        self.drag_tooltip_y: Optional[float] = None

        # Hover "+" add button
        self.hover_add_rect: Optional[QRectF] = None
        self.hover_add_time: Optional[float] = None

        self.setFocusPolicy(Qt.StrongFocus)
        self.header_width = 115
        self.track_height = 28
        self.ruler_height = 24
        self.layer_visibilities = [True] * 7
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.drop_preview_time = None

    def has_selection(self) -> bool:
        """Returns True if any clip (line, media, or word) is currently selected."""
        return (
            (self.selected_line_idx is not None and 0 <= self.selected_line_idx < len(self.lyric_lines))
            or bool(self.selected_line_indices)
            or (self.selected_media_clip_idx is not None and 0 <= self.selected_media_clip_idx < len(self.media_clips))
            or (self.selected_word_pos is not None)
        )

    def set_duration(self, duration: float):
        self.duration = max(1.0, duration)
        self.current_time = max(0.0, min(self.duration, self.current_time))
        self.scroll_offset = max(0.0, min(max(0.0, self.duration - self.zoom_seconds), self.scroll_offset))
        self.update()

    def set_lyrics(self, lines: List[LyricLine]):
        self.lyric_lines = lines
        self.selected_line_indices = {
            idx for idx in self.selected_line_indices if 0 <= idx < len(lines)
        }
        if self.selected_line_idx is not None and self.selected_line_idx >= len(lines):
            self.selected_line_idx = None
        self.update()

    def _clone_line(self, line: LyricLine, offset: float = 0.0) -> LyricLine:
        """Create an independent clip copy, preserving word timing and singer metadata."""
        words = [
            WordSyllable(w.text, w.start_time + offset, w.end_time + offset)
            for w in line.words
        ]
        return LyricLine(
            line.line_start + offset,
            line.line_end + offset,
            words,
            raw_text=line.raw_text,
            singer=getattr(line, "singer", "both"),
        )

    def _selected_indices(self):
        indices = set(self.selected_line_indices)
        if self.selected_line_idx is not None:
            indices.add(self.selected_line_idx)
        return sorted(i for i in indices if 0 <= i < len(self.lyric_lines))

    def copy_selected(self):
        """CapCut Copy: copies selected lines or media clip to clipboard."""
        if self.selected_type == 'media' and self.selected_media_clip_idx is not None:
            if 0 <= self.selected_media_clip_idx < len(self.media_clips):
                self.clipboard_media = [copy.deepcopy(self.media_clips[self.selected_media_clip_idx])]
                self.clipboard_lines = []
                return

        indices = self._selected_indices()
        if indices:
            self.clipboard_lines = [self._clone_line(self.lyric_lines[i]) for i in indices]
            self.clipboard_media = []

    def paste_selected(self):
        """CapCut Paste: pastes clipboard content at current playhead."""
        if self.clipboard_media:
            for clip in self.clipboard_media:
                clone = copy.deepcopy(clip)
                clone['id'] = str(uuid.uuid4())
                clone['startTime'] = self.current_time
                self.media_clips.append(clone)
            self.selected_media_clip_idx = len(self.media_clips) - 1
            self.selected_type = 'media'
            self.media_clips_modified.emit(self.media_clips)
            self.update()
            return

        if not self.clipboard_lines:
            return
        anchor = self.current_time
        source_start = min(line.line_start for line in self.clipboard_lines)
        offset = anchor - source_start
        pasted = []
        for line in self.clipboard_lines:
            clone = self._clone_line(line, offset)
            if clone.line_start >= self.duration:
                continue
            delta = min(0.0, self.duration - clone.line_end)
            if delta < 0:
                clone = self._clone_line(clone, delta)
            pasted.append(clone)
        if not pasted:
            return
        self.lyric_lines.extend(pasted)
        self.lyric_lines.sort(key=lambda line: line.line_start)
        self.selected_line_indices = {
            idx for idx, line in enumerate(self.lyric_lines)
            if any(line is pasted_line for pasted_line in pasted)
        }
        self.selected_line_idx = min(self.selected_line_indices)
        self.selected_type = 'line'
        self.lyrics_modified.emit(self.lyric_lines)
        self.update()

    def delete_selected(self):
        """CapCut Delete: removes selected media clip, word, or lyric line."""
        # 1. Media clip deletion
        if self.selected_type == 'media' and self.selected_media_clip_idx is not None:
            if 0 <= self.selected_media_clip_idx < len(self.media_clips):
                self.media_clips.pop(self.selected_media_clip_idx)
                self.selected_media_clip_idx = None
                self.selected_type = None
                self.media_clips_modified.emit(self.media_clips)
                self.update()
                return

        # 2. Individual word syllable deletion
        if self.selected_type == 'word' and self.selected_word_pos is not None:
            l_idx, w_idx = self.selected_word_pos
            if 0 <= l_idx < len(self.lyric_lines):
                line = self.lyric_lines[l_idx]
                if 0 <= w_idx < len(line.words):
                    line.words.pop(w_idx)
                    if line.words:
                        line.line_start = line.words[0].start_time
                        line.line_end = line.words[-1].end_time
                        line.raw_text = "".join(w.text for w in line.words)
                    else:
                        self.lyric_lines.pop(l_idx)
                    self.selected_word_pos = None
                    self.selected_type = None
                    self.lyrics_modified.emit(self.lyric_lines)
                    self.update()
                    return

        # 3. Lyric lines deletion
        indices = self._selected_indices()
        if indices:
            for idx in reversed(indices):
                if 0 <= idx < len(self.lyric_lines):
                    self.lyric_lines.pop(idx)
            self.selected_line_idx = None
            self.selected_line_indices.clear()
            self.selected_type = None
            self.lyrics_modified.emit(self.lyric_lines)
            self.update()
            return

        # 4. Fallback: if nothing selected, delete whatever clip is under the playhead
        t = self.current_time
        for idx, clip in enumerate(self.media_clips):
            st = float(clip.get('startTime', 0.0))
            dur = float(clip.get('duration', 0.0))
            if st <= t <= st + dur:
                self.media_clips.pop(idx)
                self.media_clips_modified.emit(self.media_clips)
                self.update()
                return
        for idx, line in enumerate(self.lyric_lines):
            if line.line_start <= t <= line.line_end:
                self.lyric_lines.pop(idx)
                self.lyrics_modified.emit(self.lyric_lines)
                self.update()
                return

    def ripple_delete_selected(self):
        """CapCut Ripple Delete: deletes selected clip and shifts subsequent clips leftward to close gap."""
        if self.selected_type == 'media' and self.selected_media_clip_idx is not None:
            if 0 <= self.selected_media_clip_idx < len(self.media_clips):
                removed_clip = self.media_clips.pop(self.selected_media_clip_idx)
                dur = float(removed_clip.get('duration', 0.0))
                end = float(removed_clip.get('startTime', 0.0)) + dur
                for clip in self.media_clips:
                    if float(clip.get('startTime', 0.0)) >= end:
                        clip['startTime'] = max(0.0, float(clip['startTime']) - dur)
                self.selected_media_clip_idx = None
                self.selected_type = None
                self.media_clips_modified.emit(self.media_clips)
                self.update()
                return

        indices = self._selected_indices()
        if not indices:
            for idx, line in enumerate(self.lyric_lines):
                if line.line_start <= self.current_time <= line.line_end:
                    indices = [idx]
                    break
        if not indices:
            return

        removed = [self.lyric_lines[i] for i in indices if 0 <= i < len(self.lyric_lines)]
        remaining = [line for i, line in enumerate(self.lyric_lines) if i not in set(indices)]
        intervals = sorted((line.line_start, line.line_end) for line in removed)
        for line in remaining:
            shift = sum(max(0.0, end - start) for start, end in intervals if line.line_start >= end)
            if shift:
                line.line_start -= shift
                line.line_end -= shift
                for word in line.words:
                    word.start_time -= shift
                    word.end_time -= shift
        self.lyric_lines = sorted(remaining, key=lambda line: line.line_start)
        self.selected_line_idx = None
        self.selected_line_indices.clear()
        self.selected_type = None
        self.lyrics_modified.emit(self.lyric_lines)
        self.update()

    def split_at_playhead(self):
        """CapCut Split: splits active clip (lyric line or media clip) at playhead."""
        t = self.current_time

        # 1. Split media clip if selected or under playhead
        target_media_idx = self.selected_media_clip_idx if (self.selected_type == 'media') else None
        if target_media_idx is None:
            for idx, clip in enumerate(self.media_clips):
                st = float(clip.get('startTime', 0.0))
                dur = float(clip.get('duration', 0.0))
                if st + 0.1 <= t <= st + dur - 0.1:
                    target_media_idx = idx
                    break
        if target_media_idx is not None and 0 <= target_media_idx < len(self.media_clips):
            clip = self.media_clips[target_media_idx]
            st = float(clip.get('startTime', 0.0))
            dur = float(clip.get('duration', 0.0))
            if st + 0.1 <= t <= st + dur - 0.1:
                dur_a = t - st
                dur_b = dur - dur_a
                clip_a = dict(clip)
                clip_a['duration'] = dur_a
                clip_b = dict(clip)
                clip_b['id'] = str(uuid.uuid4())
                clip_b['startTime'] = t
                clip_b['duration'] = dur_b
                self.media_clips[target_media_idx] = clip_a
                self.media_clips.insert(target_media_idx + 1, clip_b)
                self.selected_media_clip_idx = target_media_idx + 1
                self.selected_type = 'media'
                self.media_clips_modified.emit(self.media_clips)
                self.update()
                return

        # 2. Split lyric line
        target_idx = self.selected_line_idx
        if target_idx is None or not (0 <= target_idx < len(self.lyric_lines)):
            for idx, line in enumerate(self.lyric_lines):
                if line.line_start <= t <= line.line_end:
                    target_idx = idx
                    break
        
        if target_idx is None or target_idx >= len(self.lyric_lines):
            return

        line = self.lyric_lines[target_idx]
        if line.line_end - line.line_start < 0.2:
            return

        words_a = [w for w in line.words if w.end_time <= t]
        words_b = [w for w in line.words if w.start_time >= t]
        mid_words = [w for w in line.words if w.start_time < t < w.end_time]
        
        if mid_words:
            w = mid_words[0]
            words_a.append(WordSyllable(w.text, w.start_time, t))
            words_b.insert(0, WordSyllable(w.text, t, w.end_time))
        
        if not words_a or not words_b:
            mid_idx = max(1, len(line.words) // 2)
            words_a = line.words[:mid_idx]
            words_b = line.words[mid_idx:]

        text_a = "".join(w.text for w in words_a) or line.raw_text
        text_b = "".join(w.text for w in words_b) or line.raw_text
        start_a = words_a[0].start_time if words_a else line.line_start
        end_a = words_a[-1].end_time if words_a else t
        start_b = words_b[0].start_time if words_b else t
        end_b = words_b[-1].end_time if words_b else line.line_end

        line_a = LyricLine(start_a, end_a, words_a, raw_text=text_a, singer=getattr(line, 'singer', 'both'))
        line_b = LyricLine(start_b, end_b, words_b, raw_text=text_b, singer=getattr(line, 'singer', 'both'))

        self.lyric_lines[target_idx] = line_a
        self.lyric_lines.insert(target_idx + 1, line_b)
        self.selected_line_idx = target_idx + 1
        self.selected_line_indices = {self.selected_line_idx}
        self.selected_type = 'line'
        self.lyrics_modified.emit(self.lyric_lines)
        self.update()

    def duplicate_selected(self):
        """CapCut Duplicate: clones selected clip right after it."""
        if self.selected_type == 'media' and self.selected_media_clip_idx is not None:
            if 0 <= self.selected_media_clip_idx < len(self.media_clips):
                src = self.media_clips[self.selected_media_clip_idx]
                clone = dict(src)
                clone['id'] = str(uuid.uuid4())
                clone['startTime'] = float(src.get('startTime', 0.0)) + float(src.get('duration', 0.0)) + 0.1
                self.media_clips.insert(self.selected_media_clip_idx + 1, clone)
                self.selected_media_clip_idx = self.selected_media_clip_idx + 1
                self.media_clips_modified.emit(self.media_clips)
                self.update()
                return

        if self.selected_line_idx is not None and 0 <= self.selected_line_idx < len(self.lyric_lines):
            src = self.lyric_lines[self.selected_line_idx]
            duration = max(0.2, src.line_end - src.line_start)
            new_start = src.line_end + 0.1
            new_end = new_start + duration
            
            new_words = []
            for w in src.words:
                w_offset = w.start_time - src.line_start
                w_dur = max(0.05, w.end_time - w.start_time)
                new_words.append(WordSyllable(w.text, new_start + w_offset, new_start + w_offset + w_dur))
            
            new_line = LyricLine(
                new_start, 
                new_end, 
                new_words, 
                raw_text=src.raw_text, 
                singer=getattr(src, 'singer', 'both')
            )
            self.lyric_lines.insert(self.selected_line_idx + 1, new_line)
            self.selected_line_idx = self.selected_line_idx + 1
            self.selected_line_indices = {self.selected_line_idx}
            self.selected_type = 'line'
            self.lyrics_modified.emit(self.lyric_lines)
            self.update()

    def add_line_at(self, t: float):
        """CapCut + : Add new lyric line at specified timestamp."""
        duration = 2.5
        start = max(0.0, min(self.duration - 0.5, t))
        end = min(self.duration, start + duration)
        word = WordSyllable("Câu mới", start, end)
        new_line = LyricLine(start, end, [word], raw_text="Câu mới", singer="both")
        self.lyric_lines.append(new_line)
        self.lyric_lines.sort(key=lambda l: l.line_start)
        self.selected_line_idx = self.lyric_lines.index(new_line)
        self.selected_line_indices = {self.selected_line_idx}
        self.selected_type = 'line'
        self.lyrics_modified.emit(self.lyric_lines)
        self.line_selected.emit(self.selected_line_idx)
        self.update()

    def set_waveform(self, peaks: list):
        self.waveform_peaks = peaks
        self.update()

    def set_beat_times(self, beat_times: list):
        valid_times = []
        for value in beat_times or []:
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                continue
            if math.isfinite(parsed) and 0.0 <= parsed <= self.duration:
                valid_times.append(parsed)
        self.beat_times = valid_times
        self.update()

    def set_overlay_objects(self, objects: list):
        self.overlay_objects = list(objects or [])
        self.update()

    def set_effects(self, effects: dict):
        self.effects = dict(effects or {})
        self.update()

    def set_transitions(self, transitions: dict):
        self.transitions = dict(transitions or {})
        self.update()

    def set_media_labels(self, background: str = None, audio: str = None):
        if background is not None:
            self.media_label = background
        if audio is not None:
            self.audio_label = audio
        self.update()

    def set_media_clips(self, clips, assets=None):
        self.media_clips = [dict(clip) for clip in (clips or [])]
        self.media_assets = dict(assets or {})
        self.update()

    def set_current_time(self, current_time: float, is_playing=None, reveal=False):
        self.current_time = max(0.0, min(self.duration, float(current_time)))
        if is_playing is not None:
            self.set_playback_active(bool(is_playing))
        if reveal and self.follow_playhead_enabled:
            self._manual_follow_resume_at = 0.0
            self.ensure_playhead_visible(force=True)
        elif self.follow_playhead_enabled and self.playback_active:
            if time.monotonic() >= self._manual_follow_resume_at:
                self.ensure_playhead_visible()
        self.update()

    def set_zoom(self, zoom_seconds: float):
        self.zoom_seconds = max(3.0, min(120.0, zoom_seconds))
        self.scroll_offset = self._clamp_scroll_offset(self.scroll_offset)
        if (
            self.follow_playhead_enabled
            and self.playback_active
            and time.monotonic() >= self._manual_follow_resume_at
        ):
            self.ensure_playhead_visible()
        self.update()

    def _clamp_scroll_offset(self, value: float) -> float:
        return max(0.0, min(max(0.0, self.duration - self.zoom_seconds), float(value)))

    def ensure_playhead_visible(self, force=False):
        if self.duration <= self.zoom_seconds:
            self.scroll_offset = 0.0
            return
        visible_start = self.scroll_offset
        visible_end = visible_start + self.zoom_seconds
        lead_boundary = visible_start + self.zoom_seconds * 0.12
        trail_boundary = visible_start + self.zoom_seconds * 0.85
        if force:
            target = self.current_time - self.zoom_seconds * 0.25
        elif self.current_time > trail_boundary:
            target = self.current_time - self.zoom_seconds * 0.25
        elif self.current_time < lead_boundary or not (visible_start <= self.current_time <= visible_end):
            target = self.current_time - self.zoom_seconds * 0.12
        else:
            return
        self.scroll_offset = self._clamp_scroll_offset(target)

    def set_follow_playhead(self, enabled: bool):
        self.follow_playhead_enabled = bool(enabled)
        self._manual_follow_resume_at = 0.0
        if self.follow_playhead_enabled:
            self.ensure_playhead_visible(force=True)
        self.update()

    def set_playback_active(self, active: bool):
        active = bool(active)
        resumed = active and not self.playback_active
        self.playback_active = active
        if resumed:
            self._manual_follow_resume_at = 0.0
            if self.follow_playhead_enabled:
                self.ensure_playhead_visible()

    def scroll_horizontally(self, delta_seconds: float, user_initiated=True):
        previous = self.scroll_offset
        self.scroll_offset = self._clamp_scroll_offset(previous + float(delta_seconds))
        if user_initiated and abs(self.scroll_offset - previous) > 1e-9:
            self._manual_follow_resume_at = time.monotonic() + self.manual_scroll_grace_seconds
        self.update()

    def time_to_x(self, t: float) -> float:
        content_w = self.width() - self.header_width
        if content_w <= 0:
            return float(self.header_width)
        return self.header_width + ((t - self.scroll_offset) / self.zoom_seconds) * content_w

    def x_to_time(self, x: float) -> float:
        content_w = self.width() - self.header_width
        if content_w <= 0:
            return 0.0
        ratio = (x - self.header_width) / float(content_w)
        raw_t = max(0.0, min(self.duration, self.scroll_offset + ratio * self.zoom_seconds))
        if self.snap_enabled and abs(raw_t - self.current_time) < (self.zoom_seconds * 0.015):
            return self.current_time
        return raw_t

    def _snap_time(self, value: float) -> float:
        """Snap timeline trims to half-second grid if snap is enabled."""
        if not self.snap_enabled:
            return value
        return max(0.0, min(self.duration, round(value * 2.0) / 2.0))

    def _calculate_snap(self, proposed_t: float, tolerance_px: float = 10.0) -> Tuple[float, Optional[float]]:
        """Finds nearest snap target within pixel tolerance. Returns (snapped_t, snap_x or None)."""
        if not self.snap_enabled:
            return proposed_t, None
        content_w = max(1.0, float(self.width() - self.header_width))
        tol_sec = (tolerance_px / content_w) * self.zoom_seconds

        candidates = [self.current_time]
        if self.beats_enabled:
            candidates.extend(self.beat_times)
        for line in self.lyric_lines:
            candidates.append(line.line_start)
            candidates.append(line.line_end)
        for clip in self.media_clips:
            st = float(clip.get('startTime', 0.0))
            candidates.append(st)
            candidates.append(st + float(clip.get('duration', 0.0)))

        best_diff = tol_sec
        best_t = proposed_t
        for c in candidates:
            diff = abs(c - proposed_t)
            if diff < best_diff:
                best_diff = diff
                best_t = c

        if best_t != proposed_t:
            return best_t, self.time_to_x(best_t)
        return proposed_t, None

    # Drag and Drop Events
    def dragEnterEvent(self, event):
        mime = event.mimeData()
        if mime.hasFormat("application/x-lylis-asset-id") or mime.hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-lylis-asset-id") or event.mimeData().hasUrls():
            self.drop_preview_time = self.x_to_time(event.pos().x())
            self.update()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.drop_preview_time = None
        self.update()
        event.accept()

    def dropEvent(self, event):
        mime = event.mimeData()
        drop_time = self.x_to_time(event.pos().x())
        self.drop_preview_time = None
        if mime.hasFormat("application/x-lylis-asset-id"):
            asset_id = bytes(mime.data("application/x-lylis-asset-id")).decode("utf-8")
            self.media_asset_dropped.emit(asset_id, drop_time)
            event.acceptProposedAction()
            self.update()
            return
        paths = [url.toLocalFile() for url in mime.urls() if url.isLocalFile()]
        if paths:
            self.media_files_dropped.emit(paths, drop_time)
            event.acceptProposedAction()
        else:
            event.ignore()
        self.update()

    # Hit Testing Helpers
    def _hit_test_line(self, x: float, y: float):
        """Returns (line_idx, is_left_edge, is_right_edge) or (None, False, False)"""
        line_layer_y_3 = self.ruler_height + self.track_height * 4
        line_layer_y_6 = self.ruler_height + self.track_height * 1
        if not ((line_layer_y_3 <= y <= line_layer_y_3 + self.track_height) or
                (line_layer_y_6 <= y <= line_layer_y_6 + self.track_height)):
            return None, False, False
        for idx, line in enumerate(self.lyric_lines):
            xs = self.time_to_x(line.line_start)
            xe = self.time_to_x(line.line_end)
            if xs - 8 <= x <= xe + 8:
                if abs(x - xs) <= 8:
                    return idx, True, False
                elif abs(x - xe) <= 8:
                    return idx, False, True
                elif xs <= x <= xe:
                    return idx, False, False
        return None, False, False

    def _hit_test_media_clip(self, x: float, y: float):
        """Returns (clip_idx, is_left_edge, is_right_edge) or (None, False, False)"""
        for idx, clip in enumerate(self.media_clips):
            asset = self.media_assets.get(str(clip.get('assetId')), {})
            kind = asset.get('type', 'image')
            row = 6 if kind == 'audio' else 5
            track_y = self.ruler_height + self.track_height * row
            if track_y <= y <= track_y + self.track_height:
                start = float(clip.get('startTime', 0.0))
                end = start + float(clip.get('duration', 0.0))
                x1 = self.time_to_x(start)
                x2 = self.time_to_x(end)
                if x1 - 8 <= x <= x2 + 8:
                    if abs(x - x1) <= 8:
                        return idx, True, False
                    elif abs(x - x2) <= 8:
                        return idx, False, True
                    elif x1 <= x <= x2:
                        return idx, False, False
        return None, False, False

    def _hit_test_word(self, x: float, y: float):
        """Returns (line_idx, word_idx, is_left_edge, is_right_edge) or None"""
        track_y = self.ruler_height + self.track_height * 0
        if not (track_y <= y <= track_y + self.track_height):
            return None
        t = self.x_to_time(x)
        for line_idx, line in enumerate(self.lyric_lines):
            if line.line_start - 0.2 <= t <= line.line_end + 0.2:
                for w_idx, word in enumerate(line.words):
                    wx1 = self.time_to_x(word.start_time)
                    wx2 = self.time_to_x(word.end_time)
                    if wx1 - 5 <= x <= wx2 + 5:
                        if abs(x - wx1) <= 5:
                            return (line_idx, w_idx, True, False)
                        elif abs(x - wx2) <= 5:
                            return (line_idx, w_idx, False, True)
                        elif wx1 <= x <= wx2:
                            return (line_idx, w_idx, False, False)
        return None

    # Mouse & Keyboard Event Handlers
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setFocus()
            x = event.pos().x()
            y = event.pos().y()

            # 1. Left Track Header Controls (Eye visibility & Trash clear)
            if x < self.header_width:
                layer_idx = int((y - self.ruler_height) // self.track_height)
                if 0 <= layer_idx < 7:
                    if 14 <= x <= 32:
                        self.layer_visibilities[layer_idx] = not self.layer_visibilities[layer_idx]
                        self.update()
                        return
                    elif x >= self.header_width - 24:
                        if layer_idx in (0, 1, 4):
                            self.lyric_lines = []
                            self.selected_line_idx = None
                            self.selected_line_indices.clear()
                            self.lyrics_modified.emit(self.lyric_lines)
                        elif layer_idx == 5:
                            self.media_clips = []
                            self.selected_media_clip_idx = None
                            self.media_clips_modified.emit(self.media_clips)
                        elif layer_idx == 2:
                            self.overlay_objects = []
                        elif layer_idx == 3:
                            self.effects = {}
                        self.update()
                        return
                return

            # 2. Check if clicked on hover "+" Add button
            if self.hover_add_rect and self.hover_add_rect.contains(QPointF(x, y)) and self.hover_add_time is not None:
                self.add_line_at(self.hover_add_time)
                return

            # 3. Layer 7: Word Syllable click & drag/trim
            word_hit = self._hit_test_word(x, y)
            if word_hit:
                l_idx, w_idx, is_left, is_right = word_hit
                self.selected_type = 'word'
                self.selected_word_pos = (l_idx, w_idx)
                self.selected_line_idx = l_idx
                self.selected_line_indices = {l_idx}
                self.selected_media_clip_idx = None
                word = self.lyric_lines[l_idx].words[w_idx]
                if is_left:
                    self.is_trimming_word_start = True
                    self.trim_word_pos = (l_idx, w_idx)
                elif is_right:
                    self.is_trimming_word_end = True
                    self.trim_word_pos = (l_idx, w_idx)
                else:
                    self.is_moving_word = True
                    self.move_word_pos = (l_idx, w_idx)
                    self.move_word_drag_start_t = self.x_to_time(x)
                    self.orig_word_start = word.start_time
                    self.orig_word_end = word.end_time
                self.line_selected.emit(l_idx)
                self.time_seek_requested.emit(word.start_time)
                self.update()
                return

            # 4. Layer 3 & Layer 6: Main/Secondary Lyric Lines
            line_idx, is_l_edge, is_r_edge = self._hit_test_line(x, y)
            if line_idx is not None:
                line = self.lyric_lines[line_idx]
                self.selected_type = 'line'
                self.selected_word_pos = None
                self.selected_media_clip_idx = None
                if event.modifiers() & Qt.ControlModifier:
                    if line_idx in self.selected_line_indices:
                        self.selected_line_indices.remove(line_idx)
                    else:
                        self.selected_line_indices.add(line_idx)
                    self.selected_line_idx = max(self.selected_line_indices) if self.selected_line_indices else None
                    self.line_selected.emit(self.selected_line_idx if self.selected_line_idx is not None else -1)
                    self.update()
                    return

                if line_idx not in self.selected_line_indices:
                    self.selected_line_indices = {line_idx}
                self.selected_line_idx = line_idx

                if is_l_edge:
                    self.is_trimming_start = True
                    self.trim_line_idx = line_idx
                elif is_r_edge:
                    self.is_trimming_end = True
                    self.trim_line_idx = line_idx
                else:
                    self.is_moving_line = True
                    self.move_line_idx = line_idx
                    self.move_drag_start_t = self.x_to_time(x)
                    self.orig_line_start = line.line_start
                    self.orig_line_end = line.line_end
                    self.orig_word_times = [(w.start_time, w.end_time) for w in line.words]
                    self.moving_line_ref = line
                    self.orig_selected_clip_data = [
                        (self.lyric_lines[s_idx], (
                            self.lyric_lines[s_idx].line_start,
                            self.lyric_lines[s_idx].line_end,
                            [(w.start_time, w.end_time) for w in self.lyric_lines[s_idx].words],
                        ))
                        for s_idx in self._selected_indices()
                    ]
                self.line_selected.emit(line_idx)
                self.time_seek_requested.emit(self.x_to_time(x))
                self.update()
                return

            # 5. Layer 2 & Layer 1: Media Clips
            media_idx, is_m_left, is_m_right = self._hit_test_media_clip(x, y)
            if media_idx is not None:
                clip = self.media_clips[media_idx]
                self.selected_type = 'media'
                self.selected_media_clip_idx = media_idx
                self.selected_line_idx = None
                self.selected_line_indices.clear()
                self.selected_word_pos = None
                if is_m_left:
                    self.is_trimming_media_start = True
                    self.trim_media_idx = media_idx
                elif is_m_right:
                    self.is_trimming_media_end = True
                    self.trim_media_idx = media_idx
                else:
                    self.is_moving_media = True
                    self.move_media_idx = media_idx
                    self.move_media_drag_start_t = self.x_to_time(x)
                    self.orig_media_start = float(clip.get('startTime', 0.0))
                    self.orig_media_dur = float(clip.get('duration', 0.0))
                self.time_seek_requested.emit(float(clip.get('startTime', 0.0)))
                self.update()
                return

            # 6. Clicked on Time Ruler: scrub playhead
            if y < self.ruler_height:
                self.is_dragging_playhead = True
                t = self.x_to_time(x)
                self.time_seek_requested.emit(t)
                return

            # 7. Clicked on empty space: start CapCut Box/Marquee selection
            self.selected_line_idx = None
            self.selected_line_indices.clear()
            self.selected_media_clip_idx = None
            self.selected_word_pos = None
            self.selected_type = None
            self.is_box_selecting = True
            self.box_start_pt = event.pos()
            self.box_curr_pt = event.pos()
            t = self.x_to_time(x)
            self.time_seek_requested.emit(t)
            self.update()

    def mouseMoveEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()

        # Update hover cursors if no mouse button is pressed
        if not (self.is_dragging_playhead or self.is_moving_line or self.is_trimming_start or
                self.is_trimming_end or self.is_moving_media or self.is_trimming_media_start or
                self.is_trimming_media_end or self.is_moving_word or self.is_trimming_word_start or
                self.is_trimming_word_end or self.is_box_selecting):

            # Check lines
            l_idx, is_l, is_r = self._hit_test_line(x, y)
            if l_idx is not None:
                if is_l or is_r:
                    self.setCursor(Qt.SizeHorCursor)
                else:
                    self.setCursor(Qt.OpenHandCursor)
                return

            # Check media clips
            m_idx, is_ml, is_mr = self._hit_test_media_clip(x, y)
            if m_idx is not None:
                if is_ml or is_mr:
                    self.setCursor(Qt.SizeHorCursor)
                else:
                    self.setCursor(Qt.OpenHandCursor)
                return

            # Check words
            w_hit = self._hit_test_word(x, y)
            if w_hit:
                _, _, is_wl, is_wr = w_hit
                if is_wl or is_wr:
                    self.setCursor(Qt.SizeHorCursor)
                else:
                    self.setCursor(Qt.PointingHandCursor)
                return

            if y < self.ruler_height:
                self.setCursor(Qt.SplitHCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

        # 1. Marquee selection drag
        if self.is_box_selecting:
            self.box_curr_pt = event.pos()
            self.update()
            return

        # 2. Line Trimming (Start)
        if self.is_trimming_start and self.trim_line_idx is not None:
            self.setCursor(Qt.SizeHorCursor)
            line = self.lyric_lines[self.trim_line_idx]
            proposed_t = self.x_to_time(x)
            snapped_t, snap_x = self._calculate_snap(proposed_t)
            snapped_t = max(0.0, min(line.line_end - 0.2, snapped_t))
            shift = snapped_t - line.line_start
            line.line_start = snapped_t
            for word in line.words:
                word.start_time += shift
                word.end_time += shift
            self.snap_guideline_x = snap_x
            m, s = int(snapped_t // 60), int(snapped_t % 60)
            self.drag_tooltip_text = f"Bắt đầu: {m:02d}:{s:02d}.{int((snapped_t % 1) * 100):02d}"
            self.drag_tooltip_x = x
            self.drag_tooltip_y = y
            self.update()
            return

        # 3. Line Trimming (End)
        if self.is_trimming_end and self.trim_line_idx is not None:
            self.setCursor(Qt.SizeHorCursor)
            line = self.lyric_lines[self.trim_line_idx]
            proposed_t = self.x_to_time(x)
            snapped_t, snap_x = self._calculate_snap(proposed_t)
            snapped_t = max(line.line_start + 0.2, min(self.duration, snapped_t))
            line.line_end = snapped_t
            if line.words:
                line.words[-1].end_time = snapped_t
            self.snap_guideline_x = snap_x
            m, s = int(snapped_t // 60), int(snapped_t % 60)
            self.drag_tooltip_text = f"Kết thúc: {m:02d}:{s:02d}.{int((snapped_t % 1) * 100):02d}"
            self.drag_tooltip_x = x
            self.drag_tooltip_y = y
            self.update()
            return

        # 4. Moving Line(s)
        if self.is_moving_line and self.move_line_idx is not None:
            self.setCursor(Qt.ClosedHandCursor)
            cur_t = self.x_to_time(x)
            delta = cur_t - self.move_drag_start_t
            proposed_start = max(0.0, self.orig_line_start + delta)
            snapped_start, snap_x = self._calculate_snap(proposed_start)
            actual_delta = snapped_start - self.orig_line_start

            for line, (orig_start, orig_end, orig_words) in self.orig_selected_clip_data:
                clip_delta = actual_delta
                if orig_start + clip_delta < 0:
                    clip_delta = -orig_start
                if orig_end + clip_delta > self.duration:
                    clip_delta = self.duration - orig_end
                line.line_start = orig_start + clip_delta
                line.line_end = orig_end + clip_delta
                for w_idx, word in enumerate(line.words):
                    if w_idx < len(orig_words):
                        orig_ws, orig_we = orig_words[w_idx]
                        word.start_time = orig_ws + clip_delta
                        word.end_time = orig_we + clip_delta

            self.snap_guideline_x = snap_x
            curr_pos = self.lyric_lines[self.move_line_idx].line_start
            m, s = int(curr_pos // 60), int(curr_pos % 60)
            delta_sign = "+" if actual_delta >= 0 else ""
            self.drag_tooltip_text = f"{m:02d}:{s:02d} ({delta_sign}{actual_delta:.2f}s)"
            self.drag_tooltip_x = x
            self.drag_tooltip_y = y
            self.update()
            return

        # 5. Media Clip Trimming & Moving
        if self.is_trimming_media_start and self.trim_media_idx is not None:
            self.setCursor(Qt.SizeHorCursor)
            clip = self.media_clips[self.trim_media_idx]
            proposed_t = self.x_to_time(x)
            snapped_t, snap_x = self._calculate_snap(proposed_t)
            end_t = float(clip.get('startTime', 0.0)) + float(clip.get('duration', 0.0))
            new_st = max(0.0, min(end_t - 0.2, snapped_t))
            clip['duration'] = end_t - new_st
            clip['startTime'] = new_st
            self.snap_guideline_x = snap_x
            m, s = int(new_st // 60), int(new_st % 60)
            self.drag_tooltip_text = f"Bắt đầu: {m:02d}:{s:02d}"
            self.drag_tooltip_x = x
            self.drag_tooltip_y = y
            self.update()
            return

        if self.is_trimming_media_end and self.trim_media_idx is not None:
            self.setCursor(Qt.SizeHorCursor)
            clip = self.media_clips[self.trim_media_idx]
            proposed_t = self.x_to_time(x)
            snapped_t, snap_x = self._calculate_snap(proposed_t)
            st = float(clip.get('startTime', 0.0))
            new_dur = max(0.2, min(self.duration - st, snapped_t - st))
            clip['duration'] = new_dur
            self.snap_guideline_x = snap_x
            m, s = int((st + new_dur) // 60), int((st + new_dur) % 60)
            self.drag_tooltip_text = f"Thời lượng: {new_dur:.1f}s ({m:02d}:{s:02d})"
            self.drag_tooltip_x = x
            self.drag_tooltip_y = y
            self.update()
            return

        if self.is_moving_media and self.move_media_idx is not None:
            self.setCursor(Qt.ClosedHandCursor)
            clip = self.media_clips[self.move_media_idx]
            cur_t = self.x_to_time(x)
            delta = cur_t - self.move_media_drag_start_t
            proposed_st = max(0.0, min(self.duration - self.orig_media_dur, self.orig_media_start + delta))
            snapped_st, snap_x = self._calculate_snap(proposed_st)
            clip['startTime'] = snapped_st
            self.snap_guideline_x = snap_x
            m, s = int(snapped_st // 60), int(snapped_st % 60)
            self.drag_tooltip_text = f"Vị trí: {m:02d}:{s:02d}"
            self.drag_tooltip_x = x
            self.drag_tooltip_y = y
            self.update()
            return

        # 6. Word Trimming & Moving
        if (self.is_trimming_word_start or self.is_trimming_word_end or self.is_moving_word) and self.selected_word_pos:
            l_idx, w_idx = self.selected_word_pos
            word = self.lyric_lines[l_idx].words[w_idx]
            cur_t = self.x_to_time(x)
            if self.is_trimming_word_start:
                word.start_time = max(0.0, min(word.end_time - 0.05, cur_t))
            elif self.is_trimming_word_end:
                word.end_time = max(word.start_time + 0.05, min(self.duration, cur_t))
            elif self.is_moving_word:
                dur = self.orig_word_end - self.orig_word_start
                delta = cur_t - self.move_word_drag_start_t
                word.start_time = max(0.0, self.orig_word_start + delta)
                word.end_time = word.start_time + dur
            self.lyric_lines[l_idx].line_start = min(w.start_time for w in self.lyric_lines[l_idx].words)
            self.lyric_lines[l_idx].line_end = max(w.end_time for w in self.lyric_lines[l_idx].words)
            self.update()
            return

        # 7. Playhead Scrubbing
        if self.is_dragging_playhead:
            t = self.x_to_time(x)
            self.time_seek_requested.emit(t)

    def mouseReleaseEvent(self, event):
        # 1. Finalize Marquee Box Selection
        if self.is_box_selecting and self.box_start_pt and self.box_curr_pt:
            box_rect = QRect(self.box_start_pt, self.box_curr_pt).normalized()
            selected = set()
            for idx, line in enumerate(self.lyric_lines):
                xs = self.time_to_x(line.line_start)
                xe = self.time_to_x(line.line_end)
                line_y = self.ruler_height + self.track_height * 4
                line_rect = QRect(int(xs), line_y, max(1, int(xe - xs)), self.track_height)
                if box_rect.intersects(line_rect):
                    selected.add(idx)
            if selected:
                self.selected_line_indices = selected
                self.selected_line_idx = min(selected)
                self.selected_type = 'line'
                self.line_selected.emit(self.selected_line_idx)
            self.is_box_selecting = False
            self.box_start_pt = None
            self.box_curr_pt = None
            self.update()
            return

        # 2. Finalize Line moves/trims
        if self.is_trimming_start or self.is_trimming_end or self.is_moving_line:
            self.lyric_lines.sort(key=lambda l: l.line_start)
            if self.moving_line_ref in self.lyric_lines:
                self.selected_line_idx = self.lyric_lines.index(self.moving_line_ref)
                self.selected_line_indices = {self.selected_line_idx}
            self.lyrics_modified.emit(self.lyric_lines)

        # 3. Finalize Media moves/trims
        if self.is_trimming_media_start or self.is_trimming_media_end or self.is_moving_media:
            self.media_clips.sort(key=lambda c: float(c.get('startTime', 0.0)))
            self.media_clips_modified.emit(self.media_clips)

        # 4. Finalize Word moves/trims
        if self.is_trimming_word_start or self.is_trimming_word_end or self.is_moving_word:
            self.lyrics_modified.emit(self.lyric_lines)

        # Reset all interaction flags & feedback elements
        self.is_trimming_start = False
        self.is_trimming_end = False
        self.is_moving_line = False
        self.move_line_idx = None
        self.moving_line_ref = None
        self.orig_selected_clip_data = []

        self.is_trimming_media_start = False
        self.is_trimming_media_end = False
        self.is_moving_media = False
        self.move_media_idx = None

        self.is_trimming_word_start = False
        self.is_trimming_word_end = False
        self.is_moving_word = False
        self.move_word_pos = None

        self.is_dragging_playhead = False
        self.snap_guideline_x = None
        self.drag_tooltip_text = None
        self.drag_tooltip_x = None
        self.drag_tooltip_y = None
        self.update()

    def contextMenuEvent(self, event):
        """CapCut Right-Click Context Menu for quick split, duplicate, delete, paste."""
        x = event.pos().x()
        t = self.x_to_time(x)

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px;
                color: #1e293b;
                font-size: 11px;
                font-weight: 600;
            }
            QMenu::item {
                padding: 6px 18px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #f1f5f9;
                color: #ff2d55;
            }
        """)

        act_split = menu.addAction("✂ Tách (Split) [Ctrl+B / S]")
        act_split.triggered.connect(lambda: (self.time_seek_requested.emit(t), self.split_at_playhead()))

        act_add_line = menu.addAction("＋ Thêm câu hát tại đây (Add Line)")
        act_add_line.triggered.connect(lambda: self.add_line_at(t))

        menu.addSeparator()

        if self.has_selection():
            act_dup = menu.addAction("📋 Nhân bản (Duplicate) [Ctrl+D]")
            act_dup.triggered.connect(self.duplicate_selected)

            act_copy = menu.addAction("📑 Sao chép (Copy) [Ctrl+C]")
            act_copy.triggered.connect(self.copy_selected)

            act_del = menu.addAction("🗑 Xóa (Delete) [Del]")
            act_del.triggered.connect(self.delete_selected)

            act_ripple = menu.addAction("🌊 Xóa gộp (Ripple Delete) [Shift+Del]")
            act_ripple.triggered.connect(self.ripple_delete_selected)

        act_paste = menu.addAction("📥 Dán tại đây (Paste) [Ctrl+V]")
        act_paste.triggered.connect(lambda: (setattr(self, 'current_time', t), self.paste_selected()))

        menu.exec_(event.globalPos())

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            if modifiers & Qt.ShiftModifier:
                self.ripple_delete_selected()
            else:
                self.delete_selected()
            event.accept()
        elif event.key() == Qt.Key_C and (modifiers & Qt.ControlModifier):
            self.copy_selected()
            event.accept()
        elif event.key() == Qt.Key_V and (modifiers & Qt.ControlModifier):
            self.paste_selected()
            event.accept()
        elif (event.key() == Qt.Key_B and (modifiers & Qt.ControlModifier)) or event.key() == Qt.Key_S:
            self.split_at_playhead()
            event.accept()
        elif event.key() == Qt.Key_D and (modifiers & Qt.ControlModifier):
            self.duplicate_selected()
            event.accept()
        elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
            self.add_line_at(self.current_time)
            event.accept()
        elif event.key() == Qt.Key_Space:
            w = self.window()
            if hasattr(w, 'toggle_playback'):
                w.toggle_playback()
            event.accept()
        elif event.key() == Qt.Key_Left:
            shift = 0.1 if (modifiers & Qt.ControlModifier) else 0.5
            self.time_seek_requested.emit(max(0.0, self.current_time - shift))
            event.accept()
        elif event.key() == Qt.Key_Right:
            shift = 0.1 if (modifiers & Qt.ControlModifier) else 0.5
            self.time_seek_requested.emit(min(self.duration, self.current_time + shift))
            event.accept()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.set_zoom(self.zoom_seconds * 0.85)
            else:
                self.set_zoom(self.zoom_seconds * 1.15)
            event.accept()
        else:
            delta = event.angleDelta().y()
            shift = (self.zoom_seconds * 0.1) * (-1 if delta > 0 else 1)
            self.scroll_horizontally(shift, user_initiated=True)
            event.accept()

    # Paint Engine
    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)

            painter.fillRect(self.rect(), QColor(241, 243, 249))

            # 1. Track alternating backgrounds
            y_cursor = self.ruler_height
            for idx in range(7):
                track_y = y_cursor
                track_rect = QRect(self.header_width, track_y, self.width() - self.header_width, self.track_height)
                painter.fillRect(track_rect, QColor(255, 255, 255) if idx % 2 == 0 else QColor(248, 250, 252))
                painter.setPen(QColor(226, 232, 240))
                painter.drawLine(self.header_width, track_y, self.width(), track_y)
                y_cursor += self.track_height

            # 2. Clips, ruler and playhead clipped to timeline area
            painter.save()
            content_rect = QRect(self.header_width, 0, max(0, self.width() - self.header_width), self.height())
            painter.setClipRect(content_rect)

            self.draw_time_ruler(painter)
            if self.layer_visibilities[0]:
                self.draw_layer_7_words(painter, self.ruler_height + self.track_height * 0)
            if self.layer_visibilities[1]:
                self.draw_layer_6_badge(painter, self.ruler_height + self.track_height * 1)
            if self.layer_visibilities[2]:
                self.draw_layer_5_badge(painter, self.ruler_height + self.track_height * 2)
            if self.layer_visibilities[3]:
                self.draw_layer_4_badge(painter, self.ruler_height + self.track_height * 3)
            if self.layer_visibilities[4]:
                self.draw_layer_3_lines(painter, self.ruler_height + self.track_height * 4)
            if self.layer_visibilities[5]:
                self.draw_layer_2_media(painter, self.ruler_height + self.track_height * 5)
            if self.layer_visibilities[6]:
                self.draw_layer_1_audio(painter, self.ruler_height + self.track_height * 6)

            self.draw_media_clips(painter)
            self.draw_playhead(painter)

            # Draw Magnetic Snap Guideline
            if self.snap_guideline_x is not None and self.snap_guideline_x >= self.header_width:
                painter.setPen(QPen(QColor("#00f5d4"), 1.5, Qt.DashLine))
                painter.drawLine(int(self.snap_guideline_x), 0, int(self.snap_guideline_x), self.height())

            # Draw Marquee Selection Box
            if self.is_box_selecting and self.box_start_pt and self.box_curr_pt:
                box_rect = QRect(self.box_start_pt, self.box_curr_pt).normalized()
                painter.fillRect(box_rect, QColor(56, 189, 248, 45))
                painter.setPen(QPen(QColor("#0284c7"), 1.5, Qt.DashLine))
                painter.drawRect(box_rect)

            # Draw Floating Timecode Tooltip
            if self.drag_tooltip_text and self.drag_tooltip_x is not None and self.drag_tooltip_y is not None:
                tip_w = 90
                tip_h = 22
                tip_x = max(self.header_width + 4, min(self.width() - tip_w - 4, int(self.drag_tooltip_x - tip_w / 2)))
                tip_y = max(2, int(self.drag_tooltip_y - tip_h - 4))
                tip_rect = QRectF(tip_x, tip_y, tip_w, tip_h)
                painter.setPen(QPen(QColor("#38bdf8"), 1.2))
                painter.setBrush(QColor("#0f172a"))
                painter.drawRoundedRect(tip_rect, 4, 4)
                painter.setFont(QFont("Consolas", 8, QFont.Bold))
                painter.setPen(QColor("#ffffff"))
                painter.drawText(tip_rect, Qt.AlignCenter, self.drag_tooltip_text)

            painter.restore()

            # 3. Fixed Left Header Column
            header_rect = QRect(0, 0, self.header_width, self.height())
            painter.fillRect(header_rect, QColor(241, 243, 249))
            painter.setPen(QColor(203, 213, 225))
            painter.drawLine(self.header_width, 0, self.header_width, self.height())

            # Top "Layers" Header
            painter.fillRect(QRect(0, 0, self.header_width, self.ruler_height), QColor(186, 192, 202))
            painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
            painter.setPen(QColor(30, 41, 59))
            painter.drawText(QRect(10, 0, self.header_width - 20, self.ruler_height), Qt.AlignVCenter | Qt.AlignLeft, "Layers")
            painter.setPen(QColor(160, 168, 178))
            painter.drawLine(0, self.ruler_height - 1, self.header_width, self.ruler_height - 1)

            layers = [
                ("Layer 7", "Words"),
                ("Layer 6", "Secondary"),
                ("Layer 5", "Subtitle"),
                ("Layer 4", "Lower 3rd"),
                ("Layer 3", "Lyrics"),
                ("Layer 2", "Media"),
                ("Layer 1", "Audio")
            ]

            y_cursor = self.ruler_height
            for idx, (l_name, _l_sub) in enumerate(layers):
                track_y = y_cursor
                row_rect = QRect(0, track_y, self.header_width, self.track_height)
                painter.fillRect(row_rect, QColor(255, 255, 255) if idx % 2 == 0 else QColor(248, 250, 252))

                painter.setFont(QFont("Segoe UI", 7))
                painter.setPen(QColor(148, 163, 184))
                painter.drawText(QRect(4, track_y, 14, self.track_height), Qt.AlignVCenter | Qt.AlignLeft, "⋮⋮")
                
                is_vis = self.layer_visibilities[idx]
                painter.setPen(QColor(71, 85, 105) if is_vis else QColor(203, 213, 225))
                painter.drawText(QRect(18, track_y, 14, self.track_height), Qt.AlignVCenter | Qt.AlignLeft, "👁" if is_vis else "🚫")
                
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                painter.setPen(QColor(30, 41, 59) if is_vis else QColor(148, 163, 184))
                painter.drawText(QRect(34, track_y, 58, self.track_height), Qt.AlignVCenter | Qt.AlignLeft, l_name)

                painter.setFont(QFont("Segoe UI", 7))
                painter.setPen(QColor(148, 163, 184))
                painter.drawText(QRect(self.header_width - 18, track_y, 14, self.track_height), Qt.AlignVCenter | Qt.AlignRight, "🗑")

                painter.setPen(QColor(226, 232, 240))
                painter.drawLine(0, track_y, self.header_width, track_y)
                painter.drawLine(0, track_y + self.track_height, self.header_width, track_y + self.track_height)
                y_cursor += self.track_height
        except Exception:
            pass
        finally:
            painter.end()

    def draw_time_ruler(self, painter: QPainter):
        ruler_rect = QRect(self.header_width, 0, self.width() - self.header_width, self.ruler_height)
        painter.save()
        painter.setClipRect(ruler_rect)
        painter.fillRect(ruler_rect, QColor(186, 192, 202))
        painter.setPen(QColor(160, 168, 178))
        painter.drawLine(self.header_width, self.ruler_height - 1, self.width(), self.ruler_height - 1)

        step = 5.0 if self.zoom_seconds <= 15 else (10.0 if self.zoom_seconds <= 45 else 20.0)
        start_sec = math.floor(self.scroll_offset / step) * step
        end_sec = self.scroll_offset + self.zoom_seconds

        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        t = start_sec
        while t <= end_sec:
            x = self.time_to_x(t)
            if x >= self.header_width + 18:
                painter.setPen(QColor(130, 138, 150))
                painter.drawLine(int(x), self.ruler_height - 5, int(x), self.ruler_height)
                mins = int(t) // 60
                secs = int(t) % 60
                ts_str = f"{mins:02d}:{secs:02d}"
                painter.setPen(QColor(30, 41, 59))
                painter.drawText(QRect(int(x) - 18, 0, 36, self.ruler_height - 4), Qt.AlignCenter, ts_str)
            elif x >= self.header_width:
                painter.setPen(QColor(130, 138, 150))
                painter.drawLine(int(x), self.ruler_height - 5, int(x), self.ruler_height)
            t += step
        painter.restore()

    def draw_layer_7_words(self, painter: QPainter, y: int):
        """Layer 7: Word syllable chips with CapCut active word highlights and trim boundaries."""
        h = self.track_height
        for l_idx, line in enumerate(self.lyric_lines):
            if line.line_end < self.scroll_offset or line.line_start > self.scroll_offset + self.zoom_seconds:
                continue
            x_line_s = self.time_to_x(line.line_start)
            x_line_e = self.time_to_x(line.line_end)
            w_line = max(8.0, x_line_e - x_line_s)
            
            # Purple background grouping block
            painter.setPen(QPen(QColor("#7c3aed"), 1.0))
            painter.setBrush(QColor("#7c3aed"))
            painter.drawRoundedRect(QRectF(x_line_s, y + 2, w_line, h - 4), 3, 3)

            painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
            for w_idx, word in enumerate(line.words):
                x_start = self.time_to_x(word.start_time)
                x_end = self.time_to_x(word.end_time)
                w = max(4.0, x_end - x_start - 1)
                chip_rect = QRectF(x_start, y + 3, w, h - 6)

                is_word_selected = (self.selected_type == 'word' and self.selected_word_pos == (l_idx, w_idx))
                is_active = (word.start_time <= self.current_time <= word.end_time)

                if is_word_selected:
                    painter.setPen(QPen(QColor("#00f5d4"), 2.0))
                    painter.setBrush(QColor("#9333ea"))
                    painter.drawRoundedRect(chip_rect, 3, 3)
                elif is_active:
                    painter.setPen(QPen(QColor("#facc15"), 1.2))
                    painter.setBrush(QColor("#9333ea"))
                    painter.drawRoundedRect(chip_rect, 2, 2)

                if w >= 8:
                    painter.setPen(QColor(255, 255, 255))
                    painter.drawText(chip_rect, Qt.AlignCenter, word.text.strip())

    def draw_layer_6_badge(self, painter: QPainter, y: int):
        """Layer 6: Secondary Line / Badge track."""
        h = self.track_height
        obj_text = self.overlay_objects[0].get('content', 'KARI') if (len(self.overlay_objects) > 0 and isinstance(self.overlay_objects[0], dict)) else 'KARI'
        x_s = self.time_to_x(1.5)
        x_e = self.time_to_x(7.5)
        w = max(36.0, x_e - x_s)
        rect = QRectF(x_s, y + 3, w, h - 6)

        painter.setPen(QPen(QColor("#6b21a8"), 1.0))
        painter.setBrush(QColor("#7c3aed"))
        painter.drawRoundedRect(rect, 3, 3)

        icon_r = (h - 10) / 2.0
        icon_cx = x_s + icon_r + 4
        icon_cy = y + h / 2.0
        painter.setPen(QPen(QColor(255, 255, 255, 200), 1.0))
        painter.setBrush(QColor("#9333ea"))
        painter.drawEllipse(QPointF(icon_cx, icon_cy), icon_r, icon_r)
        
        painter.setFont(QFont("Segoe UI", 6, QFont.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(QRectF(icon_cx - icon_r, icon_cy - icon_r, icon_r * 2, icon_r * 2), Qt.AlignCenter, "KA")

        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.drawText(QRectF(x_s + icon_r * 2 + 8, y + 3, w - (icon_r * 2 + 10), h - 6), Qt.AlignVCenter | Qt.AlignLeft, obj_text)

    def draw_layer_5_badge(self, painter: QPainter, y: int):
        """Layer 5: Subtitle chip."""
        h = self.track_height
        obj_text = self.overlay_objects[1].get('content', 'Mắt Em V...') if (len(self.overlay_objects) > 1 and isinstance(self.overlay_objects[1], dict)) else 'Mắt Em V...'
        x_s = self.time_to_x(1.5)
        x_e = self.time_to_x(7.5)
        w = max(42.0, x_e - x_s)
        rect = QRectF(x_s, y + 3, w, h - 6)

        painter.setPen(QPen(QColor("#6b21a8"), 1.0))
        painter.setBrush(QColor("#7c3aed"))
        painter.drawRoundedRect(rect, 3, 3)

        icon_r = (h - 10) / 2.0
        icon_cx = x_s + icon_r + 4
        icon_cy = y + h / 2.0
        painter.setPen(QPen(QColor(255, 255, 255, 200), 1.0))
        painter.setBrush(QColor("#9333ea"))
        painter.drawEllipse(QPointF(icon_cx, icon_cy), icon_r, icon_r)
        
        painter.setFont(QFont("Segoe UI", 6, QFont.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(QRectF(icon_cx - icon_r, icon_cy - icon_r, icon_r * 2, icon_r * 2), Qt.AlignCenter, "ME")

        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.drawText(QRectF(x_s + icon_r * 2 + 8, y + 3, w - (icon_r * 2 + 10), h - 6), Qt.AlignVCenter | Qt.AlignLeft, obj_text)

    def draw_layer_4_badge(self, painter: QPainter, y: int):
        """Layer 4: Lower Third graphic badge."""
        h = self.track_height
        obj_text = self.overlay_objects[2].get('content', 'Lower 3rd...') if (len(self.overlay_objects) > 2 and isinstance(self.overlay_objects[2], dict)) else 'Lower 3rd...'
        x_s = self.time_to_x(1.5)
        x_e = self.time_to_x(7.5)
        w = max(42.0, x_e - x_s)
        rect = QRectF(x_s, y + 3, w, h - 6)

        painter.setPen(QPen(QColor("#15803d"), 1.0))
        painter.setBrush(QColor("#16a34a"))
        painter.drawRoundedRect(rect, 3, 3)

        icon_r = (h - 10) / 2.0
        icon_cx = x_s + icon_r + 4
        icon_cy = y + h / 2.0
        painter.setPen(QPen(QColor(255, 255, 255, 200), 1.0))
        painter.setBrush(QColor("#22c55e"))
        painter.drawEllipse(QPointF(icon_cx, icon_cy), icon_r, icon_r)
        
        painter.setFont(QFont("Segoe UI", 6, QFont.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(QRectF(icon_cx - icon_r, icon_cy - icon_r, icon_r * 2, icon_r * 2), Qt.AlignCenter, "L3")

        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.drawText(QRectF(x_s + icon_r * 2 + 8, y + 3, w - (icon_r * 2 + 10), h - 6), Qt.AlignVCenter | Qt.AlignLeft, obj_text)

    def draw_layer_3_lines(self, painter: QPainter, y: int):
        """Layer 3: Main Active Lyric Lines with CapCut Selection Borders & Trim Handles."""
        h = self.track_height
        if self.lyric_lines:
            for idx, line in enumerate(self.lyric_lines):
                if line.line_end < self.scroll_offset or line.line_start > self.scroll_offset + self.zoom_seconds:
                    continue
                x_start = self.time_to_x(line.line_start)
                x_end = self.time_to_x(line.line_end)
                w = max(12.0, x_end - x_start)
                bar_rect = QRectF(x_start, y + 3, w, h - 6)

                is_selected = (self.selected_type == 'line' and (idx == self.selected_line_idx or idx in self.selected_line_indices))
                is_active = (line.line_start <= self.current_time <= line.line_end)

                painter.setPen(QPen(QColor("#00f5d4") if is_selected else QColor("#b45309"), 2.0 if is_selected else 1.0))
                painter.setBrush(QColor("#ea580c") if is_active or is_selected else QColor("#d97706"))
                painter.drawRoundedRect(bar_rect, 4, 4)

                # CapCut Trim Handles on selected clip
                if is_selected and w >= 20:
                    handle_w = 5.0
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor("#00f5d4"))
                    painter.drawRoundedRect(QRectF(x_start, y + 3, handle_w, h - 6), 2, 2)
                    painter.drawRoundedRect(QRectF(x_end - handle_w, y + 3, handle_w, h - 6), 2, 2)
                    # Grip notches
                    painter.setPen(QColor(0, 0, 0, 120))
                    painter.drawLine(int(x_start + 2), int(y + 8), int(x_start + 2), int(y + h - 8))
                    painter.drawLine(int(x_end - 3), int(y + 8), int(x_end - 3), int(y + h - 8))

                painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(bar_rect, Qt.AlignCenter, line.full_text)

            # CapCut "+" Add Line button after the last clip
            last_line = max(self.lyric_lines, key=lambda l: l.line_end)
            add_x = self.time_to_x(last_line.line_end) + 10
            if add_x < self.width() - 30:
                add_btn_rect = QRectF(add_x, y + 5, self.track_height - 10, self.track_height - 10)
                self.hover_add_rect = add_btn_rect
                self.hover_add_time = last_line.line_end + 0.5
                painter.setPen(QPen(QColor("#ff2d55"), 1.2))
                painter.setBrush(QColor("#fff1f2"))
                painter.drawEllipse(add_btn_rect)
                painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
                painter.setPen(QColor("#ff2d55"))
                painter.drawText(add_btn_rect, Qt.AlignCenter, "+")
        else:
            # Default placeholder lyric bar
            x_start = self.time_to_x(1.5)
            x_end = self.time_to_x(min(self.duration, 38.0))
            w = max(12.0, x_end - x_start)
            bar_rect = QRectF(x_start, y + 3, w, h - 6)
            painter.setPen(QPen(QColor("#b45309"), 1.0))
            painter.setBrush(QColor("#ea580c"))
            painter.drawRoundedRect(bar_rect, 3, 3)
            painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(bar_rect, Qt.AlignCenter, "Tuyệt Vời")

    def draw_layer_2_media(self, painter: QPainter, y: int):
        """Layer 2: Media Track background bar."""
        h = self.track_height
        x_start = self.time_to_x(0.0)
        track_dur = max(0.1, self.duration if self.duration > 0 else 38.0)
        x_end = self.time_to_x(track_dur)
        w = max(12.0, x_end - x_start)
        rect = QRectF(x_start, y + 3, w, h - 6)

        painter.setPen(QPen(QColor("#15803d"), 1.0))
        painter.setBrush(QColor("#16a34a"))
        painter.drawRoundedRect(rect, 3, 3)

        handle_w = 4.0
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#00f5d4"))
        painter.drawRoundedRect(QRectF(x_start, y + 3, handle_w, h - 6), 2, 2)
        painter.drawRoundedRect(QRectF(x_end - handle_w, y + 3, handle_w, h - 6), 2, 2)

        lbl = self.media_label if (self.media_label and self.media_label != "No background") else "Background Media"
        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(rect, Qt.AlignCenter, lbl)

    def draw_layer_1_audio(self, painter: QPainter, y: int):
        """Layer 1: Audio Track with Waveform."""
        h = self.track_height
        x_start = self.time_to_x(0.0)
        track_dur = max(0.1, self.duration if self.duration > 0 else 38.0)
        x_end = self.time_to_x(track_dur)
        w = max(12.0, x_end - x_start)
        rect = QRectF(x_start, y + 3, w, h - 6)

        painter.setPen(QPen(QColor("#0369a1"), 1.0))
        painter.setBrush(QColor("#0284c7"))
        painter.drawRoundedRect(rect, 3, 3)

        if self.waveform_peaks:
            painter.setPen(QColor(255, 255, 255, 140))
            num_pts = len(self.waveform_peaks)
            for idx, peak in enumerate(self.waveform_peaks):
                t = (idx / float(num_pts)) * self.duration
                px = self.time_to_x(t)
                if x_start <= px <= x_end:
                    bar_h = max(2, int(peak * (h - 8)))
                    py1 = y + (h - bar_h) // 2
                    painter.drawLine(int(px), py1, int(px), py1 + bar_h)

        lbl = self.audio_label if (self.audio_label and self.audio_label != "No audio") else "Audio Track"
        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(rect, Qt.AlignCenter, lbl)

    def draw_media_clips(self, painter):
        """Render individual media clips on tracks with CapCut selection borders & trim handles."""
        colors = {'audio': QColor('#86efac'), 'video': QColor('#fdba74'), 'image': QColor('#93c5fd')}
        for idx, clip in enumerate(self.media_clips):
            asset = self.media_assets.get(str(clip.get('assetId')), {})
            kind = asset.get('type', 'image')
            row = 6 if kind == 'audio' else 5
            start = float(clip.get('startTime', 0.0))
            end = start + float(clip.get('duration', 0.0))
            x1, x2 = self.time_to_x(start), self.time_to_x(end)
            rect = QRectF(x1, self.ruler_height + self.track_height * row + 3, max(6.0, x2 - x1), self.track_height - 6)

            is_selected = (self.selected_type == 'media' and self.selected_media_clip_idx == idx)
            clip_color = colors.get(kind, QColor('#cbd5e1'))

            painter.setPen(QPen(QColor('#00f5d4') if is_selected else clip_color.darker(120), 2.0 if is_selected else 1.0))
            painter.setBrush(clip_color)
            painter.drawRoundedRect(rect, 4, 4)

            # CapCut Trim Handles on selected media clip
            if is_selected and rect.width() >= 16:
                handle_w = 4.0
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor('#00f5d4'))
                painter.drawRoundedRect(QRectF(x1, rect.y(), handle_w, rect.height()), 2, 2)
                painter.drawRoundedRect(QRectF(x2 - handle_w, rect.y(), handle_w, rect.height()), 2, 2)

            painter.setPen(QColor('#1e293b'))
            painter.setFont(QFont('Segoe UI', 8, QFont.Bold))
            painter.drawText(rect.adjusted(6, 0, -4, 0), Qt.AlignVCenter | Qt.TextSingleLine, str(asset.get('name', kind)))

    def draw_playhead(self, painter: QPainter):
        x = self.time_to_x(self.current_time)
        if x < self.header_width:
            return

        painter.save()
        painter.setClipRect(QRect(self.header_width, 0, self.width() - self.header_width, self.height()))

        painter.setPen(QPen(QColor("#ff0033"), 2.0))
        painter.drawLine(int(x), 0, int(x), self.height())

        handle_poly = QPolygonF([
            QPointF(x - 5, 0),
            QPointF(x + 5, 0),
            QPointF(x + 5, 8),
            QPointF(x, 14),
            QPointF(x - 5, 8)
        ])
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#ff0033"))
        painter.drawPolygon(handle_poly)

        # Drop preview guideline and badge
        if self.drop_preview_time is not None:
            drop_x = self.time_to_x(self.drop_preview_time)
            if drop_x >= self.header_width:
                painter.setPen(QPen(QColor("#ff2d55"), 2, Qt.DashLine))
                painter.drawLine(QPointF(drop_x, self.ruler_height), QPointF(drop_x, self.height()))

                badge_w = 76
                badge_h = 20
                badge_rect = QRectF(drop_x - badge_w / 2, self.ruler_height + 2, badge_w, badge_h)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor("#ff2d55"))
                painter.drawRoundedRect(badge_rect, 4, 4)
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                painter.setPen(QColor(255, 255, 255))
                m, s = int(self.drop_preview_time // 60), int(self.drop_preview_time % 60)
                painter.drawText(badge_rect, Qt.AlignCenter, f"＋ {m:02d}:{s:02d}")

        painter.restore()


class TimelineWidget(QWidget):
    time_seek_requested = pyqtSignal(float)
    lyrics_modified = pyqtSignal(list)
    media_clips_modified = pyqtSignal(list)
    line_selected = pyqtSignal(int)
    add_layer_requested = pyqtSignal()
    play_pause_requested = pyqtSignal()
    step_back_requested = pyqtSignal()
    step_forward_requested = pyqtSignal()
    media_asset_dropped = pyqtSignal(object, float)
    media_files_dropped = pyqtSignal(list, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(0)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. CapCut Edit Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0; padding: 2px 6px;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(6, 3, 6, 3)
        tb_layout.setSpacing(6)

        btn_style = """
            QPushButton {
                background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px;
                color: #334155; font-size: 10px; font-weight: 700; padding: 4px 8px;
            }
            QPushButton:hover { background: #fff1f2; color: #ff2d55; border-color: #fecdd3; }
        """

        self.btn_split = QPushButton("✂ Split (Tách)")
        self.btn_split.setStyleSheet(btn_style)
        self.btn_split.setToolTip("Tách clip tại vị trí kim phát (Ctrl+B / S)")
        self.btn_split.clicked.connect(self.split_line)
        tb_layout.addWidget(self.btn_split)

        self.btn_delete = QPushButton("🗑 Delete (Xóa)")
        self.btn_delete.setStyleSheet(btn_style)
        self.btn_delete.setToolTip("Xóa clip/câu hát đang chọn (Delete)")
        self.btn_delete.clicked.connect(self.delete_line)
        tb_layout.addWidget(self.btn_delete)

        self.btn_duplicate = QPushButton("📋 Duplicate")
        self.btn_duplicate.setStyleSheet(btn_style)
        self.btn_duplicate.setToolTip("Nhân bản clip đang chọn (Ctrl+D)")
        self.btn_duplicate.clicked.connect(self.duplicate_line)
        tb_layout.addWidget(self.btn_duplicate)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Plain)
        tb_layout.addWidget(separator)

        self.btn_copy = QPushButton("Copy")
        self.btn_copy.setStyleSheet(btn_style)
        self.btn_copy.setToolTip("Sao chép clip đang chọn (Ctrl+C)")
        self.btn_copy.clicked.connect(self.copy_lines)
        tb_layout.addWidget(self.btn_copy)

        self.btn_paste = QPushButton("Paste")
        self.btn_paste.setStyleSheet(btn_style)
        self.btn_paste.setToolTip("Dán clip tại vị trí kim phát (Ctrl+V)")
        self.btn_paste.clicked.connect(self.paste_lines)
        tb_layout.addWidget(self.btn_paste)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Plain)
        tb_layout.addWidget(separator)

        self.btn_ripple = QPushButton("Ripple")
        self.btn_ripple.setStyleSheet(btn_style)
        self.btn_ripple.setToolTip("Xóa gộp và thu hẹp khoảng trống (Shift+Delete)")
        self.btn_ripple.clicked.connect(self.ripple_delete_lines)
        tb_layout.addWidget(self.btn_ripple)

        self.btn_beats = QPushButton("⚡ Beats")
        self.btn_beats.setCheckable(True)
        self.btn_beats.setChecked(True)
        self.btn_beats.setStyleSheet("""
            QPushButton {
                background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px;
                color: #334155; font-size: 10px; font-weight: 700; padding: 4px 8px;
            }
            QPushButton:checked { background: #fef08a; color: #854d0e; border-color: #facc15; }
        """)
        self.btn_beats.clicked.connect(self.toggle_beats)
        tb_layout.addWidget(self.btn_beats)

        self.btn_snap = QPushButton("🧲 Snap")
        self.btn_snap.setCheckable(True)
        self.btn_snap.setChecked(True)
        self.btn_snap.setStyleSheet("""
            QPushButton {
                background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px;
                color: #334155; font-size: 10px; font-weight: 700; padding: 4px 8px;
            }
            QPushButton:checked { background: #e0f2fe; color: #0369a1; border-color: #7dd3fc; }
        """)
        self.btn_snap.clicked.connect(self.toggle_snap)
        tb_layout.addWidget(self.btn_snap)

        self.btn_follow = QPushButton("⇥ Follow")
        self.btn_follow.setCheckable(True)
        self.btn_follow.setChecked(True)
        self.btn_follow.setToolTip("Tự động cuộn theo kim phát khi đang phát nhạc")
        self.btn_follow.setStyleSheet("""
            QPushButton {
                background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px;
                color: #334155; font-size: 10px; font-weight: 700; padding: 4px 8px;
            }
            QPushButton:checked { background: #ecfdf5; color: #047857; border-color: #6ee7b7; }
        """)
        self.btn_follow.clicked.connect(self.toggle_follow_playhead)
        tb_layout.addWidget(self.btn_follow)

        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Plain)
        tb_layout.addWidget(separator)

        tb_layout.addStretch()

        # CapCut "+" Add Line button in toolbar
        self.btn_add_line = QPushButton("＋ Dòng (Line)")
        self.btn_add_line.setStyleSheet("""
            QPushButton {
                background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 4px;
                color: #047857; font-size: 10px; font-weight: 700; padding: 4px 8px;
            }
            QPushButton:hover { background: #d1fae5; }
        """)
        self.btn_add_line.setToolTip("Thêm câu hát mới tại vị trí kim phát (+)")
        self.btn_add_line.clicked.connect(lambda: self.canvas.add_line_at(self.canvas.current_time))
        tb_layout.addWidget(self.btn_add_line)

        self.btn_add_layer = QPushButton("＋ Layer")
        self.btn_add_layer.setStyleSheet("""
            QPushButton {
                background: #fff1f2; border: 1px solid #fecdd3; border-radius: 4px;
                color: #ff2d55; font-size: 10px; font-weight: 700; padding: 4px 8px;
            }
            QPushButton:hover { background: #ffe4e6; }
        """)
        self.btn_add_layer.setToolTip("Thêm Layer / Vật thể mới vào Canvas")
        self.btn_add_layer.clicked.connect(self.add_layer_requested.emit)
        tb_layout.addWidget(self.btn_add_layer)

        btn_zoom_out = QPushButton("")
        btn_zoom_out.setFixedSize(28, 28)
        btn_zoom_out.setStyleSheet(btn_style)
        btn_zoom_out.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))
        btn_zoom_out.setIconSize(QSize(16, 16))
        btn_zoom_out.setToolTip("Zoom Out Timeline")
        btn_zoom_out.clicked.connect(lambda: self.adjust_zoom(1.2))
        tb_layout.addWidget(btn_zoom_out)

        self.slider_zoom = QSlider(Qt.Horizontal)
        self.slider_zoom.setFixedWidth(65)
        self.slider_zoom.setRange(4, 45)
        self.slider_zoom.setValue(10)
        self.slider_zoom.valueChanged.connect(lambda v: self.set_zoom(float(v)))
        tb_layout.addWidget(self.slider_zoom)

        self.lbl_zoom_val = QLabel("10s")
        self.lbl_zoom_val.setStyleSheet("color: #64748b; font-family: monospace; font-size: 10px; font-weight: bold;")
        tb_layout.addWidget(self.lbl_zoom_val)

        btn_zoom_in = QPushButton("")
        btn_zoom_in.setFixedSize(28, 28)
        btn_zoom_in.setStyleSheet(btn_style)
        btn_zoom_in.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))
        btn_zoom_in.setIconSize(QSize(16, 16))
        btn_zoom_in.setToolTip("Zoom In Timeline")
        btn_zoom_in.clicked.connect(lambda: self.adjust_zoom(0.8))
        tb_layout.addWidget(btn_zoom_in)

        self.btn_fit_timeline = QPushButton("Fit Timeline")
        self.btn_fit_timeline.setStyleSheet(btn_style)
        self.btn_fit_timeline.setToolTip("Fit Timeline")
        self.btn_fit_timeline.clicked.connect(self.fit_timeline)
        tb_layout.addWidget(self.btn_fit_timeline)

        main_layout.addWidget(toolbar)

        # 2. Canvas
        self.canvas = TimelineCanvas(self)
        self.canvas.time_seek_requested.connect(self.time_seek_requested.emit)
        self.canvas.lyrics_modified.connect(self.lyrics_modified.emit)
        self.canvas.media_clips_modified.connect(self.media_clips_modified.emit)
        self.canvas.line_selected.connect(self.line_selected.emit)
        self.canvas.media_asset_dropped.connect(self.media_asset_dropped.emit)
        self.canvas.media_files_dropped.connect(self.media_files_dropped.emit)
        main_layout.addWidget(self.canvas, stretch=1)

    def split_line(self):
        self.canvas.split_at_playhead()

    def delete_line(self):
        self.canvas.delete_selected()

    def duplicate_line(self):
        self.canvas.duplicate_selected()

    def copy_lines(self):
        self.canvas.copy_selected()

    def paste_lines(self):
        self.canvas.paste_selected()

    def ripple_delete_lines(self):
        self.canvas.ripple_delete_selected()

    def toggle_beats(self):
        self.canvas.beats_enabled = self.btn_beats.isChecked()
        self.canvas.update()

    def toggle_snap(self):
        self.canvas.snap_enabled = self.btn_snap.isChecked()

    def toggle_follow_playhead(self):
        self.canvas.set_follow_playhead(self.btn_follow.isChecked())

    def adjust_zoom(self, factor: float):
        new_zoom = max(4.0, min(45.0, self.canvas.zoom_seconds * factor))
        self.slider_zoom.setValue(int(new_zoom))
        self.set_zoom(new_zoom)

    def fit_timeline(self):
        self.set_zoom(max(4.0, min(45.0, float(self.canvas.duration))))

    def set_duration(self, duration: float):
        self.canvas.set_duration(duration)

    def set_lyrics(self, lines: List[LyricLine]):
        self.canvas.set_lyrics(lines)

    def set_waveform(self, peaks: list):
        self.canvas.set_waveform(peaks)

    def set_beat_times(self, beat_times: list):
        self.canvas.set_beat_times(beat_times)

    def set_language(self, english: bool):
        if english:
            self.btn_split.setText("✂ Split")
            self.btn_delete.setText("🗑 Delete")
            self.btn_duplicate.setText("📋 Duplicate")
            self.btn_copy.setText("Copy")
            self.btn_paste.setText("Paste")
            self.btn_ripple.setText("Ripple")
            self.btn_beats.setText("⚡ Beats")
            self.btn_snap.setText("🧲 Snap")
            self.btn_follow.setText("⇥ Follow")
            self.btn_add_line.setText("＋ Line")
            self.btn_add_layer.setText("＋ Layer")
        else:
            self.btn_split.setText("✂ Tách (Split)")
            self.btn_delete.setText("🗑 Xóa (Delete)")
            self.btn_duplicate.setText("📋 Nhân bản")
            self.btn_copy.setText("Sao chép")
            self.btn_paste.setText("Dán")
            self.btn_ripple.setText("Xóa gộp")
            self.btn_beats.setText("⚡ Bắt Beat")
            self.btn_snap.setText("🧲 Hút dính")
            self.btn_follow.setText("⇥ Bám kim phát")
            self.btn_add_line.setText("＋ Dòng (Line)")
            self.btn_add_layer.setText("＋ Layer")

    def set_current_time(self, current_time: float, is_playing=None, reveal=False):
        self.canvas.set_current_time(current_time, is_playing=is_playing, reveal=reveal)

    def set_playback_active(self, active: bool):
        self.canvas.set_playback_active(active)

    def set_layer_visibility(self, layer_index: int, visible: bool):
        if 0 <= int(layer_index) < len(self.canvas.layer_visibilities):
            self.canvas.layer_visibilities[int(layer_index)] = bool(visible)
            self.canvas.update()

    def layer_visibility(self, layer_index: int) -> bool:
        if 0 <= int(layer_index) < len(self.canvas.layer_visibilities):
            return bool(self.canvas.layer_visibilities[int(layer_index)])
        return False

    def set_zoom(self, zoom_seconds: float):
        self.canvas.set_zoom(zoom_seconds)
        if hasattr(self, 'lbl_zoom_val'):
            self.lbl_zoom_val.setText(f"{int(zoom_seconds)}s")

    def set_overlay_objects(self, objects: list):
        self.canvas.set_overlay_objects(objects)

    def set_effects(self, effects: dict):
        self.canvas.set_effects(effects)

    def set_transitions(self, transitions: dict):
        self.canvas.set_transitions(transitions)

    def set_media_labels(self, background: str = None, audio: str = None):
        self.canvas.set_media_labels(background, audio)

    def set_media_clips(self, clips, assets=None):
        self.canvas.set_media_clips(clips, assets)
