"""
Lylis Karaoke Studio - Google Gemini AI Modal Dialog
Features:
- Extract full song lyrics from song name / artist using Gemini 1.5/2.0 Flash
- AI-Powered Singer Gender & Duet Role Classification (Nam / Nữ / Song ca)
- Persistent API Key Management with Google AI Studio Free Key support
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTextEdit, QTabWidget, 
    QWidget, QMessageBox, QProgressBar, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtGui import QColor, QFont
from core.ai.gemini_service import GeminiService

class GeminiWorkerThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, task_type: str, data: dict, parent=None):
        super().__init__(parent)
        self.task_type = task_type
        self.data = data

    def run(self):
        try:
            if self.task_type == "extract_lyrics":
                res = GeminiService.extract_lyrics_from_song_info(
                    self.data.get("song_title", ""),
                    self.data.get("artist", ""),
                    self.data.get("api_key", "")
                )
                self.finished.emit({"type": "extract_lyrics", "result": res})
            elif self.task_type == "detect_roles":
                roles = GeminiService.auto_detect_duet_roles(
                    self.data.get("lyric_lines", []),
                    self.data.get("song_title", ""),
                    self.data.get("api_key", "")
                )
                self.finished.emit({"type": "detect_roles", "result": roles})
        except Exception as e:
            self.error.emit(str(e))


class GeminiDialog(QDialog):
    lyrics_extracted = pyqtSignal(str, str, str)  # (raw_lrc_or_plain, title, artist)
    roles_detected = pyqtSignal(list)             # list of 'male' | 'female' | 'both'

    def __init__(self, current_lines=None, song_title="Chiếc nón ba tầm", parent=None):
        super().__init__(parent)
        self.current_lines = current_lines or []
        self.song_title = song_title
        self.setWindowTitle("🤖 Google Gemini AI - Trích Xuất Lời & Phân Vai Ca Sĩ")
        self.resize(680, 560)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header Title
        hdr = QHBoxLayout()
        lbl_h = QLabel("✨ Google Gemini AI Music Studio")
        lbl_h.setStyleSheet("font-size: 15px; font-weight: 800; color: #ff2d55;")
        hdr.addWidget(lbl_h)
        hdr.addStretch()

        self.lbl_key_status = QLabel()
        self.update_key_status_label()
        hdr.addWidget(self.lbl_key_status)
        layout.addLayout(hdr)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                padding: 8px 16px;
                font-weight: 700;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                color: #ff2d55;
                border-bottom: 2px solid #ff2d55;
            }
        """)

        # Tab 1: Lyrics Extraction
        self.tab_extract = QWidget()
        self.setup_extract_tab()
        self.tabs.addTab(self.tab_extract, "🎵 Trích Xuất Lời (AI Extraction)")

        # Tab 2: Auto Gender & Duet Role Detection
        self.tab_roles = QWidget()
        self.setup_roles_tab()
        self.tabs.addTab(self.tab_roles, "👥 Tự Động Phân Vai Nam / Nữ")

        # Tab 3: API Key Settings
        self.tab_settings = QWidget()
        self.setup_settings_tab()
        self.tabs.addTab(self.tab_settings, "🔑 Cài Đặt API Key")

        layout.addWidget(self.tabs)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        self.progress.setVisible(False)
        self.progress.setStyleSheet("QProgressBar::chunk { background-color: #ff2d55; }")
        layout.addWidget(self.progress)

    def update_key_status_label(self):
        has_key = bool(GeminiService.get_api_key())
        if has_key:
            self.lbl_key_status.setText("🟢 Gemini API Sẵn Sàng")
            self.lbl_key_status.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 700;")
        else:
            self.lbl_key_status.setText("⚪ Chưa có API Key (Sử dụng AI Heuristic)")
            self.lbl_key_status.setStyleSheet("color: #64748b; font-size: 11px;")

    def setup_extract_tab(self):
        t_layout = QVBoxLayout(self.tab_extract)
        t_layout.setContentsMargins(8, 8, 8, 8)
        t_layout.setSpacing(8)

        inputs_row = QHBoxLayout()
        inputs_row.addWidget(QLabel("Tên bài hát:"))
        self.txt_song_title = QLineEdit(self.song_title)
        self.txt_song_title.setPlaceholderText("VD: Nơi này có anh, Tiki Tiki, Cắt đôi nỗi sầu...")
        inputs_row.addWidget(self.txt_song_title, stretch=2)

        inputs_row.addWidget(QLabel("Ca sĩ:"))
        self.txt_artist = QLineEdit()
        self.txt_artist.setPlaceholderText("VD: Sơn Tùng M-TP, Suzana & VannDa...")
        inputs_row.addWidget(self.txt_artist, stretch=1)
        t_layout.addLayout(inputs_row)

        btn_run = QPushButton("🚀 Trích Xuất Lời Bài Hát Bằng Gemini AI")
        btn_run.setFixedHeight(34)
        btn_run.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff2d55, stop:1 #f59e0b);
                color: #ffffff; font-weight: 800; font-size: 12px; border: none; border-radius: 6px;
            }
            QPushButton:hover { opacity: 0.9; }
        """)
        btn_run.clicked.connect(self.run_lyrics_extraction)
        t_layout.addWidget(btn_run)

        t_layout.addWidget(QLabel("Kết quả lời bài hát & Timestamp (LRC):"))
        self.txt_extract_result = QTextEdit()
        self.txt_extract_result.setFont(QFont("Consolas", 10))
        t_layout.addWidget(self.txt_extract_result)

        btn_apply = QPushButton("📥 Áp Dụng Lời Vào Dự Án Ngay")
        btn_apply.setFixedHeight(32)
        btn_apply.setStyleSheet("background: #0f172a; color: #fff; font-weight: 700; border-radius: 6px;")
        btn_apply.clicked.connect(self.apply_extracted_lyrics)
        t_layout.addWidget(btn_apply)

    def setup_roles_tab(self):
        r_layout = QVBoxLayout(self.tab_roles)
        r_layout.setContentsMargins(8, 8, 8, 8)
        r_layout.setSpacing(8)

        lbl_desc = QLabel("Gemini AI sẽ phân tích đại từ (anh/em), đối thoại song ca và giai điệu để tự động gán vai Nam / Nữ cho từng câu.")
        lbl_desc.setStyleSheet("color: #64748b; font-size: 11px;")
        lbl_desc.setWordWrap(True)
        r_layout.addWidget(lbl_desc)

        btn_run_roles = QPushButton("⚡ AI Tự Động Phân Vai Nam / Nữ / Song Ca")
        btn_run_roles.setFixedHeight(34)
        btn_run_roles.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #ec4899);
                color: #ffffff; font-weight: 800; font-size: 12px; border: none; border-radius: 6px;
            }
            QPushButton:hover { opacity: 0.9; }
        """)
        btn_run_roles.clicked.connect(self.run_role_detection)
        r_layout.addWidget(btn_run_roles)

        self.list_roles_preview = QListWidget()
        self.populate_roles_preview_list([getattr(l, 'singer', 'both') for l in self.current_lines])
        r_layout.addWidget(self.list_roles_preview)

        btn_save_roles = QPushButton("📥 Áp Dụng Phân Vai Vào Line Assignment Matrix")
        btn_save_roles.setFixedHeight(32)
        btn_save_roles.setStyleSheet("background: #0f172a; color: #fff; font-weight: 700; border-radius: 6px;")
        btn_save_roles.clicked.connect(self.apply_detected_roles)
        r_layout.addWidget(btn_save_roles)

    def setup_settings_tab(self):
        s_layout = QVBoxLayout(self.tab_settings)
        s_layout.setContentsMargins(12, 12, 12, 12)
        s_layout.setSpacing(10)

        s_layout.addWidget(QLabel("Google Gemini API Key:"))
        self.txt_api_key = QLineEdit(GeminiService.get_api_key())
        self.txt_api_key.setEchoMode(QLineEdit.Password)
        self.txt_api_key.setPlaceholderText("AIzaSy...")
        s_layout.addWidget(self.txt_api_key)

        lbl_info = QLabel("💡 Bạn có thể nhận API Key miễn phí tại: <a href='https://aistudio.google.com/'>https://aistudio.google.com/</a>")
        lbl_info.setOpenExternalLinks(True)
        lbl_info.setStyleSheet("color: #3b82f6; font-size: 11px;")
        s_layout.addWidget(lbl_info)

        btn_save_key = QPushButton("💾 Lưu API Key")
        btn_save_key.setFixedHeight(32)
        btn_save_key.setStyleSheet("background: #10b981; color: #fff; font-weight: 700; border-radius: 6px;")
        btn_save_key.clicked.connect(self.save_api_key)
        s_layout.addWidget(btn_save_key)

        s_layout.addStretch()

    def save_api_key(self):
        key = self.txt_api_key.text().strip()
        GeminiService.save_api_key(key)
        self.update_key_status_label()
        QMessageBox.information(self, "Thành công", "Đã lưu Gemini API Key thành công!")

    def run_lyrics_extraction(self):
        title = self.txt_song_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Lưu ý", "Vui lòng nhập tên bài hát cần trích xuất.")
            return

        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.worker = GeminiWorkerThread("extract_lyrics", {
            "song_title": title,
            "artist": self.txt_artist.text().strip(),
            "api_key": self.txt_api_key.text().strip()
        })
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()

    def run_role_detection(self):
        raw_lines = [l.full_text if hasattr(l, 'full_text') else str(l) for l in self.current_lines]
        if not raw_lines:
            QMessageBox.warning(self, "Lưu ý", "Chưa có danh sách lời bài hát nào để phân vai.")
            return

        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.worker = GeminiWorkerThread("detect_roles", {
            "lyric_lines": raw_lines,
            "song_title": self.txt_song_title.text().strip(),
            "api_key": self.txt_api_key.text().strip()
        })
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()

    def on_worker_finished(self, data):
        self.progress.setVisible(False)
        t_type = data.get("type")
        res = data.get("result")

        if t_type == "extract_lyrics":
            lrc_content = res.get("lrc_text") or res.get("lyrics_plain", "")
            self.txt_extract_result.setPlainText(lrc_content)
            QMessageBox.information(self, "Thành công", f"Đã trích xuất xong lời bài hát: {res.get('title', '')}")
        elif t_type == "detect_roles":
            self.populate_roles_preview_list(res)
            self.detected_roles_cache = res
            QMessageBox.information(self, "Thành công", "Đã phân tích và phát hiện vai hát Nam / Nữ cho tất cả các dòng!")

    def on_worker_error(self, err_msg):
        self.progress.setVisible(False)
        QMessageBox.warning(self, "Thông báo", f"Quá trình xử lý: {err_msg}")

    def populate_roles_preview_list(self, roles):
        self.list_roles_preview.clear()
        for idx, line in enumerate(self.current_lines):
            t = line.full_text if hasattr(line, 'full_text') else str(line)
            role = roles[idx] if idx < len(roles) else "both"
            icon = "🔵 [NAM]" if role == "male" else ("🔴 [NỮ]" if role == "female" else "🟣 [SONG CA]")
            item = QListWidgetItem(f"{icon}  {t}")
            if role == "male":
                item.setForeground(QColor("#2563eb"))
            elif role == "female":
                item.setForeground(QColor("#db2777"))
            else:
                item.setForeground(QColor("#7c3aed"))
            self.list_roles_preview.addItem(item)

    def apply_extracted_lyrics(self):
        text = self.txt_extract_result.toPlainText().strip()
        if text:
            self.lyrics_extracted.emit(text, self.txt_song_title.text().strip(), self.txt_artist.text().strip())
            self.accept()

    def apply_detected_roles(self):
        if hasattr(self, 'detected_roles_cache') and self.detected_roles_cache:
            self.roles_detected.emit(self.detected_roles_cache)
            self.accept()
        else:
            # Fallback
            roles = GeminiService.auto_detect_duet_roles(
                [l.full_text if hasattr(l, 'full_text') else str(l) for l in self.current_lines],
                self.txt_song_title.text().strip()
            )
            self.roles_detected.emit(roles)
            self.accept()
