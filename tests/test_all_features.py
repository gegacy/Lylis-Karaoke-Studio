import os
import sys
import numpy as np
from PyQt5.QtWidgets import QApplication

# Ensure QApplication exists for GUI tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.lrc_engine import LrcEngine
from core.ass_generator import AssGenerator
from core.audio_engine import AudioEngine
from core.project_model import ProjectModel
from core.undo_manager import UndoRedoManager
from core.sample_data import ensure_sample_assets, SAMPLE_LRC_VIETNAMESE
from core.ai.voice_detector import VoiceGenderDetector
from core.ai.lyric_aligner import LyricAligner
from gui.preview_widget import PreviewWidget
from gui.inspector_panel import InspectorPanel
from gui.tabs.media_tab import MediaTab
from gui.tabs.style_tab import StyleTab
from gui.tabs.transitions_tab import TransitionsTab

def test_lrc_engine_parse_and_export():
    sample = """[00:28.84](00:28.84)Chiếc (00:29.12)nón (00:29.42)ba (00:29.79)tầm
[00:30.73](00:30.73)Tà (00:31.07)áo (00:31.57)mở {singer:female}
[00:33.95](00:33.95)Anh (00:34.24)yêu (00:34.57)em {singer:male}"""
    
    lines = LrcEngine.parse(sample)
    assert len(lines) == 3
    assert lines[0].words[0].text.strip() == "Chiếc"
    assert lines[1].singer == "female"
    assert lines[2].singer == "male"
    
    exported_lrc = LrcEngine.export_lrc(lines)
    assert "[00:28.84]" in exported_lrc
    assert "{singer:female}" in exported_lrc
    
    exported_srt = LrcEngine.export_srt(lines)
    assert "-->" in exported_srt
    assert "[Nữ]" in exported_srt

def test_ass_generator():
    lines = LrcEngine.parse(SAMPLE_LRC_VIETNAMESE)
    ass_text = AssGenerator.generate_ass(lines)
    assert "[Script Info]" in ass_text
    assert "[V4+ Styles]" in ass_text
    assert "KaraokeTop" in ass_text
    assert "KaraokeBottom" in ass_text
    assert r"{\kf" in ass_text

def test_project_model_serialization(tmp_path):
    proj = ProjectModel(title="Test Project", aspect_ratio="9:16", duration=50.0)
    proj.style["font_family"] = "Inter"
    proj.elements["particles"] = True
    proj.raw_lrc_text = SAMPLE_LRC_VIETNAMESE
    
    file_path = str(tmp_path / "test_proj.json")
    proj.save_to_file(file_path)
    
    loaded = ProjectModel.load_from_file(file_path)
    assert loaded.title == "Test Project"
    assert loaded.aspect_ratio == "9:16"
    assert loaded.style["font_family"] == "Inter"
    assert loaded.raw_lrc_text == SAMPLE_LRC_VIETNAMESE

def test_undo_manager():
    mgr = UndoRedoManager(max_depth=10)
    state1 = {"step": 1, "text": "A"}
    state2 = {"step": 2, "text": "B"}
    state3 = {"step": 3, "text": "C"}
    
    mgr.push_state(state1)
    mgr.push_state(state2)
    mgr.push_state(state3)
    
    assert mgr.can_undo()
    prev = mgr.undo(state3)
    assert prev["step"] == 2
    
    prev2 = mgr.undo(prev)
    assert prev2["step"] == 1
    
    assert mgr.can_redo()
    nxt = mgr.redo(prev2)
    assert nxt["step"] == 2

def test_audio_engine_and_sample_assets():
    bg_path, audio_path = ensure_sample_assets()
    assert os.path.exists(bg_path)
    assert os.path.exists(audio_path)
    
    engine = AudioEngine()
    loaded = engine.load_audio(audio_path)
    assert loaded is True
    assert engine.duration > 0
    assert len(engine.waveform_peaks) > 0
    
    bands = engine.get_spectrum_bands(32)
    assert len(bands) == 32

def test_voice_detector_and_aligner():
    sr = 44100
    t = np.linspace(0, 0.5, int(sr * 0.5))
    
    male_wave = np.sin(2 * np.pi * 120 * t)
    f0_male = VoiceGenderDetector.estimate_f0(male_wave, sr)
    assert 110.0 <= f0_male <= 130.0
    
    female_wave = np.sin(2 * np.pi * 240 * t)
    f0_female = VoiceGenderDetector.estimate_f0(female_wave, sr)
    assert 230.0 <= f0_female <= 250.0
    
    gender_m, _ = VoiceGenderDetector.detect_line_gender(male_wave, sr, 0.0, 0.5, "Anh đi tìm em")
    assert gender_m == "male"
    
    gender_f, _ = VoiceGenderDetector.detect_line_gender(female_wave, sr, 0.0, 0.5, "Em thương anh nhiều")
    assert gender_f == "female"
    
    whisper_dummy = [
        {
            'text': 'Chiếc nón ba tầm',
            'words': [
                {'word': 'Chiếc', 'start': 1.0, 'end': 1.5},
                {'word': 'nón', 'start': 1.5, 'end': 2.0},
                {'word': 'ba', 'start': 2.0, 'end': 2.5},
                {'word': 'tầm', 'start': 2.5, 'end': 3.0}
            ]
        }
    ]
    aligned = LyricAligner.align_official_lyrics("Chiếc nón ba tầm", whisper_dummy)
    assert len(aligned) == 1
    assert len(aligned[0]['words']) == 4

