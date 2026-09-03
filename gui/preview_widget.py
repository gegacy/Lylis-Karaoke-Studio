"""
Lylis Karaoke Studio - Exact Reference QPainter Preview Canvas
Matches all Lylis.app Studio Visuals:
- COLOR CODED Mode: Top 4 Singer Portrait Header Banner (Phùng Minh Cường, Tùng Mint, Nguyễn Văn Chung, Neko Lê), Center Lyric with Golden Amber Glow and Italic Script styling (Screenshot 6)
- KARAOKE Mode: Dual-Line Staggered Karaoke (Top line 66% left-aligned, Bottom line 78% right-aligned with 7.5% padding) and Singer Avatar Badges (Screenshots 1-3)
- Interactive Overlay Text Objects with Transform Bounding Box (Screenshot 4)
- Watermark 'MADE WITH lylis.app' + Fullscreen Expand Icon
"""
import os
import math
import random
from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QPainterPath, 
    QPen, QBrush, QLinearGradient, QRadialGradient, QConicalGradient, QPixmap, QImage, QPolygonF
)
from PyQt5.QtCore import Qt, QRect, QRectF, QPointF, pyqtSignal
from core.lrc_engine import LyricLine
from core.media_timing import looping_frame_index

class PreviewWidget(QWidget):
    object_selected = pyqtSignal(dict)
    objects_changed = pyqtSignal()
    album_track_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(440, 320)
        self.setMouseTracking(True)
        
        self.aspect_ratio = '16:9'
        self.preview_zoom = 0.0  # 0 means Fit; other values are scale factors.
        self.display_mode = "COLOR CODED" # "COLOR CODED" | "KARAOKE" | "ROW" | "SINGLE" | "BUILD"
        self.template_variant = ""
        self.track_title = "Song Title"
        self.track_artist = "Artist"
        self.portrait_focus_y = 25
        self.uppercase_lyrics = False
        self.current_time = 0.0
        self.duration = 45.0
        self.lyric_lines: List[LyricLine] = []
        self.bg_pixmap: QPixmap = None
        self.bg_video_reader = None
        self.bg_video_path = None
        self.bg_video_fps = 30.0
        self.bg_video_duration = 0.0
        self.bg_video_frame_count = 0.0
        self._video_frame_index = -1
        self.album_cover_path = ""
        self.album_cover_pixmap = QPixmap()
        self.album_tracks = []
        self.album_track_ids = []
        self.active_album_track_id = None
        self.album_title = "My Album"
        self.spectrum_bands: list = [0.0] * 32
        self.waveform_peaks: list = []

        # Typography & Style configurations matching exact reference screenshots
        self.font_family = "Playwrite IS"
        self.font_weight_str = "400 Thường"
        self.font_size = 42
        self.is_bold = False
        self.is_italic = False
        self.layout_mode = "left_right"
        self.fill_mode = "word"
        self.singer_mode = "song_ca"
        
        self.padding_x_percent = 7.5
        self.pos_y_top = 66.0
        self.pos_y_bottom = 78.0
        self.stroke_width = 3.5
        
        # Colors matching exact reference
        self.base_color = QColor("#ffffff")
        self.stroke_color = QColor(0, 0, 0, 245)
        self.active_color = QColor("#f59e0b")    # Amber Gold (#f59e0b / #ff9900)
        self.male_color = QColor("#0026ff")      # Deep Royal Electric Blue
        self.female_color = QColor("#ff0033")    # Crimson Red
        self.both_color = QColor("#ff007f")      # Magenta Pink

        # Custom Singers for COLOR CODED mode (Screenshot)
        self.custom_singers = [
            {"name": "Phùng Minh Cường", "color": "#3b82f6", "avatar": "👤"},
            {"name": "Tùng Mint", "color": "#f59e0b", "avatar": "👤"},
            {"name": "Nguyễn Văn Chung", "color": "#10b981", "avatar": "👤"},
            {"name": "Neko Lê", "color": "#ef4444", "avatar": "👤"}
        ]

        # Visual Overlays & Effects
        self.enable_particles = False
        self.particle_type = "Bokeh Orbs"
        self.enable_visualizer = False
        self.enable_pointer = True
        self.enable_watermark = False
        
        self.vignette_percent = 0
        self.enable_glow = True
        self.glow_radius = 8
        self.color_tint = "None (Original)"
        self.pointer_icon = "🎤"
        self.pointer_icons = {"male": "👨", "female": "👩", "both": "🎤"}
        self.motion_effect = "Pop & Bounce"
        self.transitions = {"start": None, "end": None}

        # Retro 90s Pop-Art Singer Icons (Male, Female, Both)
        self.retro_icons = {}
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_dir = os.path.join(base_dir, "assets", "icons")
        for role, fname in [("male", "male_retro.png"), ("female", "female_retro.png"), ("both", "both_retro.png")]:
            fpath = os.path.join(icon_dir, fname)
            if os.path.exists(fpath):
                self.retro_icons[role] = QPixmap(fpath)

        # Interactive Overlay Objects (Screenshot 4)
        self.overlay_objects: List[Dict[str, Any]] = []
        self.selected_object_idx: Optional[int] = None
        self.is_dragging_object = False
        self.interaction_mode = None
        self.drag_start_pos = None
        self._snap_x = False
        self._snap_y = False
        self.show_safe_area = False

        # 60 FPS Particle Simulation Pool
        self.particles = []
        for _ in range(36):
            self.particles.append({
                'x': random.uniform(0.0, 1.0),
                'y': random.uniform(0.0, 1.0),
                'size': random.uniform(8.0, 20.0),
                'speed': random.uniform(0.001, 0.0035),
                'opacity': random.uniform(0.3, 0.85),
                'phase': random.uniform(0, math.pi * 2)
            })

    def set_aspect_ratio(self, ratio_str: str):
        if self.is_valid_aspect_ratio(ratio_str):
            self.aspect_ratio = ratio_str.strip()
            self.update()

    @staticmethod
    def is_valid_aspect_ratio(ratio_str: str) -> bool:
        try:
            width, height = (float(part.strip()) for part in str(ratio_str).split(":", 1))
            return 0.0 < width <= 1000.0 and 0.0 < height <= 1000.0
        except (TypeError, ValueError):
            return False

    def set_preview_zoom(self, zoom: float):
        self.preview_zoom = max(0.0, min(1.0, float(zoom)))
        self.update()

    def set_background(self, filepath: str):
        self._close_video_reader()
        self.bg_pixmap = None
        self.bg_video_path = None
        if filepath:
            extension = os.path.splitext(filepath)[1].lower()
            if extension in {'.mp4', '.mov', '.mkv', '.avi', '.webm'}:
                try:
                    import imageio.v2 as imageio
                    self.bg_video_reader = imageio.get_reader(filepath)
                    metadata = self.bg_video_reader.get_meta_data()
                    self.bg_video_fps = max(1.0, float(metadata.get('fps', 30.0)))
                    self.bg_video_duration = float(metadata.get('duration', 0.0) or 0.0)
                    self.bg_video_frame_count = float(metadata.get('nframes', 0.0) or 0.0)
                    self.bg_video_path = filepath
                    self._update_video_frame(force=True)
                except Exception:
                    self._close_video_reader()
            else:
                pixmap = QPixmap(filepath)
                self.bg_pixmap = pixmap if not pixmap.isNull() else None
        self.update()

    def _close_video_reader(self):
        if self.bg_video_reader is not None:
            try:
                self.bg_video_reader.close()
            except Exception:
                pass
        self.bg_video_reader = None
        self._video_frame_index = -1
        self.bg_video_duration = 0.0
        self.bg_video_frame_count = 0.0

    def _update_video_frame(self, force=False):
        if self.bg_video_reader is None:
            return
        frame_index = looping_frame_index(
            self.current_time,
            self.bg_video_fps,
            self.bg_video_duration,
            self.bg_video_frame_count,
        )
        if not force and frame_index == self._video_frame_index:
            return
        try:
            frame = self.bg_video_reader.get_data(frame_index)
        except Exception:
            try:
                frame = self.bg_video_reader.get_data(0)
                frame_index = 0
            except Exception:
                return
        if len(frame.shape) != 3:
            return
        height, width, channels = frame.shape
        image_format = QImage.Format_RGBA8888 if channels == 4 else QImage.Format_RGB888
        qimage = QImage(frame.data, width, height, frame.strides[0], image_format).copy()
        self.bg_pixmap = QPixmap.fromImage(qimage)
        self._video_frame_index = frame_index

    def set_lyrics(self, lines: List[LyricLine]):
        self.lyric_lines = lines
        self.update()

    def set_waveform(self, peaks: list):
        """Provide normalized audio peaks for audio-reactive template stages."""
        self.waveform_peaks = [max(0.0, min(1.0, float(value))) for value in (peaks or [])]
        self.update()

    def add_overlay_object(self, obj: dict):
        self.overlay_objects.append(obj)
        self.selected_object_idx = len(self.overlay_objects) - 1
        self.object_selected.emit(obj)
        self.update()

    def update_selected_object(self, props: dict):
        if self.selected_object_idx is not None and 0 <= self.selected_object_idx < len(self.overlay_objects):
            self.overlay_objects[self.selected_object_idx].update(props)
            self.update()

    def update_playback(self, current_time: float, duration: float, spectrum_bands: list = None):
        self.current_time = current_time
        self.duration = max(1.0, duration)
        self._update_video_frame()
        if spectrum_bands is not None:
            self.spectrum_bands = spectrum_bands
        self.update()

    def set_transitions(self, transitions: dict):
        self.transitions = dict(transitions or {"start": None, "end": None})
        self.update()

    def delete_selected_object(self):
        if self.selected_object_idx is None:
            return None
        if 0 <= self.selected_object_idx < len(self.overlay_objects):
            removed = self.overlay_objects.pop(self.selected_object_idx)
            self.selected_object_idx = None
            self.update()
            return removed
        return None

    def get_viewport_rect(self) -> QRect:
        """Computes the aspect ratio viewport matching exact canvas card."""
        w = self.width() - 20
        h = self.height() - 20
        
        try:
            ratio_width, ratio_height = (float(part.strip()) for part in self.aspect_ratio.split(":", 1))
            target_ratio = ratio_width / ratio_height
        except (AttributeError, TypeError, ValueError, ZeroDivisionError):
            target_ratio = 16.0 / 9.0
            
        view_w = w
        view_h = int(w / target_ratio)
        if view_h > h:
            view_h = h
            view_w = int(h * target_ratio)
        if self.preview_zoom > 0.0:
            view_w = max(1, min(view_w, int(1920 * self.preview_zoom)))
            view_h = max(1, min(view_h, int(view_w / target_ratio)))
            
        x = 10 + (w - view_w) // 2
        y = 10 + (h - view_h) // 2
        return QRect(x, y, view_w, view_h)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            painter.fillRect(self.rect(), QColor(241, 243, 249))

            v_rect = self.get_viewport_rect()
            if v_rect.width() < 10 or v_rect.height() < 10:
                return
            
            # Rounded Canvas Path for smooth clipping & shadow
            clip_path = QPainterPath()
            clip_path.addRoundedRect(QRectF(v_rect), 12, 12)

            # Soft drop shadow under the canvas container
            painter.save()
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 25))
            painter.drawRoundedRect(QRectF(v_rect.x() + 2, v_rect.y() + 4, v_rect.width(), v_rect.height()), 12, 12)
            painter.restore()

            painter.save()
            painter.setClipPath(clip_path)
            painter.fillRect(v_rect, QColor(0, 0, 0))
            painter.restore()
            painter.save()
            painter.setClipPath(clip_path)
            self.apply_scene_transition(painter, v_rect)

            # 1. Draw Background Image / Video
            if self.bg_pixmap and not self.bg_pixmap.isNull():
                scaled = self.bg_pixmap.scaled(
                    v_rect.size(),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
                sx = (scaled.width() - v_rect.width()) // 2
                sy = (scaled.height() - v_rect.height()) // 2
                painter.drawPixmap(v_rect.x(), v_rect.y(), scaled, sx, sy, v_rect.width(), v_rect.height())
            else:
                grad = QLinearGradient(v_rect.topLeft(), v_rect.bottomLeft())
                grad.setColorAt(0.0, QColor(245, 245, 247))
                grad.setColorAt(1.0, QColor(228, 231, 236))
                painter.fillRect(v_rect, grad)

            self.draw_color_tint(painter, v_rect)

            # 2. Atmospheric Particle Simulation Engine
            if self.enable_particles:
                self.draw_atmospheric_particles(painter, v_rect)

            if self.enable_visualizer:
                self.draw_audio_visualizer(painter, v_rect)

            # 3. COLOR CODED Mode: Top Singer Portrait Cards Banner (Screenshot 6)
            if self.template_variant == "multi_song_album":
                self.draw_multi_song_album_stage(painter, v_rect)
            elif self.template_variant == "ambient_album_player":
                self.draw_ambient_album_stage(painter, v_rect)
            elif self.template_variant == "walters_lyric_queue":
                self.draw_walters_lyric_queue_stage(painter, v_rect)
            elif self.template_variant == "ksector_2000s_editorial":
                self.draw_ksector_2000s_stage(painter, v_rect)
            elif self.template_variant == "falling_u_douyin_dj":
                self.draw_falling_u_douyin_stage(painter, v_rect)
            elif self.template_variant == "eminem_rap_hiphop_album":
                self.draw_eminem_rap_hiphop_stage(painter, v_rect)
            elif self.display_mode == "COLOR CODED":
                if self.template_variant == "tiki_tiki":
                    self.draw_tiki_tiki_stage(painter, v_rect)
                else:
                    self.draw_singer_banner(painter, v_rect)

            # 4. Custom Overlay Objects (Screenshot 4)
            if self.show_safe_area:
                self.draw_safe_area_guides(painter, v_rect)
            self.draw_overlay_objects(painter, v_rect)

            # 5. Lyric Text (COLOR CODED Golden Center Script vs KARAOKE Staggered)
            if self.template_variant == "multi_song_album":
                self.draw_multi_song_album_lyrics(painter, v_rect)
            elif self.template_variant == "ambient_album_player":
                self.draw_ambient_album_lyrics(painter, v_rect)
            elif self.template_variant == "walters_lyric_queue":
                self.draw_walters_lyric_queue(painter, v_rect)
            elif self.template_variant == "ksector_2000s_editorial":
                self.draw_ksector_2000s_lyrics(painter, v_rect)
            elif self.template_variant == "falling_u_douyin_dj":
                self.draw_falling_u_douyin_lyrics(painter, v_rect)
            elif self.template_variant == "eminem_rap_hiphop_album":
                self.draw_eminem_rap_hiphop_lyrics(painter, v_rect)
            elif self.display_mode == "COLOR CODED":
                if self.template_variant == "tiki_tiki":
                    self.draw_tiki_tiki_lyrics(painter, v_rect)
                else:
                    self.draw_color_coded_lyrics(painter, v_rect)
            else:
                self.draw_karaoke_lyrics(painter, v_rect)

            self.draw_vignette(painter, v_rect)

            if self.enable_watermark:
                self.draw_watermark(painter, v_rect)

            painter.restore()

            # Canvas Border Stroke
            painter.setPen(QPen(QColor(226, 232, 240), 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(QRectF(v_rect), 12, 12)
        finally:
            painter.end()

    def apply_scene_transition(self, painter: QPainter, v_rect: QRect):
        for position in ('start', 'end'):
            transition = self.transitions.get(position) if self.transitions else None
            if not transition:
                continue
            seconds = max(0.1, float(transition.get('duration', 1.5)))
            amount = (self.current_time / seconds) if position == 'start' else ((self.duration - self.current_time) / seconds)
            amount = max(0.0, min(1.0, amount))
            if amount >= 1.0:
                continue
            name = str(transition.get('name', 'Fade'))
            if 'Slide' in name:
                direction = 1.0 if position == 'start' else -1.0
                painter.translate(direction * v_rect.width() * (1.0 - amount), 0)
            elif 'Zoom' in name:
                scale = 0.85 + 0.15 * amount
                center = v_rect.center()
                painter.translate(center.x(), center.y())
                painter.scale(scale, scale)
                painter.translate(-center.x(), -center.y())
            else:
                painter.setOpacity(painter.opacity() * amount)

    def draw_color_tint(self, painter: QPainter, v_rect: QRect):
        # 1. CapCut Color Filters
        tint = self.color_tint
        if 'Cinematic' in tint or 'Teal' in tint:
            grad = QLinearGradient(v_rect.topLeft(), v_rect.bottomRight())
            grad.setColorAt(0.0, QColor(0, 180, 216, 40))
            grad.setColorAt(1.0, QColor(247, 127, 0, 35))
            painter.fillRect(v_rect, grad)
        elif 'VHS' in tint or 'Retro' in tint:
            painter.fillRect(v_rect, QColor(250, 204, 21, 28))
        elif 'Pastel' in tint or 'Lofi' in tint:
            painter.fillRect(v_rect, QColor(244, 114, 182, 30))
        elif 'Cyberpunk' in tint or 'Neon' in tint:
            painter.fillRect(v_rect, QColor(0, 210, 255, 36))
        elif 'Moody' in tint or 'Noir' in tint or 'Dark' in tint:
            painter.fillRect(v_rect, QColor(10, 15, 30, 90))
        elif 'Vintage' in tint or 'Gold' in tint or 'Warm' in tint:
            painter.fillRect(v_rect, QColor(245, 158, 11, 35))
        elif 'Emerald' in tint:
            painter.fillRect(v_rect, QColor(0, 160, 90, 28))

        # 2. CapCut Brightness Adjustment
        brightness = getattr(self, 'brightness', 0)
        if brightness > 0:
            painter.fillRect(v_rect, QColor(255, 255, 255, int(brightness * 2.2)))
        elif brightness < 0:
            painter.fillRect(v_rect, QColor(0, 0, 0, int(abs(brightness) * 2.2)))

        # 3. CapCut Contrast Adjustment
        contrast = getattr(self, 'contrast', 0)
        if contrast > 0:
            painter.fillRect(v_rect, QColor(0, 0, 0, int(contrast * 1.2)))

    def draw_audio_visualizer(self, painter: QPainter, v_rect: QRect):
        if not self.spectrum_bands:
            return
        painter.save()
        vis_mode = getattr(self, 'visualizer_mode', 'Bar Spectrum')
        band_count = len(self.spectrum_bands)

        if "Radial" in vis_mode or "Circle" in vis_mode or "360" in vis_mode:
            # 360-Degree Circular Visualizer around center
            center = v_rect.center()
            base_radius = min(v_rect.width(), v_rect.height()) * 0.22
            angle_step = 360.0 / float(max(1, band_count))
            for index, value in enumerate(self.spectrum_bands):
                angle_deg = index * angle_step
                rad = math.radians(angle_deg)
                bar_len = max(3.0, float(value) * base_radius * 0.85)
                
                x1 = center.x() + math.cos(rad) * base_radius
                y1 = center.y() + math.sin(rad) * base_radius
                x2 = center.x() + math.cos(rad) * (base_radius + bar_len)
                y2 = center.y() + math.sin(rad) * (base_radius + bar_len)

                painter.setPen(QPen(QColor(0, 210, 255, 200), 2.5, Qt.SolidLine, Qt.RoundCap))
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        elif "Wave" in vis_mode or "Ribbon" in vis_mode:
            # Smooth Neon Wave Ribbon
            wave_path = QPainterPath()
            available_w = v_rect.width() * 0.85
            start_x = v_rect.center().x() - available_w / 2.0
            baseline = v_rect.bottom() - v_rect.height() * 0.07
            step_x = available_w / float(max(1, band_count - 1))
            
            wave_path.moveTo(start_x, baseline)
            for index, value in enumerate(self.spectrum_bands):
                wx = start_x + index * step_x
                wy = baseline - (float(value) * v_rect.height() * 0.14)
                wave_path.lineTo(wx, wy)
            
            painter.setPen(QPen(QColor(255, 45, 85, 220), 3.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(wave_path)

        else:
            # Standard Bottom Bar Spectrum
            available_w = v_rect.width() * 0.62
            bar_w = max(2.0, available_w / max(1, band_count) - 2.0)
            start_x = v_rect.center().x() - available_w / 2.0
            baseline = v_rect.bottom() - v_rect.height() * 0.05
            max_h = v_rect.height() * 0.12
            painter.setPen(Qt.NoPen)
            for index, value in enumerate(self.spectrum_bands):
                height = max(2.0, float(value) * max_h)
                painter.setBrush(QColor(255, 255, 255, 125))
                painter.drawRoundedRect(QRectF(start_x + index * (bar_w + 2), baseline - height, bar_w, height), 1.5, 1.5)

        painter.restore()

    def draw_vignette(self, painter: QPainter, v_rect: QRect):
        strength = max(0.0, min(1.0, float(self.vignette_percent) / 100.0))
        if strength <= 0:
            return
        center = v_rect.center()
        radius = max(v_rect.width(), v_rect.height()) * 0.7
        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
        gradient.setColorAt(0.58, QColor(0, 0, 0, 0))
        gradient.setColorAt(1.0, QColor(0, 0, 0, int(210 * strength)))
        painter.fillRect(v_rect, gradient)

    def draw_atmospheric_particles(self, painter: QPainter, v_rect: QRect):
        """Renders 60 FPS live floating particles (Golden Sparkles, Hearts, Sakura, Snow, Bokeh, Music Notes)."""
        painter.save()
        p_type = self.particle_type
        
        icon_char = "✨"
        p_color = QColor(245, 158, 11)
        if "Hearts" in p_type or "❤️" in p_type:
            icon_char = "❤️"
            p_color = QColor(255, 45, 85)
        elif "Sakura" in p_type or "🌸" in p_type:
            icon_char = "🌸"
            p_color = QColor(251, 113, 133)
        elif "Snow" in p_type or "❄️" in p_type:
            icon_char = "❄️"
            p_color = QColor(186, 230, 253)
        elif "Notes" in p_type or "🎵" in p_type:
            icon_char = "🎵"
            p_color = QColor(168, 85, 247)
        elif "Bokeh" in p_type or "🫧" in p_type:
            icon_char = None

        for p in self.particles:
            p['y'] = (p['y'] - p['speed']) % 1.0
            p['x'] = (p['x'] + math.sin(p['phase'] + self.current_time * 2.0) * 0.001) % 1.0

            px = v_rect.x() + int(p['x'] * v_rect.width())
            py = v_rect.y() + int(p['y'] * v_rect.height())
            p_size = max(6, int(p['size'] * (v_rect.width() / 1000.0)))
            
            if icon_char is not None:
                painter.setFont(QFont("Segoe UI Emoji", p_size))
                painter.setPen(QColor(p_color.red(), p_color.green(), p_color.blue(), int(p['opacity'] * 255)))
                painter.drawText(px, py, icon_char)
            else:
                orb_grad = QRadialGradient(px, py, p_size)
                orb_grad.setColorAt(0.0, QColor(255, 255, 255, int(p['opacity'] * 140)))
                orb_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
                painter.setPen(Qt.NoPen)
                painter.setBrush(orb_grad)
                painter.drawEllipse(px - p_size, py - p_size, p_size * 2, p_size * 2)

        painter.restore()

    def draw_singer_banner(self, painter: QPainter, v_rect: QRect):
        """Draws top Singer Portrait cards with real-time active singer pulse & halo."""
        num_singers = len(self.custom_singers)
        if num_singers == 0:
            return

        banner_h = int(v_rect.height() * 0.28)
        card_w = v_rect.width() / float(num_singers)

        # Detect currently singing artist
        active_singer_name = ""
        for line in self.lyric_lines:
            if line.line_start <= self.current_time <= line.line_end:
                s_role = getattr(line, 'singer', 'both')
                if s_role in ('both', 'all'):
                    active_singer_name = "both"
                else:
                    for idx, s in enumerate(self.custom_singers):
                        if (s_role == s.get('name') or 
                            s_role == s.get('role') or 
                            (s_role == 'female' and idx == 0) or 
                            (s_role == 'male' and idx == 1)):
                            active_singer_name = s.get('name', '')
                            break
                break

        painter.save()
        for idx, s in enumerate(self.custom_singers):
            cx = v_rect.x() + idx * card_w
            cy = v_rect.y()
            c_rect = QRectF(cx, cy, card_w, banner_h)
            is_active = (active_singer_name == "both" or s.get('name') == active_singer_name)

            # Card backdrop with active highlight
            if is_active:
                bg_col = QColor(30, 41, 59, 230)
            else:
                bg_col = QColor(15, 23, 42, 190)
            painter.fillRect(c_rect, bg_col)
            
            # Singer Portrait Avatar with Artist Face Photo support
            base_size = min(card_w * 0.45, banner_h * 0.55)
            pulse_extra = (math.sin(self.current_time * 8.0) * 3.0) if is_active else 0.0
            avatar_size = base_size + pulse_extra

            ax = cx + (card_w - avatar_size) / 2
            ay = cy + (banner_h * 0.15) - (pulse_extra / 2.0)
            circle_rect = QRectF(ax, ay, avatar_size, avatar_size)

            # Active Singer Glowing Halo Ring
            if is_active:
                halo_color = QColor(s.get('color', '#ec4899'))
                halo_pen = QPen(QColor(halo_color.red(), halo_color.green(), halo_color.blue(), 160), 6.0)
                painter.setPen(halo_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(circle_rect.adjusted(-3, -3, 3, 3))
            
            # Check if artist face photo is uploaded
            img_path = s.get('image_path', '')
            has_photo = False
            if img_path and os.path.exists(img_path):
                face_pix = QPixmap(img_path)
                if not face_pix.isNull():
                    has_photo = True
                    painter.save()
                    path = QPainterPath()
                    path.addEllipse(circle_rect)
                    painter.setClipPath(path)
                    scaled_face = face_pix.scaled(
                        int(avatar_size), int(avatar_size),
                        Qt.KeepAspectRatioByExpanding,
                        Qt.SmoothTransformation
                    )
                    fx = ax + (avatar_size - scaled_face.width()) / 2.0
                    fy = ay + (avatar_size - scaled_face.height()) / 2.0
                    painter.drawPixmap(int(fx), int(fy), scaled_face)
                    painter.restore()

            if not has_photo:
                painter.setPen(QPen(QColor(s.get('color', '#f59e0b')), 2.0 if is_active else 1.5))
                painter.setBrush(QColor(30, 41, 59))
                painter.drawEllipse(circle_rect)

                painter.setFont(QFont("Segoe UI Emoji", int(avatar_size * 0.5)))
                painter.setPen(QColor(255, 255, 255))
                avatar_symbol = s.get('avatar', '👤')
                painter.drawText(circle_rect, Qt.AlignCenter, avatar_symbol)
            else:
                # Color ring border around photo
                painter.setPen(QPen(QColor(s.get('color', '#f59e0b')), 3.0 if is_active else 2.0))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(circle_rect)

            # Singer Name Banner Label
            lbl_bg_rect = QRectF(cx, cy + banner_h - 24, card_w, 24)
            if is_active:
                painter.fillRect(lbl_bg_rect, QColor(s.get('color', '#ec4899')))
            else:
                painter.fillRect(lbl_bg_rect, QColor(0, 0, 0, 180))
            
            painter.setFont(QFont("Montserrat", 8, QFont.Bold))
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(lbl_bg_rect, Qt.AlignCenter, s['name'] + (" 🎤" if is_active else ""))

            # Vertical separator line
            if idx > 0:
                painter.setPen(QColor(255, 255, 255, 40))
                painter.drawLine(int(cx), int(cy), int(cx), int(cy + banner_h))

        painter.restore()

    def _draw_overlay_objects_legacy(self, painter: QPainter, v_rect: QRect):
        """Draws custom overlay objects (text, shapes, lower thirds, spinning vinyl)."""
        if not self.overlay_objects:
            return

        painter.save()
        scale = v_rect.width() / 1000.0

        for idx, obj in enumerate(self.overlay_objects):
            o_type = obj.get("type", "text")
            x = v_rect.x() + int(float(obj.get("x_pct", 10.0)) / 100.0 * v_rect.width())
            y = v_rect.y() + int(float(obj.get("y_pct", 10.0)) / 100.0 * v_rect.height())
            w = int(float(obj.get("w_pct", 30.0)) / 100.0 * v_rect.width())
            h = int(float(obj.get("h_pct", 10.0)) / 100.0 * v_rect.height())
            is_selected = (self.selected_object_idx == idx)

            if o_type == "text":
                content = str(obj.get("content", "Text"))
                f_size = max(10, int(int(obj.get("font_size", 32)) * scale))
                font = QFont(obj.get("font_family", "Montserrat"), f_size)
                font.setBold(obj.get("font_weight", 600) >= 600)
                painter.setFont(font)

                col = QColor(obj.get("color", "#ffffff"))
                stroke_col = QColor(obj.get("stroke_color", "#000000"))
                stroke_w = max(0, int(obj.get("stroke_width", 2)))

                path = QPainterPath()
                path.addText(float(x), float(y + f_size), font, content)
                if stroke_w > 0:
                    painter.strokePath(path, QPen(stroke_col, stroke_w * scale))
                painter.fillPath(path, QBrush(col))

            elif o_type == "shape":
                col = QColor(obj.get("color", "#ff2d55"))
                s_rect = QRectF(x, y, w, h)
                painter.setPen(Qt.NoPen)
                painter.setBrush(col)
                painter.drawRoundedRect(s_rect, 6, 6)

            elif o_type == "lower_third":
                s_rect = QRectF(x, y, w, h)
                bg_col = QColor(obj.get("color", "#0f172a"))
                bg_col.setAlpha(235)
                painter.setPen(Qt.NoPen)
                painter.setBrush(bg_col)
                painter.drawRoundedRect(s_rect, 6, 6)

                # Accent strip
                painter.fillRect(QRectF(x, y, max(4, int(w * 0.015)), h), QColor("#ff2d55"))

                # Title & Subtitle
                t_font = QFont("Arial", max(9, int(h * 0.32)), QFont.Bold)
                sub_font = QFont("Arial", max(8, int(h * 0.22)))
                tx = x + int(w * 0.04)

                painter.setFont(t_font)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(int(tx), int(y + h * 0.45), str(obj.get("title", "TITLE")))

                painter.setFont(sub_font)
                painter.setPen(QColor(148, 163, 184))
                painter.drawText(int(tx), int(y + h * 0.80), str(obj.get("subtitle", "Subtitle")))

            elif o_type == "vinyl":
                radius = min(w, h) // 2
                cx, cy = x + radius, y + radius

                # Outer vinyl disc
                painter.setPen(QPen(QColor(51, 65, 85), 2))
                painter.setBrush(QColor(15, 23, 42))
                painter.drawEllipse(QPointF(cx, cy), radius, radius)

                # Concentric grooves
                for r_step in range(int(radius * 0.45), int(radius * 0.95), max(3, int(radius * 0.08))):
                    painter.setPen(QPen(QColor(30, 41, 59, 160), 1))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(QPointF(cx, cy), r_step, r_step)

                # Center Label (Spinning)
                center_r = int(radius * 0.36)
                rot_angle = (self.current_time * 120.0) % 360.0
                painter.save()
                painter.translate(cx, cy)
                painter.rotate(rot_angle)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor("#ff2d55"))
                painter.drawEllipse(QPointF(0, 0), center_r, center_r)

                # Label text
                painter.setFont(QFont("Arial", max(6, int(center_r * 0.28)), QFont.Bold))
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(QRectF(-center_r, -center_r, center_r * 2, center_r * 2), Qt.AlignCenter, "LYLIS")
                painter.restore()

                # Spindle hole
                hole_r = max(2, int(radius * 0.06))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 0, 0))
                painter.drawEllipse(QPointF(cx, cy), hole_r, hole_r)

            # Selection bounding box
            if is_selected:
                painter.setPen(QPen(QColor("#00d2ff"), 2, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(QRectF(x - 2, y - 2, w + 4, h + 4))

        painter.restore()

    def _mousePressEvent_legacy(self, event):
        v_rect = self.get_viewport_rect()
        pos = event.pos()
        if not v_rect.contains(pos):
            return

        # Check if clicked on any overlay object (reverse order for top-most first)
        for idx in reversed(range(len(self.overlay_objects))):
            obj = self.overlay_objects[idx]
            x = v_rect.x() + int(float(obj.get("x_pct", 10.0)) / 100.0 * v_rect.width())
            y = v_rect.y() + int(float(obj.get("y_pct", 10.0)) / 100.0 * v_rect.height())
            w = int(float(obj.get("w_pct", 30.0)) / 100.0 * v_rect.width())
            h = int(float(obj.get("h_pct", 10.0)) / 100.0 * v_rect.height())
            if QRect(x, y, w, h).contains(pos):
                self.selected_object_idx = idx
                self._dragging_obj = True
                self._drag_start_pos = pos
                self._obj_start_x = obj.get("x_pct", 10.0)
                self._obj_start_y = obj.get("y_pct", 10.0)
                self.object_selected.emit(obj)
                self.update()
                return

        self.selected_object_idx = None
        self._dragging_obj = False
        self.update()

    def _mouseMoveEvent_legacy(self, event):
        if getattr(self, '_dragging_obj', False) and self.selected_object_idx is not None:
            if 0 <= self.selected_object_idx < len(self.overlay_objects):
                v_rect = self.get_viewport_rect()
                dx = event.x() - self._drag_start_pos.x()
                dy = event.y() - self._drag_start_pos.y()
                dx_pct = (dx / float(v_rect.width())) * 100.0
                dy_pct = (dy / float(v_rect.height())) * 100.0

                obj = self.overlay_objects[self.selected_object_idx]
                new_x = max(0.0, min(90.0, self._obj_start_x + dx_pct))
                new_y = max(0.0, min(90.0, self._obj_start_y + dy_pct))
                obj['x_pct'] = round(new_x, 1)
                obj['y_pct'] = round(new_y, 1)
                self.update()

    def _mouseReleaseEvent_legacy(self, event):
        self._dragging_obj = False

    def _active_lyric(self):
        if not self.lyric_lines:
            return None, None
        for idx, line in enumerate(self.lyric_lines):
            if line.line_start - 2.0 <= self.current_time <= line.line_end + 0.6:
                return idx, line
        return None, None

    @staticmethod
    def _format_player_time(seconds: float) -> str:
        seconds = max(0, int(seconds))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def set_album_tracks(self, tracks, active_track_id=None):
        """Normalize album tracks while retaining stable IDs for playlist selection."""
        normalized = []
        for index, item in enumerate(tracks or []):
            if isinstance(item, dict):
                track = dict(item)
                track_id = str(track.get('id') or f'track_{index + 1:04d}')
                track['id'] = track_id
                track['title'] = str(track.get('title') or track.get('name') or f'Track {index + 1:02d}')
                track.setdefault('artist', '')
                track.setdefault('audioSrc', '')
                track.setdefault('cover', '')
                track.setdefault('duration', 0)
                track.setdefault('lyrics', [])
                track.setdefault('lyricTiming', [])
            else:
                track_id = f'track_{index + 1:04d}'
                track = {'id': track_id, 'title': str(item).strip() or f'Track {index + 1:02d}'}
            normalized.append(track)
        self.album_tracks = normalized
        self.album_track_ids = [track['id'] for track in normalized]
        self.active_album_track_id = active_track_id if active_track_id in self.album_track_ids else (self.album_track_ids[0] if self.album_track_ids else None)
        active = next((track for track in normalized if track.get('id') == self.active_album_track_id), None)
        self.setToolTip(active.get('title', '') if active else '')
        self.update()

    def draw_multi_song_album_stage(self, painter: QPainter, v_rect: QRect):
        """Render the clean, luxury multi-song album layout with an independent cover & track queue."""
        painter.save()
        # 1. Dark ambient background with soft atmospheric glow
        painter.fillRect(v_rect, QColor(8, 12, 20, 235))
        radius = v_rect.width() * 0.45
        for x_pct, y_pct, color in (
            (0.18, 0.16, QColor(139, 92, 246, 95)),
            (0.78, 0.72, QColor(14, 165, 233, 85)),
            (0.85, 0.15, QColor(16, 185, 129, 70)),
        ):
            glow = QRadialGradient(
                v_rect.x() + v_rect.width() * x_pct,
                v_rect.y() + v_rect.height() * y_pct,
                radius,
            )
            glow.setColorAt(0, color)
            glow.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
            painter.fillRect(v_rect, glow)

        # 2. Left side: Album Cover Card (square with rounded corners & glass glow)
        cover_size = min(v_rect.width() * 0.38, v_rect.height() * 0.50)
        cover = QRectF(
            v_rect.x() + v_rect.width() * 0.055,
            v_rect.y() + v_rect.height() * 0.08,
            cover_size,
            cover_size,
        )
        cover_path = QPainterPath()
        cover_path.addRoundedRect(cover, 12, 12)
        painter.save()
        painter.setClipPath(cover_path)
        active_pix = self.album_cover_pixmap if (getattr(self, 'album_cover_pixmap', None) and not self.album_cover_pixmap.isNull()) else self.bg_pixmap
        if active_pix and not active_pix.isNull():
            scaled = active_pix.scaled(int(cover.width()), int(cover.height()), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            sx = max(0, (scaled.width() - int(cover.width())) // 2)
            sy = max(0, (scaled.height() - int(cover.height())) // 2)
            painter.drawPixmap(cover.toRect(), scaled, QRect(sx, sy, int(cover.width()), int(cover.height())))
        else:
            cover_gradient = QLinearGradient(cover.topLeft(), cover.bottomRight())
            cover_gradient.setColorAt(0, QColor("#38bdf8"))
            cover_gradient.setColorAt(0.5, QColor("#818cf8"))
            cover_gradient.setColorAt(1.0, QColor("#c084fc"))
            painter.fillRect(cover, cover_gradient)
            painter.setPen(QColor(255, 255, 255, 200))
            painter.setFont(QFont("Montserrat", max(16, int(cover_size * 0.085)), QFont.Black))
            painter.drawText(cover, Qt.AlignCenter, "ALBUM ART")
        painter.restore()
        painter.setPen(QPen(QColor(255, 255, 255, 45), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(cover, 12, 12)

        # 3. Left side below cover: Track Info & Progress Bar
        left = cover.left()
        right = cover.right()
        
        # Track Title & Artist
        t_y = cover.bottom() + v_rect.height() * 0.04
        title_font = QFont(self.font_family or "Montserrat", max(11, int(v_rect.height() * 0.026)), QFont.Bold)
        painter.setFont(title_font)
        metrics = QFontMetrics(title_font)
        active_track = next((track for track in self.album_tracks if track.get('id') == self.active_album_track_id), None)
        t_text = active_track.get('title', 'Track 01') if active_track else (self.track_title if self.track_title and self.track_title != "Song Title" else (getattr(self, 'project_title', '') or "Track 01"))
        title_w = max(right - left, v_rect.width() * 0.40)
        title = metrics.elidedText(t_text, Qt.ElideRight, int(title_w))
        painter.setPen(Qt.white)
        painter.drawText(QRectF(left, t_y, title_w, v_rect.height() * 0.035), Qt.AlignLeft | Qt.AlignVCenter, title)

        artist_font = QFont(self.font_family or "Montserrat", max(9, int(v_rect.height() * 0.018)))
        painter.setFont(artist_font)
        a_text = (active_track.get('artist') or "Album Artist") if active_track else (self.track_artist if self.track_artist and self.track_artist != "Artist" else ("Album Artist" if not self.custom_singers else ", ".join([s['name'] for s in self.custom_singers[:2]])))
        artist = QFontMetrics(artist_font).elidedText(a_text, Qt.ElideRight, int(title_w))
        painter.setPen(QColor(148, 163, 184))
        painter.drawText(QRectF(left, t_y + v_rect.height() * 0.035, title_w, v_rect.height() * 0.028), Qt.AlignLeft | Qt.AlignVCenter, artist)

        # Progress Bar Line with 2-digit timestamps
        prog_y = t_y + v_rect.height() * 0.085
        prog_val = max(0.0, min(1.0, self.current_time / max(1.0, self.duration)))
        painter.setPen(QPen(QColor(255, 255, 255, 60), max(2, int(v_rect.height() * 0.005)), Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(left, prog_y), QPointF(right, prog_y))
        painter.setPen(QPen(QColor(168, 85, 247), max(2, int(v_rect.height() * 0.005)), Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(left, prog_y), QPointF(left + (right - left) * prog_val, prog_y))

        time_font = QFont("Montserrat", max(8, int(v_rect.height() * 0.016)), QFont.Bold)
        painter.setFont(time_font)
        painter.setPen(QColor(203, 213, 225))
        time_rect = QRectF(left, prog_y + 4, right - left, v_rect.height() * 0.025)
        painter.drawText(time_rect, Qt.AlignLeft | Qt.AlignVCenter, self._format_player_time(self.current_time))
        painter.drawText(time_rect, Qt.AlignRight | Qt.AlignVCenter, self._format_player_time(self.duration))

        # 4. Right Top Panel: Playlist Track Queue Card
        tracks = list(self.album_tracks or [])
        if not tracks:
            tracks = [{'id': f'track_{i + 1:04d}', 'title': f'Track {i + 1:02d}'} for i in range(5)]
        queue = QRectF(v_rect.x() + v_rect.width() * 0.48, v_rect.y() + v_rect.height() * 0.08,
                       v_rect.width() * 0.46, v_rect.height() * 0.50)
        painter.setPen(QPen(QColor(255, 255, 255, 35), 1))
        painter.setBrush(QColor(15, 23, 42, 180))
        painter.drawRoundedRect(queue, 12, 12)

        q_hdr_font = QFont(self.font_family or "Montserrat", max(11, int(v_rect.height() * 0.025)), QFont.Bold)
        painter.setFont(q_hdr_font)
        painter.setPen(Qt.white)
        painter.drawText(QRectF(queue.left() + 16, queue.top() + 10, queue.width() - 32, 26),
                         Qt.AlignLeft | Qt.AlignVCenter, f"💿 {self.album_title or 'My Album'}")
        
        max_visible = 6
        total_tracks = len(tracks)
        active_idx = next((index for index, track in enumerate(tracks) if track.get('id') == self.active_album_track_id), 0)
        if total_tracks <= max_visible:
            start_idx = 0
            visible_count = total_tracks
        else:
            start_idx = max(0, min(total_tracks - max_visible, active_idx - max_visible // 2))
            visible_count = max_visible

        row_h = min(28.0, max(18.0, (queue.height() - 44) / max(1, visible_count)))
        for offset in range(visible_count):
            index = start_idx + offset
            if index >= total_tracks:
                break
            track = tracks[index]
            row = QRectF(queue.left() + 8, queue.top() + 40 + offset * row_h, queue.width() - 16, row_h - 3)
            if index == active_idx:
                painter.setBrush(QColor(139, 92, 246, 170))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(row, 5, 5)
            painter.setPen(QColor(255, 255, 255, 250 if index == active_idx else 150))
            painter.setFont(QFont(self.font_family or "Montserrat", max(9, int(row.height() * 0.42)), QFont.Bold if index == active_idx else QFont.Normal))
            painter.drawText(row.adjusted(10, 0, -8, 0), Qt.AlignVCenter | Qt.AlignLeft,
                             f"{index + 1:02d}  {QFontMetrics(painter.font()).elidedText(track.get('title', 'Track'), Qt.ElideRight, int(row.width() - 24))}")
        painter.restore()

    def draw_multi_song_album_lyrics(self, painter: QPainter, v_rect: QRect):
        """Keep lyrics readable in the dedicated right-bottom zone beside the album player."""
        active_idx, active_line = self._active_lyric()
        painter.save()
        rect = QRectF(v_rect.x() + v_rect.width() * 0.48, v_rect.y() + v_rect.height() * 0.64,
                      v_rect.width() * 0.46, v_rect.height() * 0.28)
        if active_line is None:
            painter.setFont(QFont(self.font_family or "Montserrat", max(11, int(v_rect.height() * 0.024)), QFont.Normal))
            painter.setPen(QColor(148, 163, 184, 130))
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, "🎵 Sẵn sàng phát lời bài hát...")
            painter.restore()
            return
        font = QFont(self.font_family or "Montserrat", max(15, int(self.font_size * v_rect.width() / 1200)), QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(0, 0, 0, 190))
        painter.drawText(rect.translated(2, 2), Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, active_line.full_text)
        painter.setPen(self.active_color if active_idx is not None else Qt.white)
        painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, active_line.full_text)
        painter.restore()

    def draw_ambient_album_stage(self, painter: QPainter, v_rect: QRect):
        """Draw a cover-led music player with soft red/teal ambient lighting."""
        painter.save()
        painter.fillRect(v_rect, QColor(4, 12, 10, 218))
        radius = v_rect.width() * 0.42
        for x_pct, y_pct, color in (
            (0.16, 0.12, QColor(230, 35, 24, 115)),
            (0.72, 0.78, QColor(15, 184, 166, 100)),
            (0.93, 0.05, QColor(10, 70, 55, 100)),
        ):
            glow = QRadialGradient(
                v_rect.x() + v_rect.width() * x_pct,
                v_rect.y() + v_rect.height() * y_pct,
                radius,
            )
            glow.setColorAt(0, color)
            glow.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
            painter.fillRect(v_rect, glow)

        cover_size = min(v_rect.width() * 0.4, v_rect.height() * 0.72)
        cover = QRectF(
            v_rect.x() + v_rect.width() * 0.025,
            v_rect.y() + v_rect.height() * 0.065,
            cover_size,
            cover_size,
        )
        cover_path = QPainterPath()
        cover_path.addRoundedRect(cover, 10, 10)
        painter.save()
        painter.setClipPath(cover_path)
        active_pix = self.album_cover_pixmap if (getattr(self, 'album_cover_pixmap', None) and not self.album_cover_pixmap.isNull()) else self.bg_pixmap
        if active_pix and not active_pix.isNull():
            scaled = active_pix.scaled(int(cover.width()), int(cover.height()), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            sx = max(0, (scaled.width() - int(cover.width())) // 2)
            sy = max(0, (scaled.height() - int(cover.height())) // 2)
            painter.drawPixmap(cover.toRect(), scaled, QRect(sx, sy, int(cover.width()), int(cover.height())))
        else:
            cover_gradient = QLinearGradient(cover.topLeft(), cover.bottomRight())
            cover_gradient.setColorAt(0, QColor("#7dd3c7"))
            cover_gradient.setColorAt(1, QColor("#182a27"))
            painter.fillRect(cover, cover_gradient)
            painter.setPen(QColor(255, 255, 255, 170))
            painter.setFont(QFont("Montserrat", max(18, int(cover_size * 0.09)), QFont.Black))
            painter.drawText(cover, Qt.AlignCenter, "ALBUM ART")
        painter.restore()
        painter.setPen(QPen(QColor(255, 255, 255, 28), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(cover, 10, 10)

        left = cover.left() + cover.width() * 0.05
        right = cover.right() - cover.width() * 0.05
        progress_y = cover.bottom() + v_rect.height() * 0.12
        progress = max(0.0, min(1.0, self.current_time / max(1.0, self.duration)))
        painter.setPen(QPen(QColor(255, 255, 255, 70), max(2, int(v_rect.height() * 0.006)), Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(left, progress_y), QPointF(right, progress_y))
        painter.setPen(QPen(QColor(255, 255, 255), max(2, int(v_rect.height() * 0.006)), Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(left, progress_y), QPointF(left + (right - left) * progress, progress_y))

        small = QFont("Montserrat", max(8, int(v_rect.height() * 0.017)))
        painter.setFont(small)
        painter.setPen(QColor(255, 255, 255, 180))
        time_rect = QRectF(left, progress_y - v_rect.height() * 0.055, right - left, v_rect.height() * 0.035)
        painter.drawText(time_rect, Qt.AlignLeft | Qt.AlignVCenter, self._format_player_time(self.current_time))
        painter.drawText(time_rect, Qt.AlignRight | Qt.AlignVCenter, self._format_player_time(self.duration))

        title_font = QFont("Montserrat", max(10, int(v_rect.height() * 0.022)), QFont.Bold)
        painter.setFont(title_font)
        metrics = QFontMetrics(title_font)
        active_track = next((track for track in self.album_tracks if track.get('id') == self.active_album_track_id), None)
        if active_track is not None:
            self.track_title = active_track.get('title', 'Track 01')
        t_text = self.track_title if self.track_title and self.track_title != "Song Title" else (getattr(self, 'project_title', '') or "Chiếc nón ba tầm")
        title = metrics.elidedText(t_text, Qt.ElideRight, int(right - left))
        painter.setPen(Qt.white)
        painter.drawText(QRectF(left, progress_y + v_rect.height() * 0.018, right - left, v_rect.height() * 0.04), Qt.AlignCenter, title)
        
        artist_font = QFont("Montserrat", max(8, int(v_rect.height() * 0.016)))
        painter.setFont(artist_font)
        if active_track is not None:
            self.track_artist = active_track.get('artist') or 'Album Artist'
        a_text = self.track_artist if self.track_artist and self.track_artist != "Artist" else ("Lylis Artist" if not self.custom_singers else ", ".join([s['name'] for s in self.custom_singers[:2]]))
        artist = QFontMetrics(artist_font).elidedText(a_text, Qt.ElideRight, int(right - left))
        painter.setPen(QColor(255, 255, 255, 175))
        painter.drawText(QRectF(left, progress_y + v_rect.height() * 0.055, right - left, v_rect.height() * 0.035), Qt.AlignCenter, artist)
        painter.restore()

    def draw_ambient_album_lyrics(self, painter: QPainter, v_rect: QRect):
        active_idx, active_line = self._active_lyric()
        if active_line is None:
            return
        display = self.lyric_lines[active_idx:min(len(self.lyric_lines), active_idx + 3)]
        if not display:
            return

        x = v_rect.x() + v_rect.width() * 0.50
        width = v_rect.width() * 0.46
        available_h = v_rect.height() * 0.68
        block_h = min(v_rect.height() * 0.20, available_h / max(1, len(display)))
        y = v_rect.y() + (v_rect.height() - (len(display) * block_h)) / 2.0
        base_size = max(14, int(self.font_size * v_rect.width() / 1300))

        painter.save()
        for index, line in enumerate(display):
            f_size = base_size + (2 if index == 0 else 0)
            font = QFont(self.font_family or "Montserrat", f_size, QFont.Bold if index == 0 else QFont.DemiBold)
            painter.setFont(font)
            
            rect = QRectF(x, y + index * block_h, width, block_h * 0.92)
            shadow_rect = QRectF(x + 1.5, y + index * block_h + 2.0, width, block_h * 0.92)
            
            # Soft dark drop shadow for 100% legibility
            painter.setPen(QColor(0, 0, 0, 180 if index == 0 else 120))
            painter.drawText(shadow_rect, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, line.full_text)

            # Text fill (Pure white for active line, luminous soft frosted white for upcoming lines)
            text_color = QColor(255, 255, 255, 255) if index == 0 else QColor(220, 235, 230, 160)
            painter.setPen(text_color)
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, line.full_text)

        painter.restore()

    def draw_walters_lyric_queue_stage(self, painter: QPainter, v_rect: QRect):
        """Draw the muted cover-and-title stage from the Walters reference."""
        painter.save()
        painter.fillRect(v_rect, QColor(24, 24, 28, 235))

        stage_center_y = v_rect.y() + v_rect.height() * 0.54
        cover_size = min(v_rect.width() * 0.32, v_rect.height() * 0.54)
        cover_x = v_rect.x() + v_rect.width() * 0.08
        cover_y = stage_center_y - cover_size / 2.0
        cover = QRectF(cover_x, cover_y, cover_size, cover_size)

        # Soft drop shadow for cover
        shadow = cover.translated(v_rect.height() * 0.012, v_rect.height() * 0.012)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 110))
        painter.drawRoundedRect(shadow, 16, 16)

        cover_path = QPainterPath()
        cover_path.addRoundedRect(cover, 16, 16)
        painter.save()
        painter.setClipPath(cover_path)
        active_pix = self.album_cover_pixmap if (getattr(self, 'album_cover_pixmap', None) and not self.album_cover_pixmap.isNull()) else self.bg_pixmap
        if active_pix and not active_pix.isNull():
            scaled = active_pix.scaled(
                int(cover.width()), int(cover.height()), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            sx = max(0, (scaled.width() - int(cover.width())) // 2)
            sy = max(0, (scaled.height() - int(cover.height())) // 2)
            painter.drawPixmap(cover.toRect(), scaled, QRect(sx, sy, int(cover.width()), int(cover.height())))
        else:
            # Elegant vinyl artwork placeholder
            gradient = QLinearGradient(cover.topLeft(), cover.bottomRight())
            gradient.setColorAt(0.0, QColor("#3b82f6"))
            gradient.setColorAt(0.5, QColor("#ec4899"))
            gradient.setColorAt(1.0, QColor("#f59e0b"))
            painter.fillRect(cover, gradient)
            painter.setPen(QColor(255, 255, 255, 220))
            painter.setFont(QFont("Montserrat", max(12, int(cover_size * 0.09)), QFont.Bold))
            painter.drawText(cover, Qt.AlignCenter, "ALBUM ART")
        painter.restore()

        # Top Title Banner
        title_font = QFont(self.font_family or "Montserrat", max(15, int(v_rect.height() * 0.05)), QFont.Bold)
        title_rect = QRectF(
            v_rect.x() + v_rect.width() * 0.08,
            v_rect.y() + v_rect.height() * 0.05,
            v_rect.width() * 0.84,
            v_rect.height() * 0.08,
        )
        title = QFontMetrics(title_font).elidedText(
            self.track_title or "Song Title", Qt.ElideRight, int(title_rect.width())
        )
        painter.setFont(title_font)
        # Drop shadow for title
        painter.setPen(QColor(0, 0, 0, 160))
        painter.drawText(title_rect.translated(1.5, 1.5), Qt.AlignHCenter | Qt.AlignVCenter, title)
        painter.setPen(QColor(255, 255, 255, 250))
        painter.drawText(title_rect, Qt.AlignHCenter | Qt.AlignVCenter, title)
        painter.restore()

    def draw_walters_lyric_queue(self, painter: QPainter, v_rect: QRect):
        active_idx, active_line = self._active_lyric()
        if active_line is None:
            return

        x = v_rect.x() + v_rect.width() * 0.45
        width = v_rect.width() * 0.49
        row_h = int(v_rect.height() * 0.115)
        start_idx = max(0, active_idx - 1)
        end_idx = min(len(self.lyric_lines), active_idx + 3)
        display = list(enumerate(self.lyric_lines[start_idx:end_idx], start=start_idx))
        y = v_rect.y() + int(v_rect.height() * 0.42) - max(0, active_idx - start_idx) * row_h
        base_size = max(13, int(self.font_size * v_rect.width() / 1280))

        painter.save()
        for order, (line_idx, line) in enumerate(display):
            line_y = y + order * row_h
            offset_lines = line_idx - active_idx
            is_active = (line_idx == active_idx)

            line_font = QFont(self.font_family or "Montserrat", base_size, QFont.Bold)
            fm_line = QFontMetrics(line_font)
            curr_sz = base_size
            while curr_sz > 11 and fm_line.horizontalAdvance(line.full_text) > width - 20:
                curr_sz -= 1
                line_font.setPointSize(curr_sz)
                fm_line = QFontMetrics(line_font)

            rect = QRectF(x, line_y, width, row_h)
            if is_active:
                pill_rect = QRectF(x - 14, line_y + 2, width + 10, row_h - 4)
                painter.setPen(QPen(QColor(255, 255, 255, 45), 1.0))
                painter.setBrush(QColor(255, 255, 255, 34))
                painter.drawRoundedRect(pill_rect, 10, 10)

                # Active text drop shadow
                painter.setFont(line_font)
                painter.setPen(QColor(0, 0, 0, 180))
                painter.drawText(rect.translated(1.5, 1.5), Qt.AlignLeft | Qt.AlignVCenter, line.full_text)
                painter.setPen(QColor(255, 255, 255, 255))
                painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, line.full_text)
            else:
                alpha = 110 if offset_lines < 0 else (80 if offset_lines == 1 else 45)
                painter.setFont(line_font)
                painter.setPen(QColor(255, 255, 255, alpha))
                painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter, line.full_text)
        painter.restore()

    def draw_ksector_2000s_stage(self, painter: QPainter, v_rect: QRect):
        """Draw the warm portrait, burgundy band, and ivory Y2K title card."""
        painter.save()
        painter.fillRect(v_rect, QColor("#f9f6ed"))

        portrait_rect = QRectF(v_rect.x(), v_rect.y(), v_rect.width(), v_rect.height() * 0.50)
        if self.bg_pixmap and not self.bg_pixmap.isNull():
            scaled = self.bg_pixmap.scaled(
                int(portrait_rect.width()), int(portrait_rect.height()),
                Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation,
            )
            sx = max(0, (scaled.width() - int(portrait_rect.width())) // 2)
            focus_y = max(0.0, min(1.0, float(self.portrait_focus_y) / 100.0))
            sy = max(0, min(
                scaled.height() - int(portrait_rect.height()),
                int(scaled.height() * focus_y - portrait_rect.height() / 2),
            ))
            painter.drawPixmap(
                portrait_rect.toRect(), scaled,
                QRect(sx, sy, int(portrait_rect.width()), int(portrait_rect.height())),
            )
        else:
            warm_bg = QLinearGradient(portrait_rect.topLeft(), portrait_rect.bottomRight())
            warm_bg.setColorAt(0.0, QColor("#d6a06d"))
            warm_bg.setColorAt(1.0, QColor("#65364a"))
            painter.fillRect(portrait_rect, warm_bg)
        painter.fillRect(portrait_rect, QColor(169, 77, 37, 38))

        band_rect = QRectF(
            v_rect.x(), v_rect.y() + v_rect.height() * 0.34,
            v_rect.width(), v_rect.height() * 0.165,
        )
        band_gradient = QLinearGradient(band_rect.topLeft(), band_rect.bottomLeft())
        band_gradient.setColorAt(0.0, QColor(104, 20, 69, 35))
        band_gradient.setColorAt(1.0, QColor(138, 20, 34, 240))
        painter.fillRect(band_rect, band_gradient)

        artist_font = QFont("Arial", max(14, int(v_rect.height() * 0.046)), QFont.Bold)
        artist_font.setItalic(True)
        painter.setFont(artist_font)
        painter.setPen(QColor(255, 255, 255, 248))
        painter.drawText(
            QRectF(
                v_rect.x() + v_rect.width() * 0.215,
                v_rect.y() + v_rect.height() * 0.395,
                v_rect.width() * 0.5,
                v_rect.height() * 0.08,
            ),
            Qt.AlignLeft | Qt.AlignVCenter,
            self.track_artist or "Artist",
        )

        has_started = bool(self.lyric_lines) and self.current_time >= self.lyric_lines[0].line_start
        if not has_started:
            title = (self.track_title or "SONG TITLE").upper()
            title_size = max(28, int(v_rect.height() * 0.15))
            title_font = QFont("Impact", title_size, QFont.Bold)
            title_font.setStretch(80)
            max_width = v_rect.width() * 0.82
            while title_size > max(18, int(v_rect.height() * 0.06)) and QFontMetrics(title_font).horizontalAdvance(title) > max_width:
                title_size -= 1
                title_font.setPointSize(title_size)
            title_rect = QRectF(
                v_rect.x() + v_rect.width() * 0.09,
                v_rect.y() + v_rect.height() * 0.535,
                v_rect.width() * 0.82,
                v_rect.height() * 0.22,
            )
            painter.setFont(title_font)
            painter.setPen(QColor(78, 43, 30, 110))
            painter.drawText(title_rect.translated(4, 4), Qt.AlignCenter, title)
            painter.setPen(QColor("#892237"))
            painter.drawText(title_rect, Qt.AlignCenter, title)

            caption_font = QFont("Segoe UI", max(12, int(v_rect.height() * 0.032)), QFont.Bold)
            painter.setFont(caption_font)
            painter.setPen(QColor(107, 51, 36, 230))
            if self.track_artist and self.track_artist != 'Artist':
                caption = f"{self.track_artist}  •  {title}"
            else:
                caption = f"{title}"
            painter.drawText(
                QRectF(
                    v_rect.x() + v_rect.width() * 0.1,
                    v_rect.y() + v_rect.height() * 0.84,
                    v_rect.width() * 0.8,
                    v_rect.height() * 0.08,
                ),
                Qt.AlignCenter,
                caption,
            )
        painter.restore()

    def draw_ksector_2000s_lyrics(self, painter: QPainter, v_rect: QRect):
        active_idx = next(
            (index for index, line in enumerate(self.lyric_lines)
             if line.line_start <= self.current_time <= line.line_end),
            None,
        )
        if active_idx is None:
            return

        line = self.lyric_lines[active_idx]
        colors = {
            "male": self.male_color,
            "female": self.female_color,
            "both": self.both_color,
        }
        color = colors.get(getattr(line, "singer", "both"), self.both_color)
        text = line.full_text.upper() if self.uppercase_lyrics else line.full_text
        max_width = v_rect.width() * 0.84
        size = max(24, int(self.font_size * v_rect.width() / 1280))
        font = QFont(self.font_family or "Impact", size, QFont.Bold)
        font.setStretch(80)
        while size > max(16, int(v_rect.height() * 0.045)) and QFontMetrics(font).horizontalAdvance(text) > max_width:
            size -= 1
            font.setPointSize(size)

        active_rect = QRectF(
            v_rect.x() + v_rect.width() * 0.08,
            v_rect.y() + v_rect.height() * 0.605,
            v_rect.width() * 0.84,
            v_rect.height() * 0.13,
        )
        painter.save()
        painter.setFont(font)
        painter.setPen(QColor(76, 44, 31, 105))
        painter.drawText(active_rect.translated(4, 4), Qt.AlignCenter, text)
        painter.setPen(color)
        painter.drawText(active_rect, Qt.AlignCenter, text)

        context_font = QFont("Segoe UI", max(11, int(v_rect.height() * 0.029)), QFont.Bold)
        painter.setFont(context_font)
        context_metrics = QFontMetrics(context_font)
        context_width = int(v_rect.width() * 0.84)
        if active_idx > 0:
            painter.setPen(QColor(color.red(), color.green(), color.blue(), 115))
            previous_text = context_metrics.elidedText(
                self.lyric_lines[active_idx - 1].full_text, Qt.ElideRight, context_width
            )
            painter.drawText(
                QRectF(v_rect.x() + v_rect.width() * 0.08, v_rect.y() + v_rect.height() * 0.535,
                       v_rect.width() * 0.84, v_rect.height() * 0.06),
                Qt.AlignCenter, previous_text,
            )
        painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 55), max(1, int(v_rect.height() * 0.002))))
        painter.drawLine(
            QPointF(v_rect.x() + v_rect.width() * 0.33, v_rect.y() + v_rect.height() * 0.785),
            QPointF(v_rect.x() + v_rect.width() * 0.67, v_rect.y() + v_rect.height() * 0.785),
        )
        if active_idx + 1 < len(self.lyric_lines):
            painter.setPen(QColor(color.red(), color.green(), color.blue(), 145))
            next_text = context_metrics.elidedText(
                self.lyric_lines[active_idx + 1].full_text, Qt.ElideRight, context_width
            )
            painter.drawText(
                QRectF(v_rect.x() + v_rect.width() * 0.08, v_rect.y() + v_rect.height() * 0.80,
                       v_rect.width() * 0.84, v_rect.height() * 0.07),
                Qt.AlignCenter, next_text,
            )
        painter.restore()

    def draw_falling_u_douyin_stage(self, painter: QPainter, v_rect: QRect):
        """
        Draw Douyin DJ Remix Stage inspired by Falling U (DJSKing Remix):
        - Deep cyber club backdrop with rotating laser cones and neon particle glows
        - Realistic high-gloss Vinyl turntable with grooved specular reflection, rotating center label & DJ tonearm
        - Fitted neon Douyin DJ badge & track title header
        - Beat-reactive neon EQ spectrum with mirror floor reflection
        """
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # 1. Dark Cyber Ambient Background with Laser Glows
        bg_grad = QLinearGradient(v_rect.topLeft(), v_rect.bottomRight())
        bg_grad.setColorAt(0.0, QColor("#080214"))
        bg_grad.setColorAt(0.5, QColor("#0d0a21"))
        bg_grad.setColorAt(1.0, QColor("#050816"))
        painter.fillRect(v_rect, bg_grad)
        
        # Radial laser spotlights radiating from disc center
        disc_cx = v_rect.x() + v_rect.width() * 0.22
        disc_cy = v_rect.y() + v_rect.height() * 0.52
        
        laser_glow = QRadialGradient(disc_cx, disc_cy, v_rect.width() * 0.45)
        laser_glow.setColorAt(0.0, QColor(168, 85, 247, 95))   # Neon Violet
        laser_glow.setColorAt(0.4, QColor(6, 182, 212, 50))    # Cyan
        laser_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(v_rect, laser_glow)

        # Right side ambient violet glow
        r_glow = QRadialGradient(v_rect.x() + v_rect.width() * 0.75, v_rect.y() + v_rect.height() * 0.50, v_rect.width() * 0.38)
        r_glow.setColorAt(0.0, QColor(217, 70, 239, 45))
        r_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(v_rect, r_glow)

        # 2. Realistic DJ Vinyl Turntable Record (Left Side)
        disc_size = min(v_rect.width() * 0.36, v_rect.height() * 0.64)
        disc_rect = QRectF(disc_cx - disc_size / 2.0, disc_cy - disc_size / 2.0, disc_size, disc_size)

        # Outer Neon Reactive Pulse Rim
        pulse = 1.0 + 0.03 * math.sin(self.current_time * 12.0)
        pulse_rect = QRectF(disc_cx - (disc_size * pulse) / 2.0, disc_cy - (disc_size * pulse) / 2.0, disc_size * pulse, disc_size * pulse)
        painter.setPen(QPen(QColor(0, 245, 212, 130), 2.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(pulse_rect)

        # Vinyl Outer Edge & Body
        painter.setPen(QPen(QColor(50, 52, 65), 2.0))
        painter.setBrush(QColor(14, 15, 20))
        painter.drawEllipse(disc_rect)

        # Fine Concentric Vinyl Grooves with metallic specular rings
        for r_factor in [0.94, 0.88, 0.82, 0.76, 0.70, 0.64, 0.58]:
            gr_size = disc_size * r_factor
            gr_rect = QRectF(disc_cx - gr_size / 2.0, disc_cy - gr_size / 2.0, gr_size, gr_size)
            alpha = 35 if int(r_factor * 100) % 2 == 0 else 18
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 1.0))
            painter.drawEllipse(gr_rect)

        # Conical Specular Light Reflection across Vinyl Face
        conic = QConicalGradient(disc_cx, disc_cy, (self.current_time * 30.0) % 360.0)
        conic.setColorAt(0.00, QColor(255, 255, 255, 0))
        conic.setColorAt(0.12, QColor(255, 255, 255, 30))
        conic.setColorAt(0.25, QColor(255, 255, 255, 0))
        conic.setColorAt(0.50, QColor(255, 255, 255, 0))
        conic.setColorAt(0.62, QColor(255, 255, 255, 30))
        conic.setColorAt(0.75, QColor(255, 255, 255, 0))
        conic.setColorAt(1.00, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(conic)
        painter.drawEllipse(disc_rect)

        # Rotating Vinyl Center Label
        center_size = disc_size * 0.40
        painter.save()
        painter.translate(disc_cx, disc_cy)
        rotation = (self.current_time * 90.0) % 360.0
        painter.rotate(rotation)

        center_path = QPainterPath()
        center_path.addEllipse(QRectF(-center_size / 2.0, -center_size / 2.0, center_size, center_size))
        painter.setClipPath(center_path)

        active_pix = self.album_cover_pixmap if (getattr(self, 'album_cover_pixmap', None) and not self.album_cover_pixmap.isNull()) else self.bg_pixmap
        if active_pix and not active_pix.isNull():
            scaled = active_pix.scaled(int(center_size), int(center_size), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            sx = max(0, (scaled.width() - int(center_size)) // 2)
            sy = max(0, (scaled.height() - int(center_size)) // 2)
            painter.drawPixmap(QRect(-int(center_size / 2), -int(center_size / 2), int(center_size), int(center_size)), scaled, QRect(sx, sy, int(center_size), int(center_size)))
        else:
            center_grad = QLinearGradient(QPointF(-center_size / 2, -center_size / 2), QPointF(center_size / 2, center_size / 2))
            center_grad.setColorAt(0.0, QColor("#d946ef"))
            center_grad.setColorAt(0.5, QColor("#3b82f6"))
            center_grad.setColorAt(1.0, QColor("#06b6d4"))
            painter.fillRect(QRectF(-center_size / 2.0, -center_size / 2.0, center_size, center_size), center_grad)
            painter.setPen(QColor(255, 255, 255, 230))
            painter.setFont(QFont("Montserrat", max(8, int(center_size * 0.16)), QFont.Black))
            painter.drawText(QRectF(-center_size / 2.0, -center_size / 2.0, center_size, center_size), Qt.AlignCenter, "DJ MIX")
        
        # Silver center ring & spindle hole
        painter.setPen(QPen(QColor(220, 225, 235), 1.5))
        painter.setBrush(QColor(10, 4, 22))
        hole_size = center_size * 0.20
        painter.drawEllipse(QRectF(-hole_size / 2.0, -hole_size / 2.0, hole_size, hole_size))
        painter.restore()

        # Stylized DJ Tonearm Needle resting on disc
        arm_top_x = disc_cx + disc_size * 0.45
        arm_top_y = disc_cy - disc_size * 0.52
        arm_pivot_size = max(10.0, disc_size * 0.08)
        painter.setPen(QPen(QColor(200, 205, 220), 2.0))
        painter.setBrush(QColor(40, 42, 54))
        painter.drawEllipse(QRectF(arm_top_x - arm_pivot_size / 2, arm_top_y - arm_pivot_size / 2, arm_pivot_size, arm_pivot_size))
        
        needle_x = disc_cx + disc_size * 0.22
        needle_y = disc_cy + disc_size * 0.10
        painter.setPen(QPen(QColor(220, 225, 240), 2.0, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(QPointF(arm_top_x, arm_top_y), QPointF(needle_x + 10, needle_y - 20))
        painter.drawLine(QPointF(needle_x + 10, needle_y - 20), QPointF(needle_x, needle_y))
        
        # Cartridge head
        painter.setBrush(QColor("#00f5d4"))
        painter.drawRoundedRect(QRectF(needle_x - 3, needle_y - 3, 6, 6), 1, 1)

        # 3. Top DJ Badge & Track Info Header (Properly Measured, Never Clipped)
        badge_text = "⚡ DOUYIN DJ CLUB REMIX ⚡"
        badge_font_sz = max(9, int(v_rect.height() * 0.024))
        badge_font = QFont("Montserrat", badge_font_sz, QFont.Black)
        painter.setFont(badge_font)
        badge_fm = QFontMetrics(badge_font)
        
        badge_w = badge_fm.horizontalAdvance(badge_text) + 28.0
        badge_h = max(22.0, badge_fm.height() + 10.0)
        badge_x = v_rect.x() + (v_rect.width() - badge_w) / 2.0
        badge_y = v_rect.y() + v_rect.height() * 0.04
        badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)
        
        # Frosted glass badge pill with neon cyan-violet border
        painter.setPen(QPen(QColor("#00f5d4"), 1.5))
        painter.setBrush(QColor(14, 8, 30, 235))
        painter.drawRoundedRect(badge_rect, badge_h / 2.0, badge_h / 2.0)

        painter.setPen(QColor("#00f5d4"))
        painter.drawText(badge_rect, Qt.AlignCenter, badge_text)

        # Track Title Subheader
        t_text = (self.track_title or "FALLING U (DJSKING REMIX)").upper()
        title_font_sz = max(11, int(v_rect.height() * 0.034))
        title_font = QFont("Montserrat", title_font_sz, QFont.Black)
        title_font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        painter.setFont(title_font)
        title_fm = QFontMetrics(title_font)
        
        title_y = badge_rect.bottom() + v_rect.height() * 0.012
        title_rect = QRectF(v_rect.x() + v_rect.width() * 0.05, title_y, v_rect.width() * 0.90, title_fm.height() + 4.0)
        
        painter.setPen(QColor(0, 0, 0, 180))
        painter.drawText(QRectF(title_rect.x() + 1, title_rect.y() + 1, title_rect.width(), title_rect.height()), Qt.AlignCenter, t_text)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(title_rect, Qt.AlignCenter, t_text)

        # 4. Neon Audio Equalizer Spectrum Bars (Bottom Right under lyrics)
        eq_y = v_rect.y() + v_rect.height() * 0.90
        eq_w = v_rect.width() * 0.50
        eq_x = v_rect.x() + v_rect.width() * 0.44
        num_bars = 26
        bar_step = eq_w / num_bars
        bar_w = max(2.5, bar_step * 0.62)
        
        peaks = getattr(self, 'waveform_peaks', None) or []
        for i in range(num_bars):
            # Dynamic energy simulation synced with audio peaks if available
            peak_val = 0.5
            if peaks:
                peak_idx = int((i / float(num_bars)) * len(peaks)) % len(peaks)
                peak_val = peaks[peak_idx]
            wave_val = abs(math.sin(self.current_time * 9.0 + i * 0.40) * math.cos(self.current_time * 5.0 + i * 0.25))
            combined_val = (wave_val * 0.6 + peak_val * 0.4)
            
            bh = max(3.0, combined_val * v_rect.height() * 0.09)
            bx = eq_x + i * bar_step
            
            # Upward glowing bar
            bar_grad = QLinearGradient(bx, eq_y, bx, eq_y - bh)
            bar_grad.setColorAt(0.0, QColor("#00f5d4"))   # Electric Cyan
            bar_grad.setColorAt(0.5, QColor("#ffe600"))   # Gold
            bar_grad.setColorAt(1.0, QColor("#ff007f"))   # Neon Magenta
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(bar_grad)
            painter.drawRoundedRect(QRectF(bx, eq_y - bh, bar_w, bh), 2.0, 2.0)

            # Downward mirror floor reflection
            ref_bh = bh * 0.40
            ref_grad = QLinearGradient(bx, eq_y, bx, eq_y + ref_bh)
            ref_grad.setColorAt(0.0, QColor(0, 245, 212, 70))
            ref_grad.setColorAt(1.0, QColor(0, 245, 212, 0))
            painter.setBrush(ref_grad)
            painter.drawRoundedRect(QRectF(bx, eq_y + 1, bar_w, ref_bh), 1.5, 1.5)

        painter.restore()

    def draw_falling_u_douyin_lyrics(self, painter: QPainter, v_rect: QRect):
        """Draw ultra-crisp Douyin karaoke lyrics with glowing sweep and sleek typography."""
        active_idx, active_line = self._active_lyric()
        if active_line is None:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # Right pane bounds with generous safety margins
        lx = v_rect.x() + v_rect.width() * 0.42
        lw = v_rect.width() * 0.53
        ly = v_rect.y() + v_rect.height() * 0.40

        # 1. Main Active Singing Line
        font_sz = max(20, int(self.font_size * v_rect.width() / 1280))
        font = QFont(self.font_family or "Montserrat", font_sz, QFont.Black)
        painter.setFont(font)
        fm = QFontMetrics(font)

        full_text = active_line.full_text
        while font_sz > 12 and fm.horizontalAdvance(full_text) > (lw - 16):
            font_sz -= 1
            font.setPointSize(font_sz)
            painter.setFont(font)
            fm = QFontMetrics(font)

        line_h = fm.height()
        text_w = fm.horizontalAdvance(full_text)
        text_x = lx + (lw - text_w) / 2.0
        text_y = ly + fm.ascent()

        # Outline & Drop Shadow for 100% Contrast
        stroke_width = max(3.5, font_sz * 0.13)
        stroke_pen = QPen(QColor(0, 0, 0, 245), stroke_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        
        text_path = QPainterPath()
        text_path.addText(QPointF(text_x, text_y), font, full_text)
        
        # Deep black drop shadow
        shadow_path = QPainterPath()
        shadow_path.addText(QPointF(text_x + 3.5, text_y + 3.5), font, full_text)
        painter.strokePath(shadow_path, stroke_pen)
        painter.fillPath(shadow_path, QColor(0, 0, 0, 195))

        # Main text outline stroke
        painter.strokePath(text_path, stroke_pen)

        # Base unfilled text (Crisp pure white)
        painter.fillPath(text_path, QColor(255, 255, 255, 235))

        # 2. Dynamic Karaoke Sweep (Word-by-word or Line progress)
        line_dur = max(0.1, active_line.line_end - active_line.line_start)
        progress = max(0.0, min(1.0, (self.current_time - active_line.line_start) / line_dur))
        
        if progress > 0:
            sweep_w = text_w * progress
            painter.save()
            painter.setClipRect(QRectF(text_x - 4, ly - 10, sweep_w + 6, line_h + 20))
            
            # Glowing Gradient Fill (Cyan -> Luminous Gold -> Hot Pink)
            grad = QLinearGradient(text_x, ly, text_x + text_w, ly)
            grad.setColorAt(0.0, QColor("#00f5d4"))   # Electric Cyan
            grad.setColorAt(0.5, QColor("#ffe600"))   # Luminous Gold
            grad.setColorAt(1.0, QColor("#ff007f"))   # Hot Neon Pink
            
            painter.strokePath(text_path, stroke_pen)
            painter.fillPath(text_path, QBrush(grad))
            painter.restore()

        # 3. Upcoming Line in Clean Floating Glow (No heavy box)
        if active_idx + 1 < len(self.lyric_lines):
            next_line = self.lyric_lines[active_idx + 1]
            sub_sz = max(12, int(font_sz * 0.68))
            sub_font = QFont(self.font_family or "Montserrat", sub_sz, QFont.Bold)
            painter.setFont(sub_font)
            sub_fm = QFontMetrics(sub_font)
            sub_text = next_line.full_text

            while sub_sz > 10 and sub_fm.horizontalAdvance(sub_text) > (lw - 24):
                sub_sz -= 1
                sub_font.setPointSize(sub_sz)
                sub_fm = QFontMetrics(sub_font)

            sub_w = sub_fm.horizontalAdvance(sub_text)
            sub_x = lx + (lw - sub_w) / 2.0
            sub_y = ly + line_h + v_rect.height() * 0.05 + sub_fm.ascent()

            # Subtitle black outline + translucent white fill
            sub_path = QPainterPath()
            sub_path.addText(QPointF(sub_x, sub_y), sub_font, sub_text)
            painter.strokePath(sub_path, QPen(QColor(0, 0, 0, 220), max(2.5, sub_sz * 0.12), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.fillPath(sub_path, QColor(220, 235, 255, 190))

        painter.restore()

    def draw_eminem_rap_hiphop_stage(self, painter: QPainter, v_rect: QRect):
        """
        Draw Best of Eminem / Rap & HipHop 3D Animated Album Stage (Reference: https://youtu.be/OOKMf-kMEdg):
        - Dramatic fiery dark club lighting with drifting embers/smoke
        - 3D Glass Jewel Case with Album Cover Art + Parental Advisory badge
        - Spinning Holographic Chrome Compact Disc (CD) sliding out from the case
        - Top Rap & HipHop Playlist glowing badge and Track Title Header
        - Dual Stereo VU / Multi-band LED Peak Visualizer Bars
        """
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # 1. Dark fiery rap stage atmosphere
        bg_grad = QLinearGradient(v_rect.topLeft(), v_rect.bottomRight())
        bg_grad.setColorAt(0.0, QColor("#120508"))
        bg_grad.setColorAt(0.5, QColor("#1a080d"))
        bg_grad.setColorAt(1.0, QColor("#090204"))
        painter.fillRect(v_rect, bg_grad)

        # Deep crimson / amber stage light spots
        spot_center = QPointF(v_rect.x() + v_rect.width() * 0.22, v_rect.y() + v_rect.height() * 0.52)
        spot_grad = QRadialGradient(spot_center, v_rect.width() * 0.40)
        spot_grad.setColorAt(0.0, QColor(239, 68, 68, 90))   # Crimson Red
        spot_grad.setColorAt(0.5, QColor(245, 158, 11, 40))  # Amber
        spot_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(v_rect, spot_grad)

        # Animated drifting embers / spark particles
        for i in range(16):
            px = v_rect.x() + ((i * 73 + int(self.current_time * 25)) % int(v_rect.width()))
            py = v_rect.bottom() - ((i * 47 + int(self.current_time * 60)) % int(v_rect.height()))
            p_sz = max(1.5, (i % 3) + 1.0)
            p_alpha = int(120 + 80 * math.sin(self.current_time * 4.0 + i))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 140, 0, p_alpha))
            painter.drawEllipse(QPointF(px, py), p_sz, p_sz)

        # 2. 3D CD Jewel Case & Sliding Compact Disc (Left Side)
        case_w = min(v_rect.width() * 0.28, v_rect.height() * 0.56)
        case_h = case_w
        case_x = v_rect.x() + v_rect.width() * 0.08
        case_y = v_rect.y() + (v_rect.height() - case_h) * 0.55

        # CD Disc (Sliding out to the right of the case)
        cd_size = case_w * 0.94
        cd_cx = case_x + case_w * 0.72  # Halfway slid out
        cd_cy = case_y + case_h * 0.50
        cd_rect = QRectF(cd_cx - cd_size / 2.0, cd_cy - cd_size / 2.0, cd_size, cd_size)

        # Outer CD specular disc
        painter.setPen(QPen(QColor(180, 190, 205), 1.5))
        painter.setBrush(QColor(25, 28, 36))
        painter.drawEllipse(cd_rect)

        # Holographic Rainbow Conical Reflection Sweep
        cd_conic = QConicalGradient(cd_cx, cd_cy, (self.current_time * 120.0) % 360.0)
        cd_conic.setColorAt(0.00, QColor(0, 245, 212, 60))   # Cyan
        cd_conic.setColorAt(0.18, QColor(255, 0, 128, 70))   # Pink
        cd_conic.setColorAt(0.35, QColor(255, 230, 0, 60))   # Yellow
        cd_conic.setColorAt(0.50, QColor(0, 245, 212, 60))   # Cyan
        cd_conic.setColorAt(0.68, QColor(255, 0, 128, 70))   # Pink
        cd_conic.setColorAt(0.85, QColor(255, 230, 0, 60))   # Yellow
        cd_conic.setColorAt(1.00, QColor(0, 245, 212, 60))   # Cyan
        painter.setPen(Qt.NoPen)
        painter.setBrush(cd_conic)
        painter.drawEllipse(cd_rect)

        # Inner CD data tracks & center hole
        inner_r = cd_size * 0.38
        painter.setPen(QPen(QColor(255, 255, 255, 45), 1.0))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(cd_cx - inner_r / 2.0, cd_cy - inner_r / 2.0, inner_r, inner_r))

        clear_hub = cd_size * 0.22
        painter.setPen(QPen(QColor(255, 255, 255, 90), 1.0))
        painter.setBrush(QColor(15, 8, 12, 230))
        painter.drawEllipse(QRectF(cd_cx - clear_hub / 2.0, cd_cy - clear_hub / 2.0, clear_hub, clear_hub))

        center_spindle = cd_size * 0.09
        painter.setBrush(QColor("#080214"))
        painter.drawEllipse(QRectF(cd_cx - center_spindle / 2.0, cd_cy - center_spindle / 2.0, center_spindle, center_spindle))

        # 3D Jewel Case Shadow
        shadow_rect = QRectF(case_x + 8, case_y + 8, case_w, case_h)
        painter.fillRect(shadow_rect, QColor(0, 0, 0, 120))

        # Jewel Case Cover Art
        cover_rect = QRectF(case_x, case_y, case_w, case_h)
        active_pix = self.album_cover_pixmap if (getattr(self, 'album_cover_pixmap', None) and not self.album_cover_pixmap.isNull()) else self.bg_pixmap
        if active_pix and not active_pix.isNull():
            scaled = active_pix.scaled(int(case_w), int(case_h), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            sx = max(0, (scaled.width() - int(case_w)) // 2)
            sy = max(0, (scaled.height() - int(case_h)) // 2)
            painter.drawPixmap(cover_rect.toRect(), scaled, QRect(sx, sy, int(case_w), int(case_h)))
        else:
            c_grad = QLinearGradient(cover_rect.topLeft(), cover_rect.bottomRight())
            c_grad.setColorAt(0.0, QColor("#3b0712"))
            c_grad.setColorAt(0.6, QColor("#180509"))
            c_grad.setColorAt(1.0, QColor("#0a0204"))
            painter.fillRect(cover_rect, c_grad)
            painter.setPen(QColor(255, 255, 255, 240))
            painter.setFont(QFont("Impact", max(14, int(case_w * 0.12)), QFont.Bold))
            painter.drawText(cover_rect, Qt.AlignCenter, "RAP & HIPHOP\nGREATEST HITS")

        # Glass Case Glossy Specular Overlay & Plastic Spine
        glass_grad = QLinearGradient(cover_rect.topLeft(), cover_rect.bottomRight())
        glass_grad.setColorAt(0.0, QColor(255, 255, 255, 65))
        glass_grad.setColorAt(0.3, QColor(255, 255, 255, 10))
        glass_grad.setColorAt(0.7, QColor(0, 0, 0, 20))
        glass_grad.setColorAt(1.0, QColor(255, 255, 255, 35))
        painter.setPen(QPen(QColor(255, 255, 255, 90), 1.5))
        painter.setBrush(glass_grad)
        painter.drawRect(cover_rect)

        # Left spine ribbed strip
        spine_w = max(4.0, case_w * 0.04)
        painter.fillRect(QRectF(case_x, case_y, spine_w, case_h), QColor(20, 20, 25, 220))
        painter.setPen(QPen(QColor(255, 255, 255, 50), 1.0))
        for sp_y in range(int(case_y) + 4, int(case_y + case_h) - 4, 6):
            painter.drawLine(int(case_x + 1), sp_y, int(case_x + spine_w - 1), sp_y)

        # PARENTAL ADVISORY EXPLICIT CONTENT Badge (Bottom-Right of Jewel Case)
        pa_w = case_w * 0.36
        pa_h = pa_w * 0.46
        pa_rect = QRectF(cover_rect.right() - pa_w - 6, cover_rect.bottom() - pa_h - 6, pa_w, pa_h)
        painter.fillRect(pa_rect, QColor(255, 255, 255, 245))
        painter.setPen(QPen(Qt.black, 1.0))
        painter.drawRect(pa_rect)
        painter.setFont(QFont("Impact", max(5, int(pa_h * 0.38)), QFont.Bold))
        painter.drawText(QRectF(pa_rect.x(), pa_rect.y() + 1, pa_rect.width(), pa_rect.height() * 0.5), Qt.AlignCenter, "PARENTAL")
        painter.setFont(QFont("Arial", max(4, int(pa_h * 0.28)), QFont.Black))
        painter.drawText(QRectF(pa_rect.x(), pa_rect.y() + pa_rect.height() * 0.45, pa_rect.width(), pa_rect.height() * 0.5), Qt.AlignCenter, "ADVISORY")

        # 3. Top Rap Playlist Banner & Header
        badge_text = "🔥 BEST OF RAP & HIPHOP PLAYLIST 🔥"
        badge_font_sz = max(9, int(v_rect.height() * 0.024))
        badge_font = QFont("Montserrat", badge_font_sz, QFont.Black)
        painter.setFont(badge_font)
        badge_fm = QFontMetrics(badge_font)
        
        badge_w = badge_fm.horizontalAdvance(badge_text) + 28.0
        badge_h = max(22.0, badge_fm.height() + 10.0)
        badge_x = v_rect.x() + (v_rect.width() - badge_w) / 2.0
        badge_y = v_rect.y() + v_rect.height() * 0.04
        badge_rect = QRectF(badge_x, badge_y, badge_w, badge_h)
        
        # Fire gradient border pill
        painter.setPen(QPen(QColor("#ef4444"), 1.5))
        painter.setBrush(QColor(24, 6, 12, 235))
        painter.drawRoundedRect(badge_rect, badge_h / 2.0, badge_h / 2.0)
        painter.setPen(QColor("#f59e0b"))
        painter.drawText(badge_rect, Qt.AlignCenter, badge_text)

        # Track Title & Artist Subheader
        title_font = QFont("Impact", max(13, int(v_rect.height() * 0.040)), QFont.Bold)
        title_font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        painter.setFont(title_font)
        title_fm = QFontMetrics(title_font)
        
        t_artist = (self.track_artist or "EMINEM").upper()
        t_name = (self.track_title or "LOSE YOURSELF").upper()
        t_full = f"{t_artist} — {t_name}" if t_artist != "ARTIST" else t_name
        
        title_y = badge_rect.bottom() + v_rect.height() * 0.012
        title_rect = QRectF(v_rect.x() + v_rect.width() * 0.05, title_y, v_rect.width() * 0.90, title_fm.height() + 4.0)
        
        # Shadow + Main text
        painter.setPen(QColor(0, 0, 0, 220))
        painter.drawText(QRectF(title_rect.x() + 1.5, title_rect.y() + 1.5, title_rect.width(), title_rect.height()), Qt.AlignCenter, t_full)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(title_rect, Qt.AlignCenter, t_full)

        # 4. Multi-band Stereo LED Equalizer Spectrum (Bottom Right)
        eq_y = v_rect.y() + v_rect.height() * 0.90
        eq_w = v_rect.width() * 0.48
        eq_x = v_rect.x() + v_rect.width() * 0.46
        num_bars = 28
        bar_step = eq_w / num_bars
        bar_w = max(2.5, bar_step * 0.65)
        
        peaks = getattr(self, 'waveform_peaks', None) or []
        for i in range(num_bars):
            peak_val = 0.5
            if peaks:
                peak_idx = int((i / float(num_bars)) * len(peaks)) % len(peaks)
                peak_val = peaks[peak_idx]
            wave_val = abs(math.sin(self.current_time * 10.0 + i * 0.35) * math.cos(self.current_time * 6.0 + i * 0.20))
            combined_val = (wave_val * 0.55 + peak_val * 0.45)
            
            bh = max(3.0, combined_val * v_rect.height() * 0.10)
            bx = eq_x + i * bar_step
            
            # LED Gradient (Green -> Amber -> Red Peak)
            bar_grad = QLinearGradient(bx, eq_y, bx, eq_y - bh)
            bar_grad.setColorAt(0.0, QColor("#10b981"))   # Emerald Green
            bar_grad.setColorAt(0.6, QColor("#f59e0b"))   # Amber
            bar_grad.setColorAt(1.0, QColor("#ef4444"))   # Crimson Red
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(bar_grad)
            painter.drawRoundedRect(QRectF(bx, eq_y - bh, bar_w, bh), 1.5, 1.5)

            # Mirror reflection
            ref_bh = bh * 0.35
            ref_grad = QLinearGradient(bx, eq_y, bx, eq_y + ref_bh)
            ref_grad.setColorAt(0.0, QColor(245, 158, 11, 70))
            ref_grad.setColorAt(1.0, QColor(245, 158, 11, 0))
            painter.setBrush(ref_grad)
            painter.drawRoundedRect(QRectF(bx, eq_y + 1, bar_w, ref_bh), 1.0, 1.0)

        painter.restore()

    def draw_eminem_rap_hiphop_lyrics(self, painter: QPainter, v_rect: QRect):
        """Draw bold kinetic rap lyrics with fire gradient highlight and high contrast."""
        active_idx, active_line = self._active_lyric()
        if active_line is None:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # Right pane bounds
        lx = v_rect.x() + v_rect.width() * 0.44
        lw = v_rect.width() * 0.51
        ly = v_rect.y() + v_rect.height() * 0.40

        # 1. Main Active Rap Line
        font_sz = max(22, int(self.font_size * v_rect.width() / 1280))
        font = QFont(self.font_family or "Impact", font_sz, QFont.Bold)
        painter.setFont(font)
        fm = QFontMetrics(font)

        full_text = active_line.full_text.upper() if getattr(self, 'uppercase_lyrics', True) else active_line.full_text
        while font_sz > 14 and fm.horizontalAdvance(full_text) > (lw - 16):
            font_sz -= 1
            font.setPointSize(font_sz)
            painter.setFont(font)
            fm = QFontMetrics(font)

        line_h = fm.height()
        text_w = fm.horizontalAdvance(full_text)
        text_x = lx + (lw - text_w) / 2.0
        text_y = ly + fm.ascent()

        # Outline & Drop Shadow for 100% Contrast
        stroke_width = max(3.5, font_sz * 0.12)
        stroke_pen = QPen(QColor(0, 0, 0, 250), stroke_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        
        text_path = QPainterPath()
        text_path.addText(QPointF(text_x, text_y), font, full_text)
        
        # Deep black drop shadow
        shadow_path = QPainterPath()
        shadow_path.addText(QPointF(text_x + 3.5, text_y + 3.5), font, full_text)
        painter.strokePath(shadow_path, stroke_pen)
        painter.fillPath(shadow_path, QColor(0, 0, 0, 210))

        # Main outline stroke
        painter.strokePath(text_path, stroke_pen)

        # Base unfilled text
        painter.fillPath(text_path, QColor(255, 255, 255, 235))

        # 2. Dynamic Karaoke Sweep (Fire gradient)
        line_dur = max(0.1, active_line.line_end - active_line.line_start)
        progress = max(0.0, min(1.0, (self.current_time - active_line.line_start) / line_dur))
        
        if progress > 0:
            sweep_w = text_w * progress
            painter.save()
            painter.setClipRect(QRectF(text_x - 4, ly - 10, sweep_w + 6, line_h + 20))
            
            grad = QLinearGradient(text_x, ly, text_x + text_w, ly)
            grad.setColorAt(0.0, QColor("#ef4444"))   # Flame Red
            grad.setColorAt(0.5, QColor("#f59e0b"))   # Amber Gold
            grad.setColorAt(1.0, QColor("#ffffff"))   # Pure White Tip
            
            painter.strokePath(text_path, stroke_pen)
            painter.fillPath(text_path, QBrush(grad))
            painter.restore()

        # 3. Upcoming Line Preview
        if active_idx + 1 < len(self.lyric_lines):
            next_line = self.lyric_lines[active_idx + 1]
            sub_sz = max(13, int(font_sz * 0.65))
            sub_font = QFont(self.font_family or "Impact", sub_sz, QFont.Bold)
            painter.setFont(sub_font)
            sub_fm = QFontMetrics(sub_font)
            sub_text = next_line.full_text.upper() if getattr(self, 'uppercase_lyrics', True) else next_line.full_text

            while sub_sz > 10 and sub_fm.horizontalAdvance(sub_text) > (lw - 24):
                sub_sz -= 1
                sub_font.setPointSize(sub_sz)
                sub_fm = QFontMetrics(sub_font)

            sub_w = sub_fm.horizontalAdvance(sub_text)
            sub_x = lx + (lw - sub_w) / 2.0
            sub_y = ly + line_h + v_rect.height() * 0.05 + sub_fm.ascent()

            sub_path = QPainterPath()
            sub_path.addText(QPointF(sub_x, sub_y), sub_font, sub_text)
            painter.strokePath(sub_path, QPen(QColor(0, 0, 0, 220), max(2.5, sub_sz * 0.11), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.fillPath(sub_path, QColor(255, 220, 220, 180))

        painter.restore()

    def draw_tiki_tiki_stage(self, painter: QPainter, v_rect: QRect):
        """Draw the reference's split portraits, active-singer dimming and paper tear for N custom singers."""
        singers = self.custom_singers if self.custom_singers else [
            {"name": "SUZANA", "role": "female", "color": "#b50b56", "avatar": "S", "image_path": ""},
            {"name": "VANNDA", "role": "male", "color": "#a9470b", "avatar": "V", "image_path": ""}
        ]
        if not singers:
            return
        painter.save()
        stage_h = int(v_rect.height() * 0.49)
        num_singers = max(1, len(singers))
        card_w = v_rect.width() / float(num_singers)
        _, active_line = self._active_lyric()
        active_role = getattr(active_line, 'singer', 'both') if active_line else 'both'

        for idx in range(num_singers):
            singer = singers[idx]
            role = singer.get('role', 'female' if idx == 0 else ('male' if idx == 1 else singer.get('name', f'singer_{idx}')))
            s_name = singer.get('name', f'SINGER {idx+1}')
            card = QRectF(v_rect.x() + idx * card_w, v_rect.y(), card_w, stage_h)
            color = QColor(singer.get('color', '#b50b56'))
            gradient = QLinearGradient(card.topLeft(), card.bottomRight())
            gradient.setColorAt(0, color.lighter(135))
            gradient.setColorAt(1, color.darker(190))
            painter.fillRect(card, gradient)

            image_path = singer.get('image_path', '')
            if image_path and os.path.exists(image_path):
                pix = QPixmap(image_path)
                if not pix.isNull():
                    scaled = pix.scaled(int(card.width()), int(card.height()), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                    sx = max(0, (scaled.width() - int(card.width())) // 2)
                    sy = max(0, (scaled.height() - int(card.height())) // 2)
                    painter.drawPixmap(card.toRect(), scaled, QRect(sx, sy, int(card.width()), int(card.height())))
            else:
                painter.setPen(QColor(255, 255, 255, 110))
                painter.setFont(QFont("Montserrat", max(24, int(stage_h * 0.28)), QFont.Black))
                painter.drawText(card, Qt.AlignCenter, singer.get('avatar', s_name[:1]))

            # Active singer dimming: when both/all sing, NONE are dimmed.
            is_active_singer = (active_role in ('both', 'all') or active_role == role or active_role == s_name or (active_role == 'female' and idx == 0) or (active_role == 'male' and idx == 1))
            if not is_active_singer:
                painter.fillRect(card, QColor(8, 12, 18, 205))

            label_h = max(22, int(v_rect.height() * 0.052))
            label = QRectF(card.left(), card.bottom() - label_h, card.width(), label_h)
            painter.fillRect(label, QColor(color.red(), color.green(), color.blue(), 235))
            name_font = QFont("Arial", max(9, int(label_h * 0.52)), QFont.Black)
            name_font.setItalic(True)
            painter.setFont(name_font)
            painter.setPen(QPen(Qt.white, max(1, int(v_rect.width() / 900))))
            painter.drawText(label, Qt.AlignCenter, s_name.upper())

        paper_top = v_rect.y() + stage_h
        tear = max(4, int(v_rect.height() * 0.012))
        points = [QPointF(v_rect.left(), v_rect.bottom()), QPointF(v_rect.left(), paper_top)]
        step = max(10, int(v_rect.width() / 42))
        x = v_rect.left()
        index = 0
        while x <= v_rect.right():
            offset = -tear if index % 3 == 0 else tear if index % 3 == 1 else 0
            points.append(QPointF(x, paper_top + offset))
            x += step
            index += 1
        points.append(QPointF(v_rect.right(), v_rect.bottom()))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#fbfaf0"))
        painter.drawPolygon(QPolygonF(points))
        painter.restore()

    def draw_tiki_tiki_lyrics(self, painter: QPainter, v_rect: QRect):
        """Show the active line and its stanza cleanly vertically centered on the warm paper field."""
        active_idx, active_line = self._active_lyric()
        if active_line is None:
            return
        lines = self.lyric_lines[active_idx:min(len(self.lyric_lines), active_idx + 3)]
        if not lines:
            return

        stage_h = int(v_rect.height() * 0.49)
        tear = max(4, int(v_rect.height() * 0.012))
        paper_top = v_rect.y() + stage_h + tear
        paper_bottom = v_rect.bottom() - int(v_rect.height() * 0.04)
        available_h = max(20, paper_bottom - paper_top)

        max_width = int(v_rect.width() * 0.88)
        size = max(15, int(self.font_size * v_rect.width() / 1300))
        font = QFont(self.font_family or "Arial", size)
        font.setItalic(True)
        painter.save()
        painter.setFont(font)
        metrics = QFontMetrics(font)

        while size > 12 and any(metrics.horizontalAdvance(line.full_text) > max_width for line in lines):
            size -= 1
            font.setPointSize(size)
            painter.setFont(font)
            metrics = QFontMetrics(font)

        line_h = min(int(available_h / max(1, len(lines))), int(metrics.height() * 1.35))
        total_text_h = len(lines) * line_h
        y = paper_top + (available_h - total_text_h) / 2.0

        for line in lines:
            role = getattr(line, 'singer', 'both')
            if role in ('both', 'all'):
                color = self.both_color
            elif role == 'female' or (len(self.custom_singers) > 0 and (role == self.custom_singers[0].get('role') or role == self.custom_singers[0].get('name'))):
                color = QColor(self.custom_singers[0].get('color', '#b50b56'))
            elif role == 'male' or (len(self.custom_singers) > 1 and (role == self.custom_singers[1].get('role') or role == self.custom_singers[1].get('name'))):
                color = QColor(self.custom_singers[1].get('color', '#a9470b'))
            else:
                matched_col = None
                for s in self.custom_singers:
                    if role in (s.get('role'), s.get('name')):
                        matched_col = QColor(s.get('color', '#10b981'))
                        break
                color = matched_col or self.both_color

            is_active = (line == active_line)
            f = QFont(font)
            if is_active:
                f.setBold(True)
            painter.setFont(f)

            rect = QRectF(v_rect.left() + v_rect.width() * 0.05, y, v_rect.width() * 0.9, line_h)
            
            # Subtle drop shadow for clarity
            shadow_rect = QRectF(rect.x() + 1, rect.y() + 1, rect.width(), rect.height())
            painter.setPen(QColor(0, 0, 0, 45 if is_active else 20))
            painter.drawText(shadow_rect, Qt.AlignHCenter | Qt.AlignVCenter, line.full_text)

            text_color = color if is_active else QColor(color.red(), color.green(), color.blue(), 165)
            painter.setPen(text_color)
            painter.drawText(rect, Qt.AlignHCenter | Qt.AlignVCenter, line.full_text)
            y += line_h

        painter.restore()

    def draw_color_coded_lyrics(self, painter: QPainter, v_rect: QRect):
        """Draws center lyric in golden warm glow script with kinetic motion matching TIKI TIKI."""
        if not self.lyric_lines:
            return

        # Find active line within lead-in or singing window
        active_line = None
        for line in self.lyric_lines:
            if line.line_start - 2.0 <= self.current_time <= line.line_end + 0.8:
                active_line = line
                break

        if not active_line:
            return

        scale = v_rect.width() / 1000.0
        calc_size = max(18, int(self.font_size * scale * 1.35))

        font = QFont(self.font_family, calc_size)
        if "Montserrat" in self.font_family:
            font.setBold(True)
        else:
            font.setItalic(True)
        painter.setFont(font)
        fm = QFontMetrics(font)

        max_width = v_rect.width() * 0.86
        while calc_size > 16 and fm.horizontalAdvance(active_line.full_text) > max_width:
            calc_size -= 1
            font.setPointSize(calc_size)
            fm = QFontMetrics(font)
        painter.setFont(font)

        tw = fm.horizontalAdvance(active_line.full_text)
        tx = v_rect.x() + (v_rect.width() - tw) // 2
        base_ty = v_rect.y() + int(v_rect.height() * 0.65)

        # Kinetic Motion Entry Offset (Pop & Bounce / Slide Up)
        t_entry = self.current_time - active_line.line_start
        dy = 0.0
        if 0.0 <= t_entry <= 0.35:
            if "Bounce" in self.motion_effect:
                dy = math.sin((t_entry / 0.35) * math.pi) * -14.0
            elif "Slide" in self.motion_effect:
                dy = max(0.0, 1.0 - (t_entry / 0.35)) * 18.0

        ty = base_ty + dy

        curr_x = tx
        for word in active_line.words:
            w_text = word.text
            w_w = fm.horizontalAdvance(w_text)
            
            if self.current_time < word.start_time:
                sweep_prog = 0.0
            elif self.current_time >= word.end_time:
                sweep_prog = 1.0
            else:
                dur = max(0.05, word.end_time - word.start_time)
                sweep_prog = (self.current_time - word.start_time) / dur
                sweep_prog = max(0.0, min(1.0, sweep_prog))

            # 1. Soft Drop Shadow for maximum contrast against any background
            shadow_path = QPainterPath()
            shadow_path.addText(float(curr_x + 2.0 * scale), float(ty + 2.0 * scale), font, w_text)
            painter.fillPath(shadow_path, QBrush(QColor(0, 0, 0, 180)))

            text_path = QPainterPath()
            text_path.addText(float(curr_x), float(ty), font, w_text)

            # 2. Golden Glow Aura on swept words
            if self.enable_glow and sweep_prog > 0.0:
                glow_col = QColor(245, 158, 11, int(140 * sweep_prog))
                glow_pen = QPen(glow_col, 12 * scale, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.strokePath(text_path, glow_pen)

            # 3. High Contrast Outline Stroke
            painter.strokePath(text_path, QPen(QColor(0, 0, 0, 240), 3.2 * scale, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            
            # 4. Base unsung text fill (Pure White)
            painter.fillPath(text_path, QBrush(QColor(255, 255, 255)))

            # 5. Progressive Active Word Sweep
            if sweep_prog > 0.0:
                painter.save()
                swept_w = w_w * sweep_prog
                clip_rect = QRectF(curr_x - 4, ty - calc_size * 1.5, swept_w + 4, calc_size * 2.0)
                painter.setClipRect(clip_rect)

                # Crisp stroked active text
                painter.strokePath(text_path, QPen(QColor(0, 0, 0, 240), 3.2 * scale, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

                # Golden Gradient Fill (#fbbf24 -> #d97706)
                grad = QLinearGradient(curr_x, ty - calc_size, curr_x, ty)
                grad.setColorAt(0.0, QColor("#fbbf24"))
                grad.setColorAt(1.0, QColor("#d97706"))
                painter.fillPath(text_path, QBrush(grad))
                painter.restore()

            curr_x += w_w

    def draw_karaoke_lyrics(self, painter: QPainter, v_rect: QRect):
        if not self.lyric_lines:
            return

        LEAD_IN = 2.0
        LINGER = 0.5
        display_lines = []

        if self.display_mode in {'SINGLE', 'BUILD'}:
            for i, line in enumerate(self.lyric_lines):
                s_vis = max(0.0, line.line_start - LEAD_IN) if i == 0 else max(self.lyric_lines[i - 1].line_end + 0.2, line.line_start - LEAD_IN)
                if s_vis <= self.current_time <= line.line_end + LINGER:
                    display_lines.append((0, line))
                    break
        else:
            # Alternating Dual-Line Karaoke Staggering:
            # Slot 0 (Top slot) holds even-indexed lines (0, 2, 4, 6...)
            for i in range(0, len(self.lyric_lines), 2):
                l = self.lyric_lines[i]
                start_vis = max(0.0, l.line_start - LEAD_IN) if i == 0 else max(self.lyric_lines[i - 2].line_end + 0.2, min(self.lyric_lines[i - 1].line_start, l.line_start - LEAD_IN))
                end_vis = l.line_end + LINGER
                if start_vis <= self.current_time <= end_vis:
                    display_lines.append((0, l))
                    break

            # Slot 1 (Bottom slot) holds odd-indexed lines (1, 3, 5, 7...)
            for j in range(1, len(self.lyric_lines), 2):
                l = self.lyric_lines[j]
                start_vis = min(self.lyric_lines[0].line_start, l.line_start - LEAD_IN) if j == 1 else max(self.lyric_lines[j - 2].line_end + 0.2, min(self.lyric_lines[j - 1].line_start, l.line_start - LEAD_IN))
                end_vis = l.line_end + LINGER
                if start_vis <= self.current_time <= end_vis:
                    display_lines.append((1, l))
                    break

        if not display_lines:
            return

        scale_factor = v_rect.width() / 1000.0
        calc_font_size = max(16, int(self.font_size * scale_factor))
        
        font = QFont(self.font_family, calc_font_size)
        font.setItalic(self.is_italic)
        if "900" in self.font_weight_str or "Cực Đậm" in self.font_weight_str:
            font.setWeight(QFont.Black)
        else:
            font.setWeight(QFont.Bold)
        painter.setFont(font)
        fm = QFontMetrics(font)

        max_line_width = v_rect.width() * 0.84
        minimum_font_size = max(8, int(16 * scale_factor))

        def rendered_line_width(line):
            return sum(fm.horizontalAdvance(word.text) for word in line.words)

        while calc_font_size > minimum_font_size and any(
            rendered_line_width(line) > max_line_width for _, line in display_lines
        ):
            calc_font_size -= 1
            font.setPointSize(calc_font_size)
            fm = QFontMetrics(font)
        painter.setFont(font)

        if self.display_mode in {'SINGLE', 'BUILD'}:
            top_y = v_rect.y() + int(v_rect.height() * (self.pos_y_bottom / 100.0))
            bottom_y = top_y
        else:
            top_y = v_rect.y() + int(v_rect.height() * (self.pos_y_top / 100.0))
            bottom_y = v_rect.y() + int(v_rect.height() * (self.pos_y_bottom / 100.0))
        pad_x_px = int(v_rect.width() * (self.padding_x_percent / 100.0))

        for slot_order, line in display_lines:
            y_pos = top_y if (slot_order == 0) else bottom_y
            total_text_w = rendered_line_width(line)
            singer = getattr(line, 'singer', 'both')
            active_fill_col = self.female_color if singer == "female" else (self.both_color if singer == "both" else self.male_color)
            
            if self.layout_mode == 'left_right':
                if slot_order == 0:
                    start_x = v_rect.x() + pad_x_px
                else:
                    start_x = v_rect.x() + v_rect.width() - total_text_w - pad_x_px
            else:
                align = getattr(self, 'text_alignment', 'center')
                if align == 'left':
                    start_x = v_rect.x() + pad_x_px
                elif align == 'right':
                    start_x = v_rect.x() + v_rect.width() - total_text_w - pad_x_px
                else:
                    start_x = v_rect.x() + (v_rect.width() - total_text_w) // 2

            is_singing_now = line.line_start <= self.current_time <= line.line_end
            
            # Kinetic Motion Entry Offset (Pop & Bounce / Slide Up / Fade)
            t_entry = self.current_time - line.line_start
            dy = 0.0
            if 0.0 <= t_entry <= 0.35 and is_singing_now:
                if "Bounce" in self.motion_effect:
                    dy = math.sin((t_entry / 0.35) * math.pi) * -12.0
                elif "Slide" in self.motion_effect:
                    dy = max(0.0, 1.0 - (t_entry / 0.35)) * 16.0

            actual_y = y_pos + dy

            if self.enable_pointer and is_singing_now:
                retro_pix = self.retro_icons.get(singer)
                if retro_pix is None or retro_pix.isNull():
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    fpath = os.path.join(base_dir, "assets", "icons", f"{singer}_retro.png")
                    if os.path.exists(fpath):
                        self.retro_icons[singer] = QPixmap(fpath)
                        retro_pix = self.retro_icons.get(singer)

                target_h = max(34, int(calc_font_size * 1.65))
                if retro_pix and not retro_pix.isNull() and retro_pix.height() > 0:
                    target_w = max(34, int(target_h * (retro_pix.width() / float(retro_pix.height()))))
                    badge_x = start_x - target_w - int(calc_font_size * 0.32)
                    badge_y = actual_y - fm.ascent() + (fm.ascent() - target_h) / 2.0

                    painter.save()
                    scaled_icon = retro_pix.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    # Subtle drop shadow for sticker pop
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(0, 0, 0, 90))
                    painter.drawPixmap(int(badge_x), int(badge_y), scaled_icon)
                    painter.restore()
                else:
                    target_w = target_h
                    badge_x = start_x - target_w - int(calc_font_size * 0.32)
                    badge_y = actual_y - fm.ascent() + (fm.ascent() - target_h) / 2.0

                    painter.save()
                    badge_rect = QRectF(badge_x, badge_y, target_w, target_h)
                    painter.setPen(QPen(QColor(255, 255, 255), 2.5))
                    painter.setBrush(QColor("#0026ff") if singer == "male" else (QColor("#ff0033") if singer == "female" else QColor("#ff007f")))
                    painter.drawRoundedRect(badge_rect, 8, 8)

                    icon_font = QFont("Segoe UI Emoji", int(calc_font_size * 0.7))
                    painter.setFont(icon_font)
                    painter.setPen(QColor(255, 255, 255))
                    icon_char = self.pointer_icons.get(singer, self.pointer_icon or "🎤")
                    painter.drawText(badge_rect, Qt.AlignCenter, icon_char)
                    painter.restore()
                painter.setFont(font)

            curr_x = start_x
            for word in line.words:
                w_text = word.text
                w_w = fm.horizontalAdvance(w_text)
                
                if self.current_time < word.start_time:
                    sweep_prog = 0.0
                elif self.current_time >= word.end_time:
                    sweep_prog = 1.0
                else:
                    dur = max(0.05, word.end_time - word.start_time)
                    sweep_prog = (self.current_time - word.start_time) / dur
                    sweep_prog = max(0.0, min(1.0, sweep_prog))

                # 1. Soft Drop Shadow for maximum readability
                shadow_path = QPainterPath()
                shadow_path.addText(float(curr_x + 2.0 * scale_factor), float(actual_y + 2.0 * scale_factor), font, w_text)
                painter.fillPath(shadow_path, QBrush(QColor(0, 0, 0, 190)))

                text_path = QPainterPath()
                text_path.addText(float(curr_x), float(actual_y), font, w_text)

                if self.enable_glow and self.glow_radius > 0 and sweep_prog > 0.0:
                    glow_pen = QPen(
                        QColor(active_fill_col.red(), active_fill_col.green(), active_fill_col.blue(), 90),
                        (self.stroke_width + self.glow_radius) * scale_factor,
                        Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin
                    )
                    painter.strokePath(text_path, glow_pen)

                pen = QPen(self.stroke_color, (self.stroke_width + 1.8) * scale_factor, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.strokePath(text_path, pen)
                painter.fillPath(text_path, QBrush(self.base_color))

                if sweep_prog > 0.0:
                    painter.save()
                    swept_w = w_w * sweep_prog
                    
                    clip_rect = QRectF(curr_x - 4, actual_y - calc_font_size * 1.8, swept_w + 4, calc_font_size * 2.5)
                    painter.setClipRect(clip_rect)

                    active_pen = QPen(
                        QColor(0, 0, 0, 245),
                        (self.stroke_width + 1.8) * scale_factor,
                        Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin
                    )
                    painter.strokePath(text_path, active_pen)
                    painter.fillPath(text_path, QBrush(active_fill_col))
                    painter.restore()

                curr_x += w_w

    def draw_overlay_objects(self, painter: QPainter, v_rect: QRect):
        for idx, obj in enumerate(self.overlay_objects):
            if not obj.get('visible', True):
                continue
            ox = v_rect.x() + int((obj.get('x_pct', 28.5) / 100.0) * v_rect.width())
            oy = v_rect.y() + int((obj.get('y_pct', 46.8) / 100.0) * v_rect.height())
            ow = int((obj.get('w_pct', 40.0) / 100.0) * v_rect.width())
            oh = int((obj.get('h_pct', 10.0) / 100.0) * v_rect.height())
            
            obj_rect = QRect(ox, oy, ow, oh)
            painter.save()
            painter.setOpacity(max(0.0, min(1.0, float(obj.get('opacity', 1.0)))))
            rotation = float(obj.get('rotation', 0))
            if rotation:
                center = obj_rect.center()
                painter.translate(center.x(), center.y())
                painter.rotate(rotation)
                painter.translate(-center.x(), -center.y())

            if obj.get('type') == 'shape':
                painter.setPen(QPen(QColor(obj.get('stroke_color', obj.get('color', '#ff2d55'))), max(0, int(obj.get('stroke_width', 0)))))
                painter.setBrush(QColor(obj.get('color', '#ff2d55')))
                painter.drawRoundedRect(QRectF(obj_rect), 6, 6)
            elif obj.get('type') == 'lower_third':
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(obj.get('color', '#0f172a')))
                painter.drawRoundedRect(QRectF(obj_rect), 6, 6)
                
                painter.setFont(QFont("Montserrat", 11, QFont.Bold))
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(QRect(ox + 14, oy + 4, ow - 28, 20), Qt.AlignLeft, obj.get('title', ''))
                
                painter.setFont(QFont("Segoe UI", 9))
                painter.setPen(QColor(203, 213, 225))
                painter.drawText(QRect(ox + 14, oy + 24, ow - 28, 18), Qt.AlignLeft, obj.get('subtitle', ''))
            elif obj.get('type') == 'vinyl':
                disc_size = min(ow, oh)
                dx = ox + (ow - disc_size) / 2.0
                dy = oy + (oh - disc_size) / 2.0
                disc_rect = QRectF(dx, dy, disc_size, disc_size)
                
                # Outer black vinyl body
                painter.setPen(QPen(QColor(40, 40, 48), 2.0))
                painter.setBrush(QColor(15, 15, 22))
                painter.drawEllipse(disc_rect)
                
                # Concentric grooves
                for r_pct in (0.92, 0.84, 0.76, 0.68, 0.60):
                    r_sz = disc_size * r_pct
                    r_rx = dx + (disc_size - r_sz) / 2.0
                    r_ry = dy + (disc_size - r_sz) / 2.0
                    painter.setPen(QPen(QColor(255, 255, 255, 20), 1.0))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(QRectF(r_rx, r_ry, r_sz, r_sz))
                
                # Center Spinning Album Label
                label_sz = disc_size * 0.40
                lx = dx + (disc_size - label_sz) / 2.0
                ly = dy + (disc_size - label_sz) / 2.0
                label_rect = QRectF(lx, ly, label_sz, label_sz)
                
                painter.save()
                spin_angle = (self.current_time * 45.0) % 360.0
                painter.translate(disc_rect.center().x(), disc_rect.center().y())
                painter.rotate(spin_angle)
                painter.translate(-disc_rect.center().x(), -disc_rect.center().y())
                
                grad = QLinearGradient(label_rect.topLeft(), label_rect.bottomRight())
                grad.setColorAt(0.0, QColor("#ff2d55"))
                grad.setColorAt(1.0, QColor("#f59e0b"))
                painter.setPen(Qt.NoPen)
                painter.setBrush(grad)
                painter.drawEllipse(label_rect)
                
                painter.setFont(QFont("Montserrat", max(7, int(label_sz * 0.18)), QFont.Bold))
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(label_rect, Qt.AlignCenter, obj.get('title', 'VINYL')[:8])
                painter.restore()
                
                # Center Spindle Hole
                hole_sz = disc_size * 0.08
                hx = dx + (disc_size - hole_sz) / 2.0
                hy = dy + (disc_size - hole_sz) / 2.0
                painter.setPen(QPen(QColor(220, 220, 220), 1.5))
                painter.setBrush(QColor(241, 243, 249))
                painter.drawEllipse(QRectF(hx, hy, hole_sz, hole_sz))
            else:
                content = obj.get('content', 'Nhập nội dung văn bản...')
                f_size = max(12, int(obj.get('font_size', 32) * (v_rect.width() / 1000.0)))
                f_fam = obj.get('font_family', 'Montserrat')
                
                font = QFont(f_fam, f_size)
                weight = int(obj.get('font_weight', 600))
                font.setWeight(QFont.Black if weight >= 900 else QFont.Bold if weight >= 700 else QFont.DemiBold if weight >= 600 else QFont.Normal)
                painter.setFont(font)
                
                fm = QFontMetrics(font)
                tw = fm.horizontalAdvance(content)
                alignment = obj.get('alignment', 'center')
                if alignment == 'left':
                    tx = ox
                elif alignment == 'right':
                    tx = ox + ow - tw
                else:
                    tx = ox + (ow - tw) // 2
                ty = oy + oh // 2 + fm.ascent() // 2
                
                t_path = QPainterPath()
                t_path.addText(float(tx), float(ty), font, content)
                
                painter.strokePath(t_path, QPen(QColor(obj.get('stroke_color', '#000000')), float(obj.get('stroke_width', 2))))
                painter.fillPath(t_path, QBrush(QColor(obj.get('color', '#ffffff'))))

            painter.restore()

            if self.selected_object_idx == idx:
                painter.save()
                sel_pen = QPen(QColor(0, 210, 255), 1.5, Qt.DashLine)
                painter.setPen(sel_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(obj_rect)
                
                handle_color = QColor(0, 210, 255)
                painter.setPen(Qt.NoPen)
                painter.setBrush(handle_color)
                handle_size = 6
                
                points = [
                    obj_rect.topLeft(),
                    obj_rect.topRight(),
                    obj_rect.bottomLeft(),
                    obj_rect.bottomRight()
                ]
                for pt in points:
                    painter.drawRect(pt.x() - handle_size // 2, pt.y() - handle_size // 2, handle_size, handle_size)

                rotation_anchor = QPointF(obj_rect.center().x(), obj_rect.top() - 18)
                painter.setPen(QPen(handle_color, 1.2))
                painter.drawLine(obj_rect.center().x(), obj_rect.top(), int(rotation_anchor.x()), int(rotation_anchor.y()))
                painter.setBrush(handle_color)
                painter.drawEllipse(rotation_anchor, 4, 4)
                
                painter.restore()

        if self._snap_x:
            painter.setPen(QPen(QColor("#ff4fb8"), 1.0, Qt.DashLine))
            painter.drawLine(v_rect.center().x(), v_rect.top(), v_rect.center().x(), v_rect.bottom())
        if self._snap_y:
            painter.setPen(QPen(QColor("#ff4fb8"), 1.0, Qt.DashLine))
            painter.drawLine(v_rect.left(), v_rect.center().y(), v_rect.right(), v_rect.center().y())

    def draw_safe_area_guides(self, painter: QPainter, v_rect: QRect):
        painter.save()
        painter.setPen(QPen(QColor(255, 255, 255, 45), 1.0, Qt.DashLine))
        margin_x = max(8, int(v_rect.width() * 0.05))
        margin_y = max(8, int(v_rect.height() * 0.05))
        painter.drawRect(v_rect.adjusted(margin_x, margin_y, -margin_x, -margin_y))
        painter.restore()

    def draw_watermark(self, painter: QPainter, v_rect: QRect):
        painter.save()
        painter.setFont(QFont("Segoe UI", max(7, int(v_rect.width() * 0.009)), QFont.DemiBold))
        painter.setPen(QColor(255, 255, 255, 145))
        painter.drawText(v_rect.adjusted(0, 0, -12, -8), Qt.AlignRight | Qt.AlignBottom, "MADE WITH LYLIS")
        painter.restore()

    def mousePressEvent(self, event):
        v_rect = self.get_viewport_rect()
        if event.button() == Qt.LeftButton:
            if self.template_variant == 'multi_song_album':
                tracks = list(self.album_tracks or [])
                queue = QRectF(v_rect.x() + v_rect.width() * 0.48, v_rect.y() + v_rect.height() * 0.08,
                               v_rect.width() * 0.46, v_rect.height() * 0.50)
                max_visible = 6
                total_tracks = len(tracks)
                active_idx = next((index for index, track in enumerate(tracks) if track.get('id') == self.active_album_track_id), 0)
                start_idx = 0 if total_tracks <= max_visible else max(0, min(total_tracks - max_visible, active_idx - max_visible // 2))
                visible_count = min(total_tracks, max_visible)
                row_h = min(28.0, max(18.0, (queue.height() - 44) / max(1, visible_count)))
                for offset in range(visible_count):
                    index = start_idx + offset
                    if index >= total_tracks:
                        break
                    row = QRectF(queue.left() + 8, queue.top() + 40 + offset * row_h, queue.width() - 16, row_h - 3)
                    if row.contains(event.pos()):
                        self.album_track_selected.emit(str(tracks[index].get('id')))
                        return
            clicked_obj = None
            interaction_mode = None
            for idx, obj in enumerate(reversed(self.overlay_objects)):
                if not obj.get('visible', True):
                    continue
                real_idx = len(self.overlay_objects) - 1 - idx
                ox = v_rect.x() + int((obj.get('x_pct', 28.5) / 100.0) * v_rect.width())
                oy = v_rect.y() + int((obj.get('y_pct', 46.8) / 100.0) * v_rect.height())
                ow = int((obj.get('w_pct', 40.0) / 100.0) * v_rect.width())
                oh = int((obj.get('h_pct', 10.0) / 100.0) * v_rect.height())
                obj_rect = QRect(ox, oy, ow, oh)
                resize_rect = QRect(obj_rect.right() - 8, obj_rect.bottom() - 8, 16, 16)
                rotate_rect = QRect(obj_rect.center().x() - 9, obj_rect.top() - 27, 18, 18)
                if real_idx == self.selected_object_idx and rotate_rect.contains(event.pos()):
                    clicked_obj = real_idx
                    interaction_mode = 'rotate'
                    break
                if real_idx == self.selected_object_idx and resize_rect.contains(event.pos()):
                    clicked_obj = real_idx
                    interaction_mode = 'resize'
                    break
                if obj_rect.contains(event.pos()):
                    clicked_obj = real_idx
                    interaction_mode = 'move'
                    break
            
            self.selected_object_idx = clicked_obj
            if clicked_obj is not None:
                obj = self.overlay_objects[clicked_obj]
                self.interaction_mode = interaction_mode
                self.is_dragging_object = interaction_mode in {'resize', 'rotate'} or not obj.get('locked', False)
                self.drag_start_pos = event.pos()
                self.object_selected.emit(obj)
            else:
                self.object_selected.emit({})
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_dragging_object and self.selected_object_idx is not None:
            v_rect = self.get_viewport_rect()
            dx = event.pos().x() - self.drag_start_pos.x()
            dy = event.pos().y() - self.drag_start_pos.y()
            self.drag_start_pos = event.pos()
            
            obj = self.overlay_objects[self.selected_object_idx]
            if self.interaction_mode == 'resize':
                obj['w_pct'] = max(2.0, min(100.0 - float(obj.get('x_pct', 0.0)), float(obj.get('w_pct', 1.0)) + (dx / float(v_rect.width())) * 100.0))
                obj['h_pct'] = max(2.0, min(100.0 - float(obj.get('y_pct', 0.0)), float(obj.get('h_pct', 1.0)) + (dy / float(v_rect.height())) * 100.0))
                self.object_selected.emit(obj)
                self.update()
                return
            if self.interaction_mode == 'rotate':
                center_x = v_rect.x() + ((float(obj.get('x_pct', 0.0)) + float(obj.get('w_pct', 0.0)) / 2.0) / 100.0) * v_rect.width()
                center_y = v_rect.y() + ((float(obj.get('y_pct', 0.0)) + float(obj.get('h_pct', 0.0)) / 2.0) / 100.0) * v_rect.height()
                obj['rotation'] = round(math.degrees(math.atan2(event.pos().y() - center_y, event.pos().x() - center_x)) + 90.0, 1)
                self.object_selected.emit(obj)
                self.update()
                return
            max_x = max(0.0, 100.0 - float(obj.get('w_pct', 0)))
            max_y = max(0.0, 100.0 - float(obj.get('h_pct', 0)))
            obj['x_pct'] = max(0.0, min(max_x, obj.get('x_pct', 0) + (dx / float(v_rect.width())) * 100.0))
            obj['y_pct'] = max(0.0, min(max_y, obj.get('y_pct', 0) + (dy / float(v_rect.height())) * 100.0))
            center_x_pct = float(obj['x_pct']) + float(obj.get('w_pct', 0.0)) / 2.0
            center_y_pct = float(obj['y_pct']) + float(obj.get('h_pct', 0.0)) / 2.0
            self._snap_x = abs(center_x_pct - 50.0) <= 1.0
            self._snap_y = abs(center_y_pct - 50.0) <= 1.0
            if self._snap_x:
                obj['x_pct'] = 50.0 - float(obj.get('w_pct', 0.0)) / 2.0
            if self._snap_y:
                obj['y_pct'] = 50.0 - float(obj.get('h_pct', 0.0)) / 2.0
            self.object_selected.emit(obj)
            self.update()

    def mouseReleaseEvent(self, event):
        changed = self.is_dragging_object
        self.is_dragging_object = False
        self.interaction_mode = None
        self._snap_x = False
        self._snap_y = False
        if changed:
            self.objects_changed.emit()

    def closeEvent(self, event):
        self._close_video_reader()
        super().closeEvent(event)
