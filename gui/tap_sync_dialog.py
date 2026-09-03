"""
Lylis Karaoke Studio - Real-Time Tap-to-Sync LRC Recorder Dialog
"""
import re
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QProgressBar, QMessageBox, QFrame, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QTextCursor
from core.lrc_engine import LrcEngine

class TapSyncDialog(QDialog):
    def __init__(self, audio_engine, initial_text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("⏰ Tạo thời gian LRC - Tap to Sync Studio (Spacebar)")
        self.resize(780, 640)
        self.setStyleSheet("""
            QDialog { background: #0b0f19; color: #f8fafc; font-family: 'Segoe UI', system-ui, sans-serif; }
            QLabel { color: #e2e8f0; }
            QGroupBox { border: 1px solid #1e293b; border-radius: 8px; margin-top: 8px; }
        """)

        self.audio_engine = audio_engine
        self.words_to_sync = []
        self.current_word_idx = 0
        self.recorded_timestamps = []
        self.is_recording = False
        self.generated_lrc = ""
        self.latency_offset_ms = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # 1. Header Info Card
        header_card = QFrame()
        header_card.setStyleSheet("background: #111827; border: 1px solid #1f2937; border-radius: 10px; padding: 12px 16px;")
        hc_layout = QVBoxLayout(header_card)
        hc_layout.setSpacing(4)
        
        lbl_title = QLabel("🎙️ Real-Time Spacebar Tap-to-Sync Synchronizer")
        lbl_title.setStyleSheet("color: #38bdf8; font-size: 15px; font-weight: 800;")
        hc_layout.addWidget(lbl_title)

        lbl_info = QLabel("1. Dán lời bài hát (mỗi dòng một câu) vào khung bên dưới.\n2. Nhấn 'Start Sync' và gõ phím SPACEBAR (Cách) theo từng từ khi bài hát đang phát.")
        lbl_info.setStyleSheet("color: #94a3b8; font-size: 11px; line-height: 1.5;")
        hc_layout.addWidget(lbl_info)
        layout.addWidget(header_card)

        # 2. Raw Text Input Area
        self.txt_input = QTextEdit()
        self.txt_input.setFont(QFont("Segoe UI", 11))
        self.txt_input.setMinimumHeight(135)
        self.txt_input.setPlaceholderText("Dán lời bài hát thuần vào đây (chia theo từng câu)...")
        self.txt_input.setStyleSheet("""
            QTextEdit {
                background: #090d16;
                border: 1.5px solid #1e293b;
                border-radius: 8px;
                padding: 10px 12px;
                color: #f1f5f9;
                font-size: 12px;
                line-height: 1.5;
            }
            QTextEdit:focus { border-color: #38bdf8; }
        """)
        
        # Clean initial text if it was LRC
        clean_text = ""
        if initial_text:
            for line in initial_text.splitlines():
                clean_line = re.sub(r'\[\d{1,2}:\d{2}(?:\.\d+)?\]', '', line)
                clean_line = re.sub(r'[\(\<]\d{1,2}:\d{2}(?:\.\d+)?[\)\>]', '', clean_line).strip()
                clean_line = re.sub(r'\{(?:singer|voice):[^}]+\}', '', clean_line, flags=re.IGNORECASE).strip()
                if clean_line:
                    clean_text += clean_line + "\n"
        self.txt_input.setPlainText(clean_text.strip() or "Chiếc nón ba tầm nghiêng che nắng\nÁo lụa hồng thắm duyên nàng\nAnh chẳng cần non kia\nKhông trông núi nọ ở hờ\nChỉ cần em ở bên cạnh")
        self.txt_input.moveCursor(QTextCursor.Start)
        layout.addWidget(self.txt_input)

        # 3. Latency Compensation Row
        latency_card = QFrame()
        latency_card.setStyleSheet("background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 6px 12px;")
        latency_row = QHBoxLayout(latency_card)
        latency_row.setContentsMargins(4, 2, 4, 2)
        
        lbl_lat = QLabel("⚡ Độ trễ phím (Latency Compensation):")
        lbl_lat.setStyleSheet("font-size: 11px; font-weight: 600; color: #94a3b8;")
        latency_row.addWidget(lbl_lat)
        
        self.spin_latency = QSpinBox()
        self.spin_latency.setRange(-500, 500)
        self.spin_latency.setSuffix(" ms")
        self.spin_latency.setValue(0)
        self.spin_latency.setStyleSheet("background: #1e293b; border: 1px solid #334155; border-radius: 5px; color: #38bdf8; font-weight: 700; padding: 3px 8px;")
        self.spin_latency.valueChanged.connect(lambda value: setattr(self, 'latency_offset_ms', value))
        latency_row.addWidget(self.spin_latency)
        latency_row.addStretch()
        layout.addWidget(latency_card)

        # 4. Large Teleprompter Display Box
        teleprompter = QFrame()
        teleprompter.setFixedHeight(105)
        teleprompter.setStyleSheet("background: #0a0e1a; border: 2px solid #1e293b; border-radius: 12px;")
        tp_layout = QHBoxLayout(teleprompter)
        tp_layout.setContentsMargins(16, 0, 16, 0)
        tp_layout.setSpacing(14)

        self.lbl_prev_word = QLabel("")
        self.lbl_prev_word.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_prev_word.setStyleSheet("color: #475569; font-size: 16px; font-weight: 600;")
        tp_layout.addWidget(self.lbl_prev_word, stretch=1)

        self.lbl_curr_word = QLabel("READY")
        self.lbl_curr_word.setAlignment(Qt.AlignCenter)
        self.lbl_curr_word.setStyleSheet("""
            color: #00f5d4; font-size: 26px; font-weight: 900;
            background: #111827; border: 2px solid #00f5d4; border-radius: 10px;
            padding: 10px 24px;
        """)
        tp_layout.addWidget(self.lbl_curr_word, stretch=2)

        self.lbl_next_word = QLabel("")
        self.lbl_next_word.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl_next_word.setStyleSheet("color: #a78bfa; font-size: 16px; font-weight: 700;")
        tp_layout.addWidget(self.lbl_next_word, stretch=1)

        layout.addWidget(teleprompter)

        # 5. Progress Bar & Counter
        prog_row = QHBoxLayout()
        self.prog_bar = QProgressBar()
        self.prog_bar.setStyleSheet("""
            QProgressBar { background: #111827; border: 1px solid #1f2937; border-radius: 6px; height: 10px; text-align: center; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a855f7, stop:1 #00f5d4); border-radius: 5px; }
        """)
        self.prog_bar.setValue(0)
        prog_row.addWidget(self.prog_bar, stretch=1)

        self.lbl_counter = QLabel("0 / 0 words")
        self.lbl_counter.setStyleSheet("color: #00f5d4; font-family: 'Consolas', monospace; font-weight: 800; font-size: 12px;")
        prog_row.addWidget(self.lbl_counter)
        layout.addLayout(prog_row)

        # 6. Controls Action Bar
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        self.btn_start = QPushButton("▶ Start Sync (Space)")
        self.btn_start.setFixedHeight(40)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff2d55, stop:1 #fb7185);
                color: #ffffff; font-weight: 800; padding: 8px 18px;
                border-radius: 8px; border: none; font-size: 12px;
            }
            QPushButton:hover { background: #ff476d; }
        """)
        self.btn_start.clicked.connect(self.start_sync)
        ctrl_row.addWidget(self.btn_start)

        self.btn_tap = QPushButton("👆 TAP (SPACE)")
        self.btn_tap.setFixedHeight(40)
        self.btn_tap.setEnabled(False)
        self.btn_tap.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f5d4, stop:1 #38bdf8);
                color: #042f2e; font-weight: 900; padding: 8px 24px;
                border-radius: 8px; border: none; font-size: 13px;
            }
            QPushButton:hover { background: #5eead4; }
            QPushButton:disabled { background: #1e293b; color: #475569; }
        """)
        self.btn_tap.clicked.connect(self.record_word_tap)
        ctrl_row.addWidget(self.btn_tap)

        self.btn_undo_tap = QPushButton("↶ Undo Tap")
        self.btn_undo_tap.setFixedHeight(40)
        self.btn_undo_tap.setEnabled(False)
        self.btn_undo_tap.setStyleSheet("""
            QPushButton {
                background: #1e293b; color: #cbd5e1; font-weight: 700;
                border: 1px solid #334155; border-radius: 8px; padding: 8px 16px; font-size: 12px;
            }
            QPushButton:hover { background: #334155; color: #ffffff; }
            QPushButton:disabled { background: #0f172a; color: #475569; border-color: #1e293b; }
        """)
        self.btn_undo_tap.clicked.connect(self.undo_last_tap)
        ctrl_row.addWidget(self.btn_undo_tap)

        self.btn_finish = QPushButton("✓ Finish & Apply")
        self.btn_finish.setFixedHeight(40)
        self.btn_finish.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
                color: #ffffff; font-weight: 800; padding: 8px 20px;
                border-radius: 8px; border: none; font-size: 12px;
            }
            QPushButton:hover { background: #34d399; }
        """)
        self.btn_finish.clicked.connect(self.finish_sync)
        ctrl_row.addWidget(self.btn_finish)

        layout.addLayout(ctrl_row)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer_tick)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            if self.is_recording:
                self.record_word_tap()
                event.accept()
                return
        elif event.key() == Qt.Key_Z and (event.modifiers() & Qt.ControlModifier):
            if self.is_recording:
                self.undo_last_tap()
                event.accept()
                return
        super().keyPressEvent(event)

    def start_sync(self):
        if self.audio_engine is None or not self.audio_engine.current_file:
            QMessageBox.warning(self, "No Audio", "Load an audio track before starting tap sync.")
            return
        raw_text = self.txt_input.toPlainText().strip()
        if not raw_text:
            QMessageBox.warning(self, "No Lyrics", "Please enter lyrics first.")
            return

        self.lines_raw = raw_text.splitlines()
        self.words_to_sync = []
        for line_idx, line in enumerate(self.lines_raw):
            words = line.strip().split(' ')
            for w in words:
                if w.strip():
                    self.words_to_sync.append({
                        'text': w.strip(),
                        'line_idx': line_idx
                    })

        if not self.words_to_sync:
            QMessageBox.warning(self, "No Words", "No valid words found to sync.")
            return

        self.current_word_idx = 0
        self.recorded_timestamps = []
        self.is_recording = True
        self.btn_tap.setEnabled(True)
        self.btn_undo_tap.setEnabled(True)
        self.btn_start.setText("⏹ Restart Sync")

        self.update_teleprompter()

        # Start audio playback from beginning
        self.audio_engine.seek(0.0)
        self.audio_engine.play()
        self.timer.start(50)

    def record_word_tap(self):
        if not self.is_recording or self.current_word_idx >= len(self.words_to_sync):
            return

        t = self.audio_engine.get_current_time()
        adjusted_t = max(0.0, t + (self.latency_offset_ms / 1000.0))
        
        self.recorded_timestamps.append(adjusted_t)
        self.current_word_idx += 1

        if self.current_word_idx >= len(self.words_to_sync):
            self.finish_sync()
        else:
            self.update_teleprompter()

    def undo_last_tap(self):
        if self.current_word_idx > 0 and self.recorded_timestamps:
            self.current_word_idx -= 1
            self.recorded_timestamps.pop()
            self.update_teleprompter()

    def update_teleprompter(self):
        total = len(self.words_to_sync)
        idx = self.current_word_idx

        # Prev
        if idx > 0:
            self.lbl_prev_word.setText(self.words_to_sync[idx - 1]['text'])
        else:
            self.lbl_prev_word.setText("")

        # Current
        if idx < total:
            self.lbl_curr_word.setText(self.words_to_sync[idx]['text'])
        else:
            self.lbl_curr_word.setText("DONE! ✓")

        # Next
        if idx + 1 < total:
            self.lbl_next_word.setText(self.words_to_sync[idx + 1]['text'])
        else:
            self.lbl_next_word.setText("")

        # Progress
        prog = int((idx / max(1, total)) * 100)
        self.prog_bar.setValue(prog)
        self.lbl_counter.setText(f"{idx} / {total} words")

    def on_timer_tick(self):
        if self.is_recording:
            if not self.audio_engine.is_playing:
                self.finish_sync()

    def finish_sync(self):
        self.timer.stop()
        self.is_recording = False
        self.btn_tap.setEnabled(False)
        self.btn_undo_tap.setEnabled(False)

        if not self.recorded_timestamps:
            QMessageBox.warning(self, "No taps", "Tap at least one word before applying the synchronization.")
            return

        # Build Word-Level Synced LRC string
        line_buckets = {}
        for w_idx, word_meta in enumerate(self.words_to_sync[:len(self.recorded_timestamps)]):
            l_idx = word_meta['line_idx']
            if l_idx not in line_buckets:
                line_buckets[l_idx] = []
            line_buckets[l_idx].append((self.recorded_timestamps[w_idx], word_meta['text']))

        lrc_lines = []
        for l_idx in sorted(line_buckets.keys()):
            words_in_line = line_buckets[l_idx]
            if not words_in_line:
                continue
            first_ts = words_in_line[0][0]
            line_ts_str = LrcEngine.format_timestamp(first_ts)
            words_str = " ".join([f"({LrcEngine.format_timestamp(ts)}){txt}" for ts, txt in words_in_line])
            lrc_lines.append(f"[{line_ts_str}]{words_str}")

        self.generated_lrc = "\n".join(lrc_lines)
        self.accept()