def test_preview_widget_rendering():
    pw = PreviewWidget()
    lines = LrcEngine.parse(SAMPLE_LRC_VIETNAMESE)
    pw.set_lyrics(lines)
    pw.update_playback(30.0, 50.0, [0.5] * 32)
    pw.resize(800, 450)
    assert pw.aspect_ratio == '16:9'
    assert len(pw.lyric_lines) > 0
    assert pw.male_color.name() == "#0026ff"
    assert pw.female_color.name() == "#ff0033"

def test_media_tab_filtering():
    mt = MediaTab()
    mt.search_input.setText("sample_audio")
    assert any(not item.isHidden() for item in mt.media_items if "sample_audio" in item.filename)
    mt.search_input.clear()
    mt.set_filter("audio")
    assert any(item.media_type == "audio" and not item.isHidden() for item in mt.media_items)

def test_style_tab_song_ca_roles():
    st = StyleTab()
    lines = LrcEngine.parse(SAMPLE_LRC_VIETNAMESE)
    st.set_lyric_lines(lines)
    assert len(st.role_row_widgets) == len(lines)
    
    # Toggle first line to first singer
    st.role_row_widgets[0].singer_checkboxes[0].setChecked(True)
    assert lines[0].singer in ("female", "male", st.custom_singers[0]["name"], st.custom_singers[0].get("role", "female"))
    
    # Toggle second line to second singer
    st.role_row_widgets[1].singer_checkboxes[1].setChecked(True)
    assert lines[1].singer in ("female", "male", st.custom_singers[1]["name"], st.custom_singers[1].get("role", "male"))

    # Toggle Both
    st.role_row_widgets[0].chk_both.setChecked(True)
    assert lines[0].singer == "both"

def test_inspector_panel_and_transitions():
    inspector = InspectorPanel()
    obj = {
        'content': 'Test Lyric Overlay',
        'font_family': 'Montserrat',
        'font_size': 48,
        'x_pct': 30.0,
        'y_pct': 50.0,
        'w_pct': 40.0,
        'h_pct': 12.0,
        'rotation': 0
    }
    inspector.set_object(obj)
    assert inspector.txt_content.text() == 'Test Lyric Overlay'
    assert inspector.spin_size.value() == 48

    tt = TransitionsTab()
    assert tt is not None

def test_templates_tab_gallery():
    from gui.tabs.templates_tab import TemplatesTab, TEMPLATES_DATA
    ttab = TemplatesTab()
    assert len(ttab.cards) == len(TEMPLATES_DATA)
    
    # Filter to duet
    ttab.set_category("duet")
    duet_visible = [card for card, t in ttab.cards if not card.isHidden()]
    assert len(duet_visible) >= 1
    
    # Search for tiki
    ttab.search_input.setText("tiki")
    tiki_cards = [card for card, t in ttab.cards if not card.isHidden()]
    assert len(tiki_cards) == 1
    assert "TIKI TIKI" in ttab.cards[0][1]["name"]

def test_capcut_editing_features():
    from gui.timeline_widget import TimelineWidget
    from gui.tabs.effects_tab import EffectsTab
    
    # 1. Timeline Split, Duplicate, and Delete
    tw = TimelineWidget()
    lines = LrcEngine.parse(SAMPLE_LRC_VIETNAMESE)
    initial_count = len(lines)
    tw.set_lyrics(lines)
    tw.set_current_time(lines[0].line_start + 0.5)
    
    # Split line
    tw.split_line()
    assert len(tw.canvas.lyric_lines) == initial_count + 1
    
    # Duplicate line
    tw.canvas.selected_line_idx = 0
    tw.canvas.selected_line_indices = {0}
    tw.duplicate_line()
    assert len(tw.canvas.lyric_lines) == initial_count + 2
    
    # Delete line
    tw.canvas.selected_line_idx = 0
    tw.canvas.selected_line_indices = {0}
    tw.delete_line()
    assert len(tw.canvas.lyric_lines) == initial_count + 1
    
    # 2. Effects Tab CapCut Adjustments
    eff = EffectsTab()
    eff.slider_brightness.setValue(15)
    eff.slider_contrast.setValue(20)
    eff.slider_saturation.setValue(10)
    eff.slider_blur.setValue(5)
    eff.combo_tint.setCurrentText("🎬 Cinematic Teal & Orange")
    eff.emit_change()
    assert eff.slider_brightness.value() == 15

