"""
Lylis Karaoke Studio - Templates Tab (Rich Template Library & Preset Gallery)
Features:
- 14 complete presets, including reference-inspired editorial, album-player, and sunset lyric styles, duet, ballad, acoustic, short-form, retro, and modern looks
- Category Filter Pills & Instant Live Search
- 1-Click Complete Style & Motion Application
"""
import copy
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QLineEdit, QButtonGroup, QMessageBox
)
from PyQt5.QtCore import pyqtSignal

TEMPLATES_DATA = [
    {
        "id": "tiki_tiki",
        "name": "🔥 TIKI TIKI (Suzana & VannDa Duet)",
        "category": "duet",
        "badge": "HOT TRENDING",
        "badge_color": "#ec4899",
        "description": "Bố cục song ca 50/50 với ảnh chân dung, làm tối ca sĩ không hoạt động, mép giấy xé và lời bài hát nghiêng theo màu vai.",
        "font_family": "Montserrat",
        "font_weight": "900 Cực Đậm",
        "font_size": 44,
        "display_mode": "COLOR CODED",
        "template_variant": "tiki_tiki",
        "motion_effect": "Pop & Bounce (Nảy chữ nhịp điệu)",
        "fill_color": "#b50b56",
        "male_color": "#173357",
        "female_color": "#b50b56",
        "both_color": "#7a2456",
        "particles": False,
        "particle_type": "None",
        "enable_glow": False,
        "glow_radius": 0,
        "vignette": 0,
        "custom_singers": [
            {"name": "SUZANA", "role": "female", "color": "#b50b56", "avatar": "S", "image_path": ""},
            {"name": "VANNDA", "role": "male", "color": "#a9470b", "avatar": "V", "image_path": ""}
        ]
    },
    {
        "id": "ambient_album_player",
        "name": "🎧 Ambient Album Player",
        "category": "modern",
        "badge": "NEW",
        "badge_color": "#14b8a6",
        "description": "Trình phát nhạc tối giản với ảnh bìa lớn, nền ambient đỏ/xanh, thanh tiến độ và hàng đợi lời bài hát cuộn bên phải.",
        "font_family": "Montserrat",
        "font_weight": "700 Bold",
        "font_size": 38,
        "display_mode": "SINGLE",
        "template_variant": "ambient_album_player",
        "motion_effect": "Slide Up Smooth (Trượt nổi mượt mà)",
        "fill_color": "#ffffff",
        "male_color": "#ffffff",
        "female_color": "#ffffff",
        "both_color": "#ffffff",
        "base_color": "#53615d",
        "particles": False,
        "particle_type": "None",
        "enable_glow": False,
        "glow_radius": 0,
        "vignette": 25,
        "track_title": "Song Title",
        "track_artist": "Artist",
        "custom_singers": []
    },
    {
        "id": "cuu_mon_hoi_uc_ballad",
        "name": "[Vietsub] Từ Cửu Môn Hồi Ức - Đẳng Thậm Ma Quân ♪",
        "category": "ballad",
        "badge": "VIDEO INSPIRED",
        "badge_color": "#b8864b",
        "description": "Album-player preset for the Vietnamese-subtitled Chinese ballad reference, with a deep ink background, warm antique-gold accents, and restrained lyric presentation.",
        "reference_url": "https://www.youtube.com/watch?v=NxEDFmqWFlo",
        "font_family": "Montserrat",
        "font_weight": "700 Bold",
        "font_size": 38,
        "display_mode": "SINGLE",
        "template_variant": "ambient_album_player",
        "motion_effect": "Fade In / Out (Mờ dần êm dịu)",
        "fill_color": "#f3e4c1",
        "male_color": "#f3e4c1",
        "female_color": "#d7a85d",
        "both_color": "#f3e4c1",
        "base_color": "#17151d",
        "layout_mode": "center",
        "text_alignment": "center",
        "stroke_width": 0,
        "particles": False,
        "particle_type": "None",
        "enable_glow": True,
        "glow_radius": 6,
        "vignette": 35,
        "brightness": -6,
        "contrast": 8,
        "saturation": -12,
        "blur": 0,
        "color_tint": "Warm Sunset",
        "visualizer": False,
        "pointer": False,
        "watermark": False,
        "custom_singers": []
    },
    {
        "id": "walters_lyric_queue",
        "name": "🎧 I Love You So Lyric Queue",
        "category": "modern",
        "badge": "VIDEO INSPIRED",
        "badge_color": "#77776d",
        "description": "Muted charcoal album-player layout inspired by The Walters reference: centered title, rounded cover art, and a five-line lyric queue with a frosted active-line highlight.",
        "reference_url": "https://youtu.be/wxWL7ybL_ZM",
        "font_family": "Montserrat",
        "font_weight": "700 Bold",
        "font_size": 34,
        "display_mode": "SINGLE",
        "template_variant": "walters_lyric_queue",
        "motion_effect": "Fade In / Out (Mờ dần êm dịu)",
        "fill_color": "#ffffff",
        "male_color": "#ffffff",
        "female_color": "#ffffff",
        "both_color": "#ffffff",
        "base_color": "#ffffff",
        "layout_mode": "center",
        "text_alignment": "left",
        "stroke_width": 0,
        "particles": False,
        "particle_type": "None",
        "enable_glow": False,
        "glow_radius": 0,
        "vignette": 20,
        "brightness": -12,
        "contrast": -4,
        "saturation": -28,
        "blur": 0,
        "color_tint": "None (Original)",
        "visualizer": False,
        "pointer": False,
        "watermark": False,
        "track_title": "The Walters - I Love You So",
        "track_artist": "The Walters",
        "custom_singers": []
    },
    {
        "id": "ksector_2000s_editorial",
        "name": "💄 10 Minutes Y2K Editorial",
        "category": "retro",
        "badge": "VIDEO INSPIRED",
        "badge_color": "#8d213c",
        "description": "Early-2000s K-pop editorial layout inspired by the Lee Hyori reference: warm portrait header, burgundy gradient band, italic artist label, ivory paper field, and oversized condensed color-coded lyrics.",
        "reference_url": "https://youtu.be/BbJ4ibqR6PQ",
        "font_family": "Impact",
        "font_weight": "900 Cực Đậm",
        "font_size": 58,
        "display_mode": "COLOR CODED",
        "template_variant": "ksector_2000s_editorial",
        "motion_effect": "Slide Up Smooth (Trượt nổi mượt mà)",
        "fill_color": "#8d213c",
        "male_color": "#6e2d1c",
        "female_color": "#8d213c",
        "both_color": "#b34a2f",
        "base_color": "#8d213c",
        "layout_mode": "center",
        "text_alignment": "center",
        "stroke_width": 0,
        "particles": False,
        "particle_type": "None",
        "enable_glow": False,
        "glow_radius": 0,
        "vignette": 8,
        "brightness": 4,
        "contrast": 12,
        "saturation": -4,
        "blur": 0,
        "color_tint": "Warm Sunset",
        "visualizer": False,
        "pointer": False,
        "watermark": False,
        "track_title": "10 MINUTES",
        "track_artist": "Lee Hyori",
        "portrait_focus_y": 25,
        "uppercase_lyrics": True,
        "custom_singers": []
    },
    {
        "id": "falling_u_douyin_dj",
        "name": "🎧 Hanako — Falling You (Reference)",
        "category": "edm",
        "badge": "VIDEO INSPIRED",
        "badge_color": "#a855f7",
        "description": "Phong cách Douyin DJ Club Remix: Khung neon phát sáng, đĩa xoay DJ vinyl reactor, sóng âm đa dải audio visualizer, hạt neon rơi và chữ phát sáng gradient cyan-magenta bốc lửa theo nhịp bass.",
        "reference_url": "https://youtu.be/kYB3N2SGuO4",
        "font_family": "Montserrat",
        "font_weight": "900 Cực Đậm",
        "font_size": 46,
        "display_mode": "SINGLE",
        "template_variant": "falling_u_douyin_dj",
        "motion_effect": "Neon Glow Wave (Sóng Neon phát sáng)",
        "fill_color": "#ffffff",
        "male_color": "#ffffff",
        "female_color": "#ffffff",
        "both_color": "#ffffff",
        "base_color": "#ffffff",
        "layout_mode": "center",
        "text_alignment": "center",
        "stroke_width": 3,
        "particles": False,
        "particle_type": "None",
        "enable_glow": False,
        "glow_radius": 0,
        "vignette": 12,
        "brightness": 0,
        "contrast": 4,
        "saturation": -10,
        "blur": 0,
        "color_tint": "Cool Cyber",
        "visualizer": False,
        "visualizer_mode": "Circular Wave (Vòng tròn động)",
        "pointer": False,
        "pointer_icon": "⚡",
        "watermark": False,
        "track_title": "FALLING YOU",
        "track_artist": "NHẠC HOT DOUYIN / TIKTOK",
        "custom_singers": []
    },
    {
        "id": "eminem_rap_hiphop_album",
        "name": "🔥 Best of Rap & HipHop Album (Animated CD)",
        "category": "modern",
        "badge": "VIDEO INSPIRED",
        "badge_color": "#ef4444",
        "description": "Bố cục Album Rap & Hip-Hop 3D với đĩa CD trượt xoay, ánh kim quang phổ cầu vồng, tem Parental Advisory, khói lửa nhiệt huyết và lời rap động lực bốc lửa.",
        "reference_url": "https://youtu.be/OOKMf-kMEdg?si=5ORR8qZBXXj8pcmG",
        "font_family": "Impact",
        "font_weight": "900 Cực Đậm",
        "font_size": 48,
        "display_mode": "SINGLE",
        "template_variant": "eminem_rap_hiphop_album",
        "motion_effect": "Pop & Bounce (Nảy chữ nhịp điệu)",
        "fill_color": "#ffffff",
        "male_color": "#ffffff",
        "female_color": "#ffffff",
        "both_color": "#ffffff",
        "base_color": "#ffffff",
        "layout_mode": "center",
        "text_alignment": "center",
        "stroke_width": 3,
        "particles": True,
        "particle_type": "Sparkles",
        "enable_glow": True,
        "glow_radius": 8,
        "vignette": 20,
        "brightness": -8,
        "contrast": 10,
        "saturation": 15,
        "blur": 0,
        "color_tint": "Warm Sunset",
        "visualizer": False,
        "pointer": False,
        "watermark": False,
        "track_title": "BEST OF RAP & HIPHOP",
        "track_artist": "Eminem",
        "custom_singers": []
    },
    {
        "id": "golden_ballad",
        "name": "🌟 Golden Ballad Classic",
        "category": "ballad",
        "badge": "CLASSIC",
        "badge_color": "#f59e0b",
        "description": "Tone vàng Amber Gold ấm áp sang trọng, chữ nghiêng Playwrite IS nghệ thuật kèm hiệu ứng hạt Bokeh lung linh.",
        "font_family": "Playwrite IS",
        "font_weight": "400 Thường",
        "font_size": 38,
        "display_mode": "COLOR CODED",
        "motion_effect": "Slide Up Smooth (Trượt nổi mượt mà)",
        "fill_color": "#f59e0b",
        "male_color": "#3b82f6",
        "female_color": "#ec4899",
        "both_color": "#f59e0b",
        "particles": True,
        "particle_type": "Bokeh Orbs 🫧",
        "enable_glow": True,
        "glow_radius": 12,
        "vignette": 45,
        "custom_singers": [
            {"name": "Ca sĩ 1", "color": "#3b82f6", "avatar": "👤", "image_path": ""},
            {"name": "Ca sĩ 2", "color": "#f59e0b", "avatar": "👤", "image_path": ""}
        ]
    },
    {
        "id": "cyberpunk_neon",
        "name": "⚡ Cyberpunk 2077 EDM Wave",
        "category": "edm",
        "badge": "CYBERPUNK",
        "badge_color": "#0026ff",
        "description": "Hai dòng so le Electric Blue & Neon Pink cực ngầu, font Montserrat siêu đậm, dải sóng nhạc spectrum audio reactive.",
        "font_family": "Montserrat",
        "font_weight": "900 Cực Đậm",
        "font_size": 52,
        "display_mode": "KARAOKE",
        "motion_effect": "Neon Glow Wave (Sóng phát sáng neon)",
        "fill_color": "#0026ff",
        "male_color": "#0026ff",
        "female_color": "#ff0033",
        "both_color": "#ff007f",
        "particles": True,
        "particle_type": "Music Notes 🎵",
        "enable_glow": True,
        "glow_radius": 14,
        "vignette": 50,
        "custom_singers": []
    },
    {
        "id": "sakura_lofi",
        "name": "🌸 Japanese Sakura & Lofi Chill",
        "category": "lofi",
        "badge": "RELAX",
        "badge_color": "#fb7185",
        "description": "Sắc hồng phấn dịu dàng, cánh hoa anh đào rơi lãng mạn, chữ mềm mại lướt êm dịu cho các bản Acoustic / Lofi.",
        "font_family": "Playwrite IS",
        "font_weight": "600 SemiBold",
        "font_size": 42,
        "display_mode": "KARAOKE",
        "motion_effect": "Slide Up Smooth (Trượt nổi mượt mà)",
        "fill_color": "#ec4899",
        "male_color": "#60a5fa",
        "female_color": "#f43f5e",
        "both_color": "#ec4899",
        "particles": True,
        "particle_type": "Sakura Petals 🌸",
        "enable_glow": True,
        "glow_radius": 8,
        "vignette": 25,
        "custom_singers": []
    },
    {
        "id": "retro_90s",
        "name": "📼 90s Retro CRT TV Karaoke",
        "category": "retro",
        "badge": "VINTAGE",
        "badge_color": "#eab308",
        "description": "Phong cách Karaoke đầu đĩa 90s huyền thoại, viền đen dày, chữ vàng quét trên nền xanh lá hoài niệm.",
        "font_family": "Impact",
        "font_weight": "900 Cực Đậm",
        "font_size": 48,
        "display_mode": "KARAOKE",
        "motion_effect": "Classic Karaoke Sweep (Quét karaoke chuẩn)",
        "fill_color": "#facc15",
        "male_color": "#22c55e",
        "female_color": "#ef4444",
        "both_color": "#eab308",
        "particles": False,
        "particle_type": "None",
        "enable_glow": False,
        "glow_radius": 0,
        "vignette": 15,
        "custom_singers": []
    },
    {
        "id": "tiktok_viral",
        "name": "🌈 TikTok Viral Rainbow Pulse",
        "category": "trending",
        "badge": "TIKTOK VIRAL",
        "badge_color": "#8b5cf6",
        "description": "Hiệu ứng chữ phóng to nhịp điệu (Kinetic Scale Pulse), màu sắc tươi sáng chuyển động nhanh cực kỳ bắt mắt cho video ngắn.",
        "font_family": "Montserrat",
        "font_weight": "900 Cực Đậm",
        "font_size": 46,
        "display_mode": "KARAOKE",
        "motion_effect": "Kinetic Scale Pulse (Phóng to từ đang hát)",
        "fill_color": "#f43f5e",
        "male_color": "#38bdf8",
        "female_color": "#f43f5e",
        "both_color": "#a855f7",
        "particles": True,
        "particle_type": "Floating Hearts ❤️",
        "enable_glow": True,
        "glow_radius": 10,
        "vignette": 30,
        "custom_singers": []
    },
    {
        "id": "riptide_sunset",
        "name": "🌅 Riptide Sunset Lyrics",
        "category": "pop",
        "badge": "VIDEO INSPIRED",
        "badge_color": "#c66b55",
        "description": "Warm sunset-cloud lyric video inspired by the reference: centered white brush lettering, dark outline, gentle fade, and no distracting overlays.",
        "font_family": "Segoe Print",
        "font_weight": "700 Bold",
        "font_size": 48,
        "display_mode": "SINGLE",
        "template_variant": "",
        "motion_effect": "Fade In / Out (Mờ dần êm dịu)",
        "base_color": "#ffffff",
        "fill_color": "#ffffff",
        "male_color": "#ffffff",
        "female_color": "#ffffff",
        "both_color": "#ffffff",
        "layout_mode": "center",
        "text_alignment": "center",
        "pos_y_bottom": 58,
        "stroke_width": 3,
        "particles": False,
        "particle_type": "None",
        "enable_glow": False,
        "glow_radius": 0,
        "vignette": 12,
        "brightness": -5,
        "contrast": 12,
        "saturation": -8,
        "blur": 1,
        "color_tint": "Warm Sunset",
        "visualizer": False,
        "pointer": False,
        "watermark": False,
        "custom_singers": []
    },
    {
        "id": "midnight_noir",
        "name": "🖤 Midnight Noir Minimal",
        "category": "modern",
        "badge": "MINIMAL",
        "badge_color": "#334155",
        "description": "Clean monochrome lyric card with centered type, soft cinematic contrast, and an understated fade for moody tracks.",
        "font_family": "Inter",
        "font_weight": "700 Bold",
        "font_size": 42,
        "display_mode": "SINGLE",
        "motion_effect": "Fade In / Out (Mờ dần êm dịu)",
        "base_color": "#ffffff",
        "fill_color": "#ffffff",
        "male_color": "#ffffff",
        "female_color": "#ffffff",
        "both_color": "#ffffff",
        "layout_mode": "center",
        "text_alignment": "center",
        "pos_y_bottom": 64,
        "stroke_width": 2,
        "particles": False,
        "particle_type": "None",
        "enable_glow": False,
        "glow_radius": 0,
        "vignette": 38,
        "contrast": 18,
        "saturation": -30,
        "color_tint": "Moody Noir",
        "visualizer": False,
        "pointer": False,
        "watermark": False,
        "custom_singers": []
    },
    {
        "id": "emerald_acoustic",
        "name": "🌿 Emerald Acoustic Session",
        "category": "acoustic",
        "badge": "ORGANIC",
        "badge_color": "#059669",
        "description": "Natural green grade, softly glowing centered lyrics, and quiet bokeh for acoustic, folk, and live-session videos.",
        "font_family": "Playfair Display",
        "font_weight": "700 Bold",
        "font_size": 40,
        "display_mode": "KARAOKE",
        "motion_effect": "Slide Up Smooth (Trượt nổi mượt mà)",
        "base_color": "#ecfdf5",
        "fill_color": "#6ee7b7",
        "male_color": "#34d399",
        "female_color": "#a7f3d0",
        "both_color": "#6ee7b7",
        "layout_mode": "center",
        "text_alignment": "center",
        "pos_y_bottom": 80,
        "stroke_width": 3,
        "particles": True,
        "particle_type": "Bokeh Orbs 🫧",
        "enable_glow": True,
        "glow_radius": 7,
        "vignette": 24,
        "color_tint": "Emerald Forest",
        "visualizer": False,
        "pointer": False,
        "watermark": False,
        "custom_singers": []
    },
    {
        "id": "vertical_reel_pop",
        "name": "📱 Vertical Reel Pop",
        "category": "trending",
        "badge": "9:16 READY",
        "badge_color": "#7c3aed",
        "description": "Bold build-up lyrics for Shorts and Reels with vivid violet highlights, kinetic motion, and a clean center-safe layout.",
        "font_family": "Big Shoulders Display",
        "font_weight": "900 Cực Đậm",
        "font_size": 54,
        "display_mode": "BUILD",
        "motion_effect": "Kinetic Scale Pulse (Phóng to từ đang hát)",
        "base_color": "#ffffff",
        "fill_color": "#c084fc",
        "male_color": "#38bdf8",
        "female_color": "#fb7185",
        "both_color": "#c084fc",
        "layout_mode": "center",
        "text_alignment": "center",
        "pos_y_bottom": 72,
        "stroke_width": 4,
        "particles": True,
        "particle_type": "Music Notes 🎵",
        "enable_glow": True,
        "glow_radius": 9,
        "vignette": 30,
        "contrast": 10,
        "color_tint": "Cool Cyberpunk",
        "visualizer": True,
        "pointer": False,
        "watermark": False,
        "custom_singers": []
    },
    {
        "id": "blue_hour_ballad",
        "name": "🌌 Blue Hour Ballad",
        "category": "ballad",
        "badge": "CINEMATIC",
        "badge_color": "#2563eb",
        "description": "Elegant blue-hour duet treatment with serif typography, gentle bokeh, and restrained cyan-to-rose role colors.",
        "font_family": "Playfair Display",
        "font_weight": "700 Bold",
        "font_size": 42,
        "display_mode": "KARAOKE",
        "motion_effect": "Slide Up Smooth (Trượt nổi mượt mà)",
        "base_color": "#f8fafc",
        "fill_color": "#93c5fd",
        "male_color": "#60a5fa",
        "female_color": "#f9a8d4",
        "both_color": "#c4b5fd",
        "layout_mode": "left_right",
        "text_alignment": "center",
        "pos_y_bottom": 80,
        "stroke_width": 3,
        "particles": True,
        "particle_type": "Bokeh Orbs 🫧",
        "enable_glow": True,
        "glow_radius": 6,
        "vignette": 34,
        "color_tint": "Moody Dark Film",
        "visualizer": False,
        "pointer": True,
        "watermark": False,
        "custom_singers": []
    },
    {
        "id": "hanako_falling_you",
        "name": "🎧 Hanako — Falling You Vinyl",
        "category": "modern",
        "badge": "VIDEO INSPIRED",
        "badge_color": "#6366f1",
        "description": "Faithful Falling You layout: blurred paper background, portrait card, black vinyl record, right-side title metadata, waveform and scrubber.",
        "reference_url": "https://youtu.be/kYB3N2SGuO4",
        "font_family": "Montserrat",
        "font_weight": "700 Bold",
        "font_size": 44,
        "display_mode": "SINGLE",
        "template_variant": "hanako_falling_you",
        "motion_effect": "Fade In / Out (Mờ dần êm dịu)",
        "base_color": "#ffffff",
        "fill_color": "#ffffff",
        "male_color": "#ffffff",
        "female_color": "#ffffff",
        "both_color": "#ffffff",
        "layout_mode": "center",
        "text_alignment": "center",
        "pos_y_bottom": 82,
        "stroke_width": 0,
        "particles": False,
        "particle_type": "None",
        "enable_glow": False,
        "glow_radius": 0,
        "vignette": 12,
        "brightness": 0,
        "contrast": 4,
        "saturation": -10,
        "blur": 0,
        "color_tint": "None (Original)",
        "visualizer": False,
        "pointer": False,
        "watermark": False,
        "custom_singers": []
    },
    {
        "id": "why_not_me_sunset",
        "name": "🌴 Why Not Me Sunset Script",
        "category": "pop",
        "badge": "VIDEO INSPIRED",
        "badge_color": "#7c3aed",
        "description": "Twilight palm-road lyric style inspired by the reference: oversized white brush lettering, deep violet shadow, soft stars, and a cinematic sunset grade.",
        "reference_url": "https://youtu.be/itboc4SIxjg",
        "font_family": "Segoe Print",
        "font_weight": "700 Bold",
        "font_size": 56,
        "display_mode": "SINGLE",
        "template_variant": "",
        "motion_effect": "Fade In / Out (Mờ dần êm dịu)",
        "base_color": "#fffaff",
        "fill_color": "#fffaff",
        "male_color": "#fffaff",
        "female_color": "#fffaff",
        "both_color": "#fffaff",
        "layout_mode": "center",
        "text_alignment": "center",
        "pos_y_bottom": 63,
        "stroke_width": 5,
        "particles": True,
        "particle_type": "Golden Sparkles ✨",
        "enable_glow": True,
        "glow_radius": 6,
        "vignette": 34,
        "brightness": -8,
        "contrast": 14,
        "saturation": -10,
        "blur": 0,
        "color_tint": "Moody Noir",
        "visualizer": False,
        "pointer": False,
        "watermark": False,
        "track_title": "Why Not Me",
        "track_artist": "Enrique Iglesias",
        "custom_singers": []
    },
    {
        "id": "multi_song_album",
        "name": "💿 Multi-Song Album Player",
        "category": "modern",
        "badge": "ALBUM MODE",
        "badge_color": "#4f46e5",
        "description": "Album-player template with cover art, five-track playlist, active-song highlight, and a cinematic progress bar.",
        "font_family": "Montserrat",
        "font_weight": "700 Bold",
        "font_size": 38,
        "display_mode": "SINGLE",
        "template_variant": "multi_song_album",
        "motion_effect": "Fade In / Out (Mờ dần êm dịu)",
        "base_color": "#ffffff",
        "fill_color": "#c4b5fd",
        "male_color": "#c4b5fd",
        "female_color": "#f0abfc",
        "both_color": "#c4b5fd",
        "layout_mode": "center",
        "text_alignment": "left",
        "pos_y_bottom": 82,
        "stroke_width": 0,
        "particles": False,
        "particle_type": "None",
        "enable_glow": False,
        "glow_radius": 0,
        "vignette": 30,
        "brightness": -4,
        "contrast": 10,
        "saturation": -12,
        "color_tint": "Moody Noir",
        "visualizer": False,
        "pointer": False,
        "watermark": False,
        "album_title": "My Album",
        "album_tracks": ["Track 01", "Track 02", "Track 03", "Track 04", "Track 05"],
        "track_title": "Track 01",
        "track_artist": "Album Artist",
        "custom_singers": []
    },
    {
        "id": "reference_0wbkt_album_player",
        "name": "🎵 Reference Album Lyric Player",
        "category": "modern",
        "badge": "VIDEO INSPIRED",
        "badge_color": "#7c3aed",
        "description": "Album-style lyric player with cover art, playlist queue, active-track highlight, and clean karaoke typography.",
        "reference_url": "https://youtu.be/0wbktJULiFw",
        "font_family": "Montserrat",
        "font_weight": "700 Bold",
        "font_size": 40,
        "display_mode": "SINGLE",
        "template_variant": "multi_song_album",
        "motion_effect": "Fade In / Out",
        "base_color": "#ffffff",
        "fill_color": "#c4b5fd",
        "male_color": "#93c5fd",
        "female_color": "#f0abfc",
        "both_color": "#c4b5fd",
        "layout_mode": "center",
        "text_alignment": "left",
        "pos_y_bottom": 82,
        "stroke_width": 1,
        "particles": False,
        "enable_glow": False,
        "vignette": 28,
        "color_tint": "Moody Noir",
        "visualizer": False,
        "pointer": False,
        "watermark": False,
        "album_title": "My Album",
        "album_tracks": ["Track 01", "Track 02", "Track 03", "Track 04", "Track 05"],
        "track_title": "Track 01",
        "track_artist": "Album Artist",
        "custom_singers": []
    }
]

