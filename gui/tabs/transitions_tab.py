"""
Lylis Karaoke Studio - Transitions Tab matching exact Reference
Supports Clip Transitions (Fade Hoà tan, Slide, Wipe, Dissolve) and Position Modal (Đầu clip / Cuối clip)
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QDialog, QFrame, QMessageBox
)
from PyQt5.QtCore import pyqtSignal

class TransitionPositionDialog(QDialog):
    def __init__(self, transition_name="Fade (Hoà tan)", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vị trí hiệu ứng")
        self.setFixedSize(460, 260)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 12px;
            }
        """)
        self.chosen_position = None
        self.setup_ui(transition_name)

    def setup_ui(self, transition_name):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Title
        lbl_title = QLabel("Vị trí hiệu ứng")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0f172a;")
        layout.addWidget(lbl_title)

        lbl_sub = QLabel(f"Áp dụng <b>{transition_name}</b> vào:")
        lbl_sub.setStyleSheet("font-size: 12px; color: #64748b;")
        layout.addWidget(lbl_sub)

        # Cards: [ 🏁 ĐẦU CLIP (FADE IN) ] vs [ 🛑 CUỐI CLIP (FADE OUT) ]
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)

        # Card 1: Đầu clip
        self.btn_start = QPushButton("🏁\n\nĐẦU CLIP\nCLIP XUẤT HIỆN (FADE IN...)")
        self.btn_start.setFixedHeight(100)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: #fff1f2;
                color: #ff2d55;
                border: 1.5px solid #fecdd3;
                border-radius: 8px;
                font-weight: 700;
                font-size: 11px;
                line-height: 1.4;
                text-align: center;
                padding: 10px;
            }
            QPushButton:hover {
                background: #ffe4e6;
                border-color: #ff2d55;
            }
        """)
        self.btn_start.clicked.connect(lambda: self.select_pos("start"))
        cards_layout.addWidget(self.btn_start, stretch=1)

        # Card 2: Cuối clip
        self.btn_end = QPushButton("🛑\n\nCUỐI CLIP\nCLIP BIẾN MẤT (FADE OUT...)")
        self.btn_end.setFixedHeight(100)
        self.btn_end.setStyleSheet("""
            QPushButton {
                background: #fff1f2;
                color: #ff2d55;
                border: 1.5px solid #fecdd3;
                border-radius: 8px;
                font-weight: 700;
                font-size: 11px;
                line-height: 1.4;
                text-align: center;
                padding: 10px;
            }
            QPushButton:hover {
                background: #ffe4e6;
                border-color: #ff2d55;
            }
        """)
        self.btn_end.clicked.connect(lambda: self.select_pos("end"))
        cards_layout.addWidget(self.btn_end, stretch=1)

        layout.addLayout(cards_layout)

        # Bottom Cancel
        bot_row = QHBoxLayout()
        bot_row.addStretch()
        btn_cancel = QPushButton("HỦY")
        btn_cancel.setStyleSheet("""
            QPushButton {
                border: none;
                color: #64748b;
                font-weight: 700;
                font-size: 12px;
                padding: 6px 14px;
            }
            QPushButton:hover { color: #0f172a; }
        """)
        btn_cancel.clicked.connect(self.reject)
        bot_row.addWidget(btn_cancel)
        layout.addLayout(bot_row)

    def select_pos(self, pos: str):
        self.chosen_position = pos
        self.accept()


class TransitionItemCard(QFrame):
    add_clicked = pyqtSignal(str)

    def __init__(self, title, desc, icon_str="🔗", parent=None):
        super().__init__(parent)
        self.title = title
        self.setStyleSheet("""
            TransitionItemCard {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
            }
            TransitionItemCard:hover {
                border-color: #cbd5e1;
                background: #f8fafc;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        lbl_icon = QLabel(icon_str)
        lbl_icon.setStyleSheet("font-size: 18px; color: #8b5cf6;")
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


class TransitionsTab(QWidget):
    transition_applied = pyqtSignal(str, str)  # (name, position: 'start' | 'end')

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header_row = QHBoxLayout()
        lbl_title = QLabel("Hiệu ứng Clip (Văn bản / Media)")
        lbl_title.setStyleSheet("font-size: 12px; font-weight: 800; color: #0f172a;")
        header_row.addWidget(lbl_title)
        header_row.addStretch()
        lbl_badge = QLabel("3 hiệu ứng")
        lbl_badge.setStyleSheet("color: #94a3b8; font-size: 10px;")
        header_row.addWidget(lbl_badge)
        layout.addLayout(header_row)

        lbl_desc = QLabel("Chọn hiệu ứng để áp dụng vào đầu hoặc cuối clip.")
        lbl_desc.setStyleSheet("color: #64748b; font-size: 10px;")
        layout.addWidget(lbl_desc)

        # Transition Cards
        card1 = TransitionItemCard(
            "Fade (Hoà tan)",
            "Chuyển cảnh mờ dần mềm mại giữa 2 clip • 2s",
            "🔗"
        )
        card1.add_clicked.connect(self.open_position_dialog)
        layout.addWidget(card1)

        card2 = TransitionItemCard(
            "Slide (Trượt ngang)",
            "Trượt mượt mà từ trái hoặc phải sang • 1.5s",
            "➡️"
        )
        card2.add_clicked.connect(self.open_position_dialog)
        layout.addWidget(card2)

        card3 = TransitionItemCard(
            "Zoom (Phóng to / Thu nhỏ)",
            "Hiệu ứng phóng to điện ảnh ấn tượng • 2s",
            "🔍"
        )
        card3.add_clicked.connect(self.open_position_dialog)
        layout.addWidget(card3)

        layout.addStretch()

    def open_position_dialog(self, transition_name: str):
        dlg = TransitionPositionDialog(transition_name, self)
        if dlg.exec_():
            pos = dlg.chosen_position
            pos_label = "Đầu clip (Fade in)" if pos == "start" else "Cuối clip (Fade out)"
            self.transition_applied.emit(transition_name, pos)
            QMessageBox.information(
                self, 
                "Áp dụng chuyển cảnh", 
                f"🎉 Đã áp dụng hiệu ứng <b>{transition_name}</b> vào <b>{pos_label}</b> thành công!"
            )
