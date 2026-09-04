"""
Lylis Karaoke Studio - Master Window Controller matching exact Reference Layout
Matches all 5 Reference Screenshots:
- Top Bar: MEDIA | LỜI BÀI HÁT | GIAO DIỆN | VẬT THỂ | HIỆU ỨNG | CHUYỂN CẢNH
- Song Ca Role Assignments synced between StyleTab, PreviewWidget, and Timeline
- Custom Object Creation & Right-Side Text Properties Inspector Panel (Screenshot 4)
- Transitions Tab with Fade Position Modal (Screenshot 5)
"""
import copy
import os
import random
import uuid
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QStackedWidget, QSlider, QFrame, QSplitter, QMessageBox, 
    QButtonGroup, QShortcut, QInputDialog, QFileDialog, QComboBox, QStyle
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QColor, QKeySequence, QPixmap, QIcon

from core.project_model import ProjectModel
from core.undo_manager import UndoRedoManager
from core.audio_engine import AudioEngine
from core.lrc_engine import LrcEngine
from core.auto_editor import prepare_auto_edit, detect_beat_times
from core.sample_data import ensure_sample_assets, SAMPLE_LRC_VIETNAMESE
from gui.preview_widget import PreviewWidget
from gui.timeline_widget import TimelineWidget
from gui.inspector_panel import InspectorPanel
from gui.tabs.media_tab import MediaTab
from gui.tabs.lyrics_tab import LyricsTab
from gui.tabs.style_tab import StyleTab
from gui.tabs.elements_tab import ElementsTab
from gui.tabs.effects_tab import EffectsTab
from gui.tabs.transitions_tab import TransitionsTab
from gui.tabs.templates_tab import TemplatesTab
from gui.tabs.templates_tab import TEMPLATES_DATA
from gui.tap_sync_dialog import TapSyncDialog
from gui.export_dialog import ExportDialog
from gui.style_theme import DARK_THEME_QSS

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lylis - Online Lyric Video & Karaoke Editor")
        self.resize(1620, 980)
        self.setMinimumSize(1180, 760)
        self.setStyleSheet(DARK_THEME_QSS)

        # Set Window Icon
        from core.paths import get_asset_path
        icon_path = get_asset_path("app_icon.ico")
        if not os.path.exists(icon_path):
            icon_path = get_asset_path("app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Core Engines
        self.project = ProjectModel()
        self.undo_manager = UndoRedoManager(max_depth=50)
        self.audio_engine = AudioEngine()
        self.current_lrc_lines = []
        self.album_state = {
            'id': 'album_default', 'title': 'My Album', 'artist': 'Album Artist',
            'cover': '', 'tracks': [], 'activeTrackId': None, 'selectedTrackId': None,
        }
        self._last_applied_speed = 1.0
        self._restoring_state = False
        self._asset_panel_width = 340
        self._inspector_panel_width = 300
        self._preview_focus_mode = False
        self._focus_visibility = {}
        self.playback_mode = 'once'
        self._audio_was_playing = False
        self.audio_effect_timer = QTimer(self)
        self.audio_effect_timer.setSingleShot(True)
        self.audio_effect_timer.setInterval(350)
        self.audio_effect_timer.timeout.connect(self.apply_audio_settings)
        self.sample_bg_path, self.sample_audio_path = ensure_sample_assets()

        self.setup_ui()
        self.setup_shortcuts()
        self.load_initial_demo()

        # 60 FPS Main Render Loop Timer
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self.on_render_tick)
        self.render_timer.start(16)

        # 30-Second Background Auto-Save Timer
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.perform_autosave)
        self.autosave_timer.start(30000)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Z"), self, self.on_undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self.on_redo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self.on_redo)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_project)
        QShortcut(QKeySequence("Ctrl+O"), self, self.open_project)
        QShortcut(QKeySequence("Ctrl+E"), self, self.auto_edit_project)
        QShortcut(QKeySequence(Qt.Key_Space), self, self.toggle_playback)
        QShortcut(QKeySequence("Ctrl+B"), self, self.timeline_widget.split_line)
        QShortcut(QKeySequence("S"), self, self.timeline_widget.split_line)
        QShortcut(QKeySequence("Ctrl+D"), self, self.timeline_widget.duplicate_line)
        QShortcut(QKeySequence("Ctrl+C"), self, self.timeline_widget.copy_lines)
        QShortcut(QKeySequence("Ctrl+V"), self, self.timeline_widget.paste_lines)
        QShortcut(QKeySequence("Shift+Delete"), self, self.timeline_widget.ripple_delete_lines)
        QShortcut(QKeySequence(Qt.Key_Left), self, lambda: self.seek_relative(-1.0 / 30.0))
        QShortcut(QKeySequence(Qt.Key_Right), self, lambda: self.seek_relative(1.0 / 30.0))
        QShortcut(QKeySequence("Shift+Left"), self, lambda: self.seek_relative(-5.0))
        QShortcut(QKeySequence("Shift+Right"), self, lambda: self.seek_relative(5.0))
        QShortcut(QKeySequence("F11"), self, self.toggle_preview_focus)
        QShortcut(QKeySequence("Escape"), self, self.exit_preview_focus)
        QShortcut(QKeySequence("Delete"), self, self.delete_active_selection)
        QShortcut(QKeySequence("Backspace"), self, self.delete_active_selection)
        QShortcut(QKeySequence("F1"), self, self.open_license_dialog)

    def setup_ui(self):
        main_widget = QWidget()
        main_widget.setObjectName("EditorRoot")
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # =====================================================================
        # 1. TOP HEADER BAR (Matching Lylis Studio Reference)
        # [‹  MEDIA   LỜI BÀI HÁT   GIAO DIỆN   VẬT THỂ   HIỆU ỨNG   CHUYỂN CẢNH   🚀 Xuất Video]
        # =====================================================================
        header_bar = QWidget()
        self.header_bar = header_bar
        header_bar.setObjectName("TopToolbar")
        header_bar.setFixedHeight(50)
        header_bar.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-bottom: 1px solid #e2e8f0;
            }
        """)
        h_layout = QHBoxLayout(header_bar)
        h_layout.setContentsMargins(14, 0, 14, 0)
        h_layout.setSpacing(12)

        # Left Back Arrow `<`
        lbl_back = QLabel("‹")
        lbl_back.setStyleSheet("font-size: 22px; font-weight: bold; color: #64748b; margin-right: 4px;")
        h_layout.addWidget(lbl_back)

        self.btn_toggle_assets = QPushButton("☰")
        self.btn_toggle_assets.setFixedSize(30, 28)
        self.btn_toggle_assets.setToolTip("Show or hide the asset library")
        self.btn_toggle_assets.clicked.connect(self.toggle_asset_panel)
        h_layout.addWidget(self.btn_toggle_assets)

        self.btn_toggle_inspector = QPushButton("⚙")
        self.btn_toggle_inspector.setFixedSize(30, 28)
        self.btn_toggle_inspector.setToolTip("Show or hide the properties inspector")
        self.btn_toggle_inspector.clicked.connect(self.toggle_inspector_panel)
        h_layout.addWidget(self.btn_toggle_inspector)

        # Top Navigation Action Buttons
        self.nav_buttons = []

        self.btn_nav_media = QPushButton("📁 MEDIA")
        self.btn_nav_media.setCheckable(True)
        self.btn_nav_media.clicked.connect(lambda: self.switch_tab(0))
        h_layout.addWidget(self.btn_nav_media)
        self.nav_buttons.append((0, self.btn_nav_media))

        self.btn_nav_lyrics = QPushButton("📝 LỜI BÀI HÁT")
        self.btn_nav_lyrics.setCheckable(True)
        self.btn_nav_lyrics.clicked.connect(lambda: self.switch_tab(1))
        h_layout.addWidget(self.btn_nav_lyrics)
        self.nav_buttons.append((1, self.btn_nav_lyrics))

        self.btn_nav_style = QPushButton("🎨 GIAO DIỆN")
        self.btn_nav_style.setCheckable(True)
        self.btn_nav_style.setChecked(True)
        self.btn_nav_style.clicked.connect(lambda: self.switch_tab(2))
        h_layout.addWidget(self.btn_nav_style)
        self.nav_buttons.append((2, self.btn_nav_style))

        self.btn_nav_objects = QPushButton("✨ VẬT THỂ")
        self.btn_nav_objects.setCheckable(True)
        self.btn_nav_objects.clicked.connect(lambda: self.switch_tab(3))
        h_layout.addWidget(self.btn_nav_objects)
        self.nav_buttons.append((3, self.btn_nav_objects))

        self.btn_nav_effects = QPushButton("🎬 HIỆU ỨNG")
        self.btn_nav_effects.setCheckable(True)
        self.btn_nav_effects.clicked.connect(lambda: self.switch_tab(4))
        h_layout.addWidget(self.btn_nav_effects)
        self.nav_buttons.append((4, self.btn_nav_effects))

        self.btn_nav_transitions = QPushButton("🔄 CHUYỂN CẢNH")
        self.btn_nav_transitions.setCheckable(True)
        self.btn_nav_transitions.clicked.connect(lambda: self.switch_tab(5))
        h_layout.addWidget(self.btn_nav_transitions)
        self.nav_buttons.append((5, self.btn_nav_transitions))

        self.btn_nav_templates = QPushButton("🌟 MẪU VIDEO")
        self.btn_nav_templates.setCheckable(True)
        self.btn_nav_templates.clicked.connect(lambda: self.switch_tab(6))
        h_layout.addWidget(self.btn_nav_templates)
        self.nav_buttons.append((6, self.btn_nav_templates))

        self.btn_open_project = QPushButton("Mở")
        self.btn_open_project.setToolTip("Open project (Ctrl+O)")
        self.btn_open_project.clicked.connect(self.open_project)
        h_layout.addWidget(self.btn_open_project)

        self.btn_save_project = QPushButton("Lưu")
        self.btn_save_project.setToolTip("Save project (Ctrl+S)")
        self.btn_save_project.clicked.connect(self.save_project)
        h_layout.addWidget(self.btn_save_project)

        self.lbl_save_status = QLabel("Saved")
        self.lbl_save_status.setObjectName("SaveStatus")
        self.lbl_save_status.setToolTip("Project save state")
        h_layout.addWidget(self.lbl_save_status)

        self.btn_clear_cache = QPushButton("🧹 Dọn Cache")
        self.btn_clear_cache.setToolTip("Tự động dọn dẹp bộ nhớ đệm cache và tệp tạm")
        self.btn_clear_cache.clicked.connect(self.on_clear_cache_clicked)
        h_layout.addWidget(self.btn_clear_cache)

        self.btn_license = QPushButton("📜 Bản quyền")
        self.btn_license.setToolTip("Xem giấy phép & bản quyền thiết kế Lylis Studio (F1)")
        self.btn_license.clicked.connect(self.open_license_dialog)
        h_layout.addWidget(self.btn_license)

        # Right Export MP4 Button
        self.btn_auto_edit = QPushButton("✨ AUTO EDIT")
        self.btn_auto_edit.setToolTip("Tự động căn lời theo nhịp, chọn kiểu dựng và thêm chuyển cảnh (Ctrl+E)")
        self.btn_auto_edit.setStyleSheet("""
            QPushButton {
                background: #0f766e;
                color: #ffffff;
                font-weight: 800;
                font-size: 11px;
                border: none;
                border-radius: 6px;
                padding: 7px 12px;
            }
            QPushButton:hover { background: #0d9488; }
        """)
        self.btn_auto_edit.clicked.connect(self.auto_edit_project)
        h_layout.addWidget(self.btn_auto_edit)

        # Right Export MP4 Button
        self.btn_export = QPushButton("🚀 Xuất Video")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff2d55, stop:1 #ff5277);
                color: #ffffff;
                font-weight: 800;
                font-size: 11px;
                border: none;
                border-radius: 6px;
                padding: 7px 18px;
            }
            QPushButton:hover { background: #ff476d; }
        """)
        self.btn_export.clicked.connect(self.open_export_dialog)
        h_layout.addWidget(self.btn_export)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["Tiếng Việt", "English"])
        self.language_combo.setFixedWidth(92)
        self.language_combo.setToolTip("Interface language")
        self.language_combo.currentIndexChanged.connect(self.set_language)
        h_layout.addWidget(self.language_combo)

        main_layout.addWidget(header_bar)

        # =====================================================================
        # 2. MAIN HORIZONTAL SPLITTER
        # Left Panel vs Right Workspace + Inspector
        # =====================================================================
        splitter_main = QSplitter(Qt.Horizontal)
        self.splitter_main = splitter_main
        splitter_main.setStyleSheet("QSplitter::handle { background: #cbd5e1; } QSplitter::handle:hover { background: #ff2d55; }")
        splitter_main.setHandleWidth(1)

        # LEFT PANEL
        left_panel = QWidget()
        self.left_panel = left_panel
        left_panel.setObjectName("LeftAssetPanel")
        left_panel.setMinimumWidth(320)
        left_panel.setMaximumWidth(420)
        left_panel.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e2e8f0;")
        lp_layout = QVBoxLayout(left_panel)
        lp_layout.setContentsMargins(14, 12, 14, 12)
        lp_layout.setSpacing(10)

        # "< Video của tôi" & "Untitled Project ✎"
        lbl_my_vids = QLabel("‹ Video của tôi")
        lbl_my_vids.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600;")
        lp_layout.addWidget(lbl_my_vids)

        proj_row = QHBoxLayout()
        self.lbl_proj_title = QLabel("Untitled Project")
        self.lbl_proj_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #0f172a;")
        proj_row.addWidget(self.lbl_proj_title)
        
        btn_edit_title = QPushButton("✎")
        btn_edit_title.setFixedSize(20, 20)
        btn_edit_title.setStyleSheet("border: none; color: #94a3b8; font-size: 13px; font-weight: bold;")
        btn_edit_title.setToolTip("Đổi tên dự án")
        btn_edit_title.clicked.connect(self.rename_project)
        proj_row.addWidget(btn_edit_title)
        proj_row.addStretch()
        lp_layout.addLayout(proj_row)

        # 7 Sub Tabs Widget (Media | Lyrics | Giao diện | Vật thể | Hiệu ứng | Chuyển cảnh | Mẫu Template)
        self.tab_widget = QStackedWidget()

        self.media_tab = MediaTab()
        self._register_media_assets(self.media_tab.media_assets())
        self.lyrics_tab = LyricsTab()
        self.style_tab = StyleTab()
        self.elements_tab = ElementsTab()
        self.effects_tab = EffectsTab()
        self.transitions_tab = TransitionsTab()
        self.templates_tab = TemplatesTab()

        self.tab_widget.addWidget(self.media_tab)
        self.tab_widget.addWidget(self.lyrics_tab)
        self.tab_widget.addWidget(self.style_tab)
        self.tab_widget.addWidget(self.elements_tab)
        self.tab_widget.addWidget(self.effects_tab)
        self.tab_widget.addWidget(self.transitions_tab)
        self.tab_widget.addWidget(self.templates_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        lp_layout.addWidget(self.tab_widget)
        splitter_main.addWidget(left_panel)

        # RIGHT WORKSPACE (Canvas + Timeline + Properties Inspector)
        right_workspace = QWidget()
        right_workspace.setObjectName("RightWorkspace")
        rw_layout = QVBoxLayout(right_workspace)
        rw_layout.setContentsMargins(0, 0, 0, 0)
        rw_layout.setSpacing(0)

        splitter_right = QSplitter(Qt.Vertical)
        self.splitter_right = splitter_right
        splitter_right.setHandleWidth(1)
        splitter_right.setStyleSheet("QSplitter::handle { background: #cbd5e1; } QSplitter::handle:hover { background: #ff2d55; }")

        # Canvas & Inspector Area
        canvas_inspector_container = QWidget()
        canvas_inspector_container.setObjectName("CanvasInspectorContainer")
        canvas_inspector_container.setStyleSheet("background-color: #f1f3f9;")
        cic_layout = QHBoxLayout(canvas_inspector_container)
        cic_layout.setContentsMargins(0, 0, 0, 0)
        cic_layout.setSpacing(0)

        # Canvas Box
        canvas_container = QWidget()
        self.canvas_container = canvas_container
        canvas_container.setObjectName("PreviewWorkspace")
        cc_layout = QVBoxLayout(canvas_container)
        cc_layout.setContentsMargins(14, 10, 14, 10)
        cc_layout.setSpacing(8)

        # Floating Aspect Ratio Selector
        aspect_top_box = QHBoxLayout()
        aspect_top_box.addStretch()

        aspect_pill_card = QFrame()
        aspect_pill_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 2px 4px;
            }
        """)
        ap_layout = QHBoxLayout(aspect_pill_card)
        ap_layout.setContentsMargins(4, 2, 4, 2)
        ap_layout.setSpacing(4)

        self.aspect_group = QButtonGroup(self)

        self.btn_aspect_916 = QPushButton("📱 9:16")
        self.btn_aspect_916.setCheckable(True)
        self.btn_aspect_916.setStyleSheet("""
            QPushButton { background: transparent; color: #64748b; border: none; border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 11px; }
            QPushButton:checked { background: #ff2d55; color: #ffffff; font-weight: 700; }
        """)
        self.aspect_group.addButton(self.btn_aspect_916)
        ap_layout.addWidget(self.btn_aspect_916)

        self.btn_aspect_169 = QPushButton("🖥️ 16:9")
        self.btn_aspect_169.setCheckable(True)
        self.btn_aspect_169.setChecked(True)
        self.btn_aspect_169.setStyleSheet("""
            QPushButton { background: transparent; color: #64748b; border: none; border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 11px; }
            QPushButton:checked { background: #ff2d55; color: #ffffff; font-weight: 700; }
        """)
        self.aspect_group.addButton(self.btn_aspect_169)
        ap_layout.addWidget(self.btn_aspect_169)

        self.btn_aspect_11 = QPushButton("⏹ 1:1")
        self.btn_aspect_11.setCheckable(True)
        self.btn_aspect_11.setStyleSheet("""
            QPushButton { background: transparent; color: #64748b; border: none; border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 11px; }
            QPushButton:checked { background: #ff2d55; color: #ffffff; font-weight: 700; }
        """)
        self.aspect_group.addButton(self.btn_aspect_11)
        ap_layout.addWidget(self.btn_aspect_11)

        self.btn_aspect_45 = QPushButton("4:5")
        self.btn_aspect_45.setCheckable(True)
        self.btn_aspect_45.setStyleSheet("""
            QPushButton { background: transparent; color: #64748b; border: none; border-radius: 5px; padding: 4px 10px; font-weight: 600; font-size: 11px; }
            QPushButton:checked { background: #ff2d55; color: #ffffff; font-weight: 700; }
        """)
        self.aspect_group.addButton(self.btn_aspect_45)
        ap_layout.addWidget(self.btn_aspect_45)

        self.btn_aspect_custom = QPushButton("Custom")
        self.btn_aspect_custom.setCheckable(True)
        self.btn_aspect_custom.setStyleSheet(self.btn_aspect_45.styleSheet())
        self.aspect_group.addButton(self.btn_aspect_custom)
        ap_layout.addWidget(self.btn_aspect_custom)

        self.btn_aspect_916.clicked.connect(lambda: self.change_aspect('9:16'))
        self.btn_aspect_169.clicked.connect(lambda: self.change_aspect('16:9'))
        self.btn_aspect_11.clicked.connect(lambda: self.change_aspect('1:1'))
        self.btn_aspect_45.clicked.connect(lambda: self.change_aspect('4:5'))
        self.btn_aspect_custom.clicked.connect(self.choose_custom_aspect)

        aspect_top_box.addWidget(aspect_pill_card)
        aspect_top_box.addStretch()
        cc_layout.addLayout(aspect_top_box)

        # Preview Widget Canvas
        self.preview_widget = PreviewWidget()
        self.preview_widget.object_selected.connect(self.on_canvas_object_selected)
        self.preview_widget.objects_changed.connect(self.sync_overlay_state)
        cc_layout.addWidget(self.preview_widget, stretch=1)

        # Transport Controls Dock under canvas
        transport_dock = QWidget()
        td_layout = QVBoxLayout(transport_dock)
        td_layout.setContentsMargins(20, 0, 20, 4)
        td_layout.setSpacing(4)

        # Scrubber Row: 01:19 ━━━━━━━━O━━━━━━━━ 01:57
        scrub_row = QHBoxLayout()
        self.lbl_time_cur = QLabel("00:00")
        self.lbl_time_cur.setStyleSheet("color: #64748b; font-size: 11px; font-family: Consolas; font-weight: 600;")
        scrub_row.addWidget(self.lbl_time_cur)

        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.sliderMoved.connect(self.on_seek_slider_moved)
        scrub_row.addWidget(self.seek_slider, stretch=1)

        self.lbl_time_dur = QLabel("00:42")
        self.lbl_time_dur.setStyleSheet("color: #64748b; font-size: 11px; font-family: Consolas; font-weight: 600;")
        scrub_row.addWidget(self.lbl_time_dur)
        td_layout.addLayout(scrub_row)

        # Button Controls: ▶  ↺  📥
        btn_center_box = QHBoxLayout()
        btn_center_box.addStretch()

        self.btn_play = QPushButton()
        self.btn_prev_track = QPushButton()
        self.btn_prev_track.setFixedSize(30, 30)
        self.btn_prev_track.setToolTip("Previous album track")
        self.btn_prev_track.clicked.connect(self.previous_album_track)
        btn_center_box.addWidget(self.btn_prev_track)

        self.btn_play.setFixedSize(34, 34)
        self.btn_play.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #ff2d55;
                border: 1px solid #fecdd3;
                border-radius: 17px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background: #fff1f2; }
        """)
        self.btn_play.clicked.connect(self.toggle_playback)
        btn_center_box.addWidget(self.btn_play)
        self.btn_next_track = QPushButton()
        self.btn_next_track.setFixedSize(30, 30)
        self.btn_next_track.setToolTip("Next album track")
        self.btn_next_track.clicked.connect(self.next_album_track)
        btn_center_box.addWidget(self.btn_next_track)

        self.btn_loop = QPushButton()
        self.btn_loop.setCheckable(True)
        self.btn_loop.setFixedSize(34, 34)
        self.btn_loop.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #64748b;
                border: 1px solid #e2e8f0;
                border-radius: 17px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:checked { background: #ff2d55; color: #ffffff; border-color: #ff2d55; }
        """)
        self.btn_loop.clicked.connect(self.toggle_loop)
        btn_center_box.addWidget(self.btn_loop)
        # Playback mode is the only repeat/shuffle control; remove the old
        # duplicate loop toggle from the visible transport.
        self.btn_loop.hide()

        self.combo_playback_mode = QComboBox()
        self.combo_playback_mode.addItems(["Play Once", "Repeat Track", "Repeat Album", "Shuffle"])
        self.combo_playback_mode.setToolTip("Album playback mode")
        self.combo_playback_mode.setFixedWidth(105)
        self.combo_playback_mode.currentIndexChanged.connect(self.on_playback_mode_changed)
        btn_center_box.addWidget(self.combo_playback_mode)

        self.btn_download = QPushButton("📥")
        self.btn_download.setFixedSize(34, 34)
        self.btn_download.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #64748b;
                border: 1px solid #e2e8f0;
                border-radius: 17px;
                font-size: 13px;
            }
            QPushButton:hover { color: #0f172a; border-color: #cbd5e1; }
        """)
        self.btn_download.clicked.connect(self.open_export_dialog)
        btn_center_box.addWidget(self.btn_download)
        # Reuse this existing compact slot for the single volume control.
        self.btn_download.clicked.disconnect()
        self.btn_download.clicked.connect(self.toggle_mute)
        self.btn_download.setText("")
        self.btn_download.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.btn_download.setIconSize(QSize(16, 16))
        self.btn_download.setFixedSize(28, 28)
        self.btn_download.setToolTip("Mute")

        self.combo_preview_zoom = QComboBox()
        self.combo_preview_zoom.addItems(["Fit", "25%", "50%", "75%", "100%"])
        self.combo_preview_zoom.setFixedWidth(74)
        self.combo_preview_zoom.setToolTip("Preview zoom")
        self.combo_preview_zoom.currentTextChanged.connect(self.on_preview_zoom_changed)
        btn_center_box.addWidget(self.combo_preview_zoom)

        self.btn_preview_fullscreen = QPushButton()
        self.btn_preview_fullscreen.setFixedSize(34, 34)
        self.btn_preview_fullscreen.setToolTip("Focus preview (F11, Escape to exit)")
        self.btn_preview_fullscreen.clicked.connect(self.toggle_preview_focus)
        btn_center_box.addWidget(self.btn_preview_fullscreen)

        # Use one consistent icon treatment for the transport controls.
        self.btn_prev_track.setText("")
        self.btn_prev_track.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.btn_prev_track.setIconSize(QSize(17, 17))
        self.btn_play.setText("")
        self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.btn_play.setIconSize(QSize(18, 18))
        self.btn_next_track.setText("")
        self.btn_next_track.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.btn_next_track.setIconSize(QSize(17, 17))
        self.btn_play.setFixedSize(36, 36)
        self.btn_preview_fullscreen.setText("")
        self.btn_preview_fullscreen.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        self.btn_preview_fullscreen.setIconSize(QSize(16, 16))
        self.btn_preview_fullscreen.setFixedSize(28, 28)

        btn_center_box.addStretch()
        td_layout.addLayout(btn_center_box)

        cc_layout.addWidget(transport_dock)

        # Right Inspector Panel (Screenshot 4)
        self.inspector_panel = InspectorPanel()
        self.inspector_panel.property_changed.connect(self.on_overlay_property_changed)
        self.inspector_panel.delete_requested.connect(self.delete_selected_overlay)
        self.inspector_panel.closed.connect(lambda: self.inspector_panel.setVisible(False))
        self.inspector_panel.setVisible(False)

        self.canvas_inspector_splitter = QSplitter(Qt.Horizontal)
        self.canvas_inspector_splitter.setObjectName("CanvasInspectorSplitter")
        self.canvas_inspector_splitter.setHandleWidth(1)
        self.canvas_inspector_splitter.addWidget(canvas_container)
        self.canvas_inspector_splitter.addWidget(self.inspector_panel)
        self.canvas_inspector_splitter.setStretchFactor(0, 1)
        self.canvas_inspector_splitter.setStretchFactor(1, 0)
        self.canvas_inspector_splitter.setSizes([900, self._inspector_panel_width])
        cic_layout.addWidget(self.canvas_inspector_splitter)

        splitter_right.addWidget(canvas_inspector_container)

        # =====================================================================
        # 3. BOTTOM MULTI-TRACK 7-LAYER SEQUENCER
        # =====================================================================
        timeline_container = QWidget()
        self.timeline_container = timeline_container
        timeline_container.setObjectName("TimelineContainer")
        timeline_container.setStyleSheet("background-color: #f1f3f9; border-top: 1px solid #e2e8f0;")
        timeline_container.setMinimumHeight(240)
        tc_layout = QVBoxLayout(timeline_container)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(0)

        # 7-Layer Sequencer Canvas with Full CapCut Editing Suite
        self.timeline_widget = TimelineWidget()
        tc_layout.addWidget(self.timeline_widget, stretch=1)

        splitter_right.addWidget(timeline_container)
        splitter_right.setStretchFactor(0, 6)
        splitter_right.setStretchFactor(1, 4)
        splitter_right.setSizes([560, 320])
        rw_layout.addWidget(splitter_right)

        splitter_main.addWidget(right_workspace)
        splitter_main.setSizes([340, 1280])

        main_layout.addWidget(splitter_main)

        # Connect Signals across tabs
        self.media_tab.background_changed.connect(self.on_background_loaded)
        self.media_tab.audio_changed.connect(self.on_audio_loaded)
        self.media_tab.audio_playlist_changed.connect(self.on_audio_playlist_loaded)
        self.media_tab.media_imported.connect(self._register_media_assets)
        self.media_tab.analyze_lyrics_requested.connect(self.on_analyze_lyrics_requested)
        self.media_tab.asset_add_requested.connect(self.on_media_asset_add_requested)
        self.media_tab.pitch_changed.connect(self.on_audio_setting_changed)
        self.media_tab.speed_changed.connect(self.on_audio_setting_changed)
        self.media_tab.vocal_cut_toggled.connect(self.on_audio_setting_changed)
        self.media_tab.object_template_requested.connect(lambda name: self.elements_tab.create_lower_third_object())
        self.lyrics_tab.lyrics_applied.connect(self.on_lyrics_updated)
        self.lyrics_tab.tap_sync_requested.connect(self.open_tap_sync_dialog)
        self.lyrics_tab.gemini_requested.connect(self.open_gemini_dialog)
        self.style_tab.style_changed.connect(self.on_style_changed)
        self.style_tab.singer_roles_updated.connect(self.on_singer_roles_updated)
        self.style_tab.line_seek_requested.connect(self.on_timeline_seek)
        self.style_tab.ai_gender_detect_requested.connect(self.open_gemini_dialog)
        self.elements_tab.element_created.connect(self.on_element_created)
        self.elements_tab.elements_changed.connect(self.on_elements_changed)
        self.effects_tab.effects_changed.connect(self.on_effects_changed)
        self.transitions_tab.transition_applied.connect(self.on_transition_applied)
        self.templates_tab.template_selected.connect(self.on_template_applied)
        self.templates_tab.save_template_requested.connect(self.save_current_as_template)
        self.preview_widget.album_track_selected.connect(self.on_album_track_selected)
        self.timeline_widget.time_seek_requested.connect(self.on_timeline_seek)
        self.timeline_widget.lyrics_modified.connect(self.on_timeline_lyrics_modified)
        self.timeline_widget.media_clips_modified.connect(self.on_timeline_media_clips_modified)
        self.timeline_widget.line_selected.connect(self.on_timeline_line_selected)
        self.timeline_widget.add_layer_requested.connect(self.on_add_layer_clicked)
        self.timeline_widget.media_asset_dropped.connect(self.on_media_asset_dropped)
        self.timeline_widget.media_files_dropped.connect(self.on_media_files_dropped)
        self.timeline_widget.play_pause_requested.connect(self.toggle_playback)
        self.timeline_widget.step_back_requested.connect(lambda: self.on_timeline_seek(max(0.0, self.audio_engine.get_current_time() - 0.5)))
        self.timeline_widget.step_forward_requested.connect(lambda: self.on_timeline_seek(min(self.audio_engine.duration, self.audio_engine.get_current_time() + 0.5)))

        self.update_nav_highlight(2)

        # Apply initial settings from tabs
        self.style_tab.emit_change()
        self.effects_tab.emit_change()
        # English is the complete default UI; users can switch to Vietnamese from the selector.
        self.language_combo.blockSignals(True)
        self.language_combo.setCurrentIndex(1)
        self.language_combo.blockSignals(False)
        self.set_language(1)

    def _apply_english_widget_labels(self):
        """Translate static control labels in every tab without touching project content."""
        translations = {
            "Lời bài hát": "Lyrics", "GIAO DIỆN": "STYLE", "VẬT THỂ": "OBJECTS",
            "HIỆU ỨNG": "EFFECTS", "CHUYỂN CẢNH": "TRANSITIONS", "MẪU VIDEO": "TEMPLATES",
            "Tất cả": "All", "Âm thanh": "Audio", "Hình ảnh": "Images",
            "Tìm & Thay thế": "Find & Replace", "Tùy chỉnh...": "Custom...",
            "Thêm vào Timeline": "Add to Timeline", "Nhận Diện Giọng": "Detect Voice",
            "Dịch time:": "Shift time:", "Nhập file:": "Import:", "Tải xuống:": "Export:",
            "Căn lề lời bài hát (Text Alignment)": "Lyrics Alignment",
            "Trái": "Left", "Giữa": "Center", "Phải": "Right",
            "Cỡ chữ": "Font Size", "Độ dày viền chữ": "Text Stroke Width",
            "Màu chữ chính (Text Fill)": "Main Text Color", "Đổi Ảnh Bìa Album": "Change Album Cover",
            "Tên bài hát (Track Title):": "Track Title:", "Tên ca sĩ / Nghệ sĩ (Track Artist):": "Track Artist:",
            "Vị trí hiệu ứng": "Transition Position", "ĐẦU CLIP": "CLIP START",
            "CUỐI CLIP": "CLIP END", "HỦY": "CANCEL", "XÓA VẬT THỂ NÀY": "DELETE OBJECT",
            "Thuộc tính vật thể": "Object Properties", "Tiêu đề:": "Title:", "Phụ đề / Ca sĩ:": "Subtitle / Artist:",
            "Xoay:": "Rotation:", "Trên": "Top", "Dưới": "Bottom",
            "Công cụ Âm Thanh": "Audio Tools", "Đổi Tone (Key):": "Key:", "Tốc độ phát:": "Playback Speed:",
            "Bộ lọc:": "Filter:", "Độ sáng (Brightness):": "Brightness:", "Độ tương phản (Contrast):": "Contrast:",
            "Độ bão hòa (Saturation):": "Saturation:", "Mờ nền (Background Blur):": "Background Blur:",
            "Độ tối:": "Vignette:", "Bán kính:": "Radius:", "Loại hạt:": "Particle Type:",
            "Kiểu sóng nhạc:": "Visualizer:", "Thư Viện Mẫu Video (Template Gallery)": "Video Template Library",
            "Lưu mẫu hiện tại": "Save Current Template", "Tìm mẫu template": "Search templates",
        }
        for widget in self.findChildren(QWidget):
            try:
                if hasattr(widget, "text"):
                    text = widget.text()
                elif hasattr(widget, "title"):
                    text = widget.title()
                else:
                    continue
            except (RuntimeError, TypeError):
                continue
            if text in translations:
                if hasattr(widget, "setText"):
                    widget.setText(translations[text])
                elif hasattr(widget, "setTitle"):
                    widget.setTitle(translations[text])
            elif hasattr(widget, "setPlaceholderText"):
                placeholder = widget.placeholderText()
                for source, target in translations.items():
                    if source in placeholder:
                        widget.setPlaceholderText(placeholder.replace(source, target))
                        break

    def set_language(self, index: int):
        """Switch core chrome labels without changing project content or timing."""
        english = int(index) == 1
        nav_text = (
            ["📁 MEDIA", "📝 LYRICS", "🎨 STYLE", "✨ OBJECTS", "🎬 EFFECTS", "🔄 TRANSITIONS", "🌟 TEMPLATES"]
            if english else
            ["📁 MEDIA", "📝 LỜI BÀI HÁT", "🎨 GIAO DIỆN", "✨ VẬT THỂ", "🎬 HIỆU ỨNG", "🔄 CHUYỂN CẢNH", "🌟 MẪU VIDEO"]
        )
        for button, label in zip((item[1] for item in self.nav_buttons), nav_text, strict=False):
            button.setText(label)
        self.btn_open_project.setText("Open" if english else "Mở")
        self.btn_save_project.setText("Save" if english else "Lưu")
        self.btn_clear_cache.setText("🧹 Clear Cache" if english else "🧹 Dọn Cache")
        self.btn_auto_edit.setText("✨ AUTO EDIT")
        self.btn_export.setText("🚀 Export Video" if english else "🚀 Xuất Video")
        self.timeline_widget.set_language(english)
        if english:
            self._apply_english_widget_labels()
        self.project.language = "en" if english else "vi"
        self._push_project_state()

    def on_timeline_seek(self, time_s: float):
        self.audio_engine.seek(time_s)
        self.timeline_widget.set_current_time(
            time_s,
            is_playing=self.audio_engine.is_playing,
            reveal=True,
        )
        self.preview_widget.update_playback(
            time_s,
            self.audio_engine.duration or self.project.duration,
            self.audio_engine.get_spectrum_bands(32)
        )
        if self.audio_engine.duration > 0:
            self.seek_slider.blockSignals(True)
            self.seek_slider.setValue(int((time_s / self.audio_engine.duration) * 1000))
            self.seek_slider.blockSignals(False)

    def on_timeline_line_selected(self, line_idx: int):
        if 0 <= line_idx < len(self.current_lrc_lines):
            t = self.current_lrc_lines[line_idx].line_start
            self.on_timeline_seek(t)
            self.style_tab.selected_line_idx = line_idx

    def on_add_layer_clicked(self):
        self.left_panel.setVisible(True)
        self.btn_toggle_assets.setChecked(False)
        self.splitter_main.setSizes([self._asset_panel_width, max(1, self.width() - self._asset_panel_width)])
        self.tab_widget.setCurrentWidget(self.elements_tab)
        self.update_nav_highlight(3)
        self.elements_tab.create_lower_third_object()

    def toggle_asset_panel(self):
        """Collapse or restore the reusable asset/library panel."""
        if not self.left_panel.isHidden():
            self._asset_panel_width = max(self.left_panel.width(), self.left_panel.minimumWidth())
            self.left_panel.hide()
            self.btn_toggle_assets.setChecked(True)
        else:
            self.left_panel.show()
            self.splitter_main.setSizes([self._asset_panel_width, max(1, self.width() - self._asset_panel_width)])
            self.btn_toggle_assets.setChecked(False)

    def toggle_inspector_panel(self):
        """Collapse or restore the contextual properties inspector."""
        if not self.inspector_panel.isHidden():
            self._inspector_panel_width = max(self.inspector_panel.width(), self.inspector_panel.minimumWidth())
            self.inspector_panel.hide()
            self.btn_toggle_inspector.setChecked(True)
        else:
            self.inspector_panel.show()
            available = max(1, self.canvas_inspector_splitter.width())
            self.canvas_inspector_splitter.setSizes([
                max(1, available - self._inspector_panel_width),
                self._inspector_panel_width,
            ])
            self.btn_toggle_inspector.setChecked(False)

    def toggle_preview_focus(self):
        """Show an uncluttered preview without changing editor data or splitter state."""
        if self._preview_focus_mode:
            self.exit_preview_focus()
            return
        self._focus_visibility = {
            "header": not self.header_bar.isHidden(),
            "assets": not self.left_panel.isHidden(),
            "timeline": not self.timeline_container.isHidden(),
            "inspector": not self.inspector_panel.isHidden(),
        }
        self._preview_focus_mode = True
        self.header_bar.hide()
        self.left_panel.hide()
        self.timeline_container.hide()
        self.inspector_panel.hide()

    def exit_preview_focus(self):
        if not self._preview_focus_mode:
            return
        self._preview_focus_mode = False
        self.header_bar.setVisible(self._focus_visibility.get("header", True))
        self.left_panel.setVisible(self._focus_visibility.get("assets", True))
        self.timeline_container.setVisible(self._focus_visibility.get("timeline", True))
        self.inspector_panel.setVisible(self._focus_visibility.get("inspector", False))

    def on_preview_zoom_changed(self, label: str):
        zoom = 0.0 if label == "Fit" else float(label.rstrip("%")) / 100.0
        self.preview_widget.set_preview_zoom(zoom)

    def choose_custom_aspect(self):
        previous_ratio = self.project.aspect_ratio
        ratio, accepted = QInputDialog.getText(
            self,
            "Custom aspect ratio",
            "Enter width:height (for example 21:9):",
            text=self.project.aspect_ratio if ":" in self.project.aspect_ratio else "16:9",
        )
        if accepted and self.preview_widget.is_valid_aspect_ratio(ratio):
            self.change_aspect(ratio.strip())
        else:
            self.sync_aspect_buttons(previous_ratio)

    def sync_aspect_buttons(self, ratio: str):
        """Keep aspect controls consistent with restored and custom project ratios."""
        known_buttons = {
            '9:16': self.btn_aspect_916,
            '16:9': self.btn_aspect_169,
            '1:1': self.btn_aspect_11,
            '4:5': self.btn_aspect_45,
        }
        known_buttons.get(ratio, self.btn_aspect_custom).setChecked(True)

    def on_template_applied(self, t_data: dict):
        """Applies complete template settings across style, effects, motion, and singers."""
        if not isinstance(t_data, dict):
            return False
        # Templates can come from user-edited project files; normalize untrusted values
        # before handing them to Qt widgets (QSlider.setValue requires an actual int).
        normalized = copy.deepcopy(t_data)
        try:
            normalized['font_size'] = int(float(normalized.get('font_size', 42)))
        except (TypeError, ValueError):
            normalized['font_size'] = 42
        normalized['font_size'] = max(8, min(240, normalized['font_size']))
        for key, fallback in (('vignette', 35), ('glow_radius', 10), ('brightness', 0),
                              ('contrast', 0), ('saturation', 0), ('blur', 0), ('stroke_width', 4)):
            try:
                normalized[key] = int(float(normalized.get(key, fallback)))
            except (TypeError, ValueError):
                normalized[key] = fallback
        normalized['custom_singers'] = [item for item in (normalized.get('custom_singers') or []) if isinstance(item, dict)]
        normalized_album_tracks = []
        for index, item in enumerate(normalized.get('album_tracks') or []):
            if isinstance(item, dict):
                track = copy.deepcopy(item)
                track['id'] = str(track.get('id') or f'track_{index + 1:04d}')
                track['title'] = str(track.get('title') or track.get('name') or f'Track {index + 1:02d}').strip()
                track['audioSrc'] = str(track.get('audioSrc') or '')
                normalized_album_tracks.append(track)
            else:
                title = str(item).strip()
                if title:
                    normalized_album_tracks.append(title)
        normalized['album_tracks'] = normalized_album_tracks
        t_data = normalized
        self.style_tab.template_variant = t_data.get('template_variant', '')
        # Album templates carry their own editable queue metadata.
        if 'album_tracks' in t_data:
            template_tracks = list(t_data.get('album_tracks') or [])
            self.style_tab.album_tracks = [
                item.get('title', f'Track {index + 1:02d}') if isinstance(item, dict) else str(item)
                for index, item in enumerate(template_tracks)
            ]
            self.style_tab.album_title = str(t_data.get('album_title') or 'My Album')
            existing_paths = list(self.project.album_audio_paths or [])
            self.album_state['title'] = self.style_tab.album_title
            self.album_state['tracks'] = []
            for index, item in enumerate(template_tracks):
                source = item if isinstance(item, dict) else {}
                self.album_state['tracks'].append({
                    'id': str(source.get('id') or f'track_{index + 1:04d}'),
                    'title': str(source.get('title') or item or f'Track {index + 1:02d}'),
                    'artist': source.get('artist') or t_data.get('track_artist', 'Album Artist'),
                    'audioSrc': source.get('audioSrc') or (existing_paths[index] if index < len(existing_paths) else ''),
                    'cover': source.get('cover') or '',
                    'duration': source.get('duration', 0),
                    'lyrics': source.get('lyrics', []),
                    'lyricTiming': source.get('lyricTiming', []),
                })
            self.album_state['activeTrackId'] = (self.album_state['tracks'][0]['id'] if self.album_state['tracks'] else None)
            if hasattr(self.style_tab, 'txt_album_title'):
                self.style_tab.txt_album_title.blockSignals(True)
                self.style_tab.txt_album_title.setText(self.style_tab.album_title)
                self.style_tab.txt_album_title.blockSignals(False)
            if hasattr(self.style_tab, 'txt_album_tracks'):
                self.style_tab.txt_album_tracks.blockSignals(True)
                self.style_tab.txt_album_tracks.setText(', '.join(self.style_tab.album_tracks))
                self.style_tab.txt_album_tracks.blockSignals(False)
            self.preview_widget.set_album_tracks(self.album_state['tracks'], self.album_state['activeTrackId'])
            self.timeline_widget.set_media_clips(self.project.timeline_clips, self.project.media_assets)
            self.preview_widget.album_title = self.style_tab.album_title
            self.album_state['selectedTrackId'] = self.album_state['activeTrackId']
            self.on_album_track_selected(self.album_state['activeTrackId'])
        try:
            self.style_tab.portrait_focus_y = float(t_data.get('portrait_focus_y', 25))
        except (TypeError, ValueError):
            self.style_tab.portrait_focus_y = 25.0
        self.style_tab.uppercase_lyrics = bool(t_data.get('uppercase_lyrics', False))
        
        # Track Title & Artist resolution
        if t_data.get('track_title') and t_data.get('track_title') != 'Song Title':
            self.style_tab.track_title = t_data.get('track_title')
        elif self.project.title:
            self.style_tab.track_title = self.project.title
        else:
            self.style_tab.track_title = t_data.get('track_title', 'Song Title')

        if t_data.get('track_artist') and t_data.get('track_artist') != 'Artist':
            self.style_tab.track_artist = t_data.get('track_artist')
        elif t_data.get('custom_singers'):
            self.style_tab.track_artist = ", ".join(
                singer.get('name', '') for singer in t_data['custom_singers'][:2] if singer.get('name')
            ) or 'Artist'
        elif getattr(self.style_tab, 'custom_singers', None):
            self.style_tab.track_artist = ", ".join([s['name'] for s in self.style_tab.custom_singers[:2] if s.get('name')])
        else:
            self.style_tab.track_artist = t_data.get('track_artist', 'Artist')

        if hasattr(self.style_tab, 'txt_track_title'):
            self.style_tab.txt_track_title.blockSignals(True)
            self.style_tab.txt_track_title.setText(self.style_tab.track_title)
            self.style_tab.txt_track_title.blockSignals(False)
        if hasattr(self.style_tab, 'txt_track_artist'):
            self.style_tab.txt_track_artist.blockSignals(True)
            self.style_tab.txt_track_artist.setText(self.style_tab.track_artist)
            self.style_tab.txt_track_artist.blockSignals(False)

        self.style_tab.set_display_mode(t_data.get('display_mode', 'COLOR CODED'), keep_template_variant=True)
        self.style_tab.combo_font.setCurrentText(t_data.get('font_family', 'Montserrat'))
        self.style_tab.combo_weight.setCurrentText(t_data.get('font_weight', '900 Cực Đậm'))
        self.style_tab.slider_font_size.setValue(t_data.get('font_size', 42))
        self.style_tab.set_karaoke_style(t_data.get('layout_mode', 'center'))

        alignment = t_data.get('text_alignment', 'center')
        self.style_tab.text_alignment = alignment
        alignment_buttons = {
            'left': self.style_tab.btn_align_left,
            'center': self.style_tab.btn_align_center,
            'right': self.style_tab.btn_align_right,
        }
        if alignment in alignment_buttons:
            alignment_buttons[alignment].setChecked(True)

        try:
            pos_y_bottom = float(t_data.get('pos_y_bottom', 78))
        except (TypeError, ValueError):
            pos_y_bottom = 78.0
        self.style_tab.slider_pos_y.setValue(
            max(self.style_tab.slider_pos_y.minimum(), min(
                self.style_tab.slider_pos_y.maximum(), int(round(pos_y_bottom - 4))
            ))
        )
        stroke_width = int(round(float(t_data.get('stroke_width', 4))))
        self.style_tab.slider_stroke.setValue(
            max(self.style_tab.slider_stroke.minimum(), min(self.style_tab.slider_stroke.maximum(), stroke_width))
        )
        
        if hasattr(self.style_tab, 'combo_motion'):
            self.style_tab.combo_motion.setCurrentText(t_data.get('motion_effect', 'Pop & Bounce (Nảy chữ nhịp điệu)'))

        def template_color(key, fallback):
            color = QColor(str(t_data.get(key, fallback)))
            return color if color.isValid() else QColor(fallback)
        self.style_tab.fill_color = template_color('fill_color', '#f59e0b')
        self.style_tab.base_text_color = template_color('base_color', '#ffffff')
        self.style_tab.male_color = template_color('male_color', '#0026ff')
        self.style_tab.female_color = template_color('female_color', '#ff0033')
        self.style_tab.both_color = template_color('both_color', '#ff007f')
        self.style_tab.btn_text_color.setStyleSheet(f"background: {self.style_tab.fill_color.name()}; border: 1px solid #cbd5e1; border-radius: 4px;")

        # Always replace the singer list, including for templates without singers.
        # Deep-copying keeps later edits isolated from the template library data.
        self.style_tab.custom_singers = copy.deepcopy(t_data.get('custom_singers', []))
        self.style_tab.populate_singers_list()
        self.style_tab.populate_matrix_checkboxes()

        # Update Effects Tab settings
        self.effects_tab.chk_particles.setChecked(bool(t_data.get('particles', False)))
        particle_type = t_data.get('particle_type', 'None')
        particle_index = self.effects_tab.combo_particles.findText(particle_type, Qt.MatchContains)
        self.effects_tab.combo_particles.setCurrentIndex(max(0, particle_index))
        self.effects_tab.slider_vignette.setValue(int(t_data.get('vignette', 35)))
        self.effects_tab.chk_glow.setChecked(bool(t_data.get('enable_glow', False)))
        self.effects_tab.slider_glow.setValue(int(t_data.get('glow_radius', 10)))
        self.effects_tab.slider_brightness.setValue(int(t_data.get('brightness', 0)))
        self.effects_tab.slider_contrast.setValue(int(t_data.get('contrast', 0)))
        self.effects_tab.slider_saturation.setValue(int(t_data.get('saturation', 0)))
        self.effects_tab.slider_blur.setValue(int(t_data.get('blur', 0)))
        self.effects_tab.chk_visualizer.setChecked(t_data.get('visualizer', False))
        visualizer_mode = t_data.get('visualizer_mode')
        if visualizer_mode:
            visualizer_index = self.effects_tab.combo_vis_mode.findText(visualizer_mode, Qt.MatchContains)
            if visualizer_index >= 0:
                self.effects_tab.combo_vis_mode.setCurrentIndex(visualizer_index)
        self.effects_tab.chk_pointer.setChecked(t_data.get('pointer', False))
        self.effects_tab.chk_watermark.setChecked(t_data.get('watermark', False))
        self.preview_widget.pointer_icon = t_data.get('pointer_icon', self.preview_widget.pointer_icon)

        tint = t_data.get('color_tint', 'None (Original)')
        tint_index = self.effects_tab.combo_tint.findText(tint, Qt.MatchContains)
        if tint_index >= 0:
            self.effects_tab.combo_tint.setCurrentIndex(tint_index)

        # Push updates to canvas & project
        self.style_tab.emit_change()
        self.effects_tab.emit_change()

    def save_current_as_template(self):
        """Save the currently edited style as a reusable gallery preset."""
        name, accepted = QInputDialog.getText(self, "Lưu template", "Tên template:")
        if not accepted or not name.strip():
            return False
        style = copy.deepcopy(self.project.style)
        effects = copy.deepcopy(self.project.effects)
        elements = copy.deepcopy(self.project.elements)
        template = {
            "id": f"custom_{len(self.templates_tab.cards) + 1}",
            "name": f"🎨 {name.strip()}",
            "category": "custom",
            "badge": "CUSTOM",
            "badge_color": "#0f766e",
            "description": "Saved from your current editable project settings.",
            "font_family": style.get("font_family", "Montserrat"),
            "font_weight": style.get("font_weight", "700 Bold"),
            "font_size": style.get("font_size", 42),
            "display_mode": style.get("display_mode", "KARAOKE"),
            "template_variant": style.get("template_variant", ""),
            "motion_effect": style.get("motion_effect", "Pop & Bounce (Nảy chữ nhịp điệu)"),
            "fill_color": style.get("fill_color", "#f59e0b"),
            "base_color": style.get("base_color", "#ffffff"),
            "male_color": style.get("male_color", "#0026ff"),
            "female_color": style.get("female_color", "#ff0033"),
            "both_color": style.get("both_color", "#ff007f"),
            "layout_mode": style.get("layout_mode", "center"),
            "text_alignment": style.get("text_alignment", "center"),
            "pos_y_bottom": style.get("pos_y_bottom", 78),
            "stroke_width": style.get("stroke_width", 4),
            "custom_singers": copy.deepcopy(style.get("custom_singers", [])),
            "particles": effects.get("particles", False),
            "particle_type": effects.get("particle_type", "None"),
            "enable_glow": effects.get("enable_glow", False),
            "glow_radius": effects.get("glow_radius", 8),
            "vignette": effects.get("vignette_percent", effects.get("vignette", 20)),
            "brightness": effects.get("brightness", 0),
            "contrast": effects.get("contrast", 0),
            "saturation": effects.get("saturation", 0),
            "blur": effects.get("blur", 0),
            "color_tint": effects.get("color_tint", "None (Original)"),
            "visualizer": elements.get("visualizer", False),
            "pointer": elements.get("pointer", False),
            "watermark": elements.get("watermark", False),
            "track_title": style.get("track_title", "Song Title"),
            "track_artist": style.get("track_artist", "Artist"),
            "album_title": style.get("album_title", getattr(self.preview_widget, "album_title", "My Album")),
            "album_tracks": list(style.get("album_tracks", getattr(self.preview_widget, "album_tracks", [])) or []),
        }
        self.templates_tab.add_template(template)
        self.project.custom_templates.append(copy.deepcopy(template))
        QMessageBox.information(self, "Đã lưu template", f"Template '{name.strip()}' đã được thêm vào thư viện.")
        return True

    def on_element_created(self, obj: dict):
        self.preview_widget.add_overlay_object(obj)
        self.project.overlay_objects = self.preview_widget.overlay_objects
        self.timeline_widget.set_overlay_objects(self.project.overlay_objects)
        self.inspector_panel.set_object(obj)
        self.inspector_panel.setVisible(True)
        self._push_project_state()

    def on_canvas_object_selected(self, obj: dict):
        if obj:
            self.inspector_panel.set_object(obj)
            self.inspector_panel.setVisible(True)
        else:
            self.inspector_panel.setVisible(False)

    def on_overlay_property_changed(self, props: dict):
        self.preview_widget.update_selected_object(props)
        self.project.overlay_objects = self.preview_widget.overlay_objects
        self.timeline_widget.set_overlay_objects(self.project.overlay_objects)
        self._push_project_state()

    def sync_overlay_state(self):
        self.project.overlay_objects = self.preview_widget.overlay_objects
        self.timeline_widget.set_overlay_objects(self.project.overlay_objects)
        self._push_project_state()

    def delete_selected_overlay(self):
        removed = self.preview_widget.delete_selected_object()
        if removed is not None:
            self.project.overlay_objects = self.preview_widget.overlay_objects
            self.timeline_widget.set_overlay_objects(self.project.overlay_objects)
            self.inspector_panel.setVisible(False)
            self._push_project_state()

    def delete_active_selection(self):
        """Route Delete to the active timeline selection or focused editor surface."""
        if self.timeline_widget.canvas.hasFocus() or self.timeline_widget.canvas.has_selection():
            self.timeline_widget.delete_line()
        elif hasattr(self, 'preview_widget') and self.preview_widget.selected_object_idx is not None:
            self.delete_selected_overlay()
        else:
            self.timeline_widget.delete_line()

    def on_timeline_media_clips_modified(self, clips: list):
        self.project.timeline_clips = clips
        self._push_project_state()

    def _push_project_state(self):
        if not self._restoring_state:
            self.undo_manager.push_state(self.project.to_dict())
            if hasattr(self, "lbl_save_status"):
                self.lbl_save_status.setText("Unsaved changes")

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Lylis Project", f"{self.project.title}.lylis.json", "Lylis Project (*.lylis.json);;JSON (*.json)")
        if not path:
            return
        try:
            self.project.save_to_file(path)
            self.lbl_save_status.setText("Saved")
            QMessageBox.information(self, "Project saved", f"Saved project to:\n{path}")
        except (OSError, TypeError, ValueError) as exc:
            QMessageBox.critical(self, "Save failed", str(exc))

    def open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Lylis Project", "", "Lylis Project (*.lylis.json *.json);;All Files (*.*)")
        if not path:
            return
        try:
            project = ProjectModel.load_from_file(path)
            self.restore_project_state(project.to_dict())
            self.undo_manager = UndoRedoManager(max_depth=50)
            self._push_project_state()
        except (OSError, ValueError, TypeError) as exc:
            QMessageBox.critical(self, "Open failed", str(exc))

    def rename_project(self):
        new_title, ok = QInputDialog.getText(self, "Đổi tên dự án", "Nhập tên mới cho dự án:", text=self.project.title)
        if ok and new_title.strip():
            self.project.title = new_title.strip()
            self.lbl_proj_title.setText(self.project.title)
            self.setWindowTitle(f"Lylis - {self.project.title}")
            self.undo_manager.push_state(self.project.to_dict())

    def switch_tab(self, index: int):
        self.tab_widget.setCurrentIndex(index)
        self.update_nav_highlight(index)

    def on_tab_changed(self, index: int):
        self.update_nav_highlight(index)

    def update_nav_highlight(self, active_index: int):
        for idx, btn in self.nav_buttons:
            if idx == active_index:
                btn.setChecked(True)
                btn.setStyleSheet("""
                    QPushButton {
                        border: none;
                        border-bottom: 2px solid #ff2d55;
                        color: #ff2d55;
                        font-weight: 800;
                        font-size: 11px;
                        padding: 6px 12px;
                        background: transparent;
                    }
                """)
            else:
                btn.setChecked(False)
                btn.setStyleSheet("""
                    QPushButton {
                        border: none;
                        border-bottom: 2px solid transparent;
                        color: #64748b;
                        font-weight: 700;
                        font-size: 11px;
                        padding: 6px 12px;
                        background: transparent;
                    }
                    QPushButton:hover {
                        color: #0f172a;
                    }
                """)

    def load_initial_demo(self):
        self._migrate_legacy_media_assets()
        self.media_tab.sync_media_assets(self.project.media_assets.values())
        self.lyrics_tab.set_audio_engine(self.audio_engine)
        self.preview_widget.set_background(self.sample_bg_path)
        self.project.bg_path = self.sample_bg_path
        self.lbl_proj_title.setText(self.project.title)
        self.timeline_widget.set_media_labels(background=os.path.basename(self.sample_bg_path))

        if self.audio_engine.load_audio(self.sample_audio_path):
            self.timeline_widget.set_waveform(self.audio_engine.waveform_peaks)
            self.preview_widget.set_waveform(self.audio_engine.waveform_peaks)
            self.timeline_widget.set_beat_times(detect_beat_times(self.audio_engine.waveform_peaks, self.audio_engine.duration))
            self.timeline_widget.set_duration(self.audio_engine.duration)
            self.project.audio_path = self.sample_audio_path
            self.project.duration = self.audio_engine.duration
            self.lyrics_tab.set_audio_path(self.sample_audio_path)
            self.timeline_widget.set_media_labels(audio=os.path.basename(self.sample_audio_path))

        self.lyrics_tab.set_lrc_text(SAMPLE_LRC_VIETNAMESE)
        self.on_lyrics_updated(SAMPLE_LRC_VIETNAMESE)
        self._push_project_state()

    def change_aspect(self, ratio_str: str):
        if not self.preview_widget.is_valid_aspect_ratio(ratio_str):
            self.sync_aspect_buttons(self.project.aspect_ratio)
            return False
        self.preview_widget.set_aspect_ratio(ratio_str)
        self.project.aspect_ratio = ratio_str
        self.sync_aspect_buttons(ratio_str)
        self.lyrics_tab.set_export_style_config({**self.project.style, 'aspect': ratio_str})
        self._push_project_state()
        return True

    def toggle_playback(self):
        if self.audio_engine.is_playing:
            self.audio_engine.pause()
            self.btn_play.setText("")
            self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            self.audio_engine.play()
            self.btn_play.setText("")
            self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.timeline_widget.set_playback_active(self.audio_engine.is_playing)
        self.btn_play.setIcon(self.style().standardIcon(
            QStyle.SP_MediaPause if self.audio_engine.is_playing else QStyle.SP_MediaPlay
        ))

    def toggle_loop(self):
        # Kept as a compatibility slot for older callers; the mode selector
        # is now the only visible playback-mode control.
        self.audio_engine.loop = False

    def toggle_mute(self):
        muted = self.audio_engine.volume > 0
        self.audio_engine.set_volume(0.0 if muted else 1.0)
        icon = QStyle.SP_MediaVolumeMuted if muted else QStyle.SP_MediaVolume
        self.btn_download.setIcon(self.style().standardIcon(icon))
        self.btn_download.setToolTip("Unmute" if muted else "Mute")

    def on_playback_mode_changed(self, index):
        self.playback_mode = ['once', 'repeat_track', 'repeat_album', 'shuffle'][max(0, min(3, int(index)))]
        self.audio_engine.loop = self.playback_mode == 'repeat_track'

    def _handle_album_end(self):
        if self.playback_mode == 'repeat_track':
            self.audio_engine.seek(0.0)
            self.audio_engine.play()
        elif self.playback_mode == 'repeat_album':
            tracks = self.album_state.get('tracks', [])
            if tracks:
                self.on_album_track_selected(tracks[0].get('id'))
                self.audio_engine.play()
        elif self.playback_mode == 'shuffle':
            tracks = self.album_state.get('tracks', [])
            if len(tracks) > 1:
                current = self.album_state.get('activeTrackId')
                choices = [track for track in tracks if track.get('id') != current]
                self.on_album_track_selected(random.choice(choices).get('id'))
                self.audio_engine.play()
        elif self.playback_mode == 'once':
            self.next_album_track()
            if self.album_state.get('activeTrackId') and self.audio_engine.duration > 0:
                self.audio_engine.play()

    def seek_relative(self, delta_secs: float):
        curr_t = self.audio_engine.get_current_time()
        self.on_timeline_seek(curr_t + delta_secs)

    def on_seek_slider_moved(self, val):
        if self.audio_engine.duration > 0:
            target_t = (val / 1000.0) * self.audio_engine.duration
            self.audio_engine.seek(target_t)
            self.timeline_widget.set_current_time(
                target_t,
                is_playing=self.audio_engine.is_playing,
                reveal=True,
            )

    def on_zoom_changed(self, val):
        if hasattr(self, 'lbl_zoom'):
            self.lbl_zoom.setText(f"{val}s")
        elif hasattr(self.timeline_widget, 'lbl_zoom_val'):
            self.timeline_widget.lbl_zoom_val.setText(f"{int(val)}s")
        self.timeline_widget.set_zoom(val)

    def on_audio_setting_changed(self, *args):
        self.project.audio_settings = {
            'pitch_semitones': self.media_tab.slider_pitch.value(),
            'speed': [0.5, 0.75, 1.0, 1.25, 1.5][self.media_tab.combo_speed.currentIndex()],
            'vocal_cut': self.media_tab.chk_vocal_cut.isChecked(),
        }
        self.audio_effect_timer.start()

    def apply_audio_settings(self):
        settings = self.project.audio_settings
        current_time = self.audio_engine.get_current_time()
        was_playing = self.audio_engine.is_playing
        if self.audio_engine.apply_audio_settings(
            settings.get('pitch_semitones', 0),
            settings.get('speed', 1.0),
            settings.get('vocal_cut', False),
        ):
            new_speed = float(settings.get('speed', 1.0))
            if abs(new_speed - self._last_applied_speed) > 1e-6 and self.current_lrc_lines:
                factor = self._last_applied_speed / new_speed
                for line in self.current_lrc_lines:
                    line.line_start *= factor
                    line.line_end *= factor
                    for word in line.words:
                        word.start_time *= factor
                        word.end_time *= factor
                synced_lrc = LrcEngine.export_lrc(self.current_lrc_lines)
                self.project.raw_lrc_text = synced_lrc
                self.lyrics_tab.set_lrc_text(synced_lrc)
                self.preview_widget.set_lyrics(self.current_lrc_lines)
                self.timeline_widget.set_lyrics(self.current_lrc_lines)
                self._last_applied_speed = new_speed
            self.timeline_widget.set_waveform(self.audio_engine.waveform_peaks)
            self.preview_widget.set_waveform(self.audio_engine.waveform_peaks)
            self.timeline_widget.set_beat_times(detect_beat_times(self.audio_engine.waveform_peaks, self.audio_engine.duration))
            self.timeline_widget.set_duration(self.audio_engine.duration)
            self.project.duration = self.audio_engine.duration
            self.audio_engine.seek(min(current_time, self.audio_engine.duration))
            if was_playing:
                self.audio_engine.play()
            self._push_project_state()
        else:
            QMessageBox.warning(self, "Audio processing", "Could not apply the selected audio settings.")

    def on_transition_applied(self, name: str, position: str):
        duration = 1.5 if "Slide" in name else 2.0
        self.project.transitions[position] = {'name': name, 'duration': duration}
        self.preview_widget.set_transitions(self.project.transitions)
        self.timeline_widget.set_transitions(self.project.transitions)
        self._push_project_state()

    def _register_media_assets(self, assets):
        for asset in assets or []:
            if not isinstance(asset, dict):
                continue
            asset_id = str(asset.get('id') or uuid.uuid4())
            normalized = dict(asset)
            normalized['id'] = asset_id
            normalized['src'] = str(normalized.get('src') or '')
            if normalized['src']:
                self.project.media_assets[asset_id] = normalized
        self._push_project_state()

    def _migrate_legacy_media_assets(self):
        """Promote legacy global paths into the shared registry once."""
        candidates = [("legacy_audio", self.project.audio_path, "audio"), ("legacy_background", self.project.bg_path, "image")]
        for asset_id, path, media_type in candidates:
            if not path or not os.path.exists(path):
                continue
            if not any(item.get('src') == path for item in self.project.media_assets.values()):
                self.project.media_assets[asset_id] = {
                    'id': asset_id, 'name': os.path.basename(path), 'type': media_type, 'src': path
                }

    def _asset_duration(self, asset):
        if asset.get('type') == 'audio' and str(asset.get('src', '')).lower().endswith('.wav'):
            try:
                import wave
                with wave.open(asset['src'], 'rb') as stream:
                    return max(0.1, stream.getnframes() / float(stream.getframerate() or 1))
            except (OSError, wave.Error, ZeroDivisionError):
                pass
        return 5.0 if asset.get('type') == 'image' else 1.0

    def _create_media_clip(self, asset, start_time, target_track_id=None):
        duration = self._asset_duration(asset)
        clip = {
            'id': str(uuid.uuid4()),
            'assetId': asset['id'],
            'trackId': target_track_id or f"track_{asset.get('type', 'media')}",
            'startTime': max(0.0, float(start_time)),
            'duration': duration,
            'sourceStart': 0.0,
            'sourceDuration': duration,
        }
        self.project.timeline_clips.append(clip)
        self.project.duration = max(float(self.project.duration), clip['startTime'] + duration)
        self.timeline_widget.set_duration(self.project.duration)
        self.timeline_widget.set_media_clips(self.project.timeline_clips, self.project.media_assets)
        self._push_project_state()

    def add_asset_to_timeline(self, asset_id, start_time=None, target_track_id=None):
        asset = self.project.media_assets.get(str(asset_id))
        if not asset:
            return False
        clip_start = self.audio_engine.get_current_time() if start_time is None else start_time
        self._create_media_clip(asset, clip_start, target_track_id)
        return True

    def on_media_asset_add_requested(self, asset_id):
        self.add_asset_to_timeline(asset_id)

    def on_media_asset_dropped(self, asset_id, start_time):
        self.add_asset_to_timeline(asset_id, start_time=start_time)

    def on_media_files_dropped(self, paths, start_time):
        before = {asset.get('src') for asset in self.project.media_assets.values()}
        self.media_tab.import_files(paths, activate=False)
        self._register_media_assets(self.media_tab.media_assets())
        new_assets = [asset for asset in self.project.media_assets.values() if asset.get('src') in set(paths) and asset.get('src') not in before]
        for index, asset in enumerate(new_assets):
            self._create_media_clip(asset, start_time + index * self._asset_duration(asset))

    def on_audio_loaded(self, filepath, silent=False):
        if self.audio_engine.load_audio(filepath):
            self.sample_audio_path = filepath
            self.project.audio_path = filepath
            self.project.duration = self.audio_engine.duration
            self.lyrics_tab.set_audio_engine(self.audio_engine)
            self.lyrics_tab.set_audio_path(filepath)
            self.timeline_widget.set_waveform(self.audio_engine.waveform_peaks)
            self.preview_widget.set_waveform(self.audio_engine.waveform_peaks)
            self.timeline_widget.set_duration(self.audio_engine.duration)
            self.timeline_widget.set_media_labels(audio=os.path.basename(filepath))
            active_id = self.album_state.get('activeTrackId')
            active_track = next((track for track in self.album_state.get('tracks', []) if track.get('id') == active_id), None)
            if active_track is None:
                active_track = {
                    'id': f'track_{len(self.album_state.get("tracks", [])) + 1:04d}',
                    'title': os.path.splitext(os.path.basename(filepath))[0].replace('_', ' ') or 'Track 01',
                    'artist': getattr(self.style_tab, 'track_artist', 'Artist') or 'Artist',
                    'audioSrc': filepath, 'lyrics': [],
                }
                self.album_state['tracks'] = [active_track]
                self.album_state['activeTrackId'] = active_track['id']
                self.preview_widget.set_album_tracks(self.album_state['tracks'], active_track['id'])
            active_track['audioSrc'] = filepath
            active_track['duration'] = float(self.audio_engine.duration or 0.0)
            self._sync_album_state_to_project()
            if getattr(self.style_tab, 'template_variant', '') == 'ambient_album_player':
                inferred_title = os.path.splitext(os.path.basename(filepath))[0].replace('_', ' ').strip()
                self.style_tab.track_title = inferred_title or 'Song Title'
                self.style_tab.emit_change()
            self._push_project_state()
            if not silent:
                QMessageBox.information(self, "Audio Loaded", f"Audio track loaded successfully ({self.audio_engine.duration:.1f}s).")

    def on_album_track_selected(self, track_id: str):
        """Switch every album-facing surface through one activeTrackId."""
        tracks = self.album_state.get('tracks', [])
        selected = next((track for track in tracks if track.get('id') == track_id), None)
        if not selected:
            return
        previous_id = self.album_state.get('activeTrackId')
        previous = next((track for track in tracks if track.get('id') == previous_id), None)
        if previous is not None and previous.get('id') != selected.get('id'):
            previous['lyrics'] = LrcEngine.export_lrc(self.current_lrc_lines) if self.current_lrc_lines else ''
        self.audio_engine.pause()
        self.album_state['activeTrackId'] = selected['id']
        self.album_state['selectedTrackId'] = selected['id']
        self.project.album_active_track_id = selected['id']
        self.project.style['active_track_id'] = selected['id']
        self.preview_widget.active_album_track_id = selected['id']
        self.preview_widget.track_title = selected.get('title', 'Track')
        self.preview_widget.track_artist = selected.get('artist') or self.album_state.get('artist', 'Album Artist')
        self.style_tab.track_cover_path = selected.get('cover', '') or ''
        if hasattr(self.style_tab, 'btn_track_cover'):
            cover_name = os.path.basename(self.style_tab.track_cover_path)
            self.style_tab.btn_track_cover.setText(f"📷 {cover_name[:18]}..." if cover_name else "📷 Change Track Image")
        cover_path = selected.get('cover') or self.album_state.get('cover') or ''
        self.preview_widget.album_cover_path = cover_path
        self.preview_widget.album_cover_pixmap = QPixmap(cover_path) if cover_path and os.path.exists(cover_path) else QPixmap()
        self.style_tab.track_title = self.preview_widget.track_title
        self.style_tab.track_artist = self.preview_widget.track_artist
        self.style_tab.txt_track_title.blockSignals(True)
        self.style_tab.txt_track_title.setText(self.preview_widget.track_title)
        self.style_tab.txt_track_title.blockSignals(False)
        self.style_tab.txt_track_artist.blockSignals(True)
        self.style_tab.txt_track_artist.setText(self.preview_widget.track_artist)
        self.style_tab.txt_track_artist.blockSignals(False)
        selected_audio = selected.get('audioSrc', '')
        if selected_audio and os.path.exists(selected_audio):
            self.on_audio_loaded(selected_audio, silent=True)
        else:
            # Never leave the previous track audible when the selected asset is
            # missing; the selected track remains the sole content context.
            self.audio_engine.unload()
            self.timeline_widget.set_duration(float(selected.get('duration') or 1.0))
        stored_lyrics = selected.get('lyrics') or ''
        restored = LrcEngine.parse(stored_lyrics) if isinstance(stored_lyrics, str) else copy.deepcopy(stored_lyrics)
        self.current_lrc_lines = restored
        self.audio_engine.seek(0.0)
        if not selected.get('audioSrc') and selected.get('duration'):
            self.preview_widget.duration = float(selected.get('duration') or 0.0)
        self.preview_widget.current_time = 0.0
        self.preview_widget.set_lyrics(restored)
        self.timeline_widget.set_lyrics(restored)
        self.lyrics_tab.set_lrc_text(LrcEngine.export_lrc(restored) if restored else '')
        self.preview_widget.update()
        self._sync_album_state_to_project()
        self._push_project_state()

    def next_album_track(self):
        tracks = self.album_state.get('tracks', [])
        if not tracks:
            return
        was_playing = self.audio_engine.is_playing
        ids = [track.get('id') for track in tracks]
        try:
            index = ids.index(self.album_state.get('activeTrackId'))
        except ValueError:
            index = -1
        if index + 1 < len(tracks):
            self.on_album_track_selected(ids[index + 1])
            if was_playing:
                self.audio_engine.play()

    def previous_album_track(self):
        tracks = self.album_state.get('tracks', [])
        if not tracks:
            return
        if self.audio_engine.get_current_time() > 3.0:
            self.audio_engine.seek(0.0)
            return
        was_playing = self.audio_engine.is_playing
        ids = [track.get('id') for track in tracks]
        try:
            index = ids.index(self.album_state.get('activeTrackId'))
        except ValueError:
            index = 0
        if index > 0:
            self.on_album_track_selected(ids[index - 1])
            if was_playing:
                self.audio_engine.play()

    def on_audio_playlist_loaded(self, filepaths: list):
        """Load a multi-song album, keeping the first track active for editing."""
        valid_paths = [path for path in filepaths if path and os.path.exists(path)]
        if not valid_paths:
            QMessageBox.warning(self, "Album Upload", "No valid audio files were selected.")
            return False
        self.project.album_audio_paths = list(valid_paths)
        track_names = [os.path.splitext(os.path.basename(path))[0].replace('_', ' ').strip() for path in valid_paths]
        tracks = [
            {'id': f'track_{index + 1:04d}', 'title': name or f'Track {index + 1:02d}',
             'artist': self.project.style.get('track_artist', 'Album Artist'),
             'audioSrc': path, 'lyrics': []}
            for index, (path, name) in enumerate(zip(valid_paths, track_names))
        ]
        self.album_state['tracks'] = tracks
        self.album_state['activeTrackId'] = tracks[0]['id']
        self.project.album_active_track_id = tracks[0]['id']
        self.project.style['active_track_id'] = tracks[0]['id']
        self.project.style["album_tracks"] = track_names
        self.project.style.setdefault("album_title", self.project.title or "My Album")
        self.preview_widget.set_album_tracks(tracks, tracks[0]['id'])
        self.preview_widget.album_title = self.project.style["album_title"]
        self.on_audio_loaded(valid_paths[0], silent=True)
        self._push_project_state()
        QMessageBox.information(self, "Album Ready", f"Added {len(valid_paths)} songs. The first song is active for editing.")
        return True

    def auto_edit_project(self):
        """Run a deterministic, one-click CapCut-style lyric edit pass."""
        raw_text = self.lyrics_tab.get_lrc_text().strip()
        if not raw_text:
            QMessageBox.warning(self, "Chưa có lời bài hát", "Hãy nhập hoặc tải lời bài hát trước khi Auto Edit.")
            return False

        duration = float(self.audio_engine.duration or self.project.duration or 0.0)
        if duration <= 0:
            duration = 45.0
        lines, normalized_lrc = prepare_auto_edit(
            raw_text,
            duration,
            getattr(self.audio_engine, "waveform_peaks", None),
        )
        if not lines:
            QMessageBox.warning(self, "Không thể Auto Edit", "Không tìm thấy dòng lời hợp lệ để dựng video.")
            return False

        self.project.duration = duration
        self.timeline_widget.set_duration(duration)
        self.timeline_widget.set_beat_times(detect_beat_times(getattr(self.audio_engine, "waveform_peaks", []), duration))
        self.lyrics_tab.set_lrc_text(normalized_lrc)
        self.on_lyrics_updated(normalized_lrc)

        # Pick a polished default only when the user has not chosen a template.
        if not getattr(self.style_tab, "template_variant", ""):
            default_template = next((item for item in TEMPLATES_DATA if item.get("id") == "tiktok_viral"), None)
            if default_template:
                self.on_template_applied(default_template)

        if "start" not in self.project.transitions:
            self.on_transition_applied("Fade (Hoà tan)", "start")
        if "end" not in self.project.transitions:
            self.on_transition_applied("Fade (Hoà tan)", "end")

        self.timeline_widget.btn_beats.setChecked(True)
        self.timeline_widget.btn_snap.setChecked(True)
        self.timeline_widget.toggle_beats()
        self.timeline_widget.toggle_snap()
        self._push_project_state()
        QMessageBox.information(
            self,
            "Auto Edit hoàn tất",
            f"Đã căn nhịp và tạo {len(lines)} đoạn lời. Bạn có thể tinh chỉnh trên Timeline.",
        )
        return True

    def on_background_loaded(self, filepath):
        self.sample_bg_path = filepath
        self.project.bg_path = filepath
        self.preview_widget.set_background(filepath)
        self.timeline_widget.set_media_labels(background=os.path.basename(filepath))
        self._push_project_state()

    def on_analyze_lyrics_requested(self, asset_id, audio_path):
        from gui.ai_lyrics_dialog import AiLyricsDialog
        dialog = AiLyricsDialog(str(asset_id), audio_path, self)
        dialog.applied.connect(self.on_ai_lyrics_applied)
        self._ai_lyrics_dialog = dialog
        dialog.show()

    def on_ai_lyrics_applied(self, lrc_text, result):
        if not lrc_text or not LrcEngine.parse(lrc_text):
            QMessageBox.warning(self, "AI Lyrics", "No valid timed lyric lines were produced.")
            return
        lines = LrcEngine.parse(lrc_text)
        self.lyrics_tab.set_lrc_text(lrc_text)
        self.on_lyrics_updated(lrc_text)
        asset_id = getattr(self, '_ai_lyrics_dialog', None)
        asset_id = getattr(asset_id, 'asset_id', None)
        if asset_id in self.project.media_assets:
            self.project.media_assets[asset_id]['rawTranscription'] = copy.deepcopy(result)
            self.project.media_assets[asset_id]['editedLyrics'] = lrc_text
        for track in self.album_state.get('tracks', []):
            if track.get('audioSrc') == self.project.media_assets.get(asset_id, {}).get('src'):
                track['lyrics'] = lrc_text
                track['lyricTiming'] = copy.deepcopy(result.get('lines', []))
        self._sync_album_state_to_project()
        self.timeline_widget.set_lyrics(lines)
        self._push_project_state()

    def on_lyrics_updated(self, lrc_text):
        self.current_lrc_lines = LrcEngine.parse(lrc_text)
        self.project.raw_lrc_text = lrc_text
        active_track = self._active_album_track()
        if active_track is not None:
            active_track['lyrics'] = str(lrc_text or '')
            active_track['lyricTiming'] = copy.deepcopy(active_track.get('lyricTiming', []))
            self._sync_album_state_to_project()
        self.preview_widget.set_lyrics(self.current_lrc_lines)
        self.timeline_widget.set_lyrics(self.current_lrc_lines)
        self.style_tab.set_lyric_lines(self.current_lrc_lines)
        self._push_project_state()

    def _active_album_track(self):
        if self.preview_widget.template_variant not in {
            'multi_song_album', 'ambient_album_player', 'eminem_rap_hiphop_album'
        }:
            return None
        active_id = self.album_state.get('activeTrackId')
        return next(
            (track for track in self.album_state.get('tracks', []) if track.get('id') == active_id),
            None,
        )

    def _sync_album_state_to_project(self):
        """Persist the canonical in-memory album tracks without style defaults."""
        self.project.style['album_tracks'] = copy.deepcopy(self.album_state.get('tracks', []))
        self.project.style['album_title'] = self.album_state.get('title', 'My Album')
        self.project.album_active_track_id = self.album_state.get('activeTrackId')

    def on_singer_roles_updated(self, updated_lines):
        self.current_lrc_lines = updated_lines
        self.preview_widget.set_lyrics(self.current_lrc_lines)
        self.timeline_widget.set_lyrics(self.current_lrc_lines)
        synced_lrc = LrcEngine.export_lrc(self.current_lrc_lines)
        self.project.raw_lrc_text = synced_lrc
        active_track = self._active_album_track()
        if active_track is not None:
            active_track['lyrics'] = synced_lrc
            self._sync_album_state_to_project()
        self.lyrics_tab.set_lrc_text(synced_lrc)
        self._push_project_state()

    def on_style_changed(self, cfg):
        cfg = dict(cfg or {})
        track_content_changed = bool(cfg.pop('_track_content_changed', False))
        album_content_changed = bool(cfg.pop('_album_content_changed', False))
        self.preview_widget.display_mode = cfg.get('display_mode', 'KARAOKE')
        self.preview_widget.template_variant = cfg.get('template_variant', '')
        self.preview_widget.track_title = cfg.get('track_title', 'Song Title')
        self.preview_widget.track_artist = cfg.get('track_artist', 'Artist')
        track_cover = cfg.get('track_cover_path')
        if track_cover:
            active_id = self.album_state.get('activeTrackId')
            active_track = next((track for track in self.album_state.get('tracks', []) if track.get('id') == active_id), None)
            if active_track is not None:
                active_track['cover'] = str(track_cover)
                self.preview_widget.album_cover_path = str(track_cover)
                self.preview_widget.album_cover_pixmap = QPixmap(str(track_cover)) if os.path.exists(str(track_cover)) else QPixmap()
        active_id = self.album_state.get('activeTrackId')
        active_track = next((track for track in self.album_state.get('tracks', []) if track.get('id') == active_id), None)
        if track_content_changed and active_track is not None:
            active_track['title'] = self.preview_widget.track_title or active_track.get('title', 'Track')
            active_track['artist'] = self.preview_widget.track_artist or active_track.get('artist', 'Artist')
        if active_track is not None and self.preview_widget.template_variant in {
            'multi_song_album', 'ambient_album_player', 'eminem_rap_hiphop_album'
        }:
            # Album player content always comes from the active track; style
            # changes must not replace it with the single-song metadata fields.
            self.preview_widget.track_title = active_track.get('title', 'Track')
            self.preview_widget.track_artist = active_track.get('artist', 'Artist')
        self.preview_widget.portrait_focus_y = float(cfg.get('portrait_focus_y', 25))
        self.preview_widget.uppercase_lyrics = bool(cfg.get('uppercase_lyrics', False))
        self.preview_widget.motion_effect = cfg.get('motion_effect', 'Pop & Bounce')
        self.preview_widget.font_family = cfg.get('font_family', 'Playwrite IS')
        self.preview_widget.font_weight_str = cfg.get('font_weight', '400 Thường')
        self.preview_widget.font_size = cfg.get('font_size', 42)
        self.preview_widget.text_alignment = cfg.get('text_alignment', 'center')
        self.preview_widget.stroke_width = cfg.get('stroke_width', 3.5)
        self.preview_widget.is_bold = cfg.get('is_bold', False)
        self.preview_widget.is_italic = cfg.get('is_italic', False)
        self.preview_widget.layout_mode = cfg.get('layout_mode', 'left_right')
        self.preview_widget.fill_mode = cfg.get('fill_mode', 'word')
        self.preview_widget.singer_mode = cfg.get('singer_mode', 'song_ca')
        self.preview_widget.male_color = QColor(cfg.get('male_color', '#0026ff'))
        self.preview_widget.female_color = QColor(cfg.get('female_color', '#ff0033'))
        self.preview_widget.both_color = QColor(cfg.get('both_color', '#ff007f'))
        self.preview_widget.base_color = QColor(cfg.get('base_color', '#ffffff'))
        self.preview_widget.active_color = QColor(cfg.get('fill_color', '#f59e0b'))
        if 'custom_singers' in cfg:
            self.preview_widget.custom_singers = [
                {
                    'name': str(item.get('name') or f'Singer {idx + 1}'),
                    'role': item.get('role', 'both'),
                    'color': item.get('color', '#ffffff'),
                    'avatar': item.get('avatar', '👤'),
                    'image_path': item.get('image_path', ''),
                }
                for idx, item in enumerate(cfg.get('custom_singers') or [])
                if isinstance(item, dict)
            ]
        if 'album_cover_path' in cfg:
            cover_path = cfg.get('album_cover_path') or ''
            self.preview_widget.album_cover_path = cover_path
            self.preview_widget.album_cover_pixmap = (
                QPixmap(cover_path) if cover_path and os.path.exists(cover_path) else QPixmap()
            )
        if 'album_title' in cfg:
            self.preview_widget.album_title = str(cfg.get('album_title') or 'My Album')
        if album_content_changed and 'album_tracks' in cfg:
            tracks = list(cfg.get('album_tracks') or [])
            existing = self.album_state.get('tracks', [])
            normalized = []
            for index, title in enumerate(tracks):
                old = existing[index] if index < len(existing) else {}
                updated = copy.deepcopy(old) if isinstance(old, dict) else {}
                updated.update({
                    'id': str(updated.get('id') or f'track_{index + 1:04d}'),
                    'title': str(title).strip() or f'Track {index + 1:02d}',
                    'artist': updated.get('artist') or cfg.get('track_artist', 'Album Artist'),
                    'audioSrc': updated.get('audioSrc', ''),
                    'cover': updated.get('cover', ''),
                    'duration': updated.get('duration', 0),
                    'lyrics': updated.get('lyrics', []),
                    'lyricTiming': updated.get('lyricTiming', []),
                })
                normalized.append(updated)
            self.album_state['tracks'] = normalized
            if self.album_state.get('activeTrackId') not in {track['id'] for track in normalized}:
                self.album_state['activeTrackId'] = normalized[0]['id'] if normalized else None
            self.preview_widget.set_album_tracks(normalized, self.album_state.get('activeTrackId'))
            selected = next(
                (track for track in normalized if track.get('id') == self.album_state.get('activeTrackId')),
                None,
            )
            if selected is not None:
                self.preview_widget.track_title = selected.get('title', 'Track')
                self.preview_widget.track_artist = selected.get('artist', 'Artist')
        self.preview_widget.padding_x_percent = cfg.get('padding_x', 7.5)
        self.preview_widget.pos_y_top = cfg.get('pos_y_top', 66.0)
        self.preview_widget.pos_y_bottom = cfg.get('pos_y_bottom', 78.0)
        self.preview_widget.stroke_width = cfg.get('stroke_width', 3.5)
        self.preview_widget.update()
        self.project.style.update(cfg)
        if self.album_state.get('tracks'):
            # Keep structured album metadata in project persistence; the editor fields
            # may only expose a comma-separated title list.
            self.project.style['album_tracks'] = copy.deepcopy(self.album_state['tracks'])
            self.project.style['album_title'] = self.album_state.get('title', cfg.get('album_title', 'My Album'))
        self.lyrics_tab.set_export_style_config({**cfg, 'aspect': self.project.aspect_ratio})
        self._push_project_state()

    def on_elements_changed(self, cfg):
        self.preview_widget.enable_particles = cfg.get('particles', False)
        self.preview_widget.particle_type = cfg.get('particle_type', 'Bokeh Orbs')
        self.preview_widget.enable_visualizer = cfg.get('visualizer', False)
        self.preview_widget.enable_pointer = cfg.get('pointer', True)
        self.preview_widget.pointer_icon = cfg.get('pointer_icon', '🎤')
        self.preview_widget.pointer_icons = cfg.get(
            'pointer_icons', {'male': '👨', 'female': '👩', 'both': '🎤'}
        )
        self.preview_widget.enable_watermark = cfg.get('watermark', False)
        self.preview_widget.update()
        self.project.elements = cfg

    def on_effects_changed(self, cfg):
        self.preview_widget.brightness = cfg.get('brightness', 0)
        self.preview_widget.contrast = cfg.get('contrast', 0)
        self.preview_widget.saturation = cfg.get('saturation', 0)
        self.preview_widget.blur_radius = cfg.get('blur', 0)
        self.preview_widget.enable_particles = cfg.get('particles', False)
        self.preview_widget.particle_type = cfg.get('particle_type', 'Bokeh Orbs')
        self.preview_widget.vignette_percent = cfg.get('vignette_percent', 0)
        self.preview_widget.enable_glow = cfg.get('enable_glow', True)
        self.preview_widget.glow_radius = cfg.get('glow_radius', 6)
        self.preview_widget.color_tint = cfg.get('color_tint', 'None (Original)')
        self.preview_widget.enable_visualizer = cfg.get('visualizer', False)
        self.preview_widget.visualizer_mode = cfg.get('visualizer_mode', 'Bar Spectrum')
        self.preview_widget.enable_pointer = cfg.get('pointer', True)
        self.preview_widget.enable_watermark = cfg.get('watermark', False)
        self.preview_widget.update()
        self.project.effects.update({key: value for key, value in cfg.items() if key not in {'visualizer', 'pointer', 'watermark'}})
        self.project.elements.update({
            'visualizer': cfg.get('visualizer', False),
            'visualizer_mode': cfg.get('visualizer_mode', 'Bar Spectrum'),
            'pointer': cfg.get('pointer', True),
            'watermark': cfg.get('watermark', False),
        })
        self.timeline_widget.set_effects({**self.project.effects, **self.project.elements})
        self._push_project_state()

    def perform_autosave(self):
        """Background Auto-Save to prevent project loss."""
        try:
            import json
            if hasattr(self, "lbl_save_status"):
                self.lbl_save_status.setText("Saving...")
            from core.paths import get_safe_writable_path
            save_path = get_safe_writable_path(".autosave.lylis.json")
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(self.project.to_dict(), f, ensure_ascii=False, indent=2)
            if hasattr(self, "lbl_save_status"):
                self.lbl_save_status.setText("Saved")
        except Exception:
            if hasattr(self, "lbl_save_status"):
                self.lbl_save_status.setText("Unsaved changes")

    def on_timeline_lyrics_modified(self, lines: list):
        self.current_lrc_lines = lines
        synced_lrc = LrcEngine.export_lrc(lines)
        self.project.raw_lrc_text = synced_lrc
        active_track = self._active_album_track()
        if active_track is not None:
            active_track['lyrics'] = synced_lrc
            self._sync_album_state_to_project()
        self.lyrics_tab.set_lrc_text(synced_lrc)
        self.preview_widget.set_lyrics(lines)
        self.style_tab.set_lyric_lines(lines)
        self._push_project_state()

    def on_undo(self):
        prev = self.undo_manager.undo(self.project.to_dict())
        if prev:
            self.restore_project_state(prev)

    def on_redo(self):
        next_st = self.undo_manager.redo(self.project.to_dict())
        if next_st:
            self.restore_project_state(next_st)

    def restore_project_state(self, state_dict: dict):
        self._restoring_state = True
        try:
            self.project = ProjectModel.from_dict(state_dict)
            self._migrate_legacy_media_assets()
            self.media_tab.sync_media_assets(self.project.media_assets.values())
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(1 if self.project.language == 'en' else 0)
            self.language_combo.blockSignals(False)
            self.set_language(1 if self.project.language == 'en' else 0)
            self.current_lrc_lines = LrcEngine.parse(self.project.raw_lrc_text)
            self.preview_widget.set_lyrics(self.current_lrc_lines)
            self.timeline_widget.set_lyrics(self.current_lrc_lines)
            self.lyrics_tab.set_lrc_text(self.project.raw_lrc_text)
            self.style_tab.set_lyric_lines(self.current_lrc_lines)

            self.lbl_proj_title.setText(self.project.title)
            self.setWindowTitle(f"Lylis - {self.project.title}")
            if not self.preview_widget.is_valid_aspect_ratio(self.project.aspect_ratio):
                self.project.aspect_ratio = '16:9'
            self.preview_widget.set_aspect_ratio(self.project.aspect_ratio)
            self.sync_aspect_buttons(self.project.aspect_ratio)

            if self.project.bg_path and os.path.exists(self.project.bg_path):
                self.sample_bg_path = self.project.bg_path
                self.preview_widget.set_background(self.project.bg_path)
                self.timeline_widget.set_media_labels(background=os.path.basename(self.project.bg_path))
            else:
                self.sample_bg_path = ""
                self.preview_widget.set_background("")
                self.timeline_widget.set_media_labels(background="No background")
            if self.project.audio_path and os.path.exists(self.project.audio_path):
                self.sample_audio_path = self.project.audio_path
                self.audio_engine.load_audio(self.project.audio_path)
                self.lyrics_tab.set_audio_path(self.project.audio_path)
                self.timeline_widget.set_waveform(self.audio_engine.waveform_peaks)
                self.preview_widget.set_waveform(self.audio_engine.waveform_peaks)
                self.timeline_widget.set_beat_times(detect_beat_times(self.audio_engine.waveform_peaks, self.audio_engine.duration))
                self.timeline_widget.set_duration(self.audio_engine.duration)
                self.timeline_widget.set_media_labels(audio=os.path.basename(self.project.audio_path))
            else:
                self.sample_audio_path = ""
                self.audio_engine.unload()
                self.timeline_widget.set_waveform([])
                self.preview_widget.set_waveform([])
                self.timeline_widget.set_beat_times([])
                self.timeline_widget.set_duration(self.project.duration)
                self.timeline_widget.set_media_labels(audio="No audio")

            # Work from immutable snapshots: setters below emit live UI signals and
            # must not mutate the source values that are still being restored.
            style = copy.deepcopy(self.project.style)
            self.style_tab.template_variant = style.get('template_variant', '')
            self.style_tab.track_title = style.get('track_title', self.project.title or 'Song Title')
            self.style_tab.track_artist = style.get('track_artist', 'Artist')
            self.style_tab.txt_track_title.blockSignals(True)
            self.style_tab.txt_track_artist.blockSignals(True)
            self.style_tab.txt_track_title.setText(self.style_tab.track_title)
            self.style_tab.txt_track_artist.setText(self.style_tab.track_artist)
            self.style_tab.txt_track_title.blockSignals(False)
            self.style_tab.txt_track_artist.blockSignals(False)
            self.style_tab.portrait_focus_y = float(style.get('portrait_focus_y', 25))
            self.style_tab.uppercase_lyrics = bool(style.get('uppercase_lyrics', False))
            self.style_tab.set_display_mode(style.get('display_mode', 'KARAOKE'))
            self.style_tab.combo_font.setCurrentText(style.get('font_family', 'Montserrat'))
            self.style_tab.combo_weight.setCurrentText(style.get('font_weight', '900 Cực Đậm'))
            self.style_tab.slider_font_size.setValue(int(style.get('font_size', 38)))
            self.style_tab.set_karaoke_style(style.get('layout_mode', 'left_right'))
            self.style_tab.slider_pos_y.setValue(int(float(style.get('pos_y_bottom', 78)) - 4))
            self.style_tab.slider_stroke.setValue(int(float(style.get('stroke_width', 4))))
            alignment = style.get('text_alignment', 'center')
            self.style_tab.text_alignment = alignment
            {
                'left': self.style_tab.btn_align_left,
                'center': self.style_tab.btn_align_center,
                'right': self.style_tab.btn_align_right,
            }.get(alignment, self.style_tab.btn_align_center).setChecked(True)
            self.style_tab.male_color = QColor(style.get('male_color', '#0026ff'))
            self.style_tab.female_color = QColor(style.get('female_color', '#ff0033'))
            self.style_tab.both_color = QColor(style.get('both_color', '#ff007f'))
            self.style_tab.base_text_color = QColor(style.get('base_color', '#ffffff'))
            self.style_tab.fill_color = QColor(style.get('fill_color', style.get('active_color', '#f59e0b')))
            motion_index = self.style_tab.combo_motion.findText(style.get('motion_effect', ''), Qt.MatchContains)
            if motion_index >= 0:
                self.style_tab.combo_motion.setCurrentIndex(motion_index)
            self.style_tab.custom_singers = copy.deepcopy(style.get('custom_singers', []))
            self.style_tab.populate_singers_list()
            self.style_tab.populate_matrix_checkboxes()
            cover_path = style.get('album_cover_path') or ''
            self.style_tab.album_cover_path = cover_path
            self.style_tab.btn_album_cover.setText(
                f"📷 {os.path.basename(cover_path)[:15]}..." if cover_path else "📷 Chọn ảnh bìa album..."
            )
            self.preview_widget.album_cover_path = cover_path
            self.preview_widget.album_cover_pixmap = (
                QPixmap(cover_path) if cover_path and os.path.exists(cover_path) else QPixmap()
            )
            restored_tracks = []
            for index, item in enumerate(style.get('album_tracks', []) or []):
                if isinstance(item, dict):
                    track = copy.deepcopy(item)
                    track['id'] = str(track.get('id') or f'track_{index + 1:04d}')
                    track['title'] = str(track.get('title') or track.get('name') or f'Track {index + 1:02d}')
                    track['audioSrc'] = track.get('audioSrc') or (self.project.album_audio_paths[index] if index < len(self.project.album_audio_paths) else '')
                    track.setdefault('lyrics', [])
                    track.setdefault('lyricTiming', [])
                else:
                    title = str(item).strip()
                    if not title:
                        continue
                    track = {'id': f'track_{index + 1:04d}', 'title': title,
                             'artist': style.get('track_artist', 'Album Artist'),
                             'audioSrc': self.project.album_audio_paths[index] if index < len(self.project.album_audio_paths) else '',
                             'cover': '', 'duration': 0, 'lyrics': [], 'lyricTiming': []}
                restored_tracks.append(track)
            self.album_state['tracks'] = [
                track for track in restored_tracks
            ]
            restored_active = self.project.album_active_track_id
            valid_ids = {track['id'] for track in self.album_state['tracks']}
            self.album_state['activeTrackId'] = restored_active if restored_active in valid_ids else (self.album_state['tracks'][0]['id'] if self.album_state['tracks'] else None)
            self.preview_widget.set_album_tracks(self.album_state['tracks'], self.album_state['activeTrackId'])
            self.preview_widget.album_title = style.get('album_title', self.project.title or 'My Album')
            self.album_state['selectedTrackId'] = self.album_state['activeTrackId']
            self.style_tab.album_tracks = [track.get('title', 'Track') for track in self.preview_widget.album_tracks]
            self.style_tab.album_title = self.preview_widget.album_title
            if hasattr(self.style_tab, 'txt_album_title'):
                self.style_tab.txt_album_title.blockSignals(True)
                self.style_tab.txt_album_title.setText(self.style_tab.album_title)
                self.style_tab.txt_album_title.blockSignals(False)
            if hasattr(self.style_tab, 'txt_album_tracks'):
                self.style_tab.txt_album_tracks.blockSignals(True)
                self.style_tab.txt_album_tracks.setText(', '.join(self.style_tab.album_tracks))
                self.style_tab.txt_album_tracks.blockSignals(False)
            if self.album_state['activeTrackId']:
                self.on_album_track_selected(self.album_state['activeTrackId'])
            self.style_tab.emit_change()

            effects = copy.deepcopy(self.project.effects)
            elements = copy.deepcopy(self.project.elements)
            self.effects_tab.chk_particles.setChecked(bool(effects.get('particles', False)))
            self.effects_tab.combo_particles.setCurrentText(effects.get('particle_type', 'Golden Sparkles ✨'))
            self.effects_tab.slider_vignette.setValue(int(effects.get('vignette_percent', 20)))
            self.effects_tab.chk_glow.setChecked(bool(effects.get('enable_glow', True)))
            self.effects_tab.slider_glow.setValue(int(effects.get('glow_radius', 8)))
            self.effects_tab.slider_brightness.setValue(int(effects.get('brightness', 0)))
            self.effects_tab.slider_contrast.setValue(int(effects.get('contrast', 0)))
            self.effects_tab.slider_saturation.setValue(int(effects.get('saturation', 0)))
            self.effects_tab.slider_blur.setValue(int(effects.get('blur', 0)))
            tint_index = self.effects_tab.combo_tint.findText(
                effects.get('color_tint', 'None (Original)'), Qt.MatchContains
            )
            if tint_index >= 0:
                self.effects_tab.combo_tint.setCurrentIndex(tint_index)
            self.effects_tab.chk_visualizer.setChecked(bool(elements.get('visualizer', False)))
            visualizer_index = self.effects_tab.combo_vis_mode.findText(
                elements.get('visualizer_mode', 'Bar Spectrum'), Qt.MatchContains
            )
            if visualizer_index >= 0:
                self.effects_tab.combo_vis_mode.setCurrentIndex(visualizer_index)
            self.effects_tab.chk_pointer.setChecked(bool(elements.get('pointer', True)))
            self.effects_tab.chk_watermark.setChecked(bool(elements.get('watermark', False)))
            self.preview_widget.pointer_icon = elements.get('pointer_icon', '🎤')
            self.preview_widget.pointer_icons = elements.get(
                'pointer_icons', {'male': '👨', 'female': '👩', 'both': '🎤'}
            )
            self.templates_tab.set_custom_templates(self.project.custom_templates)
            self.effects_tab.emit_change()

            self.preview_widget.overlay_objects = self.project.overlay_objects
            self.preview_widget.selected_object_idx = None
            self.timeline_widget.set_overlay_objects(self.project.overlay_objects)
            self.preview_widget.set_transitions(self.project.transitions)
            self.timeline_widget.set_transitions(self.project.transitions)

            audio = self.project.audio_settings
            self._last_applied_speed = float(audio.get('speed', 1.0))
            self.media_tab.slider_pitch.setValue(int(audio.get('pitch_semitones', 0)))
            speeds = [0.5, 0.75, 1.0, 1.25, 1.5]
            speed = float(audio.get('speed', 1.0))
            self.media_tab.combo_speed.setCurrentIndex(min(range(len(speeds)), key=lambda i: abs(speeds[i] - speed)))
            self.media_tab.chk_vocal_cut.setChecked(bool(audio.get('vocal_cut', False)))
        finally:
            self._restoring_state = False
    def open_tap_sync_dialog(self):
        lrc_content = self.lyrics_tab.get_lrc_text() or SAMPLE_LRC_VIETNAMESE
        dlg = TapSyncDialog(self.audio_engine, lrc_content, self)
        if dlg.exec_():
            if dlg.generated_lrc:
                self.lyrics_tab.set_lrc_text(dlg.generated_lrc)
                self.on_lyrics_updated(dlg.generated_lrc)

    def open_gemini_dialog(self):
        from gui.gemini_dialog import GeminiDialog
        dlg = GeminiDialog(
            current_lines=self.current_lrc_lines,
            song_title=self.project.title or "Chiếc nón ba tầm",
            parent=self
        )
        dlg.lyrics_extracted.connect(self.on_gemini_lyrics_extracted)
        dlg.roles_detected.connect(self.on_gemini_roles_detected)
        dlg.exec_()

    def on_gemini_lyrics_extracted(self, lrc_or_plain: str, title: str, artist: str):
        if title:
            self.project.title = title
            self.lbl_proj_title.setText(title)
            self.style_tab.track_title = title
            self.preview_widget.track_title = title
        if artist:
            self.style_tab.track_artist = artist
            self.preview_widget.track_artist = artist

        self.lyrics_tab.set_lrc_text(lrc_or_plain)
        self.on_lyrics_updated(lrc_or_plain)
        self._push_project_state()

    def on_gemini_roles_detected(self, roles: list):
        self.style_tab.apply_detected_roles(roles)
        self._push_project_state()

    def open_export_dialog(self):
        style_cfg = dict(self.project.style)
        style_cfg.update(self.project.effects)
        style_cfg.update(self.project.elements)
        style_cfg.update({
            'aspect': self.preview_widget.aspect_ratio,
            'font_family': self.preview_widget.font_family,
            'font_size': self.preview_widget.font_size,
            'stroke_width': self.preview_widget.stroke_width,
            'pos_y': self.preview_widget.pos_y_bottom,
            'layout_mode': self.preview_widget.layout_mode,
            'is_bold': self.preview_widget.is_bold,
            'is_italic': self.preview_widget.is_italic,
            'male_color': self.preview_widget.male_color.name(),
            'female_color': self.preview_widget.female_color.name(),
            'both_color': self.preview_widget.both_color.name(),
            'display_mode': self.preview_widget.display_mode,
            'template_variant': self.preview_widget.template_variant,
            'track_title': self.preview_widget.track_title,
            'track_artist': self.preview_widget.track_artist,
            'portrait_focus_y': self.preview_widget.portrait_focus_y,
            'uppercase_lyrics': self.preview_widget.uppercase_lyrics,
            'motion_effect': self.preview_widget.motion_effect,
            'pos_y_top': self.preview_widget.pos_y_top,
            'pos_y_bottom': self.preview_widget.pos_y_bottom,
            'padding_x': self.preview_widget.padding_x_percent,
            'text_alignment': getattr(self.preview_widget, 'text_alignment', 'center'),
            'album_cover_path': getattr(self.preview_widget, 'album_cover_path', ''),
            'custom_singers': self.preview_widget.custom_singers,
            'overlay_objects': self.preview_widget.overlay_objects,
            'transitions': self.project.transitions,
        })
        dlg = ExportDialog(
            self.sample_bg_path,
            self.audio_engine.current_file or self.sample_audio_path,
            self.current_lrc_lines,
            self.audio_engine.duration,
            style_cfg,
            self
        )
        dlg.exec_()

    def open_license_dialog(self):
        """Display the Design & Software License dialog."""
        from gui.license_dialog import LicenseDialog
        dlg = LicenseDialog(self)
        dlg.exec_()

    def on_clear_cache_clicked(self):
        from core.cache_manager import CacheManager
        res = CacheManager.clear_cache()
        QMessageBox.information(
            self,
            "Dọn Dẹp Bộ Nhớ Đệm Cache",
            f"✅ Đã dọn dẹp sạch toàn bộ cache và tệp tạm!\n\n"
            f"• Số tệp tạm đã xóa: {res.get('files_removed', 0)}\n"
            f"• Dung lượng đã giải phóng: {res.get('mb_freed', 0.0)} MB"
        )

    def closeEvent(self, event):
        try:
            if hasattr(self, 'render_timer') and self.render_timer.isActive():
                self.render_timer.stop()
        except Exception:
            pass
        try:
            if hasattr(self, 'audio_effect_timer') and self.audio_effect_timer.isActive():
                self.audio_effect_timer.stop()
        except Exception:
            pass
        try:
            if hasattr(self, 'autosave_timer') and self.autosave_timer.isActive():
                self.autosave_timer.stop()
        except Exception:
            pass
        try:
            self.audio_engine.close()
        except Exception:
            pass
        try:
            from core.cache_manager import CacheManager
            CacheManager.clear_cache()
        except Exception:
            pass
        super().closeEvent(event)

    def on_render_tick(self):
        """Called every ~16ms to sync audio position, canvas, scrubber, and timeline."""
        try:
            curr_t = self.audio_engine.get_current_time()
            dur_t = self.audio_engine.duration

            # Detect a natural end once, then apply the selected album playback mode.
            now_playing = bool(self.audio_engine.is_playing)
            if self._audio_was_playing and not now_playing and dur_t > 0 and curr_t >= dur_t - 0.05:
                self._handle_album_end()
                curr_t = self.audio_engine.get_current_time()
                dur_t = self.audio_engine.duration
                now_playing = bool(self.audio_engine.is_playing)
            self._audio_was_playing = now_playing

            # Fetch spectrum bands
            bands = self.audio_engine.get_spectrum_bands(32)

            # Update preview canvas
            self.preview_widget.update_playback(curr_t, dur_t, bands)

            # Update timeline playhead
            self.timeline_widget.set_current_time(curr_t, is_playing=self.audio_engine.is_playing)

            # Update time labels: 00:47 / 03:37
            c_m, c_s = int(curr_t // 60), int(curr_t % 60)
            d_m, d_s = int(dur_t // 60), int(dur_t % 60)
            self.lbl_time_cur.setText(f"{c_m:02d}:{c_s:02d}")
            self.lbl_time_dur.setText(f"{d_m:02d}:{d_s:02d}")

            # Update slider if not currently dragging
            if not self.seek_slider.isSliderDown() and dur_t > 0:
                self.seek_slider.setValue(int((curr_t / dur_t) * 1000))

            # Reset play button text if finished
            if not self.audio_engine.is_playing:
                self.btn_play.setText("")
                self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        except Exception:
            pass
