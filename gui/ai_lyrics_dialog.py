from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QProgressBar, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import json
import os
import subprocess
import sys

from core.ai.lyric_analysis_service import LyricAnalysisService


class LyricAnalysisWorker(QThread):
    completed = pyqtSignal(dict)
    failed = pyqtSignal(str)
    stage_changed = pyqtSignal(str)

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self._process = None

    def run(self):
        self._process = None
        try:
            self.stage_changed.emit("preparing audio")
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            command = [sys.executable, "-m", "core.ai.transcribe_worker", "--path", self.path, "--language", "vi"]
            self._process = subprocess.Popen(
                command, cwd=project_root, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                encoding="utf-8", errors="replace", shell=False,
            )
            self.stage_changed.emit("transcribing audio")
            stdout, stderr = self._process.communicate(timeout=290)
            if self._process.returncode != 0:
                raise RuntimeError(stderr.strip() or f"worker exited with code {self._process.returncode}")
            result = json.loads(stdout or "{}")
            if not isinstance(result, dict):
                raise ValueError("transcription worker returned an invalid result")
            self.completed.emit(result)
        except subprocess.TimeoutExpired:
            if self._process is not None:
                self._process.kill()
                self._process.communicate()
            self.failed.emit("Transcription worker timed out.")
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self._process = None

    def requestInterruption(self):
        super().requestInterruption()
        if self._process is not None and self._process.poll() is None:
            self._process.terminate()


class AiLyricsDialog(QDialog):
    applied = pyqtSignal(str, dict)

    def __init__(self, asset_id, audio_path, parent=None):
        super().__init__(parent)
        self.asset_id = asset_id
        self.audio_path = audio_path
        self.result = {}
        self._disposed = False
        self._timed_out = False
        self.setWindowTitle("AI Lyrics Analysis")
        self.resize(650, 520)
        layout = QVBoxLayout(self)
        import os
        self.file_label = QLabel(f"Analyzing: {os.path.basename(audio_path)}")
        self.file_label.setToolTip(audio_path)
        layout.addWidget(self.file_label)
        self.status = QLabel("Preparing audio...")
        layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Timed lyrics will appear here for review...")
        layout.addWidget(self.editor, 1)
        self.btn_apply = QPushButton("Apply to Lyrics")
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self.apply_result)
        action_row = QHBoxLayout()
        action_row.addWidget(self.btn_apply)
        self.btn_retry = QPushButton("Retry")
        self.btn_retry.setVisible(False)
        self.btn_retry.clicked.connect(self.retry_analysis)
        action_row.addWidget(self.btn_retry)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.cancel_analysis)
        action_row.addWidget(self.btn_cancel)
        layout.addLayout(action_row)
        self.worker = None
        self._start_worker()

    def _start_worker(self):
        self._timed_out = False
        self.status.setText("Preparing audio...")
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.btn_retry.setVisible(False)
        self.btn_apply.setEnabled(False)
        self.worker = LyricAnalysisWorker(self.audio_path, self)
        self.worker.completed.connect(self.on_completed)
        self.worker.failed.connect(self.on_failed)
        self.worker.stage_changed.connect(self.on_stage_changed)
        self.worker.start()
        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.timeout_timer.start(5 * 60 * 1000)

    def on_timeout(self):
        if self._disposed or not self.worker.isRunning():
            return
        self._timed_out = True
        self.worker.requestInterruption()
        self.on_failed("Audio analysis timed out after 5 minutes. The editor is still safe to use.")

    def retry_analysis(self):
        if self._disposed or (self.worker and self.worker.isRunning()):
            return
        self.result = {}
        self._start_worker()

    def cancel_analysis(self):
        if self._disposed:
            return
        self._disposed = True
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
        self.status.setText("Canceled")
        self.progress.setVisible(False)
        self.btn_apply.setEnabled(False)
        self.btn_retry.setVisible(False)
        self.btn_cancel.setEnabled(False)
        self.hide()

    def on_stage_changed(self, stage):
        if not self._disposed:
            self.status.setText(stage.replace('_', ' ').capitalize() + "...")

    def closeEvent(self, event):
        # Hide immediately, but keep the worker alive until it exits. This
        # avoids QThread being destroyed while model loading is still active.
        self._disposed = True
        if self.worker.isRunning():
            self.worker.requestInterruption()
        self.hide()
        event.ignore()

    def on_completed(self, result):
        if self._disposed or self._timed_out or not isinstance(result, dict):
            return
        self.timeout_timer.stop()
        self.result = result
        self.status.setText("Complete — review and edit before applying")
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        rows = []
        for line in result.get("lines", []):
            try:
                minutes, seconds = divmod(float(line["start"]), 60)
                text = str(line.get('text') or '').strip()
                if text:
                    rows.append(f"[{int(minutes):02d}:{seconds:05.2f}]{text}")
            except (KeyError, TypeError, ValueError):
                continue
        self.editor.setPlainText("\n".join(rows))
        self.btn_apply.setEnabled(bool(rows))
        self.btn_retry.setVisible(False)
        self.btn_cancel.setText("Close")
        self.btn_cancel.setEnabled(True)

    def on_failed(self, message):
        if self._disposed or self._timed_out and not self.worker.isRunning():
            return
        self.timeout_timer.stop()
        self.progress.setVisible(False)
        self.status.setText(f"Analysis failed: {message}")
        self.status.setWordWrap(True)
        self.btn_retry.setVisible(True)
        self.btn_cancel.setEnabled(True)
        QMessageBox.warning(self, "AI Lyrics", message)

    def apply_result(self):
        if self._disposed or not self.result:
            return
        self.applied.emit(self.editor.toPlainText().strip(), self.result)
        self.accept()