def test_singer_inline_editing():
    from gui.tabs.style_tab import StyleTab
    st = StyleTab()
    assert len(st.singer_cards) > 0
    
    # Edit first singer name
    card = st.singer_cards[0]
    card.txt_name.setText("SƠN TÙNG M-TP")
    card.on_name_edited()
    
    assert st.custom_singers[0]['name'] == "SƠN TÙNG M-TP"
    assert "SƠN TÙNG M-TP" in st.matrix_checkboxes[0].text()

def test_ambient_album_template_rendering_fixes():
    from gui.preview_widget import PreviewWidget
    from core.lrc_engine import LrcEngine
    from PyQt5.QtGui import QPainter, QImage
    
    pw = PreviewWidget()
    pw.template_variant = "ambient_album_player"
    pw.set_lyrics(LrcEngine.parse(SAMPLE_LRC_VIETNAMESE))
    pw.update_playback(5.0, 42.0)
    
    img = QImage(1280, 720, QImage.Format_ARGB32)
    p = QPainter(img)
    pw.draw_ambient_album_stage(p, pw.get_viewport_rect())
    pw.draw_ambient_album_lyrics(p, pw.get_viewport_rect())
    p.end()
    assert not img.isNull()

def test_gemini_service_and_dialog():
    from core.ai.gemini_service import GeminiService
    from gui.gemini_dialog import GeminiDialog
    
    # Test fallback extraction without throwing
    res = GeminiService.extract_lyrics_from_song_info("Chiếc nón ba tầm", "Lylis")
    assert "lyrics_plain" in res or "lrc_text" in res
    
    # Test auto gender/duet roles detection
    lines = ["Anh nhớ em nhiều lắm", "Em cũng nhớ anh", "Chúng ta cùng hát"]
    roles = GeminiService.auto_detect_duet_roles(lines, "Song ca")
    assert len(roles) == 3
    assert roles[0] == "male"
    assert roles[1] == "female"
    assert roles[2] == "both"
    
    # Test Gemini Dialog UI
    dlg = GeminiDialog(current_lines=lines)
    assert dlg.tab_extract is not None
    assert dlg.tab_roles is not None

def test_cache_manager():
    from core.cache_manager import CacheManager
    
    # Auto clean start
    CacheManager.auto_clean_on_start()
    
    # Get size and clear cache
    sz = CacheManager.get_cache_size()
    assert isinstance(sz, int)
    
    res = CacheManager.clear_cache()
    assert "files_removed" in res
    assert "bytes_freed" in res
    assert "mb_freed" in res

def test_overlay_objects_preview_and_render():
    from gui.preview_widget import PreviewWidget
    from core.video_renderer import VideoRenderer
    from PIL import Image
    from PyQt5.QtGui import QPainter, QImage

    pw = PreviewWidget()
    pw.overlay_objects = [
        {'type': 'text', 'content': 'Test Text', 'x_pct': 20, 'y_pct': 30, 'w_pct': 40, 'h_pct': 10},
        {'type': 'shape', 'color': '#ff2d55', 'x_pct': 10, 'y_pct': 10, 'w_pct': 20, 'h_pct': 15},
        {'type': 'lower_third', 'title': 'SONG', 'subtitle': 'ARTIST', 'x_pct': 5, 'y_pct': 80, 'w_pct': 90, 'h_pct': 12},
        {'type': 'vinyl', 'title': 'VINYL', 'x_pct': 40, 'y_pct': 20, 'w_pct': 20, 'h_pct': 30}
    ]
    
    # Test preview drawing
    img = QImage(1280, 720, QImage.Format_ARGB32)
    p = QPainter(img)
    pw.draw_overlay_objects(p, pw.get_viewport_rect())
    p.end()
    assert not img.isNull()
    
    # Test VideoRenderer overlay drawing
    pil_frame = Image.new("RGB", (1280, 720), (30, 41, 59))
    VideoRenderer._draw_overlays(pil_frame, 0.5, {"overlay_objects": pw.overlay_objects})
    assert pil_frame.size == (1280, 720)

def test_tap_sync_dialog_instantiation():
    from core.audio_engine import AudioEngine
    from gui.tap_sync_dialog import TapSyncDialog
    
    engine = AudioEngine()
    dlg = TapSyncDialog(engine, "Chiếc nón ba tầm\nMà làm anh nhớ")
    assert dlg.txt_input is not None
    assert dlg.prog_bar is not None
    assert dlg.btn_start is not None
