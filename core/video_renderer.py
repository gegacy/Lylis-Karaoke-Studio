"""Offline video renderer shared by the preview/export feature set."""
import math
import os
import subprocess
import tempfile
from typing import Any, Callable, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from core.lrc_engine import LyricLine
from core.media_timing import looping_frame_index


class VideoRenderer:
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}

    @classmethod
    def get_system_font(cls, font_name: str, size: int, bold: bool = False, italic: bool = False):
        normalized = font_name.lower().replace(" ", "")
        windows_fonts = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
        candidates = []
        aliases = {
            "segoeprint": ("segoeprb.ttf", "segoepr.ttf") if bold else ("segoepr.ttf", "segoeprb.ttf"),
            "segoeuiemoji": ("seguiemj.ttf", "seguisym.ttf"),
        }
        for filename in aliases.get(normalized, ()):
            candidates.append(os.path.join(windows_fonts, filename))
        styled_fonts = {
            ("arial", True, True): "arialbi.ttf",
            ("arial", True, False): "arialbd.ttf",
            ("arial", False, True): "ariali.ttf",
            ("segoeui", True, True): "segoeuiz.ttf",
            ("segoeui", True, False): "segoeuib.ttf",
            ("segoeui", False, True): "segoeuii.ttf",
        }
        styled_filename = styled_fonts.get((normalized, bool(bold), bool(italic)))
        if styled_filename:
            candidates.append(os.path.join(windows_fonts, styled_filename))
        if normalized:
            candidates.extend([
                os.path.join(windows_fonts, f"{normalized}.ttf"),
                os.path.join(windows_fonts, f"{normalized}bd.ttf"),
            ])
        if bold:
            candidates.extend([
                os.path.join(windows_fonts, "arialbd.ttf"),
                os.path.join(windows_fonts, "segoeuib.ttf"),
            ])
        if italic:
            candidates.extend([
                os.path.join(windows_fonts, "segoeuii.ttf"),
                os.path.join(windows_fonts, "ariali.ttf"),
            ])
        candidates.extend([
            os.path.join(windows_fonts, "segoeui.ttf"),
            os.path.join(windows_fonts, "arial.ttf"),
            os.path.join(windows_fonts, "tahoma.ttf"),
        ])
        for path in candidates:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, max(8, int(size)))
                except OSError:
                    continue
        return ImageFont.load_default()

    @staticmethod
    def hex_to_rgb(value: Any, fallback: Tuple[int, int, int] = (255, 255, 255)) -> tuple:
        if hasattr(value, "name"):
            value = value.name()
        text = str(value or "").strip().lstrip("#")
        if len(text) == 3:
            text = "".join(ch * 2 for ch in text)
        try:
            return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4)) if len(text) == 6 else fallback
        except ValueError:
            return fallback

    @staticmethod
    def resolve_pointer_icon(style: Dict[str, Any], singer: str) -> str:
        icons = style.get("pointer_icons")
        if isinstance(icons, dict):
            icon = icons.get(singer) or icons.get("both")
            if icon:
                return str(icon)
        defaults = {"male": "👨", "female": "👩", "both": "🎤"}
        return defaults.get(singer, str(style.get("pointer_icon", "🎤") or "🎤"))

    @staticmethod
    def resolve_output_size(style: Dict[str, Any]) -> Tuple[int, int]:
        resolution = style.get("resolution")
        aspect = style.get("aspect", "16:9")
        if isinstance(resolution, (list, tuple)) and len(resolution) == 2:
            return max(64, int(resolution[0])), max(64, int(resolution[1]))
        base_height = {"720p": 720, "1080p": 1080, "4k": 2160}.get(str(resolution).lower(), 1080)
        if aspect == "9:16":
            return base_height, int(base_height * 16 / 9)
        if aspect == "1:1":
            return base_height, base_height
        return int(base_height * 16 / 9), base_height

    @staticmethod
    def fit_background(image: Image.Image, size: Tuple[int, int]) -> Image.Image:
        image = image.convert("RGB")
        target_w, target_h = size
        scale = max(target_w / image.width, target_h / image.height)
        resized = image.resize(
            (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
            Image.Resampling.LANCZOS,
        )
        left = max(0, (resized.width - target_w) // 2)
        top = max(0, (resized.height - target_h) // 2)
        return resized.crop((left, top, left + target_w, top + target_h))

    @classmethod
    def _apply_color_effects(cls, frame: Image.Image, style: Dict[str, Any]) -> Image.Image:
        # 1. Pixel Adjustments (Brightness, Contrast, Saturation, Blur)
        brightness = float(style.get("brightness", 0))
        if brightness != 0:
            factor = 1.0 + (brightness / 50.0) * 0.5
            frame = ImageEnhance.Brightness(frame).enhance(max(0.1, factor))

        contrast = float(style.get("contrast", 0))
        if contrast != 0:
            factor = 1.0 + (contrast / 50.0) * 0.5
            frame = ImageEnhance.Contrast(frame).enhance(max(0.1, factor))

        saturation = float(style.get("saturation", 0))
        if saturation != 0:
            factor = 1.0 + (saturation / 50.0) * 0.5
            frame = ImageEnhance.Color(frame).enhance(max(0.0, factor))

        blur_radius = float(style.get("blur_radius", style.get("blur", 0)))
        if blur_radius > 0:
            frame = frame.filter(ImageFilter.GaussianBlur(radius=max(0.5, blur_radius)))

        # 2. Color Grading LUT Presets
        tint = style.get("color_tint", "None (Original)")
        if "Teal & Orange" in tint:
            teal = Image.new("RGB", frame.size, (0, 180, 200))
            frame = Image.blend(ImageEnhance.Contrast(frame).enhance(1.15), teal, 0.12)
        elif "Retro VHS" in tint:
            warm = Image.new("RGB", frame.size, (255, 210, 140))
            frame = Image.blend(ImageEnhance.Color(frame).enhance(0.85), warm, 0.15)
        elif "Pastel" in tint:
            pink = Image.new("RGB", frame.size, (255, 180, 210))
            frame = Image.blend(ImageEnhance.Brightness(frame).enhance(1.08), pink, 0.14)
        elif "Cyberpunk" in tint:
            cyan = Image.new("RGB", frame.size, (0, 180, 255))
            frame = Image.blend(ImageEnhance.Contrast(frame).enhance(1.20), cyan, 0.14)
        elif "Moody" in tint:
            dark_blue = Image.new("RGB", frame.size, (15, 30, 55))
            frame = Image.blend(ImageEnhance.Contrast(frame).enhance(1.25), dark_blue, 0.20)
        elif "Warm" in tint or "Gold" in tint:
            gold = Image.new("RGB", frame.size, (255, 170, 40))
            frame = Image.blend(frame, gold, 0.14)
        elif "Noir" in tint:
            frame = ImageEnhance.Contrast(frame.convert("L").convert("RGB")).enhance(1.25)
        elif "Emerald" in tint:
            frame = Image.blend(frame, Image.new("RGB", frame.size, (0, 150, 90)), 0.10)

        # 3. Vignette
        vignette = max(0.0, min(1.0, float(style.get("vignette_percent", 0)) / 100.0))
        if vignette > 0:
            w, h = frame.size
            mask = Image.new("L", (w, h), 0)
            draw = ImageDraw.Draw(mask)
            inset_x, inset_y = int(w * 0.08), int(h * 0.08)
            draw.ellipse((-inset_x, -inset_y, w + inset_x, h + inset_y), fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(max(10, int(min(w, h) * 0.18))))
            darkness = Image.new("RGB", frame.size, (0, 0, 0))
            edge_mask = Image.eval(mask, lambda p: int((255 - p) * vignette))
            frame = Image.composite(darkness, frame, edge_mask)
        return frame

    @classmethod
    def _draw_particles(cls, frame: Image.Image, current_time: float, style: Dict[str, Any]) -> None:
        if not style.get("particles", False):
            return
        draw = ImageDraw.Draw(frame, "RGBA")
        width, height = frame.size
        particle_type = str(style.get("particle_type", "Bokeh Orbs"))
        for index in range(30):
            phase = index * 1.618
            x = int(((index * 0.347 + math.sin(current_time * 0.35 + phase) * 0.04) % 1.0) * width)
            y = int(((index * 0.613 - current_time * (0.012 + (index % 5) * 0.002)) % 1.0) * height)
            radius = max(2, int(min(width, height) * (0.003 + (index % 4) * 0.0015)))
            if "Bokeh" in particle_type:
                draw.ellipse((x - radius * 2, y - radius * 2, x + radius * 2, y + radius * 2), fill=(255, 255, 255, 38))
            elif "Snow" in particle_type:
                draw.line((x - radius, y, x + radius, y), fill=(220, 245, 255, 170), width=2)
                draw.line((x, y - radius, x, y + radius), fill=(220, 245, 255, 170), width=2)
            else:
                color = (255, 195, 35, 190) if "Golden" in particle_type else (255, 90, 150, 170)
                draw.polygon([(x, y - radius * 2), (x + radius // 2, y - radius // 2),
                              (x + radius * 2, y), (x + radius // 2, y + radius // 2),
                              (x, y + radius * 2), (x - radius // 2, y + radius // 2),
                              (x - radius * 2, y), (x - radius // 2, y - radius // 2)], fill=color)

    @classmethod
    def _draw_visualizer(cls, frame: Image.Image, current_time: float, style: Dict[str, Any]) -> None:
        if not style.get("visualizer", False):
            return
        draw = ImageDraw.Draw(frame, "RGBA")
        width, height = frame.size
        mode = style.get("visualizer_mode", "Bar Spectrum")

        if "Radial" in mode:
            # Radial Circle 360° Visualizer
            cx, cy = width // 2, height // 2
            base_r = int(min(width, height) * 0.18)
            num_bars = 48
            for i in range(num_bars):
                angle = (i / num_bars) * 2 * math.pi + current_time * 0.4
                val = abs(math.sin(current_time * 5.0 + i * 0.4) * math.cos(current_time * 3.0 + i * 0.2))
                bar_len = int(val * min(width, height) * 0.09) + 4
                x1 = int(cx + math.cos(angle) * base_r)
                y1 = int(cy + math.sin(angle) * base_r)
                x2 = int(cx + math.cos(angle) * (base_r + bar_len))
                y2 = int(cy + math.sin(angle) * (base_r + bar_len))
                col = (255, 45, 85, 200) if i % 2 == 0 else (245, 158, 11, 200)
                draw.line([(x1, y1), (x2, y2)], fill=col, width=max(2, width // 400))
        elif "Neon Wave" in mode or "Ribbon" in mode:
            # Neon Wave Ribbon Visualizer
            baseline = int(height * 0.88)
            pts = []
            steps = 40
            for i in range(steps + 1):
                x = int((i / steps) * width)
                wave = math.sin(current_time * 4.0 + i * 0.3) * math.cos(current_time * 2.5 + i * 0.15)
                y = int(baseline + wave * (height * 0.06))
                pts.append((x, y))
            for i in range(len(pts) - 1):
                draw.line([pts[i], pts[i + 1]], fill=(59, 130, 246, 180), width=max(3, height // 200))
        else:
            # Bar Spectrum (Default)
            count = 36
            total_width = int(width * 0.62)
            bar_width = max(2, total_width // count - 2)
            start_x = (width - total_width) // 2
            baseline = int(height * 0.95)
            for index in range(count):
                value = abs(math.sin(current_time * 6 + index * 0.35) * math.cos(current_time * 4 + index * 0.2))
                bar_height = max(2, int(value * height * 0.1))
                x = start_x + index * (bar_width + 2)
                draw.rounded_rectangle((x, baseline - bar_height, x + bar_width, baseline), radius=2, fill=(255, 255, 255, 140))

    @staticmethod
    def _format_player_time(seconds: float) -> str:
        seconds = max(0, int(seconds))
        return f"{seconds // 60}:{seconds % 60:02d}"

    @classmethod
    def _draw_ambient_album_stage(
        cls, frame: Image.Image, current_time: float, duration: float, style: Dict[str, Any]
    ) -> None:
        width, height = frame.size
        source = frame.copy()
        blurred = frame.filter(ImageFilter.GaussianBlur(max(12, int(height * 0.055))))
        dark = Image.new("RGB", frame.size, (3, 11, 9))
        frame.paste(Image.blend(blurred, dark, 0.72))

        ambient = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(ambient, "RGBA")
        radius = int(width * 0.32)
        glow_draw.ellipse((-radius, -radius, radius * 2, radius * 2), fill=(235, 35, 22, 135))
        glow_draw.ellipse((int(width * 0.5), int(height * 0.46), int(width * 1.15), int(height * 1.25)), fill=(15, 184, 166, 110))
        ambient = ambient.filter(ImageFilter.GaussianBlur(max(20, int(height * 0.12))))
        frame.paste(ambient, (0, 0), ambient)

        draw = ImageDraw.Draw(frame, "RGBA")
        cover_size = int(min(width * 0.4, height * 0.72))
        cover_x, cover_y = int(width * 0.025), int(height * 0.065)
        album_cov_path = style.get("album_cover_path", "")
        if album_cov_path and os.path.exists(album_cov_path):
            try:
                cover_src = Image.open(album_cov_path).convert("RGB")
            except Exception:
                cover_src = source
        else:
            cover_src = source
        cover = cls.fit_background(cover_src, (cover_size, cover_size))
        corner = max(4, int(height * 0.014))
        mask = Image.new("L", (cover_size, cover_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, cover_size - 1, cover_size - 1), radius=corner, fill=255)
        frame.paste(cover, (cover_x, cover_y), mask)
        draw.rounded_rectangle(
            (cover_x, cover_y, cover_x + cover_size, cover_y + cover_size),
            radius=corner, outline=(255, 255, 255, 30), width=max(1, height // 720),
        )

        left = cover_x + int(cover_size * 0.05)
        right = cover_x + cover_size - int(cover_size * 0.05)
        progress_y = cover_y + cover_size + int(height * 0.12)
        line_w = max(2, int(height * 0.006))
        draw.line((left, progress_y, right, progress_y), fill=(255, 255, 255, 70), width=line_w)
        progress = max(0.0, min(1.0, current_time / max(1.0, duration)))
        draw.line((left, progress_y, int(left + (right - left) * progress), progress_y), fill=(255, 255, 255, 255), width=line_w)

        small = cls.get_system_font("Segoe UI", max(10, int(height * 0.017)))
        current_label = cls._format_player_time(current_time)
        duration_label = cls._format_player_time(duration)
        draw.text((left, progress_y - int(height * 0.052)), current_label, font=small, fill=(255, 255, 255, 180))
        duration_box = draw.textbbox((0, 0), duration_label, font=small)
        draw.text((right - (duration_box[2] - duration_box[0]), progress_y - int(height * 0.052)), duration_label, font=small, fill=(255, 255, 255, 180))

        title_font = cls.get_system_font("Segoe UI", max(12, int(height * 0.022)), True)
        artist_font = cls.get_system_font("Segoe UI", max(10, int(height * 0.016)))
        title = str(style.get("track_title", "Song Title"))
        artist = str(style.get("track_artist", "Artist"))
        max_meta_width = right - left
        while len(title) > 4 and draw.textbbox((0, 0), title, font=title_font)[2] > max_meta_width:
            title = title[:-4].rstrip() + "..."
        while len(artist) > 4 and draw.textbbox((0, 0), artist, font=artist_font)[2] > max_meta_width:
            artist = artist[:-4].rstrip() + "..."
        title_box = draw.textbbox((0, 0), title, font=title_font)
        artist_box = draw.textbbox((0, 0), artist, font=artist_font)
        center = (left + right) // 2
        draw.text((center - (title_box[2] - title_box[0]) / 2, progress_y + int(height * 0.018)), title, font=title_font, fill=(255, 255, 255, 255))
        draw.text((center - (artist_box[2] - artist_box[0]) / 2, progress_y + int(height * 0.055)), artist, font=artist_font, fill=(255, 255, 255, 145))

    @classmethod
    def _draw_hanako_falling_you_stage(
        cls, frame: Image.Image, current_time: float, duration: float, style: Dict[str, Any]
    ) -> None:
        """Draw the Falling You reference composition: portrait, vinyl, metadata and scrubber."""
        width, height = frame.size
        source = frame.copy()
        blurred = source.filter(ImageFilter.GaussianBlur(max(14, int(height * 0.045))))
        frame.paste(Image.blend(blurred, Image.new("RGB", frame.size, (112, 110, 101)), 0.45))
        draw = ImageDraw.Draw(frame, "RGBA")
        cover_size = int(min(width * 0.31, height * 0.56))
        cover_x, cover_y = int(width * 0.055), int(height * 0.27)
        cover = cls.fit_background(source, (cover_size, cover_size))
        # Vinyl disc sits behind the portrait and gently rotates with playback.
        disc_size = int(cover_size * 1.08)
        disc_x = cover_x + int(cover_size * 0.72)
        disc_y = cover_y - int((disc_size - cover_size) * 0.08)
        draw.ellipse((disc_x, disc_y, disc_x + disc_size, disc_y + disc_size), fill=(8, 9, 10, 245))
        for ring in range(5):
            inset = int(disc_size * (0.10 + ring * 0.085))
            draw.ellipse((disc_x + inset, disc_y + inset, disc_x + disc_size - inset, disc_y + disc_size - inset), outline=(80, 82, 86, 160), width=max(1, height // 480))
        draw.ellipse((disc_x + disc_size // 2 - 22, disc_y + disc_size // 2 - 22, disc_x + disc_size // 2 + 22, disc_y + disc_size // 2 + 22), fill=(35, 35, 37, 255))
        frame.paste(cover, (cover_x, cover_y))
        draw.rectangle((cover_x, cover_y, cover_x + cover_size, cover_y + cover_size), outline=(255, 255, 255, 235), width=max(2, height // 360))
        right_x = int(width * 0.63)
        title_font = cls.get_system_font(style.get("font_family", "Montserrat"), max(18, int(height * 0.055)), True)
        artist_font = cls.get_system_font(style.get("font_family", "Montserrat"), max(10, int(height * 0.022)))
        title = str(style.get("track_title", "FALLING YOU")).upper()
        artist = str(style.get("track_artist", "NHẠC HOT TIKTOK"))
        draw.text((right_x, int(height * 0.38)), title, font=title_font, fill=(255, 255, 255, 250))
        draw.text((right_x, int(height * 0.455)), artist, font=artist_font, fill=(255, 255, 255, 235))
        # Minimal waveform and progress scrubber.
        base_y = int(height * 0.63)
        progress = max(0.0, min(1.0, current_time / max(1.0, duration)))
        line_left, line_right = right_x, int(width * 0.94)
        draw.line((line_left, base_y + int(height * 0.055), line_right, base_y + int(height * 0.055)), fill=(255, 255, 255, 185), width=max(1, height // 360))
        for i in range(46):
            x = line_left + int((line_right - line_left) * i / 45)
            bar = int(height * (0.008 + ((i * 17) % 7) * 0.004))
            draw.line((x, base_y - bar, x, base_y + bar), fill=(255, 255, 255, 225), width=max(1, height // 300))
        progress_x = int(line_left + (line_right - line_left) * progress)
        draw.line((line_left, base_y + int(height * 0.055), progress_x, base_y + int(height * 0.055)), fill=(255, 255, 255, 255), width=max(2, height // 180))
        draw.polygon([(progress_x, base_y + int(height * 0.075)), (progress_x - 7, base_y + int(height * 0.092)), (progress_x + 7, base_y + int(height * 0.092))], fill=(255, 255, 255, 240))

    @classmethod
    def _draw_walters_lyric_queue_stage(
        cls, frame: Image.Image, style: Dict[str, Any]
    ) -> None:
        """Draw the muted cover-and-queue composition from the video reference."""
        width, height = frame.size
        source = frame.copy()
        blurred = source.filter(ImageFilter.GaussianBlur(max(14, int(height * 0.04))))
        charcoal = Image.new("RGB", frame.size, (52, 52, 46))
        frame.paste(Image.blend(blurred, charcoal, 0.64))

        wash = Image.new("RGBA", frame.size, (86, 86, 76, 34))
        frame.paste(wash, (0, 0), wash)
        draw = ImageDraw.Draw(frame, "RGBA")

        stage_center_y = int(height * 0.54)
        cover_size = int(min(width * 0.32, height * 0.54))
        cover_x = int(width * 0.08)
        cover_y = stage_center_y - cover_size // 2
        corner = max(8, int(height * 0.025))
        shadow_pad = max(4, int(height * 0.012))
        draw.rounded_rectangle(
            (
                cover_x + shadow_pad,
                cover_y + shadow_pad,
                cover_x + cover_size + shadow_pad,
                cover_y + cover_size + shadow_pad,
            ),
            radius=corner,
            fill=(0, 0, 0, 110),
        )
        cover = cls.fit_background(source, (cover_size, cover_size))
        mask = Image.new("L", (cover_size, cover_size), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, cover_size - 1, cover_size - 1), radius=corner, fill=255
        )
        frame.paste(cover, (cover_x, cover_y), mask)

        title = str(style.get("track_title") or "Song Title")
        title_font = cls.get_system_font(
            style.get("font_family", "Montserrat"), max(16, int(height * 0.05)), True
        )
        max_title_width = int(width * 0.84)
        while len(title) > 4 and draw.textlength(title, font=title_font) > max_title_width:
            title = title[:-4].rstrip() + "..."
        title_width = draw.textlength(title, font=title_font)
        # Drop shadow for title
        draw.text(
            ((width - title_width) / 2 + 1, int(height * 0.05) + 1),
            title,
            font=title_font,
            fill=(0, 0, 0, 160),
        )
        draw.text(
            ((width - title_width) / 2, int(height * 0.05)),
            title,
            font=title_font,
            fill=(255, 255, 255, 250),
        )

    @classmethod
    def _draw_multi_song_album_stage(cls, frame: Image.Image, current_time: float, duration: float, style: Dict[str, Any]) -> None:
        """Draw an editable album playlist card with the active song highlighted."""
        width, height = frame.size
        source = frame.copy()
        blurred = source.filter(ImageFilter.GaussianBlur(max(16, int(height * 0.05))))
        frame.paste(Image.blend(blurred, Image.new("RGB", frame.size, (18, 24, 38)), 0.62))
        draw = ImageDraw.Draw(frame, "RGBA")
        cover_size = int(min(width * 0.34, height * 0.58))
        cover_x, cover_y = int(width * 0.08), int(height * 0.19)
        cover = cls.fit_background(source, (cover_size, cover_size))
        frame.paste(cover, (cover_x, cover_y))
        draw.rectangle((cover_x, cover_y, cover_x + cover_size, cover_y + cover_size), outline=(255, 255, 255, 180), width=max(2, height // 360))
        right_x = int(width * 0.52)
        title_font = cls.get_system_font(style.get("font_family", "Montserrat"), max(16, int(height * 0.045)), True)
        small_font = cls.get_system_font(style.get("font_family", "Montserrat"), max(10, int(height * 0.021)))
        draw.text((right_x, int(height * 0.16)), str(style.get("track_artist", "Album Artist")), font=small_font, fill=(196, 205, 224, 220))
        draw.text((right_x, int(height * 0.205)), str(style.get("album_title", style.get("track_title", "My Album"))), font=title_font, fill=(255, 255, 255, 250))
        tracks = style.get("album_tracks") or [style.get("track_title", "Track 01"), "Track 02", "Track 03", "Track 04", "Track 05"]
        track_titles = [track.get("title", "Track") if isinstance(track, dict) else str(track) for track in tracks]
        active_id = style.get("active_track_id") or style.get("activeTrackId")
        active = next((index for index, track in enumerate(tracks) if isinstance(track, dict) and track.get("id") == active_id), None)
        if active is None:
            active = int(max(0, min(len(track_titles) - 1, current_time / max(1.0, duration) * len(track_titles))))
        row_y = int(height * 0.34)
        row_h = max(22, int(height * 0.065))
        for index, track in enumerate(track_titles[:8]):
            y = row_y + index * row_h
            if index == active:
                draw.rounded_rectangle((right_x - 10, y - 4, int(width * 0.94), y + row_h - 6), radius=6, fill=(125, 100, 220, 150))
            draw.text((right_x, y), f"{index + 1:02d}", font=small_font, fill=(210, 215, 230, 190))
            draw.text((right_x + int(width * 0.06), y), str(track), font=small_font, fill=(255, 255, 255, 250 if index == active else 170))
        left, right, py = int(width * 0.08), int(width * 0.92), int(height * 0.89)
        progress = max(0.0, min(1.0, current_time / max(1.0, duration)))
        draw.line((left, py, right, py), fill=(255, 255, 255, 90), width=max(2, height // 360))
        draw.line((left, py, int(left + (right - left) * progress), py), fill=(196, 181, 253, 255), width=max(3, height // 180))

    @classmethod
    def _draw_multi_song_album_lyrics(
        cls, frame: Image.Image, lines: List[LyricLine], current_time: float, style: Dict[str, Any]
    ) -> None:
        if not lines:
            return
        active_line = next((line for line in lines if line.line_start - 0.5 <= current_time <= line.line_end + 0.6), None)
        if not active_line:
            active_line = next((line for line in lines if line.line_start > current_time), lines[-1])
        if not active_line:
            return
        width, height = frame.size
        draw = ImageDraw.Draw(frame, "RGBA")
        font_size = max(14, int(float(style.get("font_size", 38)) * width / 1200))
        font_family = style.get("font_family", "Montserrat")
        font = cls.get_system_font(font_family, font_size, True)
        
        text = active_line.full_text
        text_x = int(width * 0.48)
        text_y = int(height * 0.68)
        active_col = cls.hex_to_rgb(style.get("active_color", "#00d2ff"))
        draw.text((text_x + 2, text_y + 2), text, font=font, fill=(0, 0, 0, 200))
        draw.text((text_x, text_y), text, font=font, fill=active_col + (255,))

    @classmethod
    def _draw_ksector_2000s_stage(
        cls, frame: Image.Image, lines: List[LyricLine], current_time: float, style: Dict[str, Any]
    ) -> None:
        """Draw a warm Y2K magazine cover with a burgundy editorial divider."""
        width, height = frame.size
        source = frame.copy()
        frame.paste(Image.new("RGB", frame.size, (249, 246, 237)))

        portrait_height = int(height * 0.50)
        scale = max(width / source.width, portrait_height / source.height)
        resized = source.resize(
            (max(width, int(source.width * scale)), max(portrait_height, int(source.height * scale))),
            Image.Resampling.LANCZOS,
        )
        focus_y = max(0.0, min(1.0, float(style.get("portrait_focus_y", 25)) / 100.0))
        crop_x = max(0, (resized.width - width) // 2)
        crop_y = max(0, min(resized.height - portrait_height, int(resized.height * focus_y - portrait_height / 2)))
        portrait = resized.crop((crop_x, crop_y, crop_x + width, crop_y + portrait_height))
        portrait = ImageEnhance.Color(portrait).enhance(0.82)
        portrait = ImageEnhance.Contrast(portrait).enhance(1.08)
        portrait = Image.blend(portrait, Image.new("RGB", portrait.size, (184, 92, 43)), 0.16)
        frame.paste(portrait, (0, 0))

        band = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        band_draw = ImageDraw.Draw(band, "RGBA")
        band_top, band_bottom = int(height * 0.34), int(height * 0.505)
        band_span = max(1, band_bottom - band_top)
        for offset in range(band_span):
            progress = offset / band_span
            band_draw.line(
                ((0, band_top + offset), (width, band_top + offset)),
                fill=(int(104 + progress * 34), 20, int(69 - progress * 35), int(35 + progress * 205)),
            )
        frame.paste(band, (0, 0), band)

        draw = ImageDraw.Draw(frame, "RGBA")
        artist = str(style.get("track_artist") or "Artist")
        artist_font = cls.get_system_font("Arial", max(15, int(height * 0.046)), True, True)
        draw.text(
            (int(width * 0.215), int(height * 0.405)), artist,
            font=artist_font, fill=(255, 255, 255, 248),
            stroke_width=max(1, int(height * 0.0015)), stroke_fill=(98, 20, 45, 170),
        )

        has_active_line = any(line.line_start <= current_time <= line.line_end for line in lines)
        has_started = bool(lines) and current_time >= lines[0].line_start
        if has_active_line or has_started:
            return

        title = str(style.get("track_title") or "SONG TITLE").upper()
        title_size = max(28, int(height * 0.15))
        title_font = cls.get_system_font("Impact", title_size, True)
        max_width = int(width * 0.82)
        while title_size > max(18, int(height * 0.06)) and draw.textlength(title, font=title_font) > max_width:
            title_size -= 1
            title_font = cls.get_system_font("Impact", title_size, True)
        title_width = draw.textlength(title, font=title_font)
        title_x, title_y = (width - title_width) / 2, int(height * 0.545)
        shadow_offset = max(3, int(height * 0.008))
        draw.text((title_x + shadow_offset, title_y + shadow_offset), title, font=title_font, fill=(78, 43, 30, 120))
        draw.text((title_x, title_y), title, font=title_font, fill=(137, 34, 55, 255))

        caption_font = cls.get_system_font("Segoe UI", max(13, int(height * 0.032)), True)
        if artist and artist != "Artist":
            caption = f"{artist}  •  {title}"
        else:
            caption = f"{title}"
        caption_width = draw.textlength(caption, font=caption_font)
        draw.text(
            ((width - caption_width) / 2, int(height * 0.86)), caption,
            font=caption_font, fill=(107, 51, 36, 230),
        )

    @classmethod
    def _draw_singer_banner(cls, frame: Image.Image, lines: List[LyricLine], current_time: float, style: Dict[str, Any]) -> None:
        if style.get("display_mode") != "COLOR CODED":
            return
        if style.get("template_variant") == "ksector_2000s_editorial":
            return
        if style.get("template_variant") == "tiki_tiki":
            cls._draw_tiki_tiki_stage(frame, lines, current_time, style)
            return
        singers = style.get("custom_singers", []) or []
        if not singers:
            return
        draw = ImageDraw.Draw(frame, "RGBA")
        width, height = frame.size
        banner_height = int(height * 0.25)
        card_width = width / float(len(singers))
        active_role = ""
        for line in lines:
            if line.line_start <= current_time <= line.line_end:
                active_role = getattr(line, 'singer', 'both')
                break
        name_font = cls.get_system_font("Segoe UI", max(10, int(height * 0.018)), True)
        for index, singer in enumerate(singers):
            is_active = (
                active_role in ("both", "all") or 
                (index == 0 and active_role == "female") or 
                (index == 1 and active_role == "male") or 
                singer.get("name") == active_role or 
                singer.get("role") == active_role
            )
            x0, x1 = int(index * card_width), int((index + 1) * card_width)
            draw.rectangle((x0, 0, x1, banner_height), fill=(15, 23, 42, 215))
            color = cls.hex_to_rgb(singer.get("color", "#f59e0b"))
            radius = int(min(card_width, banner_height) * (0.29 if is_active else 0.25))
            center_x, center_y = int((x0 + x1) / 2), int(banner_height * 0.42)
            draw.ellipse((center_x - radius, center_y - radius, center_x + radius, center_y + radius),
                         fill=(30, 41, 59, 255), outline=color + (255,), width=max(2, int(height * 0.004)))
            label_color = color + (235,) if is_active else (0, 0, 0, 190)
            draw.rectangle((x0, banner_height - int(height * 0.04), x1, banner_height), fill=label_color)
            text = str(singer.get("name", "Singer"))
            box = draw.textbbox((0, 0), text, font=name_font)
            draw.text(((x0 + x1 - (box[2] - box[0])) / 2, banner_height - int(height * 0.032)), text, font=name_font, fill=(255, 255, 255, 255))

    @classmethod
    def _draw_tiki_tiki_stage(
        cls, frame: Image.Image, lines: List[LyricLine], current_time: float, style: Dict[str, Any]
    ) -> None:
        singers = style.get("custom_singers", []) or [
            {"name": "SUZANA", "role": "female", "color": "#b50b56", "avatar": "S", "image_path": ""},
            {"name": "VANNDA", "role": "male", "color": "#a9470b", "avatar": "V", "image_path": ""}
        ]
        if not singers:
            return
        width, height = frame.size
        stage_h = int(height * 0.49)
        num_singers = max(1, len(singers))
        card_w = width / float(num_singers)
        active_role = "both"
        for line in lines:
            if line.line_start <= current_time <= line.line_end:
                active_role = line.singer
                break
        draw = ImageDraw.Draw(frame, "RGBA")
        name_font = cls.get_system_font("Arial", max(12, int(height * 0.024)), True, True)
        avatar_font = cls.get_system_font("Arial", max(36, int(stage_h * 0.3)), True)

        for index in range(num_singers):
            singer = singers[index]
            role = singer.get("role", "female" if index == 0 else ("male" if index == 1 else singer.get("name", f"singer_{index}")))
            s_name = str(singer.get("name", f"SINGER {index+1}")).upper()
            x0 = int(index * card_w)
            x1 = width if index == num_singers - 1 else int((index + 1) * card_w)
            color = cls.hex_to_rgb(singer.get("color", "#b50b56"))
            draw.rectangle((x0, 0, x1, stage_h), fill=color + (255,))
            image_path = singer.get("image_path", "")
            if image_path and os.path.exists(image_path):
                try:
                    with Image.open(image_path) as source:
                        portrait = cls.fit_background(source, (x1 - x0, stage_h))
                    frame.paste(portrait, (x0, 0))
                except OSError:
                    image_path = ""
            if not image_path:
                avatar = str(singer.get("avatar", s_name[:1]))
                box = draw.textbbox((0, 0), avatar, font=avatar_font)
                draw.text(((x0 + x1 - (box[2] - box[0])) / 2, (stage_h - (box[3] - box[1])) / 2 - box[1]),
                          avatar, font=avatar_font, fill=(255, 255, 255, 120))
            
            is_active_singer = (active_role in ("both", "all") or active_role == role or active_role == s_name or (active_role == "female" and index == 0) or (active_role == "male" and index == 1))
            if not is_active_singer:
                draw.rectangle((x0, 0, x1, stage_h), fill=(5, 8, 12, 205))
            
            label_h = max(24, int(height * 0.052))
            draw.rectangle((x0, stage_h - label_h, x1, stage_h), fill=color + (238,))
            box = draw.textbbox((0, 0), s_name, font=name_font, stroke_width=max(1, width // 1000))
            draw.text(((x0 + x1 - (box[2] - box[0])) / 2, stage_h - label_h / 2 - (box[3] - box[1]) / 2 - box[1]),
                      s_name, font=name_font, fill=(255, 255, 255, 255), stroke_width=max(1, width // 1000),
                      stroke_fill=(65, 20, 30, 255))

        tear = max(4, int(height * 0.012))
        step = max(10, width // 42)
        points = [(0, height), (0, stage_h)]
        for index, x in enumerate(range(0, width + step, step)):
            offset = -tear if index % 3 == 0 else tear if index % 3 == 1 else 0
            points.append((min(x, width), stage_h + offset))
        points.append((width, height))
        draw.polygon(points, fill=(251, 250, 240, 255))

    @classmethod
    def _draw_overlays(cls, frame: Image.Image, current_time: float, style: Dict[str, Any]) -> None:
        overlays = style.get("overlay_objects", []) or []
        if not overlays:
            return
        draw = ImageDraw.Draw(frame, "RGBA")
        width, height = frame.size

        for obj in overlays:
            o_type = obj.get("type", "text")
            x = int(float(obj.get("x_pct", 10.0)) / 100.0 * width)
            y = int(float(obj.get("y_pct", 10.0)) / 100.0 * height)
            w = int(float(obj.get("w_pct", 30.0)) / 100.0 * width)
            h = int(float(obj.get("h_pct", 10.0)) / 100.0 * height)

            rotation = float(obj.get("rotation", 0.0))
            if abs(rotation) > 1e-6:
                layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
                unrotated = dict(obj)
                unrotated["rotation"] = 0
                cls._draw_overlays(layer, current_time, {"overlay_objects": [unrotated]})
                layer = layer.rotate(
                    -rotation,
                    resample=Image.Resampling.BICUBIC,
                    center=(x + w / 2, y + h / 2),
                )
                frame.paste(layer, (0, 0), layer)
                continue

            if o_type == "text":
                content = str(obj.get("content", "Text"))
                f_size = max(10, int(int(obj.get("font_size", 32)) * width / 1280))
                font = cls.get_system_font(
                    obj.get("font_family", "Montserrat"),
                    f_size,
                    int(obj.get("font_weight", 600)) >= 700,
                )
                col = cls.hex_to_rgb(obj.get("color", "#ffffff"))
                stroke_col = cls.hex_to_rgb(obj.get("stroke_color", "#000000"))
                stroke_w = max(0, int(float(obj.get("stroke_width", 2)) * width / 1280))
                box = draw.textbbox((0, 0), content, font=font, stroke_width=stroke_w)
                text_w, text_h = box[2] - box[0], box[3] - box[1]
                alignment = obj.get("alignment", "center")
                tx = x if alignment == "left" else x + w - text_w if alignment == "right" else x + (w - text_w) / 2
                ty = y + (h - text_h) / 2 - box[1]
                draw.text(
                    (tx, ty), content, font=font, fill=col + (255,),
                    stroke_width=stroke_w, stroke_fill=stroke_col + (255,),
                )
            elif o_type == "shape":
                col = cls.hex_to_rgb(obj.get("color", "#ff2d55"))
                draw.rounded_rectangle((x, y, x + w, y + h), radius=max(2, int(h * 0.1)), fill=col + (220,))
            elif o_type == "lower_third":
                bg_col = cls.hex_to_rgb(obj.get("color", "#0f172a"))
                draw.rounded_rectangle((x, y, x + w, y + h), radius=max(4, int(h * 0.15)), fill=bg_col + (235,))
                draw.rectangle((x, y, x + max(4, int(w * 0.015)), y + h), fill=(255, 45, 85, 255))
                t_font = cls.get_system_font("Arial", max(10, int(h * 0.38)), True)
                sub_font = cls.get_system_font("Arial", max(8, int(h * 0.26)), False)
                title = str(obj.get("title", "TITLE"))
                sub = str(obj.get("subtitle", "Subtitle"))
                tx = x + int(w * 0.04)
                draw.text((tx, y + int(h * 0.14)), title, font=t_font, fill=(255, 255, 255, 255))
                draw.text((tx, y + int(h * 0.58)), sub, font=sub_font, fill=(148, 163, 184, 255))
            elif o_type == "vinyl":
                radius = min(w, h) // 2
                cx, cy = x + w // 2, y + h // 2
                draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(15, 23, 42, 255), outline=(51, 65, 85, 255), width=2)
                for r_step in range(int(radius * 0.45), int(radius * 0.95), max(3, int(radius * 0.08))):
                    draw.ellipse((cx - r_step, cy - r_step, cx + r_step, cy + r_step), outline=(30, 41, 59, 160), width=1)
                center_r = int(radius * 0.36)
                label_size = max(2, center_r * 2)
                label = Image.new("RGBA", (label_size, label_size), (0, 0, 0, 0))
                label_draw = ImageDraw.Draw(label, "RGBA")
                label_draw.ellipse((0, 0, label_size - 1, label_size - 1), fill=(255, 45, 85, 255))
                label_font = cls.get_system_font("Arial", max(7, int(center_r * 0.32)), True)
                label_text = str(obj.get("title", "VINYL"))[:8]
                label_box = label_draw.textbbox((0, 0), label_text, font=label_font)
                label_draw.text(
                    (
                        (label_size - (label_box[2] - label_box[0])) / 2 - label_box[0],
                        (label_size - (label_box[3] - label_box[1])) / 2 - label_box[1],
                    ),
                    label_text,
                    font=label_font,
                    fill=(255, 255, 255, 255),
                )
                label = label.rotate(
                    -(current_time * 45.0) % 360.0,
                    resample=Image.Resampling.BICUBIC,
                    expand=False,
                )
                frame.paste(label, (cx - center_r, cy - center_r), label)
                hole_r = max(2, int(radius * 0.06))
                draw.ellipse((cx - hole_r, cy - hole_r, cx + hole_r, cy + hole_r), fill=(0, 0, 0, 255))

    @classmethod
    def _draw_watermark(cls, frame: Image.Image, style: Dict[str, Any]) -> None:
        if not style.get("watermark", False):
            return
        draw = ImageDraw.Draw(frame, "RGBA")
        font = cls.get_system_font("Segoe UI", max(8, int(frame.width * 0.009)), True)
        text = "MADE WITH LYLIS"
        box = draw.textbbox((0, 0), text, font=font)
        draw.text((frame.width - (box[2] - box[0]) - 14, frame.height - (box[3] - box[1]) - 12), text, font=font, fill=(255, 255, 255, 150))

    @staticmethod
    def _transition_amount(current_time: float, duration: float, position: str, seconds: float = 1.5) -> float:
        if position == "start":
            return max(0.0, min(1.0, current_time / max(0.1, seconds)))
        return max(0.0, min(1.0, (duration - current_time) / max(0.1, seconds)))

    @classmethod
    def _apply_transition(
        cls, frame: Image.Image, current_time: float, duration: float, style: Dict[str, Any]
    ) -> Image.Image:
        transitions = style.get("transitions", {}) or {}
        for position in ("start", "end"):
            transition = transitions.get(position)
            if not transition:
                continue
            amount = cls._transition_amount(current_time, duration, position, float(transition.get("duration", 1.5)))
            name = str(transition.get("name", "Fade"))
            if amount >= 1.0:
                continue
            if "Slide" in name:
                shifted = Image.new("RGB", frame.size, (0, 0, 0))
                offset = int(frame.width * (1.0 - amount)) * (-1 if position == "end" else 1)
                shifted.paste(frame, (offset, 0))
                frame = shifted
            elif "Zoom" in name:
                scale = 0.85 + 0.15 * amount
                resized = frame.resize((max(1, int(frame.width * scale)), max(1, int(frame.height * scale))), Image.Resampling.BICUBIC)
                canvas = Image.new("RGB", frame.size, (0, 0, 0))
                canvas.paste(resized, ((frame.width - resized.width) // 2, (frame.height - resized.height) // 2))
                frame = canvas
            else:
                frame = Image.blend(Image.new("RGB", frame.size, (0, 0, 0)), frame, amount)
        return frame

    @classmethod
    def _draw_overlays_legacy(cls, frame: Image.Image, style: Dict[str, Any]) -> None:
        draw = ImageDraw.Draw(frame)
        width, height = frame.size
        for obj in style.get("overlay_objects", []) or []:
            x = int(float(obj.get("x_pct", 0)) * width / 100)
            y = int(float(obj.get("y_pct", 0)) * height / 100)
            w = max(1, int(float(obj.get("w_pct", 20)) * width / 100))
            h = max(1, int(float(obj.get("h_pct", 10)) * height / 100))
            color = cls.hex_to_rgb(obj.get("color", "#ffffff"))
            if obj.get("type") == "shape":
                draw.rounded_rectangle((x, y, x + w, y + h), radius=max(2, int(min(w, h) * 0.08)), fill=color)
            elif obj.get("type") == "lower_third":
                draw.rounded_rectangle((x, y, x + w, y + h), radius=max(3, int(h * 0.08)), fill=cls.hex_to_rgb(obj.get("color", "#0f172a")))
                title_font = cls.get_system_font("Segoe UI", max(12, int(h * 0.25)), True)
                sub_font = cls.get_system_font("Segoe UI", max(10, int(h * 0.17)))
                draw.text((x + 16, y + int(h * 0.15)), obj.get("title", ""), font=title_font, fill=(255, 255, 255))
                draw.text((x + 16, y + int(h * 0.55)), obj.get("subtitle", ""), font=sub_font, fill=(203, 213, 225))
            else:
                font = cls.get_system_font(
                    str(obj.get("font_family", "Montserrat")),
                    max(10, int(float(obj.get("font_size", 32)) * width / 1280)),
                    int(obj.get("font_weight", 600)) >= 700,
                )
                text = str(obj.get("content", ""))
                box = draw.textbbox((0, 0), text, font=font, stroke_width=max(0, int(obj.get("stroke_width", 2))))
                tx = x + max(0, (w - (box[2] - box[0])) // 2)
                ty = y + max(0, (h - (box[3] - box[1])) // 2)
                draw.text(
                    (tx, ty), text, font=font, fill=color,
                    stroke_width=max(0, int(obj.get("stroke_width", 2))),
                    stroke_fill=cls.hex_to_rgb(obj.get("stroke_color", "#000000"), (0, 0, 0)),
                )

    @classmethod
    def _draw_lyrics(cls, frame: Image.Image, lines: List[LyricLine], current_time: float, style: Dict[str, Any]) -> None:
        if style.get("template_variant") == "tiki_tiki":
            cls._draw_tiki_tiki_lyrics(frame, lines, current_time, style)
            return
        if style.get("template_variant") == "ambient_album_player":
            cls._draw_ambient_album_lyrics(frame, lines, current_time, style)
            return
        if style.get("template_variant") == "walters_lyric_queue":
            cls._draw_walters_lyric_queue(frame, lines, current_time, style)
            return
        if style.get("template_variant") == "ksector_2000s_editorial":
            cls._draw_ksector_2000s_lyrics(frame, lines, current_time, style)
            return
        if style.get("template_variant") == "falling_u_douyin_dj":
            cls._draw_falling_u_douyin_lyrics(frame, lines, current_time, style)
            return
        if style.get("template_variant") == "multi_song_album":
            cls._draw_multi_song_album_lyrics(frame, lines, current_time, style)
            return
        if style.get("template_variant") == "eminem_rap_hiphop_album":
            cls._draw_eminem_rap_hiphop_lyrics(frame, lines, current_time, style)
            return
        width, height = frame.size
        draw = ImageDraw.Draw(frame)
        font_size = max(14, int(float(style.get("font_size", 42)) * width / 1280))
        font_family = style.get("font_family", "Montserrat")
        is_bold = style.get("is_bold", True)
        font = cls.get_system_font(font_family, font_size, is_bold)
        display_mode = style.get("display_mode", "KARAOKE")
        LEAD_IN = 2.0
        LINGER = 0.5
        display = []  # list of (slot_order, line)

        if display_mode in {"COLOR CODED", "SINGLE", "BUILD"}:
            for i, line in enumerate(lines):
                s_vis = max(0.0, line.line_start - LEAD_IN) if i == 0 else max(lines[i - 1].line_end + 0.2, line.line_start - LEAD_IN)
                if s_vis <= current_time <= line.line_end + LINGER:
                    display.append((0, line))
                    break
        else:
            # Alternating Dual-Line Karaoke Staggering:
            # Slot 0 (Top slot) holds even-indexed lines (0, 2, 4, 6...)
            for i in range(0, len(lines), 2):
                l = lines[i]
                start_vis = max(0.0, l.line_start - LEAD_IN) if i == 0 else max(lines[i - 2].line_end + 0.2, min(lines[i - 1].line_start, l.line_start - LEAD_IN))
                end_vis = l.line_end + LINGER
                if start_vis <= current_time <= end_vis:
                    display.append((0, l))
                    break

            # Slot 1 (Bottom slot) holds odd-indexed lines (1, 3, 5, 7...)
            for j in range(1, len(lines), 2):
                l = lines[j]
                start_vis = min(lines[0].line_start, l.line_start - LEAD_IN) if j == 1 else max(lines[j - 2].line_end + 0.2, min(lines[j - 1].line_start, l.line_start - LEAD_IN))
                end_vis = l.line_end + LINGER
                if start_vis <= current_time <= end_vis:
                    display.append((1, l))
                    break

        if not display:
            return

        max_line_width = width * 0.84
        minimum_font_size = max(8, int(14 * width / 1280))

        def rendered_line_width(line: LyricLine) -> int:
            return int(round(sum(draw.textlength(word.text, font=font) for word in line.words)))

        while font_size > minimum_font_size and any(
            rendered_line_width(line) > max_line_width for _, line in display
        ):
            font_size -= 1
            font = cls.get_system_font(font_family, font_size, is_bold)
        positions = [float(style.get("pos_y_top", 66)), float(style.get("pos_y_bottom", style.get("pos_y", 78)))]
        if display_mode in {"COLOR CODED", "SINGLE", "BUILD"}:
            positions[0] = 65.0 if display_mode == "COLOR CODED" else positions[1]
        layout = style.get("layout_mode", "left_right")
        pad = int(width * float(style.get("padding_x", 7.5)) / 100)
        stroke = max(0, int(float(style.get("stroke_width", style.get("stroke_w", 4))) * width / 1280))
        base_color = cls.hex_to_rgb(style.get("base_color", "#ffffff"))
        colors = {
            "male": cls.hex_to_rgb(style.get("male_color", "#0026ff")),
            "female": cls.hex_to_rgb(style.get("female_color", "#ff0033")),
            "both": cls.hex_to_rgb(style.get("both_color", "#ff007f")),
        }
        for slot_order, line in display:
            text_width = rendered_line_width(line)
            if layout == "left_right":
                x = pad if slot_order == 0 else width - text_width - pad
            else:
                align = style.get("text_alignment", "center")
                if align == "left":
                    x = pad
                elif align == "right":
                    x = width - text_width - pad
                else:
                    x = (width - text_width) // 2
            y = int(height * positions[slot_order] / 100) - font_size
            entry = current_time - line.line_start
            motion = str(style.get("motion_effect", ""))
            if 0 <= entry <= 0.35:
                if "Bounce" in motion:
                    y -= int(math.sin(entry / 0.35 * math.pi) * font_size * 0.3)
                elif "Slide" in motion:
                    y += int((1.0 - entry / 0.35) * font_size * 0.4)
            cursor = x
            active_color = (245, 158, 11) if display_mode == "COLOR CODED" else colors.get(line.singer, colors["both"])
            if style.get("pointer", True) and line.line_start <= current_time <= line.line_end:
                badge_size = max(12, int(font_size * 0.7))
                badge_color = colors.get(line.singer, colors["both"])
                badge_left = x - badge_size - 8
                badge_top = y
                draw.rounded_rectangle(
                    (badge_left, badge_top, x - 8, y + badge_size), radius=4, fill=badge_color
                )
                icon_font = cls.get_system_font("Segoe UI Emoji", max(10, int(badge_size * 0.65)))
                icon = cls.resolve_pointer_icon(style, line.singer)
                icon_box = draw.textbbox((0, 0), icon, font=icon_font)
                icon_width = icon_box[2] - icon_box[0]
                icon_height = icon_box[3] - icon_box[1]
                draw.text(
                    (
                        badge_left + (badge_size - icon_width) / 2 - icon_box[0],
                        badge_top + (badge_size - icon_height) / 2 - icon_box[1],
                    ),
                    icon,
                    font=icon_font,
                    fill=(255, 255, 255),
                )
            for word in line.words:
                bbox = draw.textbbox((0, 0), word.text, font=font, stroke_width=stroke)
                word_width = bbox[2] - bbox[0]
                word_advance = int(round(draw.textlength(word.text, font=font)))
                shadow_offset = max(1, int(float(style.get("shadow_offset", 2)) * width / 1280))
                draw.text(
                    (cursor + shadow_offset, y + shadow_offset), word.text, font=font,
                    fill=(0, 0, 0), stroke_width=stroke, stroke_fill=(0, 0, 0),
                )
                draw.text((cursor, y), word.text, font=font, fill=base_color, stroke_width=stroke, stroke_fill=(0, 0, 0))
                progress = 0.0 if current_time < word.start_time else 1.0 if current_time >= word.end_time else (
                    (current_time - word.start_time) / max(0.05, word.end_time - word.start_time)
                )
                if progress > 0:
                    overlay = Image.new("RGBA", (word_width + stroke * 4 + 4, font_size * 2 + stroke * 4), (0, 0, 0, 0))
                    od = ImageDraw.Draw(overlay)
                    od.text((stroke * 2, stroke * 2), word.text, font=font, fill=active_color + (255,), stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
                    crop_width = min(overlay.width, max(1, int((word_width + stroke * 2) * progress)))
                    crop = overlay.crop((0, 0, crop_width, overlay.height))
                    if style.get("enable_glow", False) and int(style.get("glow_radius", 0)) > 0:
                        glow_alpha = crop.getchannel("A").filter(ImageFilter.GaussianBlur(max(1, int(style.get("glow_radius", 6)))))
                        glow = Image.new("RGBA", crop.size, active_color + (0,))
                        glow.putalpha(glow_alpha.point(lambda value: min(120, value)))
                        frame.paste(glow, (cursor - stroke * 2, y - stroke * 2), glow)
                    frame.paste(crop, (cursor - stroke * 2, y - stroke * 2), crop)
                cursor += word_advance

    @classmethod
    def _draw_tiki_tiki_lyrics(
        cls, frame: Image.Image, lines: List[LyricLine], current_time: float, style: Dict[str, Any]
    ) -> None:
        active_index = None
        for index, line in enumerate(lines):
            if line.line_start <= current_time <= line.line_end:
                active_index = index
                break
        if active_index is None:
            active_index = next((index for index, line in enumerate(lines) if line.line_start > current_time), None)
        if active_index is None:
            return
        display = lines[active_index:active_index + 3]
        if not display:
            return

        width, height = frame.size
        stage_h = int(height * 0.49)
        tear = max(4, int(height * 0.012))
        paper_top = stage_h + tear
        paper_bottom = height - int(height * 0.04)
        available_h = max(20, paper_bottom - paper_top)

        size = max(15, int(float(style.get("font_size", 44)) * width / 1300))
        font_name = style.get("font_family", "Arial")
        font = cls.get_system_font(font_name, size, False, True)
        draw = ImageDraw.Draw(frame, "RGBA")
        max_width = int(width * 0.88)
        while size > 12 and any(draw.textbbox((0, 0), line.full_text, font=font)[2] > max_width for line in display):
            size -= 1
            font = cls.get_system_font(font_name, size, False, True)

        line_h = min(int(available_h / max(1, len(display))), int(size * 1.35))
        total_text_h = len(display) * line_h
        y = paper_top + (available_h - total_text_h) // 2

        colors = {
            "female": cls.hex_to_rgb(style.get("female_color", "#b50b56")),
            "male": cls.hex_to_rgb(style.get("male_color", "#173357")),
            "both": cls.hex_to_rgb(style.get("both_color", "#7a2456")),
        }
        for s in style.get("custom_singers", []) or []:
            s_r = s.get("role") or s.get("name")
            if s_r:
                colors[s_r] = cls.hex_to_rgb(s.get("color", "#b50b56"))
            if s.get("name"):
                colors[s["name"]] = cls.hex_to_rgb(s.get("color", "#b50b56"))
        for index, line in enumerate(display):
            box = draw.textbbox((0, 0), line.full_text, font=font)
            x = (width - (box[2] - box[0])) // 2
            color = colors.get(line.singer, colors["both"])
            fill_color = color + (255,) if index == 0 else color + (165,)
            # Soft shadow
            draw.text((x + 1, y + 1), line.full_text, font=font, fill=(0, 0, 0, 45 if index == 0 else 25))
            # Text
            draw.text((x, y), line.full_text, font=font, fill=fill_color)
            y += line_h

    @classmethod
    def _draw_ambient_album_lyrics(
        cls, frame: Image.Image, lines: List[LyricLine], current_time: float, style: Dict[str, Any]
    ) -> None:
        active_index = next(
            (index for index, line in enumerate(lines) if line.line_start <= current_time <= line.line_end),
            None,
        )
        if active_index is None:
            active_index = next((index for index, line in enumerate(lines) if line.line_start > current_time), None)
        if active_index is None:
            return
        display = lines[active_index:active_index + 3]
        if not display:
            return

        width, height = frame.size
        draw = ImageDraw.Draw(frame, "RGBA")
        size = max(14, int(float(style.get("font_size", 38)) * width / 1300))
        font = cls.get_system_font(style.get("font_family", "Montserrat"), size, True)
        x = int(width * 0.50)
        max_width = int(width * 0.46)
        available_h = int(height * 0.68)
        block_height = min(int(height * 0.20), available_h // max(1, len(display)))
        y = int(height - (len(display) * block_height)) // 2

        for order, line in enumerate(display):
            words = line.full_text.split()
            wrapped = []
            current = ""
            for word in words:
                candidate = f"{current} {word}".strip()
                if current and draw.textbbox((0, 0), candidate, font=font)[2] > max_width:
                    wrapped.append(current)
                    current = word
                else:
                    current = candidate
            if current:
                wrapped.append(current)
            
            shadow_color = (0, 0, 0, 180 if order == 0 else 120)
            text_color = (255, 255, 255, 255) if order == 0 else (220, 235, 230, 160)
            line_y = y + order * block_height
            for row, text_line in enumerate(wrapped[:2]):
                ty = line_y + row * int(size * 1.15)
                # Shadow
                draw.text((x + 2, ty + 2), text_line, font=font, fill=shadow_color)
                # Fill
                draw.text((x, ty), text_line, font=font, fill=text_color)

    @classmethod
    def _draw_walters_lyric_queue(
        cls, frame: Image.Image, lines: List[LyricLine], current_time: float, style: Dict[str, Any]
    ) -> None:
        active_index = next(
            (index for index, line in enumerate(lines) if line.line_start <= current_time <= line.line_end),
            None,
        )
        if active_index is None:
            active_index = next((index for index, line in enumerate(lines) if line.line_start > current_time), None)
        if active_index is None:
            return

        width, height = frame.size
        x = int(width * 0.45)
        max_width = int(width * 0.49)

        start_index = max(0, active_index - 1)
        end_index = min(len(lines), active_index + 3)
        display = list(enumerate(lines[start_index:end_index], start=start_index))
        base_size = max(13, int(float(style.get("font_size", 34)) * width / 1280))
        row_height = int(height * 0.115)
        y = int(height * 0.42) - max(0, active_index - start_index) * row_height

        draw = ImageDraw.Draw(frame, "RGBA")
        for order, (line_index, line) in enumerate(display):
            line_y = y + order * row_height
            offset_lines = line_index - active_index
            is_active = (line_index == active_index)

            curr_sz = base_size
            font = cls.get_system_font(style.get("font_family", "Montserrat"), curr_sz, True)
            while curr_sz > 11 and draw.textlength(line.full_text, font=font) > max_width - int(width * 0.02):
                curr_sz -= 1
                font = cls.get_system_font(style.get("font_family", "Montserrat"), curr_sz, True)

            # Center text vertically in row
            bbox = draw.textbbox((0, 0), line.full_text, font=font)
            text_h = bbox[3] - bbox[1]
            text_y = line_y + (row_height - text_h) // 2

            if is_active:
                pill_rect = (
                    x - int(width * 0.012), line_y + int(height * 0.004),
                    x + max_width + int(width * 0.008), line_y + row_height - int(height * 0.004),
                )
                draw.rounded_rectangle(
                    pill_rect,
                    radius=max(6, int(height * 0.015)),
                    fill=(255, 255, 255, 34),
                    outline=(255, 255, 255, 45),
                    width=1,
                )
                # Drop shadow
                draw.text(
                    (x + 1, text_y + 1), line.full_text, font=font,
                    fill=(0, 0, 0, 180),
                )
                draw.text(
                    (x, text_y), line.full_text, font=font,
                    fill=(255, 255, 255, 255),
                )
            else:
                alpha = 110 if offset_lines < 0 else (80 if offset_lines == 1 else 45)
                draw.text(
                    (x, text_y), line.full_text, font=font,
                    fill=(255, 255, 255, alpha),
                )

    @classmethod
    def _draw_ksector_2000s_lyrics(
        cls, frame: Image.Image, lines: List[LyricLine], current_time: float, style: Dict[str, Any]
    ) -> None:
        active_index = next(
            (index for index, line in enumerate(lines) if line.line_start <= current_time <= line.line_end),
            None,
        )
        if active_index is None:
            return

        width, height = frame.size
        draw = ImageDraw.Draw(frame, "RGBA")
        colors = {
            "male": cls.hex_to_rgb(style.get("male_color", "#6e2d1c")),
            "female": cls.hex_to_rgb(style.get("female_color", "#8d213c")),
            "both": cls.hex_to_rgb(style.get("both_color", "#b34a2f")),
        }
        active_line = lines[active_index]
        active_color = colors.get(active_line.singer, colors["both"])
        active_text = active_line.full_text.upper() if style.get("uppercase_lyrics", True) else active_line.full_text
        max_width = int(width * 0.84)
        font_size = max(24, int(float(style.get("font_size", 58)) * width / 1280))
        font = cls.get_system_font(style.get("font_family", "Impact"), font_size, True)
        while font_size > max(16, int(height * 0.045)) and draw.textlength(active_text, font=font) > max_width:
            font_size -= 1
            font = cls.get_system_font(style.get("font_family", "Impact"), font_size, True)

        active_width = draw.textlength(active_text, font=font)
        active_x = (width - active_width) / 2
        active_y = int(height * 0.625)
        shadow = max(2, int(height * 0.006))
        draw.text(
            (active_x + shadow, active_y + shadow), active_text,
            font=font, fill=(76, 44, 31, 105),
        )
        draw.text((active_x, active_y), active_text, font=font, fill=active_color + (255,))

        context_font = cls.get_system_font("Segoe UI", max(12, int(height * 0.029)), True)
        context_rows = []
        if active_index > 0:
            context_rows.append((lines[active_index - 1].full_text, int(height * 0.555), 115))
        if active_index + 1 < len(lines):
            context_rows.append((lines[active_index + 1].full_text, int(height * 0.81), 145))
        for text, y, alpha in context_rows:
            if draw.textlength(text, font=context_font) > max_width:
                while len(text) > 4 and draw.textlength(text + "...", font=context_font) > max_width:
                    text = text[:-1]
                text = text.rstrip() + "..."
            text_width = draw.textlength(text, font=context_font)
            draw.text(
                ((width - text_width) / 2, y), text,
                font=context_font, fill=active_color + (alpha,),
            )
        rule_y = int(height * 0.785)
        draw.line(
            ((int(width * 0.33), rule_y), (int(width * 0.67), rule_y)),
            fill=active_color + (55,), width=max(1, int(height * 0.002)),
        )

    @classmethod
    def _draw_falling_u_douyin_stage(
        cls, frame: Image.Image, current_time: float, duration: float, style: Dict[str, Any]
    ) -> None:
        width, height = frame.size
        # 1. Dark Cyber Ambient Background with Spotlight Glows
        dark_bg = Image.new("RGBA", (width, height), (8, 2, 20, 245))
        frame.paste(dark_bg, (0, 0), dark_bg)

        # Ambient spotlights
        spotlights = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        sp_draw = ImageDraw.Draw(spotlights, "RGBA")
        r1 = int(width * 0.40)
        cx1, cy1 = int(width * 0.22), int(height * 0.52)
        sp_draw.ellipse((cx1 - r1, cy1 - r1, cx1 + r1, cy1 + r1), fill=(168, 85, 247, 105))
        
        r2 = int(width * 0.38)
        cx2, cy2 = int(width * 0.75), int(height * 0.50)
        sp_draw.ellipse((cx2 - r2, cy2 - r2, cx2 + r2, cy2 + r2), fill=(217, 70, 239, 65))
        spotlights = spotlights.filter(ImageFilter.GaussianBlur(max(15, int(height * 0.08))))
        frame.paste(spotlights, (0, 0), spotlights)

        # 2. Realistic DJ Vinyl Turntable Disc (Left Side)
        disc_size = int(min(width * 0.36, height * 0.64))
        disc_cx = int(width * 0.22)
        disc_cy = int(height * 0.52)
        disc_x0 = disc_cx - disc_size // 2
        disc_y0 = disc_cy - disc_size // 2

        draw = ImageDraw.Draw(frame, "RGBA")
        
        # Outer reactive pulse rim
        pulse = 1.0 + 0.03 * math.sin(current_time * 12.0)
        p_sz = int(disc_size * pulse)
        draw.ellipse((disc_cx - p_sz // 2, disc_cy - p_sz // 2, disc_cx + p_sz // 2, disc_cy + p_sz // 2), outline=(0, 245, 212, 130), width=2)

        # Vinyl body
        draw.ellipse((disc_x0, disc_y0, disc_x0 + disc_size, disc_y0 + disc_size), fill=(14, 15, 20, 255), outline=(50, 52, 65, 255), width=2)

        # Concentric grooves
        for r_factor in [0.94, 0.88, 0.82, 0.76, 0.70, 0.64, 0.58]:
            gr_s = int(disc_size * r_factor)
            gx0 = disc_cx - gr_s // 2
            gy0 = disc_cy - gr_s // 2
            draw.ellipse((gx0, gy0, gx0 + gr_s, gy0 + gr_s), outline=(255, 255, 255, 25), width=1)

        center_size = int(disc_size * 0.40)
        cov_path = style.get("album_cover_path", "")
        if cov_path and os.path.exists(cov_path):
            try:
                center_img = Image.open(cov_path).convert("RGB")
            except Exception:
                center_img = Image.new("RGB", (center_size, center_size), (217, 70, 239))
        else:
            center_img = Image.new("RGB", (center_size, center_size), (217, 70, 239))

        center_img = cls.fit_background(center_img, (center_size, center_size))
        rot_angle = -(current_time * 90.0) % 360.0
        center_img = center_img.rotate(rot_angle, resample=Image.BICUBIC)

        mask = Image.new("L", (center_size, center_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, center_size - 1, center_size - 1), fill=255)
        hole_size = int(center_size * 0.20)
        hx0 = (center_size - hole_size) // 2
        ImageDraw.Draw(mask).ellipse((hx0, hx0, hx0 + hole_size, hx0 + hole_size), fill=0)

        cx0 = disc_cx - center_size // 2
        cy0 = disc_cy - center_size // 2
        frame.paste(center_img, (cx0, cy0), mask)

        # Tonearm needle
        arm_top_x = disc_cx + int(disc_size * 0.45)
        arm_top_y = disc_cy - int(disc_size * 0.52)
        needle_x = disc_cx + int(disc_size * 0.22)
        needle_y = disc_cy + int(disc_size * 0.10)
        draw.ellipse((arm_top_x - 5, arm_top_y - 5, arm_top_x + 5, arm_top_y + 5), fill=(40, 42, 54, 255), outline=(200, 205, 220, 255), width=2)
        draw.line(((arm_top_x, arm_top_y), (needle_x + 10, needle_y - 20)), fill=(220, 225, 240, 255), width=2)
        draw.line(((needle_x + 10, needle_y - 20), (needle_x, needle_y)), fill=(220, 225, 240, 255), width=2)

        # 3. Top DJ Badge & Track Info
        badge_font = cls.get_system_font("Montserrat", max(9, int(height * 0.024)), True)
        badge_text = "⚡ DOUYIN DJ CLUB REMIX ⚡"
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        badge_w = bw + 28
        badge_h = max(22, bh + 10)
        badge_x = (width - badge_w) // 2
        badge_y = int(height * 0.04)

        draw.rounded_rectangle((badge_x, badge_y, badge_x + badge_w, badge_y + badge_h), radius=badge_h // 2, fill=(14, 8, 30, 235), outline=(0, 245, 212, 255), width=1)
        draw.text((badge_x + (badge_w - bw) // 2, badge_y + (badge_h - bh) // 2), badge_text, font=badge_font, fill=(0, 245, 212, 255))

        title_font = cls.get_system_font("Montserrat", max(11, int(height * 0.034)), True)
        t_text = (style.get("track_title") or "FALLING U (DJSKING REMIX)").upper()
        t_box = draw.textbbox((0, 0), t_text, font=title_font)
        tw = t_box[2] - t_box[0]
        draw.text(((width - tw) // 2, badge_y + badge_h + int(height * 0.012)), t_text, font=title_font, fill=(255, 255, 255, 255))

        # 4. Neon Audio Equalizer Bars (Placed on the right side under lyrics)
        eq_y = int(height * 0.90)
        eq_w = int(width * 0.50)
        eq_x = int(width * 0.44)
        num_bars = 26
        bar_step = eq_w / num_bars
        bar_w = max(2, int(bar_step * 0.62))
        for i in range(num_bars):
            val = abs(math.sin(current_time * 9.0 + i * 0.40) * math.cos(current_time * 5.0 + i * 0.25))
            bh_bar = max(3, int(val * height * 0.09))
            bx = int(eq_x + i * bar_step)
            draw.rounded_rectangle((bx, eq_y - bh_bar, bx + bar_w, eq_y), radius=2, fill=(0, 245, 212, 235))
            draw.rounded_rectangle((bx, eq_y + 1, bx + bar_w, eq_y + int(bh_bar * 0.4)), radius=1, fill=(0, 245, 212, 60))

    @classmethod
    def _draw_falling_u_douyin_lyrics(
        cls, frame: Image.Image, lines: List[LyricLine], current_time: float, style: Dict[str, Any]
    ) -> None:
        active_index = next(
            (index for index, line in enumerate(lines) if line.line_start <= current_time <= line.line_end),
            None,
        )
        if active_index is None:
            return

        width, height = frame.size
        active_line = lines[active_index]
        draw = ImageDraw.Draw(frame, "RGBA")

        lx = int(width * 0.42)
        lw = int(width * 0.53)
        ly = int(height * 0.40)

        font_sz = max(20, int(float(style.get("font_size", 48)) * width / 1280))
        font = cls.get_system_font(style.get("font_family", "Montserrat"), font_sz, True)
        full_text = active_line.full_text

        while font_sz > 12 and draw.textlength(full_text, font=font) > (lw - 16):
            font_sz -= 1
            font = cls.get_system_font(style.get("font_family", "Montserrat"), font_sz, True)

        bbox = draw.textbbox((0, 0), full_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = lx + (lw - text_w) // 2
        text_y = ly

        # Outline & Drop Shadow for 100% Contrast
        stroke_w = max(3, int(font_sz * 0.12))
        draw.text((text_x + 3, text_y + 3), full_text, font=font, fill=(0, 0, 0, 195), stroke_width=stroke_w, stroke_fill=(0, 0, 0, 220))
        draw.text((text_x, text_y), full_text, font=font, fill=(255, 255, 255, 235), stroke_width=stroke_w, stroke_fill=(0, 0, 0, 245))

        # Dynamic Karaoke Sweep
        line_dur = max(0.1, active_line.line_end - active_line.line_start)
        progress = max(0.0, min(1.0, (current_time - active_line.line_start) / line_dur))
        if progress > 0:
            sweep_w = int(text_w * progress)
            hl_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            hl_draw = ImageDraw.Draw(hl_img, "RGBA")
            hl_draw.text((text_x, text_y), full_text, font=font, fill=(0, 245, 212, 255), stroke_width=stroke_w, stroke_fill=(0, 0, 0, 245))
            
            crop_mask = Image.new("L", (width, height), 0)
            ImageDraw.Draw(crop_mask).rectangle((text_x - 4, text_y - 8, text_x + sweep_w + 4, text_y + text_h + 16), fill=255)
            frame.paste(hl_img, (0, 0), crop_mask)

        # Upcoming Line (Floating Clean Subtitle)
        if active_index + 1 < len(lines):
            next_line = lines[active_index + 1]
            sub_sz = max(12, int(font_sz * 0.68))
            sub_font = cls.get_system_font(style.get("font_family", "Montserrat"), sub_sz, True)
            sub_text = next_line.full_text

            while sub_sz > 10 and draw.textlength(sub_text, font=sub_font) > (lw - 24):
                sub_sz -= 1
                sub_font = cls.get_system_font(style.get("font_family", "Montserrat"), sub_sz, True)

            sub_box = draw.textbbox((0, 0), sub_text, font=sub_font)
            sub_w = sub_box[2] - sub_box[0]
            sub_x = lx + (lw - sub_w) // 2
            sub_y = text_y + text_h + int(height * 0.05)

            sub_stroke = max(2, int(sub_sz * 0.10))
            draw.text((sub_x, sub_y), sub_text, font=sub_font, fill=(220, 235, 255, 190), stroke_width=sub_stroke, stroke_fill=(0, 0, 0, 220))

    @classmethod
    def _draw_eminem_rap_hiphop_stage(
        cls, frame: Image.Image, current_time: float, duration: float, style: Dict[str, Any]
    ) -> None:
        width, height = frame.size
        # 1. Dark fiery rap stage atmosphere
        dark_bg = Image.new("RGBA", (width, height), (18, 5, 8, 245))
        frame.paste(dark_bg, (0, 0), dark_bg)

        # Deep crimson / amber stage light spots
        spotlights = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        sp_draw = ImageDraw.Draw(spotlights, "RGBA")
        r1 = int(width * 0.40)
        cx1, cy1 = int(width * 0.22), int(height * 0.52)
        sp_draw.ellipse((cx1 - r1, cy1 - r1, cx1 + r1, cy1 + r1), fill=(239, 68, 68, 90))
        
        r2 = int(width * 0.36)
        cx2, cy2 = int(width * 0.75), int(height * 0.50)
        sp_draw.ellipse((cx2 - r2, cy2 - r2, cx2 + r2, cy2 + r2), fill=(245, 158, 11, 55))
        spotlights = spotlights.filter(ImageFilter.GaussianBlur(max(15, int(height * 0.08))))
        frame.paste(spotlights, (0, 0), spotlights)

        # Drifting spark particles
        sp_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        sp_d = ImageDraw.Draw(sp_layer, "RGBA")
        for i in range(16):
            px = (i * 73 + int(current_time * 25)) % width
            py = height - ((i * 47 + int(current_time * 60)) % height)
            p_sz = max(2, (i % 3) + 1)
            p_alpha = int(120 + 80 * math.sin(current_time * 4.0 + i))
            sp_d.ellipse((px - p_sz, py - p_sz, px + p_sz, py + p_sz), fill=(255, 140, 0, p_alpha))
        frame.paste(sp_layer, (0, 0), sp_layer)

        # 2. 3D CD Jewel Case & Sliding Compact Disc
        case_w = int(min(width * 0.28, height * 0.56))
        case_h = case_w
        case_x = int(width * 0.08)
        case_y = int((height - case_h) * 0.55)

        # CD Disc (Sliding out to the right)
        cd_size = int(case_w * 0.94)
        cd_cx = case_x + int(case_w * 0.72)
        cd_cy = case_y + int(case_h * 0.50)
        cd_x0 = cd_cx - cd_size // 2
        cd_y0 = cd_cy - cd_size // 2

        draw = ImageDraw.Draw(frame, "RGBA")
        draw.ellipse((cd_x0, cd_y0, cd_x0 + cd_size, cd_y0 + cd_size), fill=(25, 28, 36, 255), outline=(180, 190, 205, 255), width=2)

        # Inner tracks & clear hub
        for r_f in [0.85, 0.70, 0.55]:
            tr_s = int(cd_size * r_f)
            draw.ellipse((cd_cx - tr_s // 2, cd_cy - tr_s // 2, cd_cx + tr_s // 2, cd_cy + tr_s // 2), outline=(255, 255, 255, 30), width=1)

        clear_hub = int(cd_size * 0.22)
        draw.ellipse((cd_cx - clear_hub // 2, cd_cy - clear_hub // 2, cd_cx + clear_hub // 2, cd_cy + clear_hub // 2), fill=(15, 8, 12, 230), outline=(255, 255, 255, 90), width=1)
        spindle = int(cd_size * 0.09)
        draw.ellipse((cd_cx - spindle // 2, cd_cy - spindle // 2, cd_cx + spindle // 2, cd_cy + spindle // 2), fill=(8, 2, 20, 255))

        # Jewel Case Cover Art
        cov_path = style.get("album_cover_path", "")
        if cov_path and os.path.exists(cov_path):
            try:
                cover_img = Image.open(cov_path).convert("RGB")
            except Exception:
                cover_img = Image.new("RGB", (case_w, case_h), (59, 7, 18))
        else:
            cover_img = Image.new("RGB", (case_w, case_h), (59, 7, 18))

        cover_img = cls.fit_background(cover_img, (case_w, case_h))
        frame.paste(cover_img, (case_x, case_y))

        # Jewel Case Glass Specular & Outline
        draw.rectangle((case_x, case_y, case_x + case_w, case_y + case_h), outline=(255, 255, 255, 90), width=2)
        spine_w = max(4, int(case_w * 0.04))
        draw.rectangle((case_x, case_y, case_x + spine_w, case_y + case_h), fill=(20, 20, 25, 220))

        # PARENTAL ADVISORY Badge
        pa_w = int(case_w * 0.36)
        pa_h = int(pa_w * 0.46)
        pa_x = case_x + case_w - pa_w - 6
        pa_y = case_y + case_h - pa_h - 6
        draw.rectangle((pa_x, pa_y, pa_x + pa_w, pa_y + pa_h), fill=(255, 255, 255, 245), outline=(0, 0, 0, 255), width=1)
        pa_font = cls.get_system_font("Impact", max(6, int(pa_h * 0.40)), True)
        draw.text((pa_x + 3, pa_y + 1), "PARENTAL", font=pa_font, fill=(0, 0, 0, 255))
        pa_sub_font = cls.get_system_font("Arial", max(4, int(pa_h * 0.28)), True)
        draw.text((pa_x + 3, pa_y + int(pa_h * 0.50)), "ADVISORY", font=pa_sub_font, fill=(0, 0, 0, 255))

        # 3. Top Rap Playlist Banner & Header
        badge_font = cls.get_system_font("Montserrat", max(9, int(height * 0.024)), True)
        badge_text = "🔥 BEST OF RAP & HIPHOP PLAYLIST 🔥"
        bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        badge_w = bw + 28
        badge_h = max(22, bh + 10)
        badge_x = (width - badge_w) // 2
        badge_y = int(height * 0.04)

        draw.rounded_rectangle((badge_x, badge_y, badge_x + badge_w, badge_y + badge_h), radius=badge_h // 2, fill=(24, 6, 12, 235), outline=(239, 68, 68, 255), width=1)
        draw.text((badge_x + (badge_w - bw) // 2, badge_y + (badge_h - bh) // 2), badge_text, font=badge_font, fill=(245, 158, 11, 255))

        # Title
        title_font = cls.get_system_font("Impact", max(13, int(height * 0.040)), True)
        t_artist = (style.get("track_artist") or "EMINEM").upper()
        t_name = (style.get("track_title") or "LOSE YOURSELF").upper()
        t_full = f"{t_artist} — {t_name}" if t_artist != "ARTIST" else t_name
        t_box = draw.textbbox((0, 0), t_full, font=title_font)
        tw = t_box[2] - t_box[0]
        draw.text(((width - tw) // 2 + 1, badge_y + badge_h + int(height * 0.012) + 1), t_full, font=title_font, fill=(0, 0, 0, 220))
        draw.text(((width - tw) // 2, badge_y + badge_h + int(height * 0.012)), t_full, font=title_font, fill=(255, 255, 255, 255))

        # 4. Multi-band Stereo LED Equalizer Spectrum
        eq_y = int(height * 0.90)
        eq_w = int(width * 0.48)
        eq_x = int(width * 0.46)
        num_bars = 28
        bar_step = eq_w / num_bars
        bar_w = max(2, int(bar_step * 0.65))

        for i in range(num_bars):
            val = abs(math.sin(current_time * 10.0 + i * 0.35) * math.cos(current_time * 6.0 + i * 0.20))
            bh_bar = max(3, int(val * height * 0.10))
            bx = int(eq_x + i * bar_step)
            # Emerald green to amber to red peak
            bar_col = (239, 68, 68, 240) if val > 0.65 else ((245, 158, 11, 240) if val > 0.35 else (16, 185, 129, 240))
            draw.rounded_rectangle((bx, eq_y - bh_bar, bx + bar_w, eq_y), radius=1, fill=bar_col)
            draw.rounded_rectangle((bx, eq_y + 1, bx + bar_w, eq_y + int(bh_bar * 0.35)), radius=1, fill=(245, 158, 11, 60))

    @classmethod
    def _draw_eminem_rap_hiphop_lyrics(
        cls, frame: Image.Image, lines: List[LyricLine], current_time: float, style: Dict[str, Any]
    ) -> None:
        active_index = next(
            (index for index, line in enumerate(lines) if line.line_start <= current_time <= line.line_end),
            None,
        )
        if active_index is None:
            return

        width, height = frame.size
        active_line = lines[active_index]
        draw = ImageDraw.Draw(frame, "RGBA")

        lx = int(width * 0.44)
        lw = int(width * 0.51)
        ly = int(height * 0.40)

        font_sz = max(22, int(float(style.get("font_size", 48)) * width / 1280))
        font = cls.get_system_font(style.get("font_family", "Impact"), font_sz, True)
        full_text = active_line.full_text.upper() if style.get("uppercase_lyrics", True) else active_line.full_text

        while font_sz > 14 and draw.textlength(full_text, font=font) > (lw - 16):
            font_sz -= 1
            font = cls.get_system_font(style.get("font_family", "Impact"), font_sz, True)

        bbox = draw.textbbox((0, 0), full_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_x = lx + (lw - text_w) // 2
        text_y = ly

        # Outline & Drop Shadow for 100% Contrast
        stroke_w = max(3, int(font_sz * 0.12))
        draw.text((text_x + 3, text_y + 3), full_text, font=font, fill=(0, 0, 0, 210), stroke_width=stroke_w, stroke_fill=(0, 0, 0, 250))
        draw.text((text_x, text_y), full_text, font=font, fill=(255, 255, 255, 235), stroke_width=stroke_w, stroke_fill=(0, 0, 0, 250))

        # Dynamic Karaoke Sweep
        line_dur = max(0.1, active_line.line_end - active_line.line_start)
        progress = max(0.0, min(1.0, (current_time - active_line.line_start) / line_dur))
        if progress > 0:
            sweep_w = int(text_w * progress)
            hl_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            hl_draw = ImageDraw.Draw(hl_img, "RGBA")
            hl_draw.text((text_x, text_y), full_text, font=font, fill=(245, 158, 11, 255), stroke_width=stroke_w, stroke_fill=(0, 0, 0, 250))
            
            crop_mask = Image.new("L", (width, height), 0)
            ImageDraw.Draw(crop_mask).rectangle((text_x - 4, text_y - 8, text_x + sweep_w + 4, text_y + text_h + 16), fill=255)
            frame.paste(hl_img, (0, 0), crop_mask)

        # Upcoming Line
        if active_index + 1 < len(lines):
            next_line = lines[active_index + 1]
            sub_sz = max(13, int(font_sz * 0.65))
            sub_font = cls.get_system_font(style.get("font_family", "Impact"), sub_sz, True)
            sub_text = next_line.full_text.upper() if style.get("uppercase_lyrics", True) else next_line.full_text

            while sub_sz > 10 and draw.textlength(sub_text, font=sub_font) > (lw - 24):
                sub_sz -= 1
                sub_font = cls.get_system_font(style.get("font_family", "Impact"), sub_sz, True)

            sub_box = draw.textbbox((0, 0), sub_text, font=sub_font)
            sub_w = sub_box[2] - sub_box[0]
            sub_x = lx + (lw - sub_w) // 2
            sub_y = text_y + text_h + int(height * 0.05)

            sub_stroke = max(2, int(sub_sz * 0.11))
            draw.text((sub_x, sub_y), sub_text, font=sub_font, fill=(255, 220, 220, 180), stroke_width=sub_stroke, stroke_fill=(0, 0, 0, 220))

    @classmethod
    def render_frame(
        cls,
        background: Image.Image,
        lyric_lines: List[LyricLine],
        current_time: float,
        duration: float,
        style_config: Dict[str, Any],
    ) -> Image.Image:
        size = cls.resolve_output_size(style_config)
        frame = cls.fit_background(background, size)
        frame = cls._apply_color_effects(frame, style_config)
        if style_config.get("template_variant") == "ambient_album_player":
            cls._draw_ambient_album_stage(frame, current_time, duration, style_config)
        elif style_config.get("template_variant") == "walters_lyric_queue":
            cls._draw_walters_lyric_queue_stage(frame, style_config)
        elif style_config.get("template_variant") == "falling_u_douyin_dj":
            cls._draw_falling_u_douyin_stage(frame, current_time, duration, style_config)
        elif style_config.get("template_variant") == "eminem_rap_hiphop_album":
            cls._draw_eminem_rap_hiphop_stage(frame, current_time, duration, style_config)
        elif style_config.get("template_variant") == "hanako_falling_you":
            cls._draw_hanako_falling_you_stage(frame, current_time, duration, style_config)
        elif style_config.get("template_variant") == "multi_song_album":
            cls._draw_multi_song_album_stage(frame, current_time, duration, style_config)
        elif style_config.get("template_variant") == "ksector_2000s_editorial":
            cls._draw_ksector_2000s_stage(frame, lyric_lines, current_time, style_config)
        cls._draw_particles(frame, current_time, style_config)
        cls._draw_visualizer(frame, current_time, style_config)
        cls._draw_singer_banner(frame, lyric_lines, current_time, style_config)
        cls._draw_overlays(frame, current_time, style_config)
        cls._draw_lyrics(frame, lyric_lines, current_time, style_config)
        cls._draw_watermark(frame, style_config)
        return cls._apply_transition(frame, current_time, duration, style_config)

    @classmethod
    def render_video(
        cls,
        output_path: str,
        bg_path: str,
        audio_path: str,
        lyric_lines: List[LyricLine],
        duration: float,
        style_config: Dict[str, Any],
        progress_callback: Optional[Callable[[int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> bool:
        """Render an MP4. Arguments intentionally match ``RenderWorker`` order."""
        if duration <= 0 or not output_path:
            return False
        fps = max(1, min(60, int(style_config.get("fps", 30))))
        width, height = cls.resolve_output_size(style_config)
        total_frames = max(1, int(math.ceil(duration * fps)))

        video_reader = None
        video_fps = float(fps)
        video_duration = 0.0
        video_frame_count = 0.0
        background = Image.new("RGB", (width, height), (30, 41, 59))
        if bg_path and os.path.exists(bg_path):
            extension = os.path.splitext(bg_path)[1].lower()
            if extension in cls.VIDEO_EXTENSIONS:
                try:
                    import imageio.v2 as imageio
                    video_reader = imageio.get_reader(bg_path)
                    metadata = video_reader.get_meta_data()
                    video_fps = max(1.0, float(metadata.get("fps", fps)))
                    video_duration = float(metadata.get("duration", 0.0) or 0.0)
                    video_frame_count = float(metadata.get("nframes", 0.0) or 0.0)
                except Exception:
                    video_reader = None
            else:
                try:
                    background = Image.open(bg_path).convert("RGB")
                except OSError:
                    pass

        try:
            import imageio_ffmpeg
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ffmpeg = "ffmpeg"

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        output_dir = os.path.dirname(os.path.abspath(output_path))
        with tempfile.TemporaryDirectory(prefix="lylis_render_", dir=output_dir) as temp_dir:
            raw_path = os.path.join(temp_dir, "video.mp4")
            encode_cmd = [
                ffmpeg, "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
                "-s", f"{width}x{height}", "-pix_fmt", "rgb24", "-r", str(fps),
                "-i", "-", "-an", "-c:v", "libx264", "-preset", "fast",
                "-pix_fmt", "yuv420p", raw_path,
            ]
            sub_kwargs = {}
            if os.name == "nt":
                sub_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            proc = subprocess.Popen(encode_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **sub_kwargs)
            try:
                for frame_index in range(total_frames):
                    if cancel_check and cancel_check():
                        proc.terminate()
                        return False
                    current_time = frame_index / fps
                    source = background
                    if video_reader is not None:
                        source_index = looping_frame_index(
                            current_time,
                            video_fps,
                            video_duration,
                            video_frame_count,
                        )
                        try:
                            source = Image.fromarray(video_reader.get_data(source_index)).convert("RGB")
                        except Exception:
                            try:
                                source = Image.fromarray(video_reader.get_data(0)).convert("RGB")
                            except Exception:
                                source = background
                    frame = cls.render_frame(source, lyric_lines, current_time, duration, style_config)
                    if frame.mode != "RGB":
                        frame = frame.convert("RGB")
                    proc.stdin.write(frame.tobytes())
                    if progress_callback and frame_index % max(1, fps // 2) == 0:
                        progress_callback(min(90, int(frame_index * 90 / total_frames)))
                proc.stdin.close()
                proc.wait()
            finally:
                if video_reader is not None:
                    video_reader.close()
                if proc.poll() is None:
                    proc.terminate()
            if proc.returncode != 0 or not os.path.exists(raw_path):
                return False

            mux_cmd = [ffmpeg, "-y", "-i", raw_path]
            if audio_path and os.path.exists(audio_path):
                mux_cmd += ["-i", audio_path, "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest"]
            else:
                mux_cmd += ["-c:v", "copy"]
            mux_cmd.append(output_path)
            if progress_callback:
                progress_callback(94)
            result = subprocess.run(mux_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **sub_kwargs)
            success = result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0
            if progress_callback:
                progress_callback(100 if success else 0)
            return success
