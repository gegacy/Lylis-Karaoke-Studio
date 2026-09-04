"""
Lylis Karaoke Studio - Design & Software License Dialog
Displays software ownership, commercial licensing, design system specs, and third-party credits.
"""
import os
import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QTextEdit, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon, QColor
from core.paths import get_asset_path, get_app_root

class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Giấy phép & Bản quyền thiết kế - Lylis Karaoke Studio")
        self.setFixedSize(680, 560)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Window Icon
        ico_path = get_asset_path("app_icon.ico")
        if not os.path.exists(ico_path):
            ico_path = get_asset_path("app_icon.png")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))
            
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                color: #f8fafc;
                font-family: 'Segoe UI', 'Inter', sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #334155;
                background-color: #1e293b;
                border-radius: 8px;
                padding: 12px;
            }
            QTabBar::tab {
                background: #0f172a;
                color: #94a3b8;
                padding: 8px 18px;
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: #1e293b;
                color: #38bdf8;
                border: 1px solid #334155;
                border-bottom: none;
            }
            QTextEdit {
                background-color: #0b0f19;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #cbd5e1;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.4;
                padding: 8px;
            }
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 6px;
                color: #e2e8f0;
                font-weight: 600;
                font-size: 12px;
                padding: 7px 18px;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #38bdf8;
                color: #38bdf8;
            }
            QPushButton#btnClose {
                background-color: #0284c7;
                border: none;
                color: #ffffff;
            }
            QPushButton#btnClose:hover {
                background-color: #0369a1;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Header with App Icon and Branding
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        lbl_icon = QLabel()
        png_path = get_asset_path("app_icon.png")
        if os.path.exists(png_path):
            pix = QPixmap(png_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_icon.setPixmap(pix)
        else:
            lbl_icon.setText("🎙️")
            lbl_icon.setStyleSheet("font-size: 40px;")
        lbl_icon.setFixedSize(64, 64)
        header_layout.addWidget(lbl_icon)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        lbl_app_name = QLabel("Lylis Karaoke Studio")
        lbl_app_name.setStyleSheet("font-size: 20px; font-weight: 800; color: #f8fafc;")
        title_vbox.addWidget(lbl_app_name)

        lbl_app_desc = QLabel("Desktop Lyric Video & Karaoke Production Suite • Version 1.0.0 Stable")
        lbl_app_desc.setStyleSheet("font-size: 12px; color: #94a3b8;")
        title_vbox.addWidget(lbl_app_desc)

        badge_hbox = QHBoxLayout()
        badge_hbox.setSpacing(8)

        lbl_badge_status = QLabel("● ĐÃ KÍCH HOẠT (ACTIVE)")
        lbl_badge_status.setStyleSheet("""
            background-color: #064e3b;
            color: #34d399;
            font-size: 10px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid #059669;
        """)
        badge_hbox.addWidget(lbl_badge_status)

        lbl_badge_tier = QLabel("STUDIO PRO LICENSE")
        lbl_badge_tier.setStyleSheet("""
            background-color: #1e1b4b;
            color: #a78bfa;
            font-size: 10px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid #6366f1;
        """)
        badge_hbox.addWidget(lbl_badge_tier)
        badge_hbox.addStretch()

        title_vbox.addLayout(badge_hbox)
        header_layout.addLayout(title_vbox)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Tabs Container
        tabs = QTabWidget()

        # Tab 1: Software & Design License
        tab_license = QWidget()
        tab_lic_layout = QVBoxLayout(tab_license)
        tab_lic_layout.setContentsMargins(12, 12, 12, 12)
        tab_lic_layout.setSpacing(10)

        lic_info_html = """
        <div style="color: #cbd5e1; font-size: 12px; line-height: 1.6;">
            <p><b>Chủ sở hữu bản quyền & Thiết kế:</b> <span style="color: #38bdf8;">gegacy / Lylis Studio</span></p>
            <p><b>Quyền sử dụng thương mại:</b> Được cấp quyền trọn đời, toàn cầu để sản xuất video thương mại (YouTube, TikTok, Facebook, Truyền hình, Sân khấu Karaoke) không giới hạn bản quyền.</p>
            <p><b>Bảo hộ thiết kế:</b> Hệ thống giao diện CapCut Timeline, 12 Mẫu Visualizer độc quyền, và bộ nhận diện thương hiệu Lylis Studio được bảo hộ theo luật sở hữu trí tuệ.</p>
            <p><b>Mã bản quyền:</b> <code style="background:#0f172a; padding:2px 6px; border-radius:3px; color:#f472b6;">LKS-STUDIO-PRO-2026-VN-VERIFIED</code></p>
        </div>
        """
        lbl_lic_info = QLabel(lic_info_html)
        lbl_lic_info.setWordWrap(True)
        tab_lic_layout.addWidget(lbl_lic_info)

        txt_full_license = QTextEdit()
        txt_full_license.setReadOnly(True)
        license_file = os.path.join(get_app_root(), "LICENSE")
        if os.path.exists(license_file):
            try:
                with open(license_file, "r", encoding="utf-8") as f:
                    txt_full_license.setPlainText(f.read())
            except Exception:
                txt_full_license.setPlainText("Copyright (c) 2026 gegacy / Lylis Studio. All rights reserved.")
        else:
            txt_full_license.setPlainText("Copyright (c) 2026 gegacy / Lylis Studio. All rights reserved.")
        tab_lic_layout.addWidget(txt_full_license)

        tabs.addTab(tab_license, "📜 Giấy phép & Bản quyền")

        # Tab 2: Design System Specs
        tab_design = QWidget()
        tab_des_layout = QVBoxLayout(tab_design)
        tab_des_layout.setContentsMargins(12, 12, 12, 12)

        design_html = """
        <div style="color: #cbd5e1; font-size: 12px; line-height: 1.6;">
            <h3 style="color: #38bdf8; margin-top: 0;">🎨 Hệ Thống Thiết Kế Lylis Studio Pro</h3>
            <p><b>1. Kiến trúc đồ họa:</b> 60 FPS Hardware-Accelerated QPainter & Dual-Buffer Karaoke Canvas.</p>
            <p><b>2. Bộ màu nhận diện:</b> Electric Cyan (<code>#00f2fe</code>), Neon Magenta (<code>#ff007f</code>), Deep Obsidian (<code>#0f172a</code>).</p>
            <p><b>3. Bộ 12 Preset Gallery độc quyền:</b>
               <br>• <i>Tiki Tiki Sunset</i> - Lời nhạc thư pháp ấm áp trên phông giấy nghệ thuật.
               <br>• <i>Walters Lyric Queue</i> - Hàng đợi kính mờ dọc với thấu kính phóng đại động.
               <br>• <i>Ambient Album Player & Vinyl DJ</i> - Đĩa than xoay 360 độ kèm sóng nhạc LED đa tầng.
               <br>• <i>Eminem Rap & Hip-Hop</i> - Typography đậm viền neon và huy hiệu Parental Advisory.
            </p>
            <p><b>4. Trình chỉnh sửa CapCut Sequencer:</b> Timeline đa rãnh, Cắt (Split 'S'), Nhân đôi ('Ctrl+D'), Xóa dồn rãnh ('Shift+Del'), và Bắt nhịp tự động (Beat-Snapping).</p>
        </div>
        """
        lbl_design = QLabel(design_html)
        lbl_design.setWordWrap(True)
        tab_des_layout.addWidget(lbl_design)
        tab_des_layout.addStretch()

        tabs.addTab(tab_design, "✨ Thiết kế & Giao diện")

        # Tab 3: Open Source Credits
        tab_credits = QWidget()
        tab_cred_layout = QVBoxLayout(tab_credits)
        tab_cred_layout.setContentsMargins(12, 12, 12, 12)

        credits_html = """
        <div style="color: #cbd5e1; font-size: 12px; line-height: 1.6;">
            <h3 style="color: #38bdf8; margin-top: 0;">⚡ Các Thành Phần Mã Nguồn Mở</h3>
            <p>Lylis Karaoke Studio sử dụng và tuân thủ giấy phép của các thư viện mã nguồn mở:</p>
            <ul>
                <li><b>PyQt5:</b> Riverbank Computing Limited (GPL v3 / Commercial License)</li>
                <li><b>FFmpeg & imageio-ffmpeg:</b> FFmpeg Team (LGPL 2.1+ / GPL 2.0+)</li>
                <li><b>Pygame & SDL 2:</b> Pygame Community (LGPL 2.1)</li>
                <li><b>Pillow (PIL Fork):</b> Jeffrey A. Clark (Alex) & contributors (HPND License)</li>
                <li><b>NumPy:</b> NumPy Developers (BSD 3-Clause License)</li>
            </ul>
            <p>Xin trân trọng cảm ơn cộng đồng mã nguồn mở toàn cầu.</p>
        </div>
        """
        lbl_credits = QLabel(credits_html)
        lbl_credits.setWordWrap(True)
        tab_cred_layout.addWidget(lbl_credits)
        tab_cred_layout.addStretch()

        tabs.addTab(tab_credits, "🌐 Mã nguồn mở")

        layout.addWidget(tabs, stretch=1)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_open_file = QPushButton("📂 Mở tệp LICENSE")
        btn_open_file.clicked.connect(self.open_license_file)
        btn_layout.addWidget(btn_open_file)

        btn_layout.addStretch()

        btn_close = QPushButton("Đóng")
        btn_close.setObjectName("btnClose")
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def open_license_file(self):
        lic_path = os.path.join(get_app_root(), "LICENSE")
        if os.path.exists(lic_path):
            try:
                os.startfile(lic_path)
            except Exception:
                QMessageBox.information(self, "Giấy phép", f"Tệp giấy phép nằm tại:\n{lic_path}")
        else:
            QMessageBox.warning(self, "Không tìm thấy", "Không tìm thấy tệp LICENSE trong thư mục ứng dụng.")
