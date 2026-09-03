"""
Lylis Karaoke Studio - Video Export Dialog
"""
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QFileDialog, QMessageBox, QComboBox, QGroupBox
)
from PyQt5.QtCore import QThread, pyqtSignal
from core.video_renderer import VideoRenderer

class RenderWorker(QThread):
    progress_changed = pyqtSignal(int)
    finished_render = pyqtSignal(bool, str)

    def __init__(self, output_path, bg_path, audio_path, lines, duration, style_config):
        super().__init__()
        self.output_path = output_path
        self.bg_path = bg_path
        self.audio_path = audio_path
        self.lines = lines
        self.duration = duration
        self.style_config = style_config

    def run(self):
        try:
            success = VideoRenderer.render_video(
                self.output_path,
                self.bg_path,
                self.audio_path,
                self.lines,
                self.duration,
                self.style_config,
                lambda p: self.progress_changed.emit(p),
                self.isInterruptionRequested
            )
            self.finished_render.emit(success, self.output_path)
        except Exception as e:
            self.finished_render.emit(False, str(e))

class ExportDialog(QDialog):
    def __init__(self, bg_path, audio_path, lines, duration, style_config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎬 Xuất Video Karaoke MP4 (High Definition)")
        self.resize(520, 300)
        self.setStyleSheet("""
            QDialog { background: #12141c; color: #fff; }
            QLabel { color: #e2e8f0; font-size: 11px; }
            QGroupBox { border: 1px solid #232738; border-radius: 8px; margin-top: 10px; padding: 10px; font-weight: bold; }
        """)

        self.bg_path = bg_path
        self.audio_path = audio_path
        self.lines = lines
        self.duration = duration
        self.style_config = style_config

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Settings Card
        grp_settings = QGroupBox("⚙️ Video Render Settings")
        s_layout = QVBoxLayout(grp_settings)
        s_layout.setSpacing(8)

        # Resolution & FPS row
        r_row = QHBoxLayout()
        r_row.addWidget(QLabel("Resolution:"))
        self.combo_res = QComboBox()
        self.combo_res.addItems(["1080p Full HD (1920x1080)", "720p HD (1280x720)", "4K Ultra HD (3840x2160)"])
        self.combo_res.setCurrentIndex(0)
        r_row.addWidget(self.combo_res, stretch=1)

        r_row.addWidget(QLabel("Framerate:"))
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["30 fps (Standard)", "60 fps (Smooth)"])
        self.combo_fps.setCurrentIndex(0)
        r_row.addWidget(self.combo_fps)
        s_layout.addLayout(r_row)

        layout.addWidget(grp_settings)

        # Status Label
        self.lbl_status = QLabel("Ready to export high-definition MP4 karaoke video.")
        self.lbl_status.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.lbl_status)

        # Progress Bar
        self.prog_bar = QProgressBar()
        self.prog_bar.setStyleSheet("""
            QProgressBar {
                background: #1c1e28;
                border: 1px solid #282f44;
                border-radius: 4px;
                height: 10px;
                text-align: center;
                color: #ffffff;
                font-size: 9px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff2d55, stop:1 #00d2ff);
                border-radius: 3px;
            }
        """)
        self.prog_bar.setValue(0)
        layout.addWidget(self.prog_bar)

        # Action Buttons
        btn_box = QHBoxLayout()
        self.btn_start = QPushButton("🚀 Bắt đầu Xuất MP4...")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff2d55, stop:1 #ff5277);
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 9px 18px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background: #ff476d;
            }
        """)
        self.btn_start.clicked.connect(self.start_export)
        btn_box.addWidget(self.btn_start)

        self.btn_cancel = QPushButton("Đóng")
        self.btn_cancel.clicked.connect(self.cancel_or_close)
        btn_box.addWidget(self.btn_cancel)

        layout.addLayout(btn_box)
        self.worker = None

    def start_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Karaoke Video", "karaoke_output.mp4",
            "MP4 Video (*.mp4)"
        )
        if not path:
            return

        self.btn_start.setEnabled(False)
        self.lbl_status.setText("Rendering frames and audio muxing...")
        self.prog_bar.setValue(0)

        # Update resolution & fps in style config
        cfg = dict(self.style_config)
        cfg['fps'] = 60 if "60" in self.combo_fps.currentText() else 30
        if "720p" in self.combo_res.currentText():
            cfg['resolution'] = "720p"
        elif "4K" in self.combo_res.currentText():
            cfg['resolution'] = "4k"
        else:
            cfg['resolution'] = "1080p"

        self.worker = RenderWorker(
            path,
            self.bg_path,
            self.audio_path,
            self.lines,
            self.duration,
            cfg
        )
        self.worker.progress_changed.connect(self.prog_bar.setValue)
        self.worker.finished_render.connect(self.on_render_finished)
        self.worker.start()

    def cancel_or_close(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.lbl_status.setText("Cancelling export…")
            self.btn_cancel.setEnabled(False)
            return
        self.reject()

    def on_render_finished(self, success: bool, msg: str):
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(True)
        if success:
            self.prog_bar.setValue(100)
            self.lbl_status.setText(f"✓ Video rendered successfully: {os.path.basename(msg)}")
            QMessageBox.information(self, "Export Complete", f"Karaoke video exported to:\n{msg}")
            self.accept()
        else:
            self.lbl_status.setText("❌ Export failed.")
            QMessageBox.critical(self, "Export Error", f"Render failed:\n{msg}")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.worker.wait(3000)
        event.accept()
