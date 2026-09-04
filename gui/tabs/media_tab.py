"""
Lylis Karaoke Studio - Media Tab matching exact Reference Asset Library
Features:
- Filter Pills (Tất cả, Âm thanh, Hình ảnh, Video) & Live Search
- Audio Tools: Key Transpose (-6 to +6 Semitones), Speed Multiplier (0.5x - 1.5x), Karaoke Vocal Remover (Center Cut)
"""
import os
import uuid
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QLineEdit, QScrollArea, QFrame, QButtonGroup, QSlider, QCheckBox, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt5.QtGui import QDrag

class MediaItemWidget(QFrame):
    add_clicked = pyqtSignal(str)
    delete_clicked = pyqtSignal(object)
    analyze_clicked = pyqtSignal(str, str)

    def __init__(self, filename, metadata, icon_str="📄", filepath="", media_type="image", parent=None):
        super().__init__(parent)
        self.filename = filename
        self.filepath = filepath
        self.media_type = media_type  # "audio" | "image" | "video"
        self.asset_id = str(uuid.uuid4())
        self._drag_start = QPoint()
        self.setStyleSheet("""
            MediaItemWidget {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 6px 8px;
            }
            MediaItemWidget:hover {
                border-color: #cbd5e1;
                background: #f8fafc;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        # Icon
        lbl_icon = QLabel(icon_str)
        lbl_icon.setStyleSheet("font-size: 16px;")
        layout.addWidget(lbl_icon)

        # Info
        info_box = QVBoxLayout()
        info_box.setSpacing(2)
        lbl_name = QLabel(filename)
        lbl_name.setStyleSheet("font-weight: 700; color: #0f172a; font-size: 11px;")
        info_box.addWidget(lbl_name)

        lbl_meta = QLabel(metadata)
        lbl_meta.setStyleSheet("color: #94a3b8; font-size: 10px;")
        info_box.addWidget(lbl_meta)
        layout.addLayout(info_box, stretch=1)

        # Action Buttons: [+] and [🗑]
        btn_add = QPushButton("＋")
        btn_add.setFixedSize(28, 28)
        btn_add.setToolTip("Thêm vào Canvas / Timeline")
        btn_add.setStyleSheet("""
            QPushButton {
                background: #fff1f2;
                color: #ff2d55;
                border: 1px solid #fecdd3;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                padding: 0;
            }
            QPushButton:hover {
                background: #ffe4e6;
            }
        """)
        btn_add.clicked.connect(lambda: self.add_clicked.emit(self.filepath))
        layout.addWidget(btn_add)

        if self.media_type == "audio":
            btn_analyze = QPushButton("Analyze Lyrics")
            btn_analyze.setFixedHeight(28)
            btn_analyze.setToolTip("Analyze song and extract timed lyrics")
            btn_analyze.setStyleSheet("QPushButton { background: #eef2ff; color: #4f46e5; border: 1px solid #c7d2fe; border-radius: 4px; font-weight: 700; font-size: 10px; padding: 0 6px; } QPushButton:hover { background: #e0e7ff; }")
            btn_analyze.clicked.connect(lambda: self.analyze_clicked.emit(self.asset_id, self.filepath))
            layout.addWidget(btn_analyze)

        btn_del = QPushButton("🗑")
        btn_del.setFixedSize(28, 28)
        btn_del.setToolTip("Xóa Asset khỏi danh sách")
        btn_del.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94a3b8;
                border: none;
                font-size: 12px;
                padding: 0;
            }
            QPushButton:hover {
                color: #ef4444;
            }
        """)
        btn_del.clicked.connect(lambda: self.delete_clicked.emit(self))
        layout.addWidget(btn_del)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or not self.filepath:
            return super().mouseMoveEvent(event)
        if (event.pos() - self._drag_start).manhattanLength() < 8:
            return
        mime = QMimeData()
        mime.setData("application/x-lylis-asset-id", self.asset_id.encode("utf-8"))
        mime.setText(self.filepath)
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec_(Qt.CopyAction)


