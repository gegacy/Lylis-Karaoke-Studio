"""
Lylis Karaoke Studio - Elements / Objects Tab matching exact Reference Screenshot 4
Supports adding Custom Text Layers (Văn bản), Shapes (Hình vuông), and Lower Third banners.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame
)
from PyQt5.QtCore import pyqtSignal

class ObjectItemCard(QFrame):
    add_clicked = pyqtSignal(str)

    def __init__(self, title, desc, icon_str="🔤", parent=None):
        super().__init__(parent)
        self.title = title
        self.setStyleSheet("""
            ObjectItemCard {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 8px;
            }
            ObjectItemCard:hover {
                border-color: #cbd5e1;
                background: #f8fafc;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        lbl_icon = QLabel(icon_str)
        lbl_icon.setStyleSheet("font-size: 18px; color: #00d2ff;")
        layout.addWidget(lbl_icon)

        info_box = QVBoxLayout()
        info_box.setSpacing(2)
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-weight: 700; color: #0f172a; font-size: 12px;")
        info_box.addWidget(lbl_t)

        lbl_d = QLabel(desc)
        lbl_d.setStyleSheet("color: #64748b; font-size: 10px;")
        info_box.addWidget(lbl_d)
        layout.addLayout(info_box, stretch=1)

        btn_add = QPushButton("＋")
        btn_add.setFixedSize(26, 26)
        btn_add.setStyleSheet("""
            QPushButton {
                background: #fff1f2;
                color: #ff2d55;
                border: 1px solid #fecdd3;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background: #ffe4e6; }
        """)
        btn_add.clicked.connect(lambda: self.add_clicked.emit(self.title))
        layout.addWidget(btn_add)


class ElementsTab(QWidget):
    element_created = pyqtSignal(dict)
    elements_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header_row = QHBoxLayout()
        lbl_title = QLabel("Vật thể")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #0f172a;")
        header_row.addWidget(lbl_title)
        header_row.addStretch()
        lbl_count = QLabel("4 vật thể")
        lbl_count.setStyleSheet("color: #94a3b8; font-size: 11px;")
        header_row.addWidget(lbl_count)
        layout.addLayout(header_row)

        # 1. Custom Text Object
        card_text = ObjectItemCard(
            "Văn bản",
            "Chữ tuỳ chỉnh trên video",
            "🔤"
        )
        card_text.add_clicked.connect(self.create_text_object)
        layout.addWidget(card_text)

        # 2. Square / Rectangle Object
        card_rect = ObjectItemCard(
            "Hình vuông",
            "Hình vuông / hình chữ nhật",
            "🔲"
        )
        card_rect.add_clicked.connect(self.create_rect_object)
        layout.addWidget(card_rect)

        # 3. Lower Third Banner
        card_lower = ObjectItemCard(
            "Lower Third",
            "Hình chữ nhật + tên bài hát & nhạc sĩ",
            "🏷️"
        )
        card_lower.add_clicked.connect(self.create_lower_third_object)
        layout.addWidget(card_lower)

        # 4. Spinning Vinyl Record
        card_vinyl = ObjectItemCard(
            "Đĩa Than Quay (Vinyl)",
            "Đĩa than xoay theo nhịp nhạc + bìa album",
            "💿"
        )
        card_vinyl.add_clicked.connect(self.create_vinyl_object)
        layout.addWidget(card_vinyl)

        layout.addStretch()

    def create_text_object(self):
        obj = {
            'type': 'text',
            'content': 'Nhập nội dung văn bản...',
            'font_family': 'Montserrat',
            'font_size': 32,
            'font_weight': 600,
            'color': '#ffffff',
            'stroke_color': '#000000',
            'stroke_width': 3,
            'x_pct': 28.5,
            'y_pct': 46.8,
            'w_pct': 40.0,
            'h_pct': 10.0,
            'rotation': 0,
            'alignment': 'center'
        }
        self.element_created.emit(obj)

    def create_rect_object(self):
        obj = {
            'type': 'shape',
            'shape': 'rectangle',
            'color': '#ff2d55',
            'x_pct': 35.0,
            'y_pct': 50.0,
            'w_pct': 30.0,
            'h_pct': 15.0,
            'rotation': 0
        }
        self.element_created.emit(obj)

    def create_lower_third_object(self):
        obj = {
            'type': 'lower_third',
            'title': 'BÀI HÁT: CHIẾC NÓN BA TẦM',
            'subtitle': 'Ca sĩ: Lylis Artist • Nhạc: Dân ca Quan họ',
            'color': '#0f172a',
            'x_pct': 8.0,
            'y_pct': 82.0,
            'w_pct': 84.0,
            'h_pct': 12.0,
            'rotation': 0
        }
        self.element_created.emit(obj)

    def create_vinyl_object(self):
        obj = {
            'type': 'vinyl',
            'title': 'VINYL RECORD',
            'album_art': '',
            'color': '#0f172a',
            'x_pct': 38.0,
            'y_pct': 18.0,
            'w_pct': 24.0,
            'h_pct': 40.0,
            'rotation': 0
        }
        self.element_created.emit(obj)

    def emit_change(self):
        cfg = {
            'particles': True,
            'particle_type': 'Bokeh Orbs',
            'visualizer': True,
            'pointer': True,
            'pointer_icon': '🎤',
            'pointer_icons': {'male': '👨', 'female': '👩', 'both': '🎤'},
            'watermark': False
        }
        self.elements_changed.emit(cfg)
