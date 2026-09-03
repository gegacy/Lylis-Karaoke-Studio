"""
Lylis Karaoke Studio - Right-Side Text & Transform Properties Inspector
Matches exact Reference Layout:
- Text Content (Nội dung), Subtitle, Font Family, Font Size (px), Font Weight, Text Alignment
- Transform: Position / Fit, X (%), Y (%), W (%), H (%), Rotation (Xoay)
- Quick Position Snapping & Delete Action
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QComboBox, QSpinBox, QSlider, QPushButton, 
    QColorDialog, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

class InspectorPanel(QWidget):
    property_changed = pyqtSignal(dict)
    closed = pyqtSignal()
    delete_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(240)
        self.setMaximumWidth(440)
        self.resize(300, 720)
        self.setStyleSheet("""
            InspectorPanel {
                background-color: #ffffff;
                border-left: 1px solid #e2e8f0;
            }
        """)
        self.current_object = {}
        self.current_color = QColor("#ffffff")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # 1. Header: [ Text Properties    ✕ ]
        header_row = QHBoxLayout()
        self.lbl_title = QLabel("Thuộc tính vật thể")
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #0f172a;")
        header_row.addWidget(self.lbl_title)
        header_row.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(22, 22)
        btn_close.setStyleSheet("border: none; color: #94a3b8; font-size: 14px; font-weight: bold;")
        btn_close.clicked.connect(self.closed.emit)
        header_row.addWidget(btn_close)
        layout.addLayout(header_row)

        # =====================================================================
        # 2. TEXT SECTION
        # =====================================================================
        lbl_sec_text = QLabel("NỘI DUNG VĂN BẢN")
        lbl_sec_text.setStyleSheet("font-size: 10px; font-weight: 800; color: #94a3b8;")
        layout.addWidget(lbl_sec_text)

        # Content (Nội dung)
        self.lbl_c = QLabel("Tiêu đề:")
        self.lbl_c.setStyleSheet("font-size: 10px; color: #64748b;")
        layout.addWidget(self.lbl_c)

        self.txt_content = QLineEdit("Nhập nội dung văn bản...")
        self.txt_content.setStyleSheet("""
            QLineEdit {
                background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;
                padding: 6px 8px; font-size: 11px; color: #0f172a;
            }
            QLineEdit:focus { border-color: #ff2d55; background: #fff; }
        """)
        self.txt_content.textChanged.connect(self.emit_change)
        layout.addWidget(self.txt_content)

        # Subtitle (for Lower Third)
        self.lbl_sub = QLabel("Phụ đề / Ca sĩ:")
        self.lbl_sub.setStyleSheet("font-size: 10px; color: #64748b;")
        layout.addWidget(self.lbl_sub)

        self.txt_subtitle = QLineEdit("")
        self.txt_subtitle.setStyleSheet("""
            QLineEdit {
                background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;
                padding: 6px 8px; font-size: 11px; color: #0f172a;
            }
            QLineEdit:focus { border-color: #ff2d55; background: #fff; }
        """)
        self.txt_subtitle.textChanged.connect(self.emit_change)
        layout.addWidget(self.txt_subtitle)

        # Font Family
        lbl_f = QLabel("Font:")
        lbl_f.setStyleSheet("font-size: 10px; color: #64748b;")
        layout.addWidget(lbl_f)

        self.combo_font = QComboBox()
        self.combo_font.addItems(["Montserrat", "Big Shoulders Display", "Inter", "Arial", "Be Vietnam Pro", "Playfair Display"])
        self.combo_font.currentIndexChanged.connect(self.emit_change)
        layout.addWidget(self.combo_font)

        # Size & Color row
        sc_row = QHBoxLayout()
        
        size_box = QVBoxLayout()
        size_box.addWidget(QLabel("Cỡ chữ (px):"))
        self.spin_size = QSpinBox()
        self.spin_size.setRange(10, 140)
        self.spin_size.setValue(32)
        self.spin_size.valueChanged.connect(self.emit_change)
        size_box.addWidget(self.spin_size)
        sc_row.addLayout(size_box, stretch=1)

        col_box = QVBoxLayout()
        col_box.addWidget(QLabel("Màu chữ:"))
        self.btn_color = QPushButton()
        self.btn_color.setFixedHeight(24)
        self.btn_color.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px;")
        self.btn_color.clicked.connect(self.pick_color)
        col_box.addWidget(self.btn_color)
        sc_row.addLayout(col_box)

        layout.addLayout(sc_row)

        # Weight & Alignment
        lbl_w = QLabel("Độ đậm:")
        lbl_w.setStyleSheet("font-size: 10px; color: #64748b;")
        layout.addWidget(lbl_w)

        w_row = QHBoxLayout()
        self.combo_weight = QComboBox()
        self.combo_weight.addItems(["600 SemiBold", "900 Cực Đậm", "700 Bold", "400 Regular"])
        self.combo_weight.currentIndexChanged.connect(self.emit_change)
        w_row.addWidget(self.combo_weight, stretch=1)

        self.combo_alignment = QComboBox()
        self.combo_alignment.addItem("Trái", "left")
        self.combo_alignment.addItem("Giữa", "center")
        self.combo_alignment.addItem("Phải", "right")
        self.combo_alignment.currentIndexChanged.connect(self.emit_change)
        w_row.addWidget(self.combo_alignment)
        layout.addLayout(w_row)

        # =====================================================================
        # 3. TRANSFORM & QUICK POSITION
        # =====================================================================
        lbl_sec_tf = QLabel("VỊ TRÍ & KÍCH THƯỚC (TRANSFORM)")
        lbl_sec_tf.setStyleSheet("font-size: 10px; font-weight: 800; color: #94a3b8; margin-top: 6px;")
        layout.addWidget(lbl_sec_tf)

        # Quick Position Presets: [ ⬆ Trên ] [ ⏺ Giữa ] [ ⬇ Dưới ]
        snap_row = QHBoxLayout()
        snap_style = """
            QPushButton {
                background: #f1f5f9; color: #334155; border: 1px solid #e2e8f0;
                border-radius: 4px; font-size: 10px; font-weight: 600; padding: 4px;
            }
            QPushButton:hover { background: #e2e8f0; color: #0f172a; }
        """
        btn_top = QPushButton("⬆ Trên")
        btn_top.setStyleSheet(snap_style)
        btn_top.clicked.connect(lambda: self.set_position_snap(12.0))
        snap_row.addWidget(btn_top)

        btn_mid = QPushButton("⏺ Giữa")
        btn_mid.setStyleSheet(snap_style)
        btn_mid.clicked.connect(lambda: self.set_position_snap(45.0))
        snap_row.addWidget(btn_mid)

        btn_bot = QPushButton("⬇ Dưới")
        btn_bot.setStyleSheet(snap_style)
        btn_bot.clicked.connect(lambda: self.set_position_snap(82.0))
        snap_row.addWidget(btn_bot)
        layout.addLayout(snap_row)

        # X (%) & Y (%)
        xy_row = QHBoxLayout()
        x_box = QVBoxLayout()
        x_box.addWidget(QLabel("X (%):"))
        self.txt_x = QLineEdit("28.5")
        self.txt_x.textChanged.connect(self.emit_change)
        x_box.addWidget(self.txt_x)
        xy_row.addLayout(x_box)

        y_box = QVBoxLayout()
        y_box.addWidget(QLabel("Y (%):"))
        self.txt_y = QLineEdit("46.8")
        self.txt_y.textChanged.connect(self.emit_change)
        y_box.addWidget(self.txt_y)
        xy_row.addLayout(y_box)
        layout.addLayout(xy_row)

        # W (%) & H (%)
        wh_row = QHBoxLayout()
        w_box = QVBoxLayout()
        w_box.addWidget(QLabel("W (%):"))
        self.txt_w = QLineEdit("40.0")
        self.txt_w.textChanged.connect(self.emit_change)
        w_box.addWidget(self.txt_w)
        wh_row.addLayout(w_box)

        h_box = QVBoxLayout()
        h_box.addWidget(QLabel("H (%):"))
        self.txt_h = QLineEdit("10.0")
        self.txt_h.textChanged.connect(self.emit_change)
        h_box.addWidget(self.txt_h)
        wh_row.addLayout(h_box)
        layout.addLayout(wh_row)

        # Rotation (Xoay)
        rot_row = QHBoxLayout()
        rot_row.addWidget(QLabel("Xoay:"))
        self.slider_rot = QSlider(Qt.Horizontal)
        self.slider_rot.setRange(-180, 180)
        self.slider_rot.setValue(0)
        self.slider_rot.valueChanged.connect(self.on_rot_changed)
        rot_row.addWidget(self.slider_rot, stretch=1)
        self.lbl_rot = QLabel("0°")
        self.lbl_rot.setFixedWidth(30)
        rot_row.addWidget(self.lbl_rot)
        layout.addLayout(rot_row)

        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Opacity:"))
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(100)
        self.slider_opacity.valueChanged.connect(self.on_opacity_changed)
        opacity_row.addWidget(self.slider_opacity, stretch=1)
        self.lbl_opacity = QLabel("100%")
        self.lbl_opacity.setFixedWidth(38)
        opacity_row.addWidget(self.lbl_opacity)
        layout.addLayout(opacity_row)

        object_state_row = QHBoxLayout()
        self.chk_visible = QCheckBox("Visible")
        self.chk_visible.setChecked(True)
        self.chk_visible.toggled.connect(self.emit_change)
        object_state_row.addWidget(self.chk_visible)
        self.chk_locked = QCheckBox("Locked")
        self.chk_locked.toggled.connect(self.emit_change)
        object_state_row.addWidget(self.chk_locked)
        object_state_row.addStretch()
        layout.addLayout(object_state_row)

        layout.addStretch()

        # 4. Prominent Delete Button at Bottom
        self.btn_delete = QPushButton("🗑 XÓA VẬT THỂ NÀY")
        self.btn_delete.setFixedHeight(32)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background: #fff1f2;
                color: #e11d48;
                border: 1px solid #fecdd3;
                border-radius: 6px;
                font-weight: 800;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #ffe4e6;
                color: #be123c;
            }
        """)
        self.btn_delete.clicked.connect(self.delete_requested.emit)
        layout.addWidget(self.btn_delete)

    def set_position_snap(self, y_val: float):
        self.txt_y.setText(f"{y_val:.1f}")
        self.emit_change()

    def set_object(self, obj: dict):
        self.current_object = obj
        is_lower_third = (obj.get('type') == 'lower_third')
        
        self.lbl_title.setText("Thuộc tính Lower Third" if is_lower_third else "Thuộc tính Văn bản")
        self.lbl_c.setText("Tiêu đề bài hát:" if is_lower_third else "Nội dung:")
        self.lbl_sub.setVisible(is_lower_third)
        self.txt_subtitle.setVisible(is_lower_third)

        controls = [self.txt_content, self.txt_subtitle, self.combo_font, self.spin_size, self.combo_weight,
                    self.combo_alignment, self.txt_x, self.txt_y, self.txt_w, self.txt_h, self.slider_rot,
                    self.slider_opacity, self.chk_visible, self.chk_locked]
        for control in controls:
            control.blockSignals(True)
        
        self.txt_content.setText(obj.get('content', obj.get('title', '')))
        self.txt_subtitle.setText(obj.get('subtitle', ''))
        self.combo_font.setCurrentText(obj.get('font_family', 'Montserrat'))
        self.spin_size.setValue(int(obj.get('font_size', 32)))
        
        weight = int(obj.get('font_weight', 600))
        weight_index = 1 if weight >= 900 else 2 if weight >= 700 else 0 if weight >= 600 else 3
        self.combo_weight.setCurrentIndex(weight_index)
        
        align_index = self.combo_alignment.findData(obj.get('alignment', 'center'))
        self.combo_alignment.setCurrentIndex(max(0, align_index))
        
        self.txt_x.setText(f"{obj.get('x_pct', 28.5):.2f}")
        self.txt_y.setText(f"{obj.get('y_pct', 46.8):.2f}")
        self.txt_w.setText(f"{obj.get('w_pct', 40.0):.1f}")
        self.txt_h.setText(f"{obj.get('h_pct', 10.0):.1f}")
        self.slider_rot.setValue(int(obj.get('rotation', 0)))
        self.slider_opacity.setValue(int(round(float(obj.get('opacity', 1.0)) * 100.0)))
        self.chk_visible.setChecked(bool(obj.get('visible', True)))
        self.chk_locked.setChecked(bool(obj.get('locked', False)))
        
        for control in controls:
            control.blockSignals(False)
            
        self.current_color = QColor(obj.get('color', '#ffffff'))
        self.btn_color.setStyleSheet(f"background: {self.current_color.name()}; border: 1px solid #cbd5e1; border-radius: 4px;")
        self.lbl_opacity.setText(f"{self.slider_opacity.value()}%")
        self.lbl_rot.setText(f"{int(obj.get('rotation', 0))}°")

    def pick_color(self):
        col = QColorDialog.getColor(self.current_color, self, "Chọn Màu")
        if col.isValid():
            self.current_color = col
            self.btn_color.setStyleSheet(f"background: {col.name()}; border: 1px solid #cbd5e1; border-radius: 4px;")
            self.emit_change()

    def on_rot_changed(self, val):
        self.lbl_rot.setText(f"{val}°")
        self.emit_change()

    def on_opacity_changed(self, val):
        self.lbl_opacity.setText(f"{val}%")
        self.emit_change()

    def emit_change(self):
        try:
            x_val = float(self.txt_x.text())
        except ValueError:
            x_val = 28.5
        try:
            y_val = float(self.txt_y.text())
        except ValueError:
            y_val = 46.8
        try:
            w_val = float(self.txt_w.text())
        except ValueError:
            w_val = 40.0
        try:
            h_val = float(self.txt_h.text())
        except ValueError:
            h_val = 10.0

        props = {
            'content': self.txt_content.text(),
            'subtitle': self.txt_subtitle.text(),
            'font_family': self.combo_font.currentText(),
            'font_size': self.spin_size.value(),
            'font_weight': int(self.combo_weight.currentText().split()[0]),
            'alignment': self.combo_alignment.currentData(),
            'color': self.current_color.name(),
            'x_pct': max(0.0, min(100.0, x_val)),
            'y_pct': max(0.0, min(100.0, y_val)),
            'w_pct': max(1.0, min(100.0, w_val)),
            'h_pct': max(1.0, min(100.0, h_val)),
            'rotation': self.slider_rot.value(),
            'opacity': self.slider_opacity.value() / 100.0,
            'visible': self.chk_visible.isChecked(),
            'locked': self.chk_locked.isChecked(),
        }
        if self.current_object.get('type') == 'lower_third':
            props['title'] = props.pop('content')
        self.property_changed.emit(props)
