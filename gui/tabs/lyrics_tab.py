"""
Lylis Karaoke Studio - Exact Reference Lyrics Editor Tab
Features:
- Time Offset Shifting (+/- 0.1s, +/- 0.5s, +/- 1.0s, custom ms)
- Batch Search & Replace
- Text Case Formatting (UPPERCASE, Title Case, Sentence case)
- Voice Gender Auto-Detection & Multi-Format Exporters (.LRC, .SRT, .ASS)
"""
import os
import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QPlainTextEdit, QFileDialog, QMessageBox, 
    QInputDialog, QFrame
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from core.lrc_engine import LrcEngine
from core.ass_generator import AssGenerator
from core.ai.voice_detector import VoiceGenderDetector

class LyricsTab(QWidget):
    lyrics_applied = pyqtSignal(str)
    tap_sync_requested = pyqtSignal()
    voice_detect_requested = pyqtSignal()
    gemini_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_path = None
        self.audio_engine = None
        self.export_style_config = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 1. Top Header Row: [ Lời bài hát    ⏰ Tạo thời gian LRC    + Thêm vào Timeline ]
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        lbl_title = QLabel("Lời bài hát")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 800; color: #0f172a;")
        top_row.addWidget(lbl_title)

        top_row.addStretch()

        self.btn_tap_sync = QPushButton("⏰ Tạo thời gian LRC")
        self.btn_tap_sync.setFixedHeight(30)
        self.btn_tap_sync.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #ff2d55;
                border: 1px solid #fecdd3;
                border-radius: 6px;
                font-weight: 700;
                font-size: 11px;
                padding: 4px 10px;
            }
            QPushButton:hover { background: #fff1f2; }
        """)
        self.btn_tap_sync.clicked.connect(self.tap_sync_requested.emit)
        top_row.addWidget(self.btn_tap_sync)

        self.btn_apply = QPushButton("＋ Thêm vào Timeline")
        self.btn_apply.setFixedHeight(30)
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background: #ff2d55;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: 700;
                font-size: 11px;
                padding: 4px 12px;
            }
            QPushButton:hover { background: #ff476d; }
        """)
        self.btn_apply.clicked.connect(self.on_apply_clicked)
        top_row.addWidget(self.btn_apply)

        layout.addLayout(top_row)

        # 2. AI Action Bar (Gemini AI Extraction & Voice Gender Auto Detect)
        voice_row = QHBoxLayout()
        self.btn_gemini = QPushButton("🤖 Gemini AI Trích Xuất & Phân Vai")
        self.btn_gemini.setFixedHeight(28)
        self.btn_gemini.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff2d55, stop:1 #f59e0b);
                color: #ffffff; font-weight: 700; font-size: 11px; border: none; border-radius: 6px; padding: 4px 10px;
            }
            QPushButton:hover { opacity: 0.9; }
        """)
        self.btn_gemini.clicked.connect(self.gemini_requested.emit)
        voice_row.addWidget(self.btn_gemini)

        self.btn_detect_voice = QPushButton("⚡ Nhận Diện Giọng Nam/Nữ")
        self.btn_detect_voice.setFixedHeight(28)
        self.btn_detect_voice.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #ec4899);
                color: #ffffff; font-weight: 700; font-size: 11px; border: none; border-radius: 6px; padding: 4px 10px;
            }
            QPushButton:hover { opacity: 0.9; }
        """)
        self.btn_detect_voice.clicked.connect(self.on_auto_detect_voice)
        voice_row.addWidget(self.btn_detect_voice)
        layout.addLayout(voice_row)

        # 3. Quick Utilities Tool Bar: Time Offset Shifter & Text Formatting
        utils_card = QFrame()
        utils_card.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px;")
        uc_layout = QVBoxLayout(utils_card)
        uc_layout.setContentsMargins(6, 4, 6, 4)
        uc_layout.setSpacing(4)

        # Row 1: Time Offset Shift (-0.5s, -0.1s, +0.1s, +0.5s)
        shift_row = QHBoxLayout()
        shift_row.setSpacing(4)
        lbl_shift = QLabel("⏱️ Dịch time:")
        lbl_shift.setStyleSheet("font-size: 10px; font-weight: bold; color: #64748b;")
        shift_row.addWidget(lbl_shift)

        btn_style = """
            QPushButton {
                background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px;
                color: #334155; font-size: 10px; font-weight: 600; padding: 2px 6px;
            }
            QPushButton:hover { background: #f1f5f9; color: #ff2d55; border-color: #fecdd3; }
        """

        btn_m05 = QPushButton("-0.5s")
        btn_m05.setStyleSheet(btn_style)
        btn_m05.clicked.connect(lambda: self.shift_timestamps(-0.5))
        shift_row.addWidget(btn_m05)

        btn_m01 = QPushButton("-0.1s")
        btn_m01.setStyleSheet(btn_style)
        btn_m01.clicked.connect(lambda: self.shift_timestamps(-0.1))
        shift_row.addWidget(btn_m01)

        btn_p01 = QPushButton("+0.1s")
        btn_p01.setStyleSheet(btn_style)
        btn_p01.clicked.connect(lambda: self.shift_timestamps(0.1))
        shift_row.addWidget(btn_p01)

        btn_p05 = QPushButton("+0.5s")
        btn_p05.setStyleSheet(btn_style)
        btn_p05.clicked.connect(lambda: self.shift_timestamps(0.5))
        shift_row.addWidget(btn_p05)

        btn_custom_shift = QPushButton("Tùy chỉnh...")
        btn_custom_shift.setStyleSheet(btn_style)
        btn_custom_shift.clicked.connect(self.on_custom_shift)
        shift_row.addWidget(btn_custom_shift)
        shift_row.addStretch()

        uc_layout.addLayout(shift_row)

        # Row 2: Search/Replace & Text Formatting
        fmt_row = QHBoxLayout()
        fmt_row.setSpacing(4)

        btn_search = QPushButton("🔍 Tìm & Thay thế")
        btn_search.setStyleSheet(btn_style)
        btn_search.clicked.connect(self.on_search_replace)
        fmt_row.addWidget(btn_search)

        btn_upper = QPushButton("🔠 HOA")
        btn_upper.setStyleSheet(btn_style)
        btn_upper.clicked.connect(lambda: self.format_text_case("upper"))
        fmt_row.addWidget(btn_upper)

        btn_title = QPushButton("🔤 Từng Chữ")
        btn_title.setStyleSheet(btn_style)
        btn_title.clicked.connect(lambda: self.format_text_case("title"))
        fmt_row.addWidget(btn_title)

        btn_sentence = QPushButton("🔡 Đầu câu")
        btn_sentence.setStyleSheet(btn_style)
        btn_sentence.clicked.connect(lambda: self.format_text_case("sentence"))
        fmt_row.addWidget(btn_sentence)
        fmt_row.addStretch()

        uc_layout.addLayout(fmt_row)
        layout.addWidget(utils_card)

        # 4. LRC Editor Text Box
        self.text_edit = QPlainTextEdit()
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #ffffff;
                color: #1e293b;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                line-height: 1.5;
            }
            QPlainTextEdit:focus {
                border-color: #ff2d55;
            }
        """)
        layout.addWidget(self.text_edit, stretch=1)

        # 5. Bottom Action Buttons:
        # Import Actions
        imp_row = QHBoxLayout()
        imp_row.setSpacing(6)
        
        lbl_imp = QLabel("Nhập file:")
        lbl_imp.setStyleSheet("font-size: 10px; font-weight: bold; color: #64748b;")
        imp_row.addWidget(lbl_imp)

        btn_imp_lrc = QPushButton("⤓ LRC")
        btn_imp_lrc.setStyleSheet(btn_style)
        btn_imp_lrc.clicked.connect(lambda: self.import_file("lrc"))
        imp_row.addWidget(btn_imp_lrc)

        btn_imp_srt = QPushButton("⤓ SRT")
        btn_imp_srt.setStyleSheet(btn_style)
        btn_imp_srt.clicked.connect(lambda: self.import_file("srt"))
        imp_row.addWidget(btn_imp_srt)

        btn_imp_ass = QPushButton("⤓ ASS")
        btn_imp_ass.setStyleSheet(btn_style)
        btn_imp_ass.clicked.connect(lambda: self.import_file("ass"))
        imp_row.addWidget(btn_imp_ass)
        imp_row.addStretch()
        layout.addLayout(imp_row)

        # Export Actions
        exp_row = QHBoxLayout()
        exp_row.setSpacing(6)

        lbl_exp = QLabel("Tải xuống:")
        lbl_exp.setStyleSheet("font-size: 10px; font-weight: bold; color: #64748b;")
        exp_row.addWidget(lbl_exp)

        btn_exp_lrc = QPushButton("📥 .LRC")
        btn_exp_lrc.setStyleSheet(btn_style)
        btn_exp_lrc.clicked.connect(self.export_lrc)
        exp_row.addWidget(btn_exp_lrc)

        btn_exp_srt = QPushButton("📥 .SRT")
        btn_exp_srt.setStyleSheet(btn_style)
        btn_exp_srt.clicked.connect(self.export_srt)
        exp_row.addWidget(btn_exp_srt)

        btn_exp_ass = QPushButton("📥 .ASS")
        btn_exp_ass.setStyleSheet(btn_style)
        btn_exp_ass.clicked.connect(self.export_ass)
        exp_row.addWidget(btn_exp_ass)
        exp_row.addStretch()
        layout.addLayout(exp_row)

    def set_audio_path(self, path: str):
        self.audio_path = path

    def set_audio_engine(self, engine):
        self.audio_engine = engine

    def set_export_style_config(self, config: dict):
        self.export_style_config = dict(config or {})

    def set_lrc_text(self, text: str):
        self.text_edit.setPlainText(text)

    def get_lrc_text(self) -> str:
        return self.text_edit.toPlainText().strip()

    def on_apply_clicked(self):
        text = self.get_lrc_text()
        if text:
            if not LrcEngine.parse(text):
                QMessageBox.warning(self, "Invalid lyrics", "No valid [mm:ss.xx] lyric timestamps were found.")
                return
            self.lyrics_applied.emit(text)
            QMessageBox.information(self, "Lời bài hát", "🎉 Đã cập nhật lời bài hát vào Timeline thành công!")

    def shift_timestamps(self, delta_secs: float):
        text = self.get_lrc_text()
        if not text:
            return

        def offset_match(m):
            mm = int(m.group(1))
            ss = float(m.group(2).replace(':', '.'))
            total_sec = max(0.0, mm * 60.0 + ss + delta_secs)
            new_mm = int(total_sec // 60)
            new_ss = total_sec % 60
            prefix = m.group(0)[0]
            suffix = m.group(0)[-1]
            return f"{prefix}{new_mm:02d}:{new_ss:05.2f}{suffix}"

        # Shift [mm:ss.xx] and (mm:ss.xx)
        shifted_text = re.sub(r'[\[\(\<](\d{1,3}):(\d{2}(?:[\.:]\d+)?)[\]\)\>]', offset_match, text)
        self.text_edit.setPlainText(shifted_text)
        self.lyrics_applied.emit(shifted_text)

    def on_custom_shift(self):
        val, ok = QInputDialog.getDouble(
            self, "Dịch thời gian tùy chỉnh", 
            "Nhập số giây muốn dịch (vd: +0.25 hoặc -0.5):", 
            value=0.0, min=-600.0, max=600.0, decimals=3
        )
        if ok and val != 0.0:
            self.shift_timestamps(val)

    def on_search_replace(self):
        find_txt, ok1 = QInputDialog.getText(self, "Tìm & Thay thế", "Nhập từ cần tìm:")
        if not ok1 or not find_txt:
            return
        rep_txt, ok2 = QInputDialog.getText(self, "Tìm & Thay thế", f"Thay thế '{find_txt}' bằng:", text="")
        if not ok2:
            return

        text = self.get_lrc_text()
        count = text.count(find_txt)
        if count > 0:
            new_text = text.replace(find_txt, rep_txt)
            self.text_edit.setPlainText(new_text)
            self.lyrics_applied.emit(new_text)
            QMessageBox.information(self, "Tìm & Thay thế", f"Đã thay thế {count} vị trí.")
        else:
            QMessageBox.information(self, "Tìm & Thay thế", "Không tìm thấy từ cần thay thế.")

    def format_text_case(self, case_type: str):
        text = self.get_lrc_text()
        if not text:
            return

        lines = text.splitlines()
        formatted_lines = []

        for line in lines:
            # Separate timestamp tags from word text
            parts = re.split(r'(\[[^\]]+\]|\([^\)]+\)|\<[^\>]+\>|\{[^\}]+\})', line)
            new_parts = []
            for p in parts:
                if p.startswith(('[', '(', '{')):
                    new_parts.append(p)
                else:
                    if case_type == "upper":
                        new_parts.append(p.upper())
                    elif case_type == "title":
                        new_parts.append(p.title())
                    elif case_type == "sentence":
                        new_parts.append(p.capitalize())
                    else:
                        new_parts.append(p)
            formatted_lines.append("".join(new_parts))

        new_text = "\n".join(formatted_lines)
        self.text_edit.setPlainText(new_text)
        self.lyrics_applied.emit(new_text)

    def on_auto_detect_voice(self):
        text = self.get_lrc_text()
        if not text:
            QMessageBox.warning(self, "Chưa có lời bài hát", "Vui lòng nhập lời bài hát trước khi nhận diện giọng hát.")
            return

        lines = LrcEngine.parse(text)
        if not lines:
            return

        samples = getattr(self.audio_engine, 'raw_samples', None)
        sr = getattr(self.audio_engine, 'sample_rate', 44100)

        VoiceGenderDetector.detect_all_lines(lines, samples, sr)

        # Reconstruct LRC with singer tags
        male_count = 0
        female_count = 0

        for line in lines:
            singer = line.singer
            if singer == 'male':
                male_count += 1
            elif singer == 'female':
                female_count += 1

        new_lrc = LrcEngine.export_lrc(lines)
        self.text_edit.setPlainText(new_lrc)
        self.lyrics_applied.emit(new_lrc)

        QMessageBox.information(
            self, 
            "Kết quả AI Nhận Diện Giọng Hát", 
            f"🎉 Đã phân tích toàn bộ {len(lines)} câu hát thành công!\n\n"
            f"• 👨 Giọng Nam: {male_count} câu\n"
            f"• 👩 Giọng Nữ: {female_count} câu\n"
            f"• 👫 Song ca / Không rõ: {len(lines) - male_count - female_count} câu\n\n"
            f"Các thẻ {{singer:male}} và {{singer:female}} đã được tự động thêm vào từng dòng."
        )

    def import_file(self, fmt: str):
        filters = {
            "lrc": "LRC Files (*.lrc);;All Files (*.*)",
            "srt": "SRT Files (*.srt);;All Files (*.*)",
            "ass": "ASS Files (*.ass);;All Files (*.*)"
        }
        path, _ = QFileDialog.getOpenFileName(self, f"Import {fmt.upper()} File", "", filters.get(fmt, "All Files (*.*)"))
        if path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                if fmt == "srt":
                    # Convert SRT to LRC format
                    content = self.convert_srt_to_lrc(content)
                elif fmt == "ass":
                    content = self.convert_ass_to_lrc(content)
                
                self.text_edit.setPlainText(content)
                self.lyrics_applied.emit(content)
                QMessageBox.information(self, "Import Thành Công", f"Đã nhập dữ liệu từ file {os.path.basename(path)}.")
            except Exception as e:
                QMessageBox.critical(self, "Import Thất Bại", f"Lỗi đọc file: {e}")

    def convert_srt_to_lrc(self, srt_text: str) -> str:
        lines = []
        blocks = re.split(r'\n\s*\n', srt_text.strip())
        for block in blocks:
            parts = block.strip().split('\n')
            if len(parts) >= 3:
                time_match = re.search(r'(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})', parts[1])
                if time_match:
                    hh, mm, ss, ms = map(int, time_match.groups())
                    total_sec = hh * 3600 + mm * 60 + ss + ms / 1000.0
                    m_str = int(total_sec // 60)
                    s_str = total_sec % 60
                    text_content = re.sub(r'<[^>]+>', '', " ".join(parts[2:])).strip()
                    if text_content:
                        lines.append(f"[{m_str:02d}:{s_str:05.2f}]{text_content}")
        return "\n".join(lines)

    def convert_ass_to_lrc(self, ass_text: str) -> str:
        result = []
        for raw_line in ass_text.splitlines():
            if not raw_line.startswith("Dialogue:"):
                continue
            fields = raw_line.split(',', 9)
            if len(fields) < 10:
                continue
            start_text, lyric = fields[1].strip(), fields[9]
            match = re.match(r'(\d+):(\d{2}):(\d{2})\.(\d{1,2})', start_text)
            if not match:
                continue
            hours, minutes, seconds, cs = map(int, match.groups())
            start = hours * 3600 + minutes * 60 + seconds + cs / 100.0
            cursor = start
            words = []
            token_pattern = re.compile(r'\{\\(?:k|K|kf|ko)(\d+)\}([^\{]*)')
            tokens = token_pattern.findall(lyric)
            if tokens:
                for duration_cs, text in tokens:
                    clean = re.sub(r'\{[^}]*\}', '', text)
                    if clean:
                        words.append(f"({LrcEngine.format_timestamp(cursor)}){clean.strip()}")
                    cursor += int(duration_cs) / 100.0
                lyric_text = " ".join(words)
            else:
                lyric_text = re.sub(r'\{[^}]*\}', '', lyric).replace(r'\N', ' ')
            result.append(f"[{LrcEngine.format_timestamp(start)}]{lyric_text}")
        return "\n".join(result)

    def export_lrc(self):
        text = self.get_lrc_text()
        if not text:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Lưu file LRC", "lyrics.lrc", "LRC Files (*.lrc)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            QMessageBox.information(self, "Xuất LRC", f"Đã lưu file LRC thành công:\n{path}")

    def export_srt(self):
        text = self.get_lrc_text()
        if not text:
            return
        lines = LrcEngine.parse(text)
        srt_content = LrcEngine.export_srt(lines)
        path, _ = QFileDialog.getSaveFileName(self, "Lưu file SRT", "subtitles.srt", "SubRip Subtitles (*.srt)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            QMessageBox.information(self, "Xuất SRT", f"Đã lưu file SRT thành công:\n{path}")

    def export_ass(self):
        text = self.get_lrc_text()
        if not text:
            return
        lines = LrcEngine.parse(text)
        ass_content = AssGenerator.generate_ass(
            lines,
            font_name=self.export_style_config.get('font_family', 'Montserrat'),
            font_size=int(self.export_style_config.get('font_size', 54)),
            aspect_ratio=self.export_style_config.get('aspect', '16:9'),
        )
        path, _ = QFileDialog.getSaveFileName(self, "Lưu file ASS", "karaoke.ass", "Advanced SubStation Alpha (*.ass)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(ass_content)
            QMessageBox.information(self, "Xuất ASS", f"Đã lưu file ASS thành công:\n{path}")