class TemplateCardWidget(QFrame):
    apply_requested = pyqtSignal(dict)
    favorite_changed = pyqtSignal(dict, bool)

    def __init__(self, t_data: dict, parent=None):
        super().__init__(parent)
        self.data = t_data
        self.setStyleSheet("""
            TemplateCardWidget {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 10px;
            }
            TemplateCardWidget:hover {
                border-color: #ff2d55;
                background: #fffbfa;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Header: Name + Badge
        hdr = QHBoxLayout()
        lbl_name = QLabel(t_data['name'])
        lbl_name.setStyleSheet("font-size: 12px; font-weight: 800; color: #0f172a;")
        hdr.addWidget(lbl_name, stretch=1)

        lbl_badge = QLabel(t_data['badge'])
        lbl_badge.setStyleSheet(f"""
            background: {t_data['badge_color']};
            color: #ffffff;
            font-size: 9px;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 4px;
        """)
        hdr.addWidget(lbl_badge)
        self.btn_favorite = QPushButton("★" if t_data.get("_favorite") else "☆")
        self.btn_favorite.setCheckable(True)
        self.btn_favorite.setChecked(bool(t_data.get("_favorite")))
        self.btn_favorite.setFixedSize(24, 22)
        self.btn_favorite.setToolTip("Favorite template")
        self.btn_favorite.setStyleSheet("QPushButton { border: none; color: #f59e0b; font-size: 16px; }")
        self.btn_favorite.toggled.connect(self._on_favorite_toggled)
        hdr.addWidget(self.btn_favorite)
        layout.addLayout(hdr)

        # Description
        lbl_desc = QLabel(t_data['description'])
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 10px; color: #64748b; line-height: 1.4;")
        layout.addWidget(lbl_desc)

        # Specs info pills
        specs_row = QHBoxLayout()
        specs_row.setSpacing(4)
        
        font_pill = QLabel(f"🔤 {t_data['font_family']}")
        font_pill.setStyleSheet("background: #f1f5f9; color: #334155; font-size: 9px; padding: 2px 6px; border-radius: 3px;")
        specs_row.addWidget(font_pill)

        fx_pill = QLabel(f"⚡ {t_data['motion_effect'].split('(')[0].strip()}")
        fx_pill.setStyleSheet("background: #f1f5f9; color: #334155; font-size: 9px; padding: 2px 6px; border-radius: 3px;")
        specs_row.addWidget(fx_pill)

        specs_row.addStretch()
        layout.addLayout(specs_row)

        # Apply Button
        btn_apply = QPushButton("⚡ ÁP DỤNG TEMPLATE NÀY")
        btn_apply.setFixedHeight(28)
        btn_apply.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff2d55, stop:1 #ff5277);
                color: #ffffff;
                font-weight: 800;
                font-size: 10px;
                border: none;
                border-radius: 5px;
                padding: 4px;
            }
            QPushButton:hover { background: #ff476d; }
        """)
        btn_apply.clicked.connect(lambda: self.apply_requested.emit(self.data))
        layout.addWidget(btn_apply)

    def _on_favorite_toggled(self, checked):
        self.btn_favorite.setText("★" if checked else "☆")
        self.favorite_changed.emit(self.data, bool(checked))


