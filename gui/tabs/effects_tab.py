"""
Lylis Karaoke Studio - Advanced Effects & Atmospheric Engine Tab
CapCut Editing Features:
- Video Color Adjustments: Brightness, Contrast, Saturation, Background Blur
- Color Grading LUT Filters: Cinematic Teal & Orange, Retro VHS, Pastel Lofi, Cyberpunk, Moody Dark, Vintage Gold
- Atmospheric Particle Presets (Hearts, Sparkles, Sakura, Snow, Bokeh, Notes)
- Cinematic Vignette Darkness Dimmer
- Text Neon Glow Aura Controller
- Live Audio Reactive Spectrum Equalizer
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QCheckBox, QGroupBox, QComboBox, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal

class EffectsTab(QWidget):
    effects_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)

        # 1. CapCut Video Adjustments Card (Bộ chỉnh màu & hình ảnh)
        grp_adjust = QGroupBox("🎛️ Chỉnh Màu Video (CapCut Adjustments)")
        a_layout = QVBoxLayout(grp_adjust)
        a_layout.setSpacing(6)

        # Brightness
        b_row = QHBoxLayout()
        b_row.addWidget(QLabel("Độ sáng (Brightness):"))
        self.slider_brightness = QSlider(Qt.Horizontal)
        self.slider_brightness.setRange(-50, 50)
        self.slider_brightness.setValue(0)
        self.slider_brightness.valueChanged.connect(self.on_param_changed)
        b_row.addWidget(self.slider_brightness, stretch=1)
        self.lbl_bri_val = QLabel("0")
        self.lbl_bri_val.setFixedWidth(28)
        self.lbl_bri_val.setStyleSheet("color: #ff2d55; font-weight: bold; font-family: monospace;")
        b_row.addWidget(self.lbl_bri_val)
        a_layout.addLayout(b_row)

        # Contrast
        c_row = QHBoxLayout()
        c_row.addWidget(QLabel("Độ tương phản (Contrast):"))
        self.slider_contrast = QSlider(Qt.Horizontal)
        self.slider_contrast.setRange(-50, 50)
        self.slider_contrast.setValue(0)
        self.slider_contrast.valueChanged.connect(self.on_param_changed)
        c_row.addWidget(self.slider_contrast, stretch=1)
        self.lbl_con_val = QLabel("0")
        self.lbl_con_val.setFixedWidth(28)
        self.lbl_con_val.setStyleSheet("color: #ff2d55; font-weight: bold; font-family: monospace;")
        c_row.addWidget(self.lbl_con_val)
        a_layout.addLayout(c_row)

        # Saturation
        s_row = QHBoxLayout()
        s_row.addWidget(QLabel("Độ bão hòa (Saturation):"))
        self.slider_saturation = QSlider(Qt.Horizontal)
        self.slider_saturation.setRange(-50, 50)
        self.slider_saturation.setValue(0)
        self.slider_saturation.valueChanged.connect(self.on_param_changed)
        s_row.addWidget(self.slider_saturation, stretch=1)
        self.lbl_sat_val = QLabel("0")
        self.lbl_sat_val.setFixedWidth(28)
        self.lbl_sat_val.setStyleSheet("color: #ff2d55; font-weight: bold; font-family: monospace;")
        s_row.addWidget(self.lbl_sat_val)
        a_layout.addLayout(s_row)

        # Blur
        bl_row = QHBoxLayout()
        bl_row.addWidget(QLabel("Mờ nền (Background Blur):"))
        self.slider_blur = QSlider(Qt.Horizontal)
        self.slider_blur.setRange(0, 30)
        self.slider_blur.setValue(0)
        self.slider_blur.valueChanged.connect(self.on_param_changed)
        bl_row.addWidget(self.slider_blur, stretch=1)
        self.lbl_blur_val = QLabel("0")
        self.lbl_blur_val.setFixedWidth(28)
        self.lbl_blur_val.setStyleSheet("color: #ff2d55; font-weight: bold; font-family: monospace;")
        bl_row.addWidget(self.lbl_blur_val)
        a_layout.addLayout(bl_row)

        layout.addWidget(grp_adjust)

        # 2. Color Filter Presets Card
        grp_filter = QGroupBox("🎨 Bộ Lọc Màu Nghệ Thuật (Color LUTs)")
        f_layout = QVBoxLayout(grp_filter)
        f_layout.setSpacing(6)

        f_row = QHBoxLayout()
        f_row.addWidget(QLabel("Bộ lọc:"))
        self.combo_tint = QComboBox()
        self.combo_tint.addItems([
            "None (Original)", 
            "🎬 Cinematic Teal & Orange", 
            "📼 Retro VHS 90s", 
            "🌸 Pastel Soft Lofi", 
            "⚡ Cyberpunk Neon", 
            "🖤 Moody Dark Film", 
            "🍂 Warm Vintage Gold",
            "Warm Sunset", 
            "Cool Cyberpunk", 
            "Emerald Forest", 
            "Moody Noir"
        ])
        self.combo_tint.currentIndexChanged.connect(self.emit_change)
        f_row.addWidget(self.combo_tint, stretch=1)
        f_layout.addLayout(f_row)
        layout.addWidget(grp_filter)

        # 3. Atmospheric Particle Generator Card
        grp_particles = QGroupBox("✨ Atmospheric Particles (Hạt bay)")
        p_layout = QVBoxLayout(grp_particles)
        p_layout.setSpacing(6)

        self.chk_particles = QCheckBox("Kích hoạt hiệu ứng hạt bay nền")
        self.chk_particles.setChecked(False)
        self.chk_particles.stateChanged.connect(self.emit_change)
        p_layout.addWidget(self.chk_particles)

        p_row = QHBoxLayout()
        p_row.addWidget(QLabel("Loại hạt:"))
        self.combo_particles = QComboBox()
        self.combo_particles.addItems([
            "Bokeh Orbs 🫧", 
            "Golden Sparkles ✨", 
            "Floating Hearts ❤️", 
            "Sakura Petals 🌸", 
            "Snowflakes ❄️", 
            "Music Notes 🎵"
        ])
        self.combo_particles.setCurrentIndex(1)
        self.combo_particles.currentIndexChanged.connect(self.emit_change)
        p_row.addWidget(self.combo_particles, stretch=1)
        p_layout.addLayout(p_row)
        layout.addWidget(grp_particles)

        # 4. Cinematic Vignette Card
        grp_vignette = QGroupBox("🎬 Bo Góc Tối (Vignette)")
        v_layout = QVBoxLayout(grp_vignette)
        v_layout.setSpacing(6)

        v_row = QHBoxLayout()
        v_row.addWidget(QLabel("Độ tối:"))
        self.slider_vignette = QSlider(Qt.Horizontal)
        self.slider_vignette.setRange(0, 100)
        self.slider_vignette.setValue(20)
        self.slider_vignette.valueChanged.connect(self.on_vignette_changed)
        v_row.addWidget(self.slider_vignette, stretch=1)
        self.lbl_vig_val = QLabel("20%")
        self.lbl_vig_val.setFixedWidth(36)
        self.lbl_vig_val.setStyleSheet("color: #ff2d55; font-weight: bold; font-family: monospace;")
        v_row.addWidget(self.lbl_vig_val)
        v_layout.addLayout(v_row)
        layout.addWidget(grp_vignette)

        # 5. Text Glow Aura Card
        grp_glow = QGroupBox("💡 Viền Phát Sáng Neon (Text Glow)")
        g_layout = QVBoxLayout(grp_glow)
        g_layout.setSpacing(6)

        self.chk_glow = QCheckBox("Hiệu ứng viền phát sáng Neon trên chữ")
        self.chk_glow.setChecked(True)
        self.chk_glow.stateChanged.connect(self.emit_change)
        g_layout.addWidget(self.chk_glow)

        g_row = QHBoxLayout()
        g_row.addWidget(QLabel("Bán kính:"))
        self.slider_glow = QSlider(Qt.Horizontal)
        self.slider_glow.setRange(0, 24)
        self.slider_glow.setValue(8)
        self.slider_glow.valueChanged.connect(self.on_glow_changed)
        g_row.addWidget(self.slider_glow, stretch=1)
        self.lbl_glow_val = QLabel("8px")
        self.lbl_glow_val.setFixedWidth(36)
        self.lbl_glow_val.setStyleSheet("color: #ff2d55; font-weight: bold; font-family: monospace;")
        g_row.addWidget(self.lbl_glow_val)
        g_layout.addLayout(g_row)
        layout.addWidget(grp_glow)

        # 6. Preview & Overlay Helpers
        grp_overlay = QGroupBox("Trợ Năng Hiển Thị (Helpers & Visualizer)")
        o_layout = QVBoxLayout(grp_overlay)
        o_layout.setSpacing(6)

        self.chk_visualizer = QCheckBox("Audio-reactive spectrum visualizer")
        self.chk_visualizer.stateChanged.connect(self.emit_change)
        o_layout.addWidget(self.chk_visualizer)

        vis_row = QHBoxLayout()
        vis_row.addWidget(QLabel("Kiểu sóng nhạc:"))
        self.combo_vis_mode = QComboBox()
        self.combo_vis_mode.addItems([
            "Bar Spectrum (Cột sóng đứng)",
            "Radial Circle 360° (Sóng tròn xoay)",
            "Neon Wave Ribbon (Sóng lụa neon)"
        ])
        self.combo_vis_mode.currentIndexChanged.connect(self.emit_change)
        vis_row.addWidget(self.combo_vis_mode, stretch=1)
        o_layout.addLayout(vis_row)

        self.chk_pointer = QCheckBox("Singer pointer badge")
        self.chk_pointer.setChecked(True)
        self.chk_pointer.stateChanged.connect(self.emit_change)
        o_layout.addWidget(self.chk_pointer)
        self.chk_watermark = QCheckBox("LYLIS watermark")
        self.chk_watermark.stateChanged.connect(self.emit_change)
        o_layout.addWidget(self.chk_watermark)
        layout.addWidget(grp_overlay)

        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def on_param_changed(self):
        self.lbl_bri_val.setText(str(self.slider_brightness.value()))
        self.lbl_con_val.setText(str(self.slider_contrast.value()))
        self.lbl_sat_val.setText(str(self.slider_saturation.value()))
        self.lbl_blur_val.setText(str(self.slider_blur.value()))
        self.emit_change()

    def on_vignette_changed(self, val):
        self.lbl_vig_val.setText(f"{val}%")
        self.emit_change()

    def on_glow_changed(self, val):
        self.lbl_glow_val.setText(f"{val}px")
        self.emit_change()

    def emit_change(self):
        cfg = {
            'brightness': self.slider_brightness.value(),
            'contrast': self.slider_contrast.value(),
            'saturation': self.slider_saturation.value(),
            'blur': self.slider_blur.value(),
            'color_tint': self.combo_tint.currentText(),
            'particles': self.chk_particles.isChecked(),
            'particle_type': self.combo_particles.currentText(),
            'vignette_percent': self.slider_vignette.value(),
            'enable_glow': self.chk_glow.isChecked(),
            'glow_radius': self.slider_glow.value(),
            'visualizer': self.chk_visualizer.isChecked(),
            'visualizer_mode': self.combo_vis_mode.currentText(),
            'pointer': self.chk_pointer.isChecked(),
            'watermark': self.chk_watermark.isChecked(),
        }
        self.effects_changed.emit(cfg)