class MediaTab(QWidget):
    background_changed = pyqtSignal(str)
    audio_changed = pyqtSignal(str)
    audio_playlist_changed = pyqtSignal(list)
    pitch_changed = pyqtSignal(int)
    speed_changed = pyqtSignal(float)
    vocal_cut_toggled = pyqtSignal(bool)
    object_template_requested = pyqtSignal(str)
    media_imported = pyqtSignal(list)
    analyze_lyrics_requested = pyqtSignal(str, str)
    asset_add_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.media_items = []
        self.current_filter = "all"
        self.setAcceptDrops(True)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # 1. Top Action: [ + Tải lên ]
        self.btn_upload = QPushButton("＋ Tải lên (Âm thanh / Hình ảnh / Video)")
        self.btn_upload.setFixedHeight(34)
        self.btn_upload.setStyleSheet("""
            QPushButton {
                background: #ff2d55;
                color: #ffffff;
                font-weight: 700;
                font-size: 11px;
                border: none;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover { background: #ff476d; }
        """)
        self.btn_upload.clicked.connect(self.upload_multiple_media)
        main_layout.addWidget(self.btn_upload)

        self.btn_upload_album = QPushButton("💿 Add Songs / Multi Upload")
        self.btn_upload_album.setFixedHeight(32)
        self.btn_upload_album.setToolTip("Select multiple audio files for an album playlist")
        self.btn_upload_album.setStyleSheet("QPushButton { background: #4f46e5; color: white; border: none; border-radius: 6px; font-weight: 700; padding: 6px; } QPushButton:hover { background: #6366f1; }")
        self.btn_upload_album.clicked.connect(self.upload_audio_album)
        main_layout.addWidget(self.btn_upload_album)

        # 2. Audio Tools Card: Tone Transpose & Speed & Vocal Cut
        audio_card = QFrame()
        audio_card.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px;")
        ac_layout = QVBoxLayout(audio_card)
        ac_layout.setContentsMargins(8, 6, 8, 6)
        ac_layout.setSpacing(6)

        lbl_ac_title = QLabel("🎚️ Công cụ Âm Thanh (Tone & Tốc độ)")
        lbl_ac_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #0f172a;")
        ac_layout.addWidget(lbl_ac_title)

        # Transpose Pitch: -6 to +6 semitones
        pitch_row = QHBoxLayout()
        pitch_row.addWidget(QLabel("Đổi Tone (Key):"))
        self.slider_pitch = QSlider(Qt.Horizontal)
        self.slider_pitch.setRange(-6, 6)
        self.slider_pitch.setValue(0)
        self.slider_pitch.valueChanged.connect(self.on_pitch_slider_changed)
        pitch_row.addWidget(self.slider_pitch, stretch=1)
        self.lbl_pitch_val = QLabel("0 ST")
        self.lbl_pitch_val.setFixedWidth(48)
        self.lbl_pitch_val.setStyleSheet("color: #ff2d55; font-weight: bold; font-family: monospace;")
        pitch_row.addWidget(self.lbl_pitch_val)
        ac_layout.addLayout(pitch_row)

        # Playback Speed: 0.5x, 0.75x, 1.0x, 1.25x, 1.5x
        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Tốc độ phát:"))
        self.combo_speed = QComboBox()
        self.combo_speed.addItems(["0.5x Chậm", "0.75x", "1.0x Chuẩn", "1.25x", "1.5x Nhanh"])
        self.combo_speed.setCurrentIndex(2)
        self.combo_speed.currentIndexChanged.connect(self.on_speed_changed)
        speed_row.addWidget(self.combo_speed, stretch=1)
        ac_layout.addLayout(speed_row)

        # Karaoke Vocal Cut (Center Channel Cancellation)
        self.chk_vocal_cut = QCheckBox("Tách lời ca sĩ (Karaoke Center Vocal Cut)")
        self.chk_vocal_cut.setStyleSheet("font-size: 10px; font-weight: 600; color: #475569;")
        self.chk_vocal_cut.stateChanged.connect(lambda s: self.vocal_cut_toggled.emit(s == Qt.Checked))
        ac_layout.addWidget(self.chk_vocal_cut)

        main_layout.addWidget(audio_card)

        # 3. Search input box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm trong thư viện media...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 11px;
                color: #0f172a;
            }
            QLineEdit:focus { border-color: #ff2d55; }
        """)
        self.search_input.textChanged.connect(self.filter_items)
        main_layout.addWidget(self.search_input)

        # 4. Filter Pills: [ Tất cả | Âm thanh | Hình ảnh | Video ]
        filter_box = QHBoxLayout()
        filter_box.setSpacing(4)
        
        pill_style = """
            QPushButton {
                background: #ffffff;
                color: #64748b;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                font-weight: 600;
                font-size: 10px;
                padding: 5px 6px;
            }
            QPushButton:checked {
                background: #ff2d55;
                color: #ffffff;
                border-color: #ff2d55;
                font-weight: 700;
            }
            QPushButton:hover:!checked { background: #f8fafc; }
        """

        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)

        self.btn_f_all = QPushButton("Tất cả")
        self.btn_f_all.setCheckable(True)
        self.btn_f_all.setChecked(True)
        self.btn_f_all.setStyleSheet(pill_style)
        self.btn_f_all.clicked.connect(lambda: self.set_filter("all"))
        self.filter_group.addButton(self.btn_f_all)
        filter_box.addWidget(self.btn_f_all)

        self.btn_f_audio = QPushButton("Âm thanh")
        self.btn_f_audio.setCheckable(True)
        self.btn_f_audio.setStyleSheet(pill_style)
        self.btn_f_audio.clicked.connect(lambda: self.set_filter("audio"))
        self.filter_group.addButton(self.btn_f_audio)
        filter_box.addWidget(self.btn_f_audio)

        self.btn_f_img = QPushButton("Hình ảnh")
        self.btn_f_img.setCheckable(True)
        self.btn_f_img.setStyleSheet(pill_style)
        self.btn_f_img.clicked.connect(lambda: self.set_filter("image"))
        self.filter_group.addButton(self.btn_f_img)
        filter_box.addWidget(self.btn_f_img)

        self.btn_f_vid = QPushButton("Video")
        self.btn_f_vid.setCheckable(True)
        self.btn_f_vid.setStyleSheet(pill_style)
        self.btn_f_vid.clicked.connect(lambda: self.set_filter("video"))
        self.filter_group.addButton(self.btn_f_vid)
        filter_box.addWidget(self.btn_f_vid)

        main_layout.addLayout(filter_box)

        # 5. Media Items Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)

        # Populate with real bundled assets (paths remain valid outside the project cwd and in frozen builds).
        from core.paths import get_asset_path
        self.add_media_card("sample_audio.wav", "Âm thanh • Demo", "🎵", get_asset_path("sample_audio.wav"), "audio")
        self.add_media_card("sample_bg.jpg", "Hình ảnh • 1920x1080", "🖼️", get_asset_path("sample_bg.jpg"), "image")

        self.list_layout.addStretch()
        scroll.setWidget(self.list_container)
        main_layout.addWidget(scroll, stretch=1)

    def on_pitch_slider_changed(self, val):
        sign = "+" if val > 0 else ""
        self.lbl_pitch_val.setText(f"{sign}{val} ST")
        self.pitch_changed.emit(val)

    def on_speed_changed(self, idx):
        speeds = [0.5, 0.75, 1.0, 1.25, 1.5]
        sp = speeds[idx] if idx < len(speeds) else 1.0
        self.speed_changed.emit(sp)

    def add_media_card(self, filename, metadata, icon_str="📄", filepath="", media_type="image"):
        item = MediaItemWidget(filename, metadata, icon_str, filepath, media_type, self)
        item.add_clicked.connect(self.on_media_add_clicked)
        item.delete_clicked.connect(self.on_media_delete_clicked)
        item.analyze_clicked.connect(self.analyze_lyrics_requested.emit)
        self.media_items.append(item)
        self.list_layout.insertWidget(len(self.media_items) - 1, item)

    def on_media_delete_clicked(self, item_widget):
        if item_widget in self.media_items:
            self.media_items.remove(item_widget)
            self.list_layout.removeWidget(item_widget)
            item_widget.deleteLater()

    def media_assets(self):
        return [{"id": item.asset_id, "type": item.media_type, "name": item.filename, "src": item.filepath}
                for item in self.media_items if item.filepath and not item.filepath.startswith("template:")]

    def sync_media_assets(self, assets):
        """Rehydrate visible cards from the canonical project registry."""
        known = {os.path.abspath(item.filepath): item for item in self.media_items if item.filepath}
        for asset in assets or []:
            path = str(asset.get('src') or asset.get('filepath') or '')
            if not path or path.startswith('template:') or not os.path.exists(path):
                continue
            normalized = os.path.abspath(path)
            if normalized in known:
                known[normalized].asset_id = str(asset.get('id') or known[normalized].asset_id)
                continue
            media_type = asset.get('type') or self._media_type_for(path)
            if media_type not in {'audio', 'image', 'video'}:
                continue
            icon = 'ðŸŽµ' if media_type == 'audio' else ('ðŸŽ¬' if media_type == 'video' else 'ðŸ–¼ï¸')
            self.add_media_card(os.path.basename(path), media_type.title(), icon, path, media_type)
            self.media_items[-1].asset_id = str(asset.get('id') or self.media_items[-1].asset_id)

    def _media_type_for(self, path):
        ext = os.path.splitext(path)[1].lower().lstrip('.')
        if ext in {'mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg'}:
            return 'audio'
        if ext in {'mp4', 'webm', 'mov'}:
            return 'video'
        if ext in {'jpg', 'jpeg', 'png', 'webp', 'gif'}:
            return 'image'
        return None

    def import_files(self, paths, activate=False):
        existing = {os.path.abspath(item.filepath) for item in self.media_items if item.filepath}
        imported = []
        for path in paths or []:
            if not path or not os.path.isfile(path):
                continue
            path = os.path.abspath(path)
            media_type = self._media_type_for(path)
            if not media_type or path in existing:
                continue
            icon = '🎵' if media_type == 'audio' else ('🎬' if media_type == 'video' else '🖼️')
            label = 'Audio' if media_type == 'audio' else ('Video' if media_type == 'video' else 'Image')
            self.add_media_card(os.path.basename(path), f"{label} • Uploaded", icon, path, media_type)
            existing.add(path)
            imported.append(self.media_items[-1])
        if imported:
            self.media_imported.emit([{"id": i.asset_id, "type": i.media_type, "name": i.filename, "src": i.filepath} for i in imported])
            if activate:
                first = imported[0]
                (self.audio_changed if first.media_type == 'audio' else self.background_changed).emit(first.filepath)

    def upload_multiple_media(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Import Media", "", "Media Files (*.mp3 *.wav *.flac *.m4a *.aac *.ogg *.jpg *.jpeg *.png *.webp *.gif *.mp4 *.webm *.mov);;All Files (*.*)")
        self.import_files(paths, activate=True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        self.import_files([url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()])
        event.acceptProposedAction()

    def set_filter(self, filter_type: str):
        self.current_filter = filter_type
        self.filter_items()

    def filter_items(self):
        query = self.search_input.text().lower().strip()
        for item in self.media_items:
            matches_type = (self.current_filter == "all") or (item.media_type == self.current_filter)
            matches_query = (not query) or (query in item.filename.lower())
            item.setVisible(matches_type and matches_query)

    def upload_media(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Tải lên tệp Media", "", 
            "Media Files (*.mp3 *.wav *.flac *.m4a *.jpg *.jpeg *.png *.webp *.mp4 *.mov);;All Files (*.*)"
        )
        if path and os.path.exists(path):
            filename = os.path.basename(path)
            ext = filename.split('.')[-1].lower()
            
            if ext in ['mp3', 'wav', 'flac', 'm4a']:
                self.add_media_card(filename, "Âm thanh • Đã tải lên", "🎵", path, "audio")
                self.audio_changed.emit(path)
            elif ext in ['jpg', 'jpeg', 'png', 'webp']:
                self.add_media_card(filename, "Hình ảnh • Đã tải lên", "🖼️", path, "image")
                self.background_changed.emit(path)
            elif ext in ['mp4', 'mov']:
                self.add_media_card(filename, "Video • Đã tải lên", "🎬", path, "video")
                self.background_changed.emit(path)

    def upload_audio_album(self):
        """Import multiple songs in one operation and preserve their selection order."""
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add Songs to Album",
            "",
            "Audio Files (*.mp3 *.wav *.flac *.m4a *.ogg *.aac);;All Files (*.*)",
        )
        valid_paths = [path for path in paths if path and os.path.exists(path)]
        if not valid_paths:
            return
        existing_paths = {item.filepath for item in self.media_items if getattr(item, "filepath", "")}
        for index, path in enumerate(valid_paths, start=1):
            if path not in existing_paths:
                self.add_media_card(os.path.basename(path), f"Album track {index} • Uploaded", "🎵", path, "audio")
                existing_paths.add(path)
        self.audio_playlist_changed.emit(valid_paths)

    def on_media_add_clicked(self, filepath: str):
        if filepath.startswith("template:"):
            self.object_template_requested.emit(filepath.split(':', 1)[1])
            return
        if not filepath or not os.path.exists(filepath):
            return
        item = next((item for item in self.media_items if item.filepath == filepath), None)
        if item:
            self.asset_add_requested.emit(item.asset_id)