class TemplatesTab(QWidget):
    template_selected = pyqtSignal(dict)
    save_template_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_category = "all"
        self.favorites_only = False
        self.favorite_ids = set()
        self.cards = []
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Top Header
        lbl_title = QLabel("🌟 Thư Viện Mẫu Video (Template Gallery)")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #0f172a;")
        title_row = QHBoxLayout()
        title_row.addWidget(lbl_title, stretch=1)
        self.btn_save_template = QPushButton("💾 Lưu mẫu hiện tại")
        self.btn_save_template.setToolTip("Lưu các chỉnh sửa hiện tại thành template riêng")
        self.btn_save_template.clicked.connect(self.save_template_requested)
        title_row.addWidget(self.btn_save_template)
        main_layout.addLayout(title_row)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm mẫu template (TIKI TIKI, Ballad, EDM, Sakura...)...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
                color: #0f172a;
            }
            QLineEdit:focus { border-color: #ff2d55; }
        """)
        self.search_input.textChanged.connect(self.filter_templates)
        main_layout.addWidget(self.search_input)

        self.btn_favorites = QPushButton("☆ Favorites")
        self.btn_favorites.setCheckable(True)
        self.btn_favorites.setToolTip("Show favorite templates only")
        self.btn_favorites.clicked.connect(self.toggle_favorites)
        main_layout.addWidget(self.btn_favorites)

        # Category Filter Pills
        filter_rows = QVBoxLayout()
        filter_rows.setSpacing(4)
        
        pill_style = """
            QPushButton {
                background: #ffffff;
                color: #64748b;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                font-weight: 600;
                font-size: 10px;
                padding: 5px 6px;
            }
            QPushButton:checked {
                background: #ff2d55;
                color: #ffffff;
                border-color: #ff2d55;
                font-weight: 700;
            }
            QPushButton:hover:!checked { background: #f8fafc; }
        """

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        categories = [
            ("all", "Tất cả"),
            ("duet", "🎤 Song Ca"),
            ("trending", "🔥 Trending"),
            ("ballad", "🌟 Ballad"),
            ("lofi", "🌸 Lofi"),
            ("edm", "⚡ EDM"),
            ("pop", "🎸 Pop"),
            ("acoustic", "🌿 Acoustic"),
            ("modern", "✨ Modern"),
            ("retro", "📼 Retro")
        ]

        filter_box = QHBoxLayout()
        filter_box.setSpacing(4)
        for index, (cat_id, cat_name) in enumerate(categories):
            if index and index % 5 == 0:
                filter_rows.addLayout(filter_box)
                filter_box = QHBoxLayout()
                filter_box.setSpacing(4)
            btn = QPushButton(cat_name)
            btn.setCheckable(True)
            if cat_id == "all":
                btn.setChecked(True)
            btn.setStyleSheet(pill_style)
            btn.clicked.connect(lambda checked, c=cat_id: self.set_category(c))
            self.btn_group.addButton(btn)
            filter_box.addWidget(btn)

        filter_rows.addLayout(filter_box)
        main_layout.addLayout(filter_rows)

        # Scroll Area for Template Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(8)

        for t_data in TEMPLATES_DATA:
            card = TemplateCardWidget(t_data, self)
            card.apply_requested.connect(self.on_apply_template)
            card.favorite_changed.connect(self.on_favorite_changed)
            self.cards.append((card, t_data))
            self.container_layout.addWidget(card)

        self.container_layout.addStretch()
        scroll.setWidget(self.container)
        main_layout.addWidget(scroll, stretch=1)

    def set_category(self, cat: str):
        self.current_category = cat
        self.filter_templates()

    def toggle_favorites(self, checked):
        self.favorites_only = bool(checked)
        self.btn_favorites.setText("★ Favorites" if checked else "☆ Favorites")
        self.filter_templates()

    def on_favorite_changed(self, t_data, checked):
        template_id = t_data.get("id")
        if template_id:
            if checked:
                self.favorite_ids.add(template_id)
            else:
                self.favorite_ids.discard(template_id)
            t_data["_favorite"] = checked
        self.filter_templates()

    def filter_templates(self):
        q = self.search_input.text().lower().strip()
        for card, t_data in self.cards:
            matches_cat = (self.current_category == "all") or (t_data.get("category") == self.current_category)
            searchable = " ".join(str(t_data.get(key, "")) for key in ("id", "name", "description", "reference_url")).lower()
            matches_q = (not q) or (q in searchable)
            matches_favorite = (not self.favorites_only) or (t_data.get("id") in self.favorite_ids)
            card.setVisible(matches_cat and matches_q and matches_favorite)

    def on_apply_template(self, t_data: dict):
        self.template_selected.emit(t_data)
        QMessageBox.information(
            self, 
            "Áp Dụng Template", 
            f"🎉 Đã áp dụng template '{t_data['name']}' thành công!\n\n"
            f"• Kiểu hiển thị: {t_data['display_mode']}\n"
            f"• Chuyển động: {t_data['motion_effect']}\n"
            f"• Font chữ: {t_data['font_family']} ({t_data['font_weight']})\n"
            f"• Hạt hiệu ứng: {t_data.get('particle_type', 'None')}"
        )

    def add_template(self, t_data: dict):
        """Add a user template card without mutating built-in preset definitions."""
        if not isinstance(t_data, dict):
            return
        t_data = copy.deepcopy(t_data)
        t_data.setdefault('id', f'custom_{len(self.cards) + 1}')
        t_data.setdefault('name', 'Custom Template')
        t_data.setdefault('category', 'custom')
        t_data.setdefault('badge', 'CUSTOM')
        t_data.setdefault('badge_color', '#0f766e')
        t_data.setdefault('description', 'Saved custom template.')
        t_data.setdefault('font_family', 'Montserrat')
        t_data.setdefault('font_size', 42)
        t_data.setdefault('motion_effect', 'Fade')
        card = TemplateCardWidget(t_data, self)
        card.apply_requested.connect(self.on_apply_template)
        card.favorite_changed.connect(self.on_favorite_changed)
        self.cards.append((card, t_data))
        self.container_layout.insertWidget(self.container_layout.count() - 1, card)

    def set_custom_templates(self, templates: list):
        """Replace project-owned templates without leaking cards across projects."""
        self.favorite_ids = {
            item.get('id') for item in (templates or [])
            if isinstance(item, dict) and item.get('_favorite') and item.get('id')
        }
        built_in_ids = {item.get('id') for item in TEMPLATES_DATA}
        retained_cards = []
        for card, template in self.cards:
            if template.get('id') in built_in_ids:
                retained_cards.append((card, template))
                continue
            self.container_layout.removeWidget(card)
            card.setParent(None)
            card.deleteLater()
        self.cards = retained_cards

        existing_ids = {item.get('id') for _, item in self.cards}
        for template in templates or []:
            if not isinstance(template, dict):
                continue
            template_id = template.get('id')
            if not template_id or template_id in existing_ids:
                continue
            cloned = copy.deepcopy(template)
            cloned.setdefault('name', 'Custom Template')
            cloned.setdefault('category', 'custom')
            cloned.setdefault('badge', 'CUSTOM')
            cloned.setdefault('badge_color', '#0f766e')
            cloned.setdefault('description', 'Saved custom template.')
            cloned.setdefault('font_family', 'Montserrat')
            cloned.setdefault('motion_effect', 'Fade')
            cloned.setdefault('font_size', 42)
            cloned.setdefault('display_mode', 'KARAOKE')
            cloned.setdefault('badge_color', '#0f766e')
            cloned.setdefault('motion_effect', 'Fade')
            cloned.setdefault('_favorite', cloned.get('id') in self.favorite_ids)
            self.add_template(cloned)
            existing_ids.add(template_id)
        self.filter_templates()
