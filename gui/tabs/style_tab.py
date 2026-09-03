"""
Lylis Karaoke Studio - Exact Reference Style & Mode Tab
Matches all Reference Screenshots:
- Display Modes: ROW | SINGLE | BUILD | COLOR CODED | KARAOKE
- KARAOKE Mode: Staggered Trái Phải, Căn Giữa, Song Ca Duet Role Assignment (Nam/Nữ)
- COLOR CODED Mode: Custom Singers List with Artist Face Photo Upload (📷), Avatars, Colors, Multi-Singer Line Assignment Matrix, Banner
- Fully Flexible & Interconnected: Click any line to seek, auto-update matrix checkboxes, live preview/timeline sync
- Typography: Font family (Playwrite IS, Montserrat, Big Shoulders), Font Size (19px - 96px), Font Style (400 Thường, 900 Cực Đậm)
"""
import os
from typing import List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QSlider, QCheckBox, QPushButton, QGroupBox, 
    QButtonGroup, QColorDialog, QFileDialog, QScrollArea, QFrame, QInputDialog, QGridLayout, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPixmap, QIcon, QPainter, QPainterPath
from core.lrc_engine import LyricLine

class SingerItemCard(QFrame):
    delete_clicked = pyqtSignal(str)
    color_changed = pyqtSignal(str, QColor)
    image_changed = pyqtSignal(str, str)  # (singer_name, image_path)
    name_changed = pyqtSignal(str, str)

    def __init__(self, name: str, color_hex: str = "#f59e0b", image_path: str = "", parent=None):
        super().__init__(parent)
        self.name = name
        self.color = QColor(color_hex)
        self.image_path = image_path
        
        self.setStyleSheet("""
            SingerItemCard {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 4px 8px;
            }
            SingerItemCard:hover {
                border-color: #cbd5e1;
                background: #f8fafc;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)

        # Interactive Avatar Button: click to upload artist face photo
        self.btn_avatar = QPushButton()
        self.btn_avatar.setFixedSize(26, 26)
        self.btn_avatar.setCursor(Qt.PointingHandCursor)
        self.btn_avatar.setToolTip("Nhấp để tải lên ảnh chân dung / mặt ca sĩ (Artist Face Photo)")
        self.btn_avatar.clicked.connect(self.choose_face_image)
        layout.addWidget(self.btn_avatar)
        self.update_avatar_preview()

        # Editable Singer Name
        self.txt_name = QLineEdit(name)
        self.txt_name.setStyleSheet("""
            QLineEdit {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 3px 6px;
                font-size: 11px;
                font-weight: 700;
                color: #0f172a;
            }
            QLineEdit:hover { border-color: #cbd5e1; }
            QLineEdit:focus { border-color: #ff2d55; }
        """)
        self.txt_name.setToolTip("Nhấp vào đây để đổi tên ca sĩ")
        self.txt_name.editingFinished.connect(self.on_name_edited)
        layout.addWidget(self.txt_name, stretch=1)

        # Upload face photo quick icon button
        btn_upload_photo = QPushButton("📷")
        btn_upload_photo.setFixedSize(20, 20)
        btn_upload_photo.setToolTip("Tải lên ảnh mặt ca sĩ")
        btn_upload_photo.setStyleSheet("border: none; color: #64748b; font-size: 11px; background: transparent;")
        btn_upload_photo.clicked.connect(self.choose_face_image)
        layout.addWidget(btn_upload_photo)

        # Color Indicator Button
        self.btn_col = QPushButton()
        self.btn_col.setFixedSize(16, 16)
        self.btn_col.setToolTip("Đổi màu highlight ca sĩ")
        self.btn_col.setStyleSheet(f"background: {self.color.name()}; border: 1px solid #cbd5e1; border-radius: 8px;")
        self.btn_col.clicked.connect(self.pick_color)
        layout.addWidget(self.btn_col)

        # Delete Button
        self.btn_del = QPushButton("🗑")
        self.btn_del.setFixedSize(20, 20)
        self.btn_del.setToolTip("Xóa ca sĩ")
        self.btn_del.setStyleSheet("border: none; color: #ff2d55; font-size: 11px; padding: 0;")
        self.btn_del.clicked.connect(lambda: self.delete_clicked.emit(self.name))
        layout.addWidget(self.btn_del)

    def on_name_edited(self):
        new_name = self.txt_name.text().strip()
        if new_name and new_name != self.name:
            old_name = self.name
            self.name = new_name
            self.name_changed.emit(old_name, new_name)

    def update_avatar_preview(self):
        if self.image_path and os.path.exists(self.image_path):
            pix = QPixmap(self.image_path)
            if not pix.isNull():
                rounded = QPixmap(26, 26)
                rounded.fill(Qt.transparent)
                p = QPainter(rounded)
                p.setRenderHint(QPainter.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, 26, 26)
                p.setClipPath(path)
                p.drawPixmap(0, 0, 26, 26, pix.scaled(26, 26, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                p.end()
                self.btn_avatar.setIcon(QIcon(rounded))
                self.btn_avatar.setIconSize(self.btn_avatar.size())
                self.btn_avatar.setText("")
                self.btn_avatar.setStyleSheet("border: 1.5px solid #ff2d55; border-radius: 13px; background: transparent;")
                return

        self.btn_avatar.setIcon(QIcon())
        self.btn_avatar.setText("👤")
        self.btn_avatar.setStyleSheet("background: #1e293b; color: #fff; border-radius: 13px; font-size: 11px; font-weight: bold; border: none;")

    def choose_face_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 
            f"Chọn ảnh mặt ca sĩ cho '{self.name}'", 
            "", 
            "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if path and os.path.exists(path):
            self.image_path = path
            self.update_avatar_preview()
            self.image_changed.emit(self.name, path)

    def pick_color(self):
        col = QColorDialog.getColor(self.color, self, f"Chọn màu cho ca sĩ {self.name}")
        if col.isValid():
            self.color = col
            self.btn_col.setStyleSheet(f"background: {col.name()}; border: 1px solid #cbd5e1; border-radius: 8px;")
            self.color_changed.emit(self.name, self.color)


class SingerRoleRowWidget(QFrame):
    role_changed = pyqtSignal(int, str)  # (line_idx, singer_role)
    row_clicked = pyqtSignal(int)        # (line_idx)

    def __init__(self, line_idx: int, text: str, initial_singer: str = "both", singers: list = None, parent=None):
        super().__init__(parent)
        self.line_idx = line_idx
        self.text = text
        self.singer = initial_singer
        self.singers = singers or [
            {"name": "Ca sĩ 1", "role": "female", "color": "#b50b56"},
            {"name": "Ca sĩ 2", "role": "male", "color": "#a9470b"}
        ]
        self.is_selected = False
        self.setCursor(Qt.PointingHandCursor)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(6, 4, 6, 4)
        self.layout.setSpacing(6)

        self.lbl_text = QLabel(text[:28] + ("..." if len(text) > 28 else ""))
        self.lbl_text.setStyleSheet("font-size: 11px; font-weight: 600;")
        self.layout.addWidget(self.lbl_text, stretch=1)

        self.singer_checkboxes = []
        for idx, s in enumerate(self.singers):
            s_role = s.get('role', 'female' if idx == 0 else ('male' if idx == 1 else s.get('name', f'singer_{idx}')))
            s_name = s.get('name', f"Ca sĩ {idx+1}")
            chk = QCheckBox()
            chk.setFixedWidth(24)
            chk.setToolTip(f"Ca sĩ {idx+1} ({s_name})")
            is_checked = (self.singer == s_role or self.singer == s_name or (self.singer == 'female' and idx == 0) or (self.singer == 'male' and idx == 1))
            chk.setChecked(is_checked and self.singer not in ('both', 'all'))
            chk.stateChanged.connect(lambda state, r=s_role, i=idx: self.on_singer_toggled(i, r, state))
            self.layout.addWidget(chk)
            self.singer_checkboxes.append(chk)

        # Explicit Both / Song Ca Checkbox
        self.chk_both = QCheckBox()
        self.chk_both.setFixedWidth(24)
        self.chk_both.setToolTip("Cả hai / Song Ca (Both / All)")
        self.chk_both.setChecked(self.singer in ('both', 'all'))
        self.chk_both.stateChanged.connect(self.on_both_toggled)
        self.layout.addWidget(self.chk_both)

        self.update_row_appearance()

    def mousePressEvent(self, event):
        self.row_clicked.emit(self.line_idx)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update_row_appearance()

    def update_row_appearance(self):
        border_highlight = "border: 1.5px solid #ff2d55;" if self.is_selected else ""
        if self.singer in ('both', 'all'):
            self.setStyleSheet(f"background-color: #fefce8; border-radius: 4px; border-left: 3px solid #f59e0b; {border_highlight}")
            self.lbl_text.setStyleSheet("color: #b45309; font-size: 11px; font-weight: 700;")
        elif len(self.singers) > 0 and (self.singer == 'female' or self.singer == self.singers[0].get('role') or self.singer == self.singers[0].get('name')):
            col = self.singers[0].get('color', '#b50b56')
            self.setStyleSheet(f"background-color: #fdf2f8; border-radius: 4px; border-left: 3px solid {col}; {border_highlight}")
            self.lbl_text.setStyleSheet(f"color: {col}; font-size: 11px; font-weight: 700;")
        elif len(self.singers) > 1 and (self.singer == 'male' or self.singer == self.singers[1].get('role') or self.singer == self.singers[1].get('name')):
            col = self.singers[1].get('color', '#a9470b')
            self.setStyleSheet(f"background-color: #eff6ff; border-radius: 4px; border-left: 3px solid {col}; {border_highlight}")
            self.lbl_text.setStyleSheet(f"color: {col}; font-size: 11px; font-weight: 700;")
        else:
            matched_col = None
            for s in self.singers:
                if self.singer in (s.get('role'), s.get('name')):
                    matched_col = s.get('color', '#10b981')
                    break
            if matched_col:
                self.setStyleSheet(f"background-color: #f0fdf4; border-radius: 4px; border-left: 3px solid {matched_col}; {border_highlight}")
                self.lbl_text.setStyleSheet(f"color: {matched_col}; font-size: 11px; font-weight: 700;")
            else:
                self.setStyleSheet(f"background-color: #ffffff; border-radius: 4px; border-left: 3px solid #cbd5e1; {border_highlight}")
                self.lbl_text.setStyleSheet("color: #334155; font-size: 11px; font-weight: 600;")

    def on_singer_toggled(self, singer_idx: int, role: str, state: int):
        if state == Qt.Checked:
            self.chk_both.blockSignals(True)
            self.chk_both.setChecked(False)
            self.chk_both.blockSignals(False)
            for idx, chk in enumerate(self.singer_checkboxes):
                if idx != singer_idx:
                    chk.blockSignals(True)
                    chk.setChecked(False)
                    chk.blockSignals(False)
            self.singer = role
        else:
            has_checked = any(chk.isChecked() for chk in self.singer_checkboxes)
            if not has_checked:
                self.chk_both.blockSignals(True)
                self.chk_both.setChecked(True)
                self.chk_both.blockSignals(False)
                self.singer = "both"
        self.update_row_appearance()
        self.role_changed.emit(self.line_idx, self.singer)

    def on_both_toggled(self, state: int):
        if state == Qt.Checked:
            for chk in self.singer_checkboxes:
                chk.blockSignals(True)
                chk.setChecked(False)
                chk.blockSignals(False)
            self.singer = "both"
        else:
            if self.singer_checkboxes:
                self.singer_checkboxes[0].blockSignals(True)
                self.singer_checkboxes[0].setChecked(True)
                self.singer_checkboxes[0].blockSignals(False)
                self.singer = self.singers[0].get('role', 'female')
        self.update_row_appearance()
        self.role_changed.emit(self.line_idx, self.singer)

    def set_singer(self, singer: str):
        self.singer = singer
        self.chk_both.blockSignals(True)
        self.chk_both.setChecked(singer in ('both', 'all'))
        self.chk_both.blockSignals(False)
        for idx, s in enumerate(self.singers):
            s_role = s.get('role', 'female' if idx == 0 else ('male' if idx == 1 else s.get('name', f'singer_{idx}')))
            s_name = s.get('name', '')
            is_match = (singer == s_role or singer == s_name or (singer == 'female' and idx == 0) or (singer == 'male' and idx == 1))
            if idx < len(self.singer_checkboxes):
                self.singer_checkboxes[idx].blockSignals(True)
                self.singer_checkboxes[idx].setChecked(is_match and singer not in ('both', 'all'))
                self.singer_checkboxes[idx].blockSignals(False)
        self.update_row_appearance()


class StyleTab(QWidget):
    style_changed = pyqtSignal(dict)
    singer_roles_updated = pyqtSignal(list)
    line_seek_requested = pyqtSignal(float)
    ai_gender_detect_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.display_mode = "KARAOKE"
        self.layout_mode = "left_right"
        self.fill_mode = "word"
        self.singer_mode = "song_ca"
        self.portrait_focus_y = 25
        self.uppercase_lyrics = False
        
        self.male_color = QColor("#0026ff")
        self.female_color = QColor("#ff0033")
        self.both_color = QColor("#ff007f")
        
        self.base_text_color = QColor("#ffffff")
        self.fill_color = QColor("#f59e0b")
        
        # Color Coded Custom Singers List with Face Images support
        self.custom_singers = [
            {"name": "Phùng Minh Cường", "color": "#3b82f6", "avatar": "👤", "image_path": ""},
            {"name": "Tùng Mint", "color": "#f59e0b", "avatar": "👤", "image_path": ""},
            {"name": "Nguyễn Văn Chung", "color": "#10b981", "avatar": "👤", "image_path": ""},
            {"name": "Neko Lê", "color": "#ef4444", "avatar": "👤", "image_path": ""}
        ]
        self.singer_cards = []
        self.matrix_checkboxes = []

        self.lyric_lines_cache = []
        self.role_row_widgets = []
        self.selected_line_idx = 0

        self._track_title = "Chiếc nón ba tầm"
        self._track_artist = "SUZANA, VANNDA"
        self._album_title = "My Album"
        self._album_tracks = []
        self.album_cover_path = ""
        self.track_cover_path = ""
        self.template_variant = ""

        self.setup_ui()

    @property
    def track_title(self) -> str:
        if hasattr(self, 'txt_track_title'):
            return self.txt_track_title.text().strip()
        return getattr(self, '_track_title', 'Chiếc nón ba tầm')

    @track_title.setter
    def track_title(self, val: str):
        self._track_title = str(val or '')
        if hasattr(self, 'txt_track_title'):
            self.txt_track_title.blockSignals(True)
            self.txt_track_title.setText(self._track_title)
            self.txt_track_title.blockSignals(False)

    @property
    def track_artist(self) -> str:
        if hasattr(self, 'txt_track_artist'):
            return self.txt_track_artist.text().strip()
        return getattr(self, '_track_artist', 'SUZANA, VANNDA')

    @track_artist.setter
    def track_artist(self, val: str):
        self._track_artist = str(val or '')
        if hasattr(self, 'txt_track_artist'):
            self.txt_track_artist.blockSignals(True)
            self.txt_track_artist.setText(self._track_artist)
            self.txt_track_artist.blockSignals(False)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # 0. TRACK & ALBUM METADATA (Tên bài hát, Ca sĩ, Bìa đĩa)
        meta_card = QFrame()
        meta_card.setStyleSheet("""
            QFrame {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        meta_layout = QVBoxLayout(meta_card)
        meta_layout.setContentsMargins(8, 8, 8, 8)
        meta_layout.setSpacing(6)

        lbl_meta_hdr = QLabel("🎵 Thông Tin Bài Hát & Bìa Album")
        lbl_meta_hdr.setStyleSheet("font-size: 11px; font-weight: 800; color: #0f172a;")
        meta_layout.addWidget(lbl_meta_hdr)

        # Track Title
        row_title = QVBoxLayout()
        row_title.setSpacing(2)
        lbl_t = QLabel("Tên bài hát (Track Title):")
        lbl_t.setStyleSheet("font-size: 10px; font-weight: 600; color: #64748b;")
        self.txt_track_title = QLineEdit(getattr(self, 'track_title', 'Chiếc nón ba tầm'))
        self.txt_track_title.setPlaceholderText("Nhập tên bài hát (VD: Chiếc nón ba tầm, POCO POCO...)")
        self.txt_track_title.setStyleSheet("""
            QLineEdit {
                background: #ffffff; border: 1px solid #cbd5e1; border-radius: 5px;
                padding: 5px 8px; font-size: 11px; font-weight: 600; color: #0f172a;
            }
            QLineEdit:focus { border-color: #ff2d55; }
        """)
        self.txt_track_title.textChanged.connect(self.on_metadata_text_changed)
        row_title.addWidget(lbl_t)
        row_title.addWidget(self.txt_track_title)
        meta_layout.addLayout(row_title)

        # Track Artist
        row_artist = QVBoxLayout()
        row_artist.setSpacing(2)
        lbl_a = QLabel("Tên ca sĩ / Nghệ sĩ (Track Artist):")
        lbl_a.setStyleSheet("font-size: 10px; font-weight: 600; color: #64748b;")
        self.txt_track_artist = QLineEdit(getattr(self, 'track_artist', 'SUZANA, VANNDA'))
        self.txt_track_artist.setPlaceholderText("Nhập tên ca sĩ (VD: SUZANA, VANNDA, The Walters...)")
        self.txt_track_artist.setStyleSheet("""
            QLineEdit {
                background: #ffffff; border: 1px solid #cbd5e1; border-radius: 5px;
                padding: 5px 8px; font-size: 11px; font-weight: 600; color: #0f172a;
            }
            QLineEdit:focus { border-color: #ff2d55; }
        """)
        self.txt_track_artist.textChanged.connect(self.on_metadata_text_changed)
        row_artist.addWidget(lbl_a)
        row_artist.addWidget(self.txt_track_artist)
        meta_layout.addLayout(row_artist)

        # Album Cover Image Picker
        row_cover = QHBoxLayout()
        row_cover.setSpacing(6)
        
        self.btn_album_cover = QPushButton("📷 Đổi Ảnh Bìa Album...")
        self.btn_album_cover.setStyleSheet("""
            QPushButton {
                background: #ffffff; border: 1px solid #cbd5e1; border-radius: 5px;
                padding: 5px 10px; font-size: 10px; font-weight: 700; color: #334155;
            }
            QPushButton:hover { background: #f1f5f9; border-color: #ff2d55; }
        """)
        self.btn_album_cover.clicked.connect(self.choose_album_cover)
        row_cover.addWidget(self.btn_album_cover, stretch=1)

        self.album_cover_path = ""
        meta_layout.addLayout(row_cover)

        self.grp_album_tracks_meta = QFrame()
        grp_album_layout = QVBoxLayout(self.grp_album_tracks_meta)
        grp_album_layout.setContentsMargins(0, 0, 0, 0)
        grp_album_layout.setSpacing(4)

        self.btn_track_cover = QPushButton("📷 Change Track Image")
        self.btn_track_cover.setToolTip("Set artwork for the currently selected album track")
        self.btn_track_cover.clicked.connect(self.choose_track_cover)
        grp_album_layout.addWidget(self.btn_track_cover)
        self.track_cover_path = ""

        # Multi-song album metadata (used by the Album Player template).
        self.txt_album_title = QLineEdit(getattr(self, 'album_title', 'My Album'))
        self.txt_album_title.setPlaceholderText("Album title")
        self.txt_album_title.textChanged.connect(self.on_album_metadata_changed)
        grp_album_layout.addWidget(self.txt_album_title)
        self.txt_album_tracks = QLineEdit(", ".join(getattr(self, 'album_tracks', []) or []))
        self.txt_album_tracks.setPlaceholderText("Track names, separated by commas")
        self.txt_album_tracks.textChanged.connect(self.on_album_metadata_changed)
        grp_album_layout.addWidget(self.txt_album_tracks)
        self.txt_album_tracks.hide()

        meta_layout.addWidget(self.grp_album_tracks_meta)

        layout.addWidget(meta_card)

        # 1. STYLE MODE
        lbl_disp_title = QLabel("Style Mode")
        lbl_disp_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")
        layout.addWidget(lbl_disp_title)

        disp_box = QVBoxLayout()
        disp_box.setSpacing(4)

        disp_pill_style = """
            QPushButton {
                background: #ffffff;
                color: #64748b;
                border: 1px solid #e2e8f0;
                border-radius: 5px;
                font-weight: 700;
                font-size: 10px;
                padding: 6px 4px;
            }
            QPushButton:checked {
                background: #ff2d55;
                color: #ffffff;
                border-color: #ff2d55;
            }
            QPushButton:hover:!checked { background: #f8fafc; border-color: #cbd5e1; }
        """

        self.disp_group = QButtonGroup(self)
        self.disp_group.setExclusive(True)

        for mode_name in ["ROW", "SINGLE", "BUILD", "COLOR CODED", "KARAOKE"]:
            btn = QPushButton(mode_name)
            btn.setCheckable(True)
            btn.setStyleSheet(disp_pill_style)
            if mode_name == self.display_mode:
                btn.setChecked(True)
            self.disp_group.addButton(btn)
            btn.clicked.connect(lambda checked, m=mode_name: self.set_display_mode(m))
            disp_box.addWidget(btn)

        layout.addLayout(disp_box)

        # 2. 1-CLICK THEME PRESETS
        grp_themes = QGroupBox("🌟 Mẫu Giao Diện Sẵn (Theme Presets)")
        th_layout = QGridLayout(grp_themes)
        th_layout.setContentsMargins(6, 6, 6, 6)
        th_layout.setSpacing(4)

        preset_btn_style = """
            QPushButton {
                background: #ffffff; border: 1px solid #e2e8f0; border-radius: 5px;
                color: #334155; font-size: 10px; font-weight: 700; padding: 5px 4px;
            }
            QPushButton:hover { background: #fff1f2; color: #ff2d55; border-color: #fecdd3; }
        """

        btn_t1 = QPushButton("🌟 Golden Ballad")
        btn_t1.setStyleSheet(preset_btn_style)
        btn_t1.clicked.connect(lambda: self.apply_theme_preset("golden"))
        th_layout.addWidget(btn_t1, 0, 0)

        btn_t2 = QPushButton("🚀 Cyberpunk")
        btn_t2.setStyleSheet(preset_btn_style)
        btn_t2.clicked.connect(lambda: self.apply_theme_preset("cyberpunk"))
        th_layout.addWidget(btn_t2, 0, 1)

        btn_t3 = QPushButton("🌸 Sakura Rose")
        btn_t3.setStyleSheet(preset_btn_style)
        btn_t3.clicked.connect(lambda: self.apply_theme_preset("sakura"))
        th_layout.addWidget(btn_t3, 1, 0)

        btn_t4 = QPushButton("🎬 Cinema Noir")
        btn_t4.setStyleSheet(preset_btn_style)
        btn_t4.clicked.connect(lambda: self.apply_theme_preset("noir"))
        th_layout.addWidget(btn_t4, 1, 1)

        btn_t5 = QPushButton("🔥 TIKI TIKI (Suzana & VannDa Duet)")
        btn_t5.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ec4899, stop:1 #f59e0b);
                color: #ffffff; border: none; border-radius: 5px;
                font-size: 10px; font-weight: 800; padding: 6px;
            }
            QPushButton:hover { opacity: 0.9; }
        """)
        btn_t5.clicked.connect(lambda: self.apply_theme_preset("tiki_tiki"))
        th_layout.addWidget(btn_t5, 2, 0, 1, 2)

        layout.addWidget(grp_themes)

        # 3. KINETIC MOTION EFFECTS
        grp_motion = QGroupBox("⚡ Hiệu Ứng Chuyển Động (Motion Effects)")
        m_layout = QVBoxLayout(grp_motion)
        m_layout.setContentsMargins(6, 6, 6, 6)
        m_layout.setSpacing(4)

        self.combo_motion = QComboBox()
        self.combo_motion.addItems([
            "Pop & Bounce (Nảy chữ nhịp điệu)",
            "Slide Up Smooth (Trượt nổi mượt mà)",
            "Kinetic Scale Pulse (Phóng to từ đang hát)",
            "Neon Glow Wave (Sóng phát sáng neon)",
            "Typewriter (Máy đánh chữ từng từ)",
            "Fade In / Out (Mờ dần êm dịu)",
            "Classic Karaoke Sweep (Quét karaoke chuẩn)"
        ])
        self.combo_motion.setCurrentIndex(0)
        self.combo_motion.currentIndexChanged.connect(self.emit_change)
        m_layout.addWidget(self.combo_motion)
        layout.addWidget(grp_motion)

        # 4. TYPOGRAPHY & ALIGNMENT
        font_box = QVBoxLayout()
        font_box.setSpacing(6)

        lbl_f_family = QLabel("Font Family")
        lbl_f_family.setStyleSheet("font-size: 10px; color: #64748b; font-weight: 600;")
        font_box.addWidget(lbl_f_family)

        self.combo_font = QComboBox()
        self.combo_font.addItems([
            "Montserrat", "Playwrite IS", "Big Shoulders Display", "Be Vietnam Pro", 
            "Inter", "Playfair Display", "Segoe Print", "Arial", "Impact", "Georgia"
        ])
        self.combo_font.setCurrentText("Montserrat")
        self.combo_font.currentIndexChanged.connect(self.emit_change)
        font_box.addWidget(self.combo_font)

        lbl_f_weight = QLabel("Font Style")
        lbl_f_weight.setStyleSheet("font-size: 10px; color: #64748b; font-weight: 600;")
        font_box.addWidget(lbl_f_weight)

        self.combo_weight = QComboBox()
        self.combo_weight.addItems(["900 Cực Đậm", "800 ExtraBold", "700 Bold", "600 SemiBold", "400 Thường"])
        self.combo_weight.setCurrentIndex(0)
        self.combo_weight.currentIndexChanged.connect(self.emit_change)
        font_box.addWidget(self.combo_weight)

        # Alignment
        lbl_align = QLabel("Căn lề lời bài hát (Text Alignment)")
        lbl_align.setStyleSheet("font-size: 10px; color: #64748b; font-weight: 600;")
        font_box.addWidget(lbl_align)

        align_row = QHBoxLayout()
        self.btn_align_left = QPushButton("⬅ Trái")
        self.btn_align_center = QPushButton("⏺ Giữa")
        self.btn_align_right = QPushButton("➡ Phải")
        self.text_alignment = "center"

        align_pill_style = """
            QPushButton {
                background: #ffffff; color: #64748b; border: 1px solid #e2e8f0;
                border-radius: 4px; font-weight: 700; font-size: 10px; padding: 4px;
            }
            QPushButton:checked { background: #ff2d55; color: #ffffff; border-color: #ff2d55; }
        """
        for b, a_val in [(self.btn_align_left, "left"), (self.btn_align_center, "center"), (self.btn_align_right, "right")]:
            b.setCheckable(True)
            b.setStyleSheet(align_pill_style)
            b.clicked.connect(lambda checked, val=a_val: self.set_text_alignment(val))
            align_row.addWidget(b)

        self.btn_align_center.setChecked(True)
        self.align_group = QButtonGroup(self)
        self.align_group.setExclusive(True)
        self.align_group.addButton(self.btn_align_left)
        self.align_group.addButton(self.btn_align_center)
        self.align_group.addButton(self.btn_align_right)
        font_box.addLayout(align_row)

        # Font Size
        self.lbl_size_title = QLabel("Font Size (38px)")
        self.lbl_size_title.setStyleSheet("font-size: 10px; color: #64748b; font-weight: 600;")
        font_box.addWidget(self.lbl_size_title)

        self.slider_font_size = QSlider(Qt.Horizontal)
        self.slider_font_size.setRange(12, 80)
        self.slider_font_size.setValue(38)
        self.slider_font_size.valueChanged.connect(self.on_font_size_changed)
        font_box.addWidget(self.slider_font_size)

        # Text Stroke Outline (Viền chữ)
        stroke_row = QHBoxLayout()
        self.lbl_stroke_title = QLabel("Độ dày viền chữ (3.5px):")
        self.lbl_stroke_title.setStyleSheet("font-size: 10px; color: #64748b; font-weight: 600;")
        stroke_row.addWidget(self.lbl_stroke_title)
        self.slider_stroke = QSlider(Qt.Horizontal)
        self.slider_stroke.setRange(0, 12)
        self.slider_stroke.setValue(4)
        self.slider_stroke.valueChanged.connect(self.on_stroke_changed)
        stroke_row.addWidget(self.slider_stroke, stretch=1)
        font_box.addLayout(stroke_row)

        # Text Color
        font_box.addWidget(QLabel("Màu chữ chính (Text Fill Color)"))
        self.btn_text_color = QPushButton()
        self.btn_text_color.setFixedHeight(26)
        self.btn_text_color.setStyleSheet(f"background: {self.fill_color.name()}; border: 1px solid #cbd5e1; border-radius: 4px;")
        self.btn_text_color.clicked.connect(self.pick_text_color)
        font_box.addWidget(self.btn_text_color)

        layout.addLayout(font_box)

        # 3. SINGERS LIST (+ ADD SINGER, Avatar Image Upload 📷 & 🗑)
        self.grp_singers_list = QGroupBox()
        sl_layout = QVBoxLayout(self.grp_singers_list)
        sl_layout.setContentsMargins(8, 8, 8, 8)
        sl_layout.setSpacing(6)

        sl_hdr = QHBoxLayout()
        lbl_sl = QLabel("Singers List (Thêm ảnh mặt ca sĩ 📷)")
        lbl_sl.setStyleSheet("font-size: 11px; font-weight: 700; color: #0f172a;")
        sl_hdr.addWidget(lbl_sl)
        sl_hdr.addStretch()

        btn_add_singer = QPushButton("＋ ADD SINGER")
        btn_add_singer.setStyleSheet("border: none; color: #ff2d55; font-size: 10px; font-weight: 700; background: transparent;")
        btn_add_singer.clicked.connect(self.on_add_singer)
        sl_hdr.addWidget(btn_add_singer)
        sl_layout.addLayout(sl_hdr)

        self.singers_cards_layout = QVBoxLayout()
        self.singers_cards_layout.setSpacing(4)
        sl_layout.addLayout(self.singers_cards_layout)
        self.populate_singers_list()

        layout.addWidget(self.grp_singers_list)

        # 4. LINE ASSIGNMENT
        self.grp_line_assign = QGroupBox()
        la_layout = QVBoxLayout(self.grp_line_assign)
        la_layout.setContentsMargins(8, 8, 8, 8)
        la_layout.setSpacing(6)

        la_hdr = QHBoxLayout()
        lbl_la = QLabel("Line Assignment (Nhấp vào câu để gán ca sĩ)")
        lbl_la.setStyleSheet("font-size: 11px; font-weight: 700; color: #0f172a;")
        btn_ai_roles = QPushButton("🤖 AI Phân Vai (Gemini)")
        btn_ai_roles.setStyleSheet("border: 1px solid #fecdd3; color: #ff2d55; font-size: 10px; font-weight: 700; background: #fff1f2; border-radius: 4px; padding: 2px 8px;")
        btn_ai_roles.clicked.connect(self.ai_gender_detect_requested.emit)
        la_hdr.addWidget(btn_ai_roles)

        btn_reset_la = QPushButton("RESET")
        btn_reset_la.setStyleSheet("border: none; color: #64748b; font-size: 10px; font-weight: 700; background: transparent;")
        btn_reset_la.clicked.connect(self.reset_all_roles)
        la_hdr.addWidget(btn_reset_la)
        la_layout.addLayout(la_hdr)

        # 2x2 Grid Matrix of Singers Checkboxes for Selected Line
        self.matrix_widget = QWidget()
        self.matrix_layout = QGridLayout(self.matrix_widget)
        self.matrix_layout.setContentsMargins(4, 4, 4, 4)
        self.matrix_layout.setSpacing(6)
        la_layout.addWidget(self.matrix_widget)

        # Singer Column Header Row (Labels for each checkbox column)
        self.header_widget = QWidget()
        self.header_widget.setStyleSheet("background: #f8fafc; border-radius: 4px; border-bottom: 1px solid #e2e8f0; padding: 2px 0px;")
        self.line_assign_header_layout = QHBoxLayout(self.header_widget)
        self.line_assign_header_layout.setContentsMargins(6, 4, 6, 4)
        self.line_assign_header_layout.setSpacing(6)
        la_layout.addWidget(self.header_widget)

        # Lyrics preview list
        self.lines_preview_layout = QVBoxLayout()
        self.lines_preview_layout.setSpacing(3)
        la_layout.addLayout(self.lines_preview_layout)

        self.populate_matrix_checkboxes()

        layout.addWidget(self.grp_line_assign)

        # 5. KARAOKE CONTROLS
        self.grp_karaoke_controls = QGroupBox("Karaoke Controls")
        kc_layout = QVBoxLayout(self.grp_karaoke_controls)
        kc_layout.setSpacing(8)

        kc_layout.addWidget(QLabel("Phong cách Karaoke"))
        self.btn_left_right = QPushButton("TRÁI PHẢI")
        self.btn_left_right.setCheckable(True)
        self.btn_left_right.setChecked(True)
        self.btn_left_right.setStyleSheet(disp_pill_style)
        self.btn_left_right.clicked.connect(lambda: self.set_karaoke_style("left_right"))
        kc_layout.addWidget(self.btn_left_right)

        self.btn_center = QPushButton("CĂN GIỮA")
        self.btn_center.setCheckable(True)
        self.btn_center.setStyleSheet(disp_pill_style)
        self.btn_center.clicked.connect(lambda: self.set_karaoke_style("center"))
        kc_layout.addWidget(self.btn_center)
        self.karaoke_layout_group = QButtonGroup(self)
        self.karaoke_layout_group.setExclusive(True)
        self.karaoke_layout_group.addButton(self.btn_left_right)
        self.karaoke_layout_group.addButton(self.btn_center)

        kc_layout.addWidget(QLabel("Tọa độ lyrics (66% / 78%)"))
        self.slider_pos_y = QSlider(Qt.Horizontal)
        self.slider_pos_y.setRange(30, 90)
        self.slider_pos_y.setValue(74)
        self.slider_pos_y.valueChanged.connect(self.emit_change)
        kc_layout.addWidget(self.slider_pos_y)

        layout.addWidget(self.grp_karaoke_controls)

        self.update_mode_visibility()

        layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def populate_singers_list(self):
        for c in self.singer_cards:
            self.singers_cards_layout.removeWidget(c)
            c.deleteLater()
        self.singer_cards.clear()

        for s in self.custom_singers:
            card = SingerItemCard(s['name'], s['color'], s.get('image_path', ''), getattr(self, 'grp_singers_list', self))
            card.delete_clicked.connect(self.on_delete_singer)
            card.color_changed.connect(self.on_singer_color_changed)
            card.image_changed.connect(self.on_singer_image_changed)
            card.name_changed.connect(self.on_singer_name_changed)
            self.singer_cards.append(card)
            self.singers_cards_layout.addWidget(card)

    def on_singer_name_changed(self, old_name: str, new_name: str):
        for s in self.custom_singers:
            if s['name'] == old_name:
                s['name'] = new_name
                break
        self.populate_matrix_checkboxes()
        self.emit_change()

    def populate_matrix_checkboxes(self):
        for i in reversed(range(self.matrix_layout.count())): 
            w = self.matrix_layout.itemAt(i).widget()
            if w: w.deleteLater()
        self.matrix_checkboxes.clear()

        # Add checkbox for each custom singer
        for idx, s in enumerate(self.custom_singers):
            row = idx // 2
            col = idx % 2
            chk = QCheckBox(f"👤 {s['name']}")
            chk.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {s.get('color', '#334155')};")
            chk.stateChanged.connect(lambda state, s_idx=idx: self.on_matrix_checkbox_toggled(s_idx, state))
            self.matrix_checkboxes.append(chk)
            self.matrix_layout.addWidget(chk, row, col)

        # Add explicit BOTH (Song Ca / Cả hai) checkbox
        both_idx = len(self.custom_singers)
        row = both_idx // 2
        col = both_idx % 2
        chk_both = QCheckBox("👥 CẢ HAI (BOTH)")
        chk_both.setStyleSheet("font-size: 10px; font-weight: 800; color: #f59e0b;")
        chk_both.stateChanged.connect(lambda state, s_idx=both_idx: self.on_matrix_checkbox_toggled(s_idx, state))
        self.matrix_checkboxes.append(chk_both)
        self.matrix_layout.addWidget(chk_both, row, col)

        self.update_line_assign_header()
        self.sync_matrix_with_selected_line()

    def update_line_assign_header(self):
        if not hasattr(self, 'line_assign_header_layout'):
            return
        for i in reversed(range(self.line_assign_header_layout.count())):
            w = self.line_assign_header_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        lbl_title = QLabel("📝 Lời bài hát (Lyric Line)")
        lbl_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748b;")
        self.line_assign_header_layout.addWidget(lbl_title, stretch=1)

        for idx, s in enumerate(self.custom_singers):
            s_name = s.get('name', f'Ca sĩ {idx+1}')
            col = s.get('color', '#3b82f6')
            tag = s.get('avatar') or s_name[:2].upper()
            lbl_s = QLabel(tag)
            lbl_s.setFixedWidth(24)
            lbl_s.setAlignment(Qt.AlignCenter)
            lbl_s.setToolTip(f"Cột Ca sĩ {idx+1}: {s_name}")
            lbl_s.setStyleSheet(f"background: {col}18; color: {col}; border: 1px solid {col}60; border-radius: 3px; font-size: 9px; font-weight: 800; padding: 2px 0px;")
            self.line_assign_header_layout.addWidget(lbl_s)

        lbl_both = QLabel("👥")
        lbl_both.setFixedWidth(24)
        lbl_both.setAlignment(Qt.AlignCenter)
        lbl_both.setToolTip("Cột Cả hai / Song ca (Both / All)")
        lbl_both.setStyleSheet("background: #fef3c7; color: #b45309; border: 1px solid #fcd34d; border-radius: 3px; font-size: 9px; font-weight: 800; padding: 2px 0px;")
        self.line_assign_header_layout.addWidget(lbl_both)

    def sync_matrix_with_selected_line(self):
        if not hasattr(self, 'selected_line_idx') or self.selected_line_idx >= len(self.lyric_lines_cache):
            return
        line = self.lyric_lines_cache[self.selected_line_idx]
        cur_role = getattr(line, 'singer', 'both')
        for idx, chk in enumerate(self.matrix_checkboxes):
            chk.blockSignals(True)
            if idx == len(self.custom_singers):
                chk.setChecked(cur_role in ('both', 'all'))
            elif idx < len(self.custom_singers):
                s = self.custom_singers[idx]
                s_role = s.get('role', 'female' if idx == 0 else ('male' if idx == 1 else s.get('name', f'singer_{idx}')))
                is_match = (cur_role == s_role or cur_role == s.get('name') or (cur_role == 'female' and idx == 0) or (cur_role == 'male' and idx == 1))
                chk.setChecked(is_match and cur_role not in ('both', 'all'))
            chk.blockSignals(False)

    def on_matrix_checkbox_toggled(self, singer_idx: int, state: int):
        if state != Qt.Checked:
            return
        if self.selected_line_idx < len(self.lyric_lines_cache):
            for idx, checkbox in enumerate(self.matrix_checkboxes):
                if idx != singer_idx:
                    checkbox.blockSignals(True)
                    checkbox.setChecked(False)
                    checkbox.blockSignals(False)
            
            if singer_idx == len(self.custom_singers):
                assigned_role = "both"
            elif singer_idx == 0:
                assigned_role = self.custom_singers[0].get('role', 'female')
            elif singer_idx == 1:
                assigned_role = self.custom_singers[1].get('role', 'male')
            else:
                assigned_role = self.custom_singers[singer_idx].get('role') or self.custom_singers[singer_idx].get('name') or f"singer_{singer_idx}"
            
            self.lyric_lines_cache[self.selected_line_idx].singer = assigned_role
            if self.selected_line_idx < len(self.role_row_widgets):
                self.role_row_widgets[self.selected_line_idx].set_singer(assigned_role)
            self.singer_roles_updated.emit(self.lyric_lines_cache)
            self.emit_change()

    def on_add_singer(self):
        name, ok = QInputDialog.getText(self, "Add Singer", "Nhập tên ca sĩ mới:")
        if ok and name.strip():
            img_path, _ = QFileDialog.getOpenFileName(
                self, 
                f"Chọn ảnh chân dung / mặt cho ca sĩ '{name.strip()}' (Tùy chọn)", 
                "", 
                "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)"
            )
            palette = ["#f59e0b", "#10b981", "#8b5cf6", "#06b6d4", "#ec4899", "#3b82f6"]
            chosen_color = palette[len(self.custom_singers) % len(palette)]
            self.custom_singers.append({
                "name": name.strip(), 
                "role": f"singer_{len(self.custom_singers)}",
                "color": chosen_color, 
                "avatar": name.strip()[:1].upper() or "👤", 
                "image_path": img_path or ""
            })
            self.populate_singers_list()
            self.populate_matrix_checkboxes()
            self.set_lyric_lines(self.lyric_lines_cache)
            self.emit_change()

    def on_delete_singer(self, name: str):
        self.custom_singers = [s for s in self.custom_singers if s['name'] != name]
        self.populate_singers_list()
        self.populate_matrix_checkboxes()
        self.set_lyric_lines(self.lyric_lines_cache)
        self.emit_change()

    def on_singer_color_changed(self, name: str, col: QColor):
        for s in self.custom_singers:
            if s['name'] == name:
                s['color'] = col.name()
        self.update_line_assign_header()
        for w in self.role_row_widgets:
            w.update_row_appearance()
        self.emit_change()

    def on_singer_image_changed(self, name: str, img_path: str):
        for s in self.custom_singers:
            if s['name'] == name:
                s['image_path'] = img_path
        self.update_line_assign_header()
        self.emit_change()

    def set_display_mode(self, mode: str, keep_template_variant: bool = False):
        self.display_mode = mode
        if not keep_template_variant:
            # If user explicitly chooses a Style Mode (ROW, SINGLE, BUILD, COLOR CODED, KARAOKE),
            # clear stage-locking template variants so canvas immediately switches to the chosen style!
            if getattr(self, 'template_variant', '') in {
                "multi_song_album", "ambient_album_player", "walters_lyric_queue",
                "ksector_2000s_editorial", "falling_u_douyin_dj", "eminem_rap_hiphop_album",
                "tiki_tiki"
            }:
                self.template_variant = ""
        # Sync the button group visual checked state
        if hasattr(self, 'disp_group'):
            for btn in self.disp_group.buttons():
                if btn.text() == mode:
                    btn.setChecked(True)
                    break
        self.update_mode_visibility()
        self.emit_change()

    def update_mode_visibility(self):
        is_color_coded = (self.display_mode == "COLOR CODED")
        is_karaoke = (self.display_mode == "KARAOKE")
        is_album_template = getattr(self, 'template_variant', '') in {"multi_song_album", "ambient_album_player", "eminem_rap_hiphop_album"}
        self.grp_singers_list.setVisible(is_color_coded)
        self.grp_line_assign.setVisible(is_color_coded)
        self.grp_karaoke_controls.setVisible(is_karaoke)
        if hasattr(self, 'grp_album_tracks_meta'):
            self.grp_album_tracks_meta.setVisible(is_album_template)

    def set_karaoke_style(self, style: str):
        self.layout_mode = style
        self.btn_left_right.setChecked(style == "left_right")
        self.btn_center.setChecked(style == "center")
        self.emit_change()

    def pick_text_color(self):
        col = QColorDialog.getColor(self.fill_color, self, "Select Text Color")
        if col.isValid():
            self.fill_color = col
            self.btn_text_color.setStyleSheet(f"background: {col.name()}; border: 1px solid #cbd5e1; border-radius: 4px;")
            self.emit_change()

    def on_font_size_changed(self, val):
        self.lbl_size_title.setText(f"Font Size ({val}px)")
        self.emit_change()

    def apply_theme_preset(self, preset_name: str):
        if preset_name == "golden":
            self.template_variant = ""
            self.set_display_mode("COLOR CODED", keep_template_variant=True)
            self.combo_font.setCurrentText("Playwrite IS")
            self.combo_weight.setCurrentText("400 Thường")
            self.slider_font_size.setValue(38)
            self.fill_color = QColor("#f59e0b")
            self.base_text_color = QColor("#ffffff")
            self.btn_text_color.setStyleSheet(f"background: {self.fill_color.name()}; border: 1px solid #cbd5e1; border-radius: 4px;")
        elif preset_name == "cyberpunk":
            self.template_variant = ""
            self.set_display_mode("KARAOKE", keep_template_variant=True)
            self.combo_font.setCurrentText("Montserrat")
            self.combo_weight.setCurrentText("900 Cực Đậm")
            self.slider_font_size.setValue(56)
            self.fill_color = QColor("#00d2ff")
            self.male_color = QColor("#0026ff")
            self.female_color = QColor("#ff0033")
            self.both_color = QColor("#ff007f")
            self.btn_text_color.setStyleSheet(f"background: {self.fill_color.name()}; border: 1px solid #cbd5e1; border-radius: 4px;")
        elif preset_name == "sakura":
            self.template_variant = ""
            self.set_display_mode("KARAOKE", keep_template_variant=True)
            self.combo_font.setCurrentText("Playwrite IS")
            self.combo_weight.setCurrentText("600 SemiBold")
            self.slider_font_size.setValue(44)
            self.fill_color = QColor("#ec4899")
            self.female_color = QColor("#ec4899")
            self.both_color = QColor("#f43f5e")
            self.btn_text_color.setStyleSheet(f"background: {self.fill_color.name()}; border: 1px solid #cbd5e1; border-radius: 4px;")
        elif preset_name == "noir":
            self.template_variant = ""
            self.set_display_mode("SINGLE", keep_template_variant=True)
            self.combo_font.setCurrentText("Inter")
            self.combo_weight.setCurrentText("700 Bold")
            self.slider_font_size.setValue(48)
            self.fill_color = QColor("#ffffff")
            self.btn_text_color.setStyleSheet(f"background: {self.fill_color.name()}; border: 1px solid #cbd5e1; border-radius: 4px;")
        elif preset_name == "tiki_tiki":
            self.template_variant = "tiki_tiki"
            self.set_display_mode("COLOR CODED", keep_template_variant=True)
            self.combo_font.setCurrentText("Montserrat")
            self.combo_weight.setCurrentText("900 Cực Đậm")
            self.slider_font_size.setValue(44)
            self.combo_motion.setCurrentIndex(0)
            self.custom_singers = [
                {"name": "SUZANA", "role": "female", "color": "#b50b56", "avatar": "S", "image_path": ""},
                {"name": "VANNDA", "role": "male", "color": "#a9470b", "avatar": "V", "image_path": ""}
            ]
            self.populate_singers_list()
            self.populate_matrix_checkboxes()
        elif preset_name == "multi_song_album":
            self.template_variant = "multi_song_album"
            self.set_display_mode("SINGLE", keep_template_variant=True)
            self.combo_font.setCurrentText("Montserrat")
            self.combo_weight.setCurrentText("700 Bold")
            self.slider_font_size.setValue(38)
        self.emit_change()

    def set_lyric_lines(self, lines: List[LyricLine]):
        self.lyric_lines_cache = lines
        
        for w in self.role_row_widgets:
            w.deleteLater()
        self.role_row_widgets = []

        for i in reversed(range(self.lines_preview_layout.count())): 
            w = self.lines_preview_layout.itemAt(i).widget()
            if w: w.deleteLater()

        for idx, line in enumerate(lines):
            singer = getattr(line, 'singer', 'both')
            parent_widget = getattr(self, 'grp_line_assign', self)
            row_w = SingerRoleRowWidget(idx, line.full_text, singer, self.custom_singers, parent_widget)
            row_w.role_changed.connect(self.on_role_row_changed)
            row_w.row_clicked.connect(self.on_line_row_clicked)
            self.role_row_widgets.append(row_w)
            self.lines_preview_layout.addWidget(row_w)

        self.update_line_assign_header()
        if self.role_row_widgets:
            self.role_row_widgets[0].set_selected(True)
            self.sync_matrix_with_selected_line()

    def on_line_row_clicked(self, line_idx: int):
        self.selected_line_idx = line_idx
        for idx, w in enumerate(self.role_row_widgets):
            w.set_selected(idx == line_idx)
        self.sync_matrix_with_selected_line()
        if line_idx < len(self.lyric_lines_cache):
            line = self.lyric_lines_cache[line_idx]
            self.line_seek_requested.emit(line.line_start)

    def on_role_row_changed(self, line_idx: int, singer: str):
        if line_idx < len(self.lyric_lines_cache):
            self.lyric_lines_cache[line_idx].singer = singer
            if line_idx == getattr(self, 'selected_line_idx', 0):
                self.sync_matrix_with_selected_line()
            self.singer_roles_updated.emit(self.lyric_lines_cache)
            self.emit_change()

    def reset_all_roles(self):
        for line in self.lyric_lines_cache:
            line.singer = "both"
        for w in self.role_row_widgets:
            w.set_singer("both")
        self.singer_roles_updated.emit(self.lyric_lines_cache)
        self.emit_change()

    def apply_detected_roles(self, roles: list):
        if not self.lyric_lines_cache:
            return
        for idx, role in enumerate(roles):
            if idx < len(self.lyric_lines_cache):
                self.lyric_lines_cache[idx].singer = role
        for idx, w in enumerate(self.role_row_widgets):
            if idx < len(roles):
                w.set_singer(roles[idx])
        self.singer_roles_updated.emit(self.lyric_lines_cache)
        self.emit_change()
    def set_text_alignment(self, align: str):
        self.text_alignment = align
        self.emit_change()

    def on_stroke_changed(self, val):
        self.lbl_stroke_title.setText(f"Độ dày viền chữ ({val}px):")
        self.emit_change()

    def on_metadata_text_changed(self):
        self.track_title = self.txt_track_title.text().strip()
        self.track_artist = self.txt_track_artist.text().strip()
        self.emit_change(track_content_changed=True)

    def choose_album_cover(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh bìa Album", "", "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if path and os.path.exists(path):
            self.album_cover_path = path
            self.btn_album_cover.setText(f"📷 {os.path.basename(path)[:15]}...")
            self.emit_change()

    def choose_track_cover(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Track Image", "", "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if path and os.path.exists(path):
            self.track_cover_path = path
            self.btn_track_cover.setText(f"📷 {os.path.basename(path)[:18]}...")
            self.emit_change()

    def on_album_metadata_changed(self):
        self.album_title = self.txt_album_title.text().strip() or "My Album"
        self.album_tracks = [item.strip() for item in self.txt_album_tracks.text().split(',') if item.strip()]
        self.emit_change(album_content_changed=True)

    def emit_change(self, track_content_changed=False, album_content_changed=False):
        cfg = {
            'display_mode': self.display_mode,
            'template_variant': getattr(self, 'template_variant', ''),
            'track_title': self.txt_track_title.text().strip() if hasattr(self, 'txt_track_title') else getattr(self, 'track_title', 'Song Title'),
            'track_artist': self.txt_track_artist.text().strip() if hasattr(self, 'txt_track_artist') else getattr(self, 'track_artist', 'Artist'),
            'album_cover_path': getattr(self, 'album_cover_path', ''),
            'album_title': self.txt_album_title.text().strip() if hasattr(self, 'txt_album_title') and self.txt_album_title.text().strip() else getattr(self, 'album_title', 'My Album'),
            'album_tracks': [item.strip() for item in self.txt_album_tracks.text().split(',') if item.strip()] if hasattr(self, 'txt_album_tracks') else list(getattr(self, 'album_tracks', []) or []),
            'track_cover_path': getattr(self, 'track_cover_path', ''),
            'portrait_focus_y': getattr(self, 'portrait_focus_y', 25),
            'uppercase_lyrics': getattr(self, 'uppercase_lyrics', False),
            'motion_effect': self.combo_motion.currentText() if hasattr(self, 'combo_motion') else "Pop & Bounce",
            'font_family': self.combo_font.currentText(),
            'font_weight': self.combo_weight.currentText(),
            'font_size': self.slider_font_size.value(),
            'text_alignment': getattr(self, 'text_alignment', 'center'),
            'is_bold': "Đậm" in self.combo_weight.currentText() or "Bold" in self.combo_weight.currentText(),
            'is_italic': False,
            'layout_mode': self.layout_mode,
            'fill_mode': self.fill_mode,
            'singer_mode': self.singer_mode,
            'male_color': self.male_color.name(),
            'female_color': self.female_color.name(),
            'both_color': self.both_color.name(),
            'base_color': self.base_text_color.name(),
            'fill_color': self.fill_color.name(),
            'custom_singers': self.custom_singers,
            'pos_y_top': float(self.slider_pos_y.value() - 8),
            'pos_y_bottom': float(self.slider_pos_y.value() + 4),
            'stroke_width': self.slider_stroke.value() if hasattr(self, 'slider_stroke') else 4
        }
        cfg['_track_content_changed'] = bool(track_content_changed)
        cfg['_album_content_changed'] = bool(album_content_changed)
        self.style_changed.emit(cfg)
