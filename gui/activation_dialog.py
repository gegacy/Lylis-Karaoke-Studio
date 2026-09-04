"""
Lylis Karaoke Studio - Anti-Bypass License Activation Modal Dialog
Enforces hardware-bound cryptographic activation before granting application access.
"""
import os
import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon, QClipboard
from core.paths import get_asset_path
from core.license_manager import LicenseManager

class ActivationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kích Hoạt Bản Quyền - Lylis Karaoke Studio")
        self.setFixedSize(540, 480)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        
        # Set Window Icon
        ico_path = get_asset_path("app_icon.ico")
        if not os.path.exists(ico_path):
            ico_path = get_asset_path("app_icon.png")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))

        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0b0f19;
                color: #f8fafc;
                font-family: 'Segoe UI', 'Inter', sans-serif;
            }
            QLabel {
                color: #e2e8f0;
            }
            QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #ffffff;
                font-size: 13px;
                padding: 10px 12px;
                selection-background-color: #0284c7;
            }
            QLineEdit:focus {
                border: 1px solid #38bdf8;
                background-color: #0f172a;
            }
            QLineEdit:read-only {
                background-color: #0f172a;
                color: #38bdf8;
                font-family: 'Consolas', monospace;
                font-weight: bold;
                border: 1px dashed #334155;
            }
            QPushButton {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
                color: #f8fafc;
                font-size: 12px;
                font-weight: 600;
                padding: 9px 16px;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #38bdf8;
                color: #38bdf8;
            }
            QPushButton#btnActivate {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #06b6d4);
                border: none;
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 11px 20px;
            }
            QPushButton#btnActivate:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:1 #0891b2);
            }
            QPushButton#btnExit {
                background-color: transparent;
                border: 1px solid #ef4444;
                color: #ef4444;
            }
            QPushButton#btnExit:hover {
                background-color: #450a0a;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Header Section
        header = QHBoxLayout()
        header.setSpacing(16)

        lbl_icon = QLabel()
        png_path = get_asset_path("app_icon.png")
        if os.path.exists(png_path):
            pix = QPixmap(png_path).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_icon.setPixmap(pix)
        else:
            lbl_icon.setText("🔒")
            lbl_icon.setStyleSheet("font-size: 36px;")
        lbl_icon.setFixedSize(56, 56)
        header.addWidget(lbl_icon)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)

        lbl_title = QLabel("KÍCH HOẠT BẢN QUYỀN")
        lbl_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #f8fafc; letter-spacing: 0.5px;")
        title_vbox.addWidget(lbl_title)

        lbl_sub = QLabel("Lylis Karaoke Studio Pro • Bảo Vệ Độc Quyền")
        lbl_sub.setStyleSheet("font-size: 12px; color: #94a3b8;")
        title_vbox.addWidget(lbl_sub)

        header.addLayout(title_vbox)
        header.addStretch()
        layout.addLayout(header)

        # Subtle divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("color: #1e293b; background-color: #1e293b;")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        # Machine ID field with copy button
        lbl_mach = QLabel("MÃ THIẾT BỊ CỦA BẠN (MACHINE ID):")
        lbl_mach.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8;")
        layout.addWidget(lbl_mach)

        mach_layout = QHBoxLayout()
        mach_layout.setSpacing(8)

        self.txt_machine_id = QLineEdit()
        self.txt_machine_id.setReadOnly(True)
        self.txt_machine_id.setText(LicenseManager.get_machine_id())
        mach_layout.addWidget(self.txt_machine_id, stretch=1)

        self.btn_copy = QPushButton("📋 Sao Chép")
        self.btn_copy.setFixedWidth(105)
        self.btn_copy.clicked.connect(self.copy_machine_id)
        mach_layout.addWidget(self.btn_copy)
        layout.addLayout(mach_layout)

        # Client Name field
        lbl_name = QLabel("TÊN ĐĂNG KÝ HOẶC EMAIL:")
        lbl_name.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8;")
        layout.addWidget(lbl_name)

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Nhập họ tên hoặc email đăng ký...")
        layout.addWidget(self.txt_name)

        # License Key field
        lbl_key = QLabel("MÃ KÍCH HOẠT (LICENSE KEY):")
        lbl_key.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8;")
        layout.addWidget(lbl_key)

        self.txt_key = QLineEdit()
        self.txt_key.setPlaceholderText("LKS-XXXX-XXXX-XXXX-XXXX")
        self.txt_key.textChanged.connect(self.on_key_text_changed)
        layout.addWidget(self.txt_key)

        # Status / Error Label
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size: 12px; font-weight: 600; color: #f87171;")
        self.lbl_status.setWordWrap(True)
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(12)

        btn_exit = QPushButton("Thoát Ứng Dụng")
        btn_exit.setObjectName("btnExit")
        btn_exit.setFixedWidth(130)
        btn_exit.clicked.connect(self.reject)
        btn_box.addWidget(btn_exit)

        btn_box.addStretch()

        btn_activate = QPushButton("🚀 Kích Hoạt Ngay")
        btn_activate.setObjectName("btnActivate")
        btn_activate.setFixedWidth(160)
        btn_activate.clicked.connect(self.perform_activation)
        btn_box.addWidget(btn_activate)

        layout.addLayout(btn_box)

        # Help footer
        lbl_footer = QLabel("Gửi Mã Thiết Bị cho tác giả gegacy để nhận mã bản quyền chính hãng.")
        lbl_footer.setAlignment(Qt.AlignCenter)
        lbl_footer.setStyleSheet("font-size: 11px; color: #64748b; margin-top: 4px;")
        layout.addWidget(lbl_footer)

    def on_key_text_changed(self, text: str):
        """Auto format and uppercase key."""
        upper = text.upper()
        if text != upper:
            self.txt_key.setText(upper)

    def copy_machine_id(self):
        cb = QApplication.clipboard()
        cb.setText(self.txt_machine_id.text())
        self.btn_copy.setText("✓ Đã Chép!")
        QTimer.singleShot(1800, lambda: self.btn_copy.setText("📋 Sao Chép"))

    def perform_activation(self):
        key = self.txt_key.text().strip()
        name = self.txt_name.text().strip()

        if not name:
            self.lbl_status.setText("⚠️ Vui lòng nhập Tên đăng ký hoặc Email.")
            self.lbl_status.setStyleSheet("color: #fbbf24; font-size: 12px; font-weight: 600;")
            self.txt_name.setFocus()
            return

        if not key:
            self.lbl_status.setText("⚠️ Vui lòng nhập Mã kích hoạt bản quyền.")
            self.lbl_status.setStyleSheet("color: #fbbf24; font-size: 12px; font-weight: 600;")
            self.txt_key.setFocus()
            return

        ok, msg = LicenseManager.activate(key, name)
        if ok:
            self.lbl_status.setText(f"✅ {msg}")
            self.lbl_status.setStyleSheet("color: #34d399; font-size: 12px; font-weight: 700;")
            QTimer.singleShot(700, self.accept)
        else:
            self.lbl_status.setText(f"❌ {msg}")
            self.lbl_status.setStyleSheet("color: #f87171; font-size: 12px; font-weight: 600;")
