import json

from PIL import Image, ImageChops
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap

from core.lrc_engine import LrcEngine, LyricLine
from core.auto_editor import prepare_auto_edit, detect_beat_times
from core.media_timing import looping_frame_index
from core.project_model import ProjectModel
from core.video_renderer import VideoRenderer
from gui.main_window import MainWindow
from gui.timeline_widget import TimelineCanvas, TimelineWidget
from gui.tabs.lyrics_tab import LyricsTab
from gui.tabs.templates_tab import TEMPLATES_DATA


app = QApplication.instance() or QApplication([])


def test_auto_edit_times_plain_lyrics_and_exports_lrc():
    lines, exported = prepare_auto_edit("one two\nthree four\nfive", 9.0)
    assert len(lines) == 3
    assert [line.full_text for line in lines] == ["one two", "three four", "five"]
    assert lines[0].line_start == 0.0
    assert lines[0].line_end <= lines[1].line_start
    assert exported.startswith("[00:00.00]")
    assert "(00:00.00)one" in exported


def test_auto_edit_snaps_nearby_lines_to_strong_beats():
    peaks = [0.1] * 100
    peaks[20] = 1.0
    peaks[55] = 0.95
    beats = detect_beat_times(peaks, 10.0)
    assert beats and abs(beats[0] - (20 / 99 * 10.0)) < 0.2
    lines, _ = prepare_auto_edit("one\ntwo\nthree\nfour\nfive", 10.0, peaks)
    assert abs(lines[1].line_start - beats[0]) < 0.19


def test_full_project_state_is_json_serializable_and_round_trips(tmp_path):
    project = ProjectModel(title="Integrated")
    assert project.elements["pointer_icon"] == "🎤"
    assert project.elements["pointer_icons"] == {"male": "👨", "female": "👩", "both": "🎤"}
    project.style.update({"male_color": "#123456", "display_mode": "KARAOKE"})
    project.effects["vignette_percent"] = 25
    project.transitions["start"] = {"name": "Fade", "duration": 1.5}
    project.overlay_objects = [{"type": "shape", "color": "#ff0000", "x_pct": 10}]
    project.audio_settings["speed"] = 0.75

    json.dumps(project.to_dict())
    path = tmp_path / "project.lylis.json"
    project.save_to_file(str(path))
    loaded = ProjectModel.load_from_file(str(path))

    assert loaded.effects["vignette_percent"] == 25
    assert loaded.transitions["start"]["name"] == "Fade"
    assert loaded.overlay_objects[0]["type"] == "shape"
    assert loaded.audio_settings["speed"] == 0.75


def test_ass_import_and_timestamp_rollover_are_stable():
    tab = LyricsTab()
    ass = r"""[Events]
Dialogue: 0,0:00:59.99,0:01:01.00,KaraokeTop,,0,0,0,,{\kf50}Xin {\kf50}chào
"""
    converted = tab.convert_ass_to_lrc(ass)
    lines = LrcEngine.parse(converted)
    assert len(lines) == 1
    assert [word.text.strip() for word in lines[0].words] == ["Xin", "chào"]
    assert LrcEngine.format_timestamp(59.999) == "01:00.00"


def test_background_video_timing_uses_source_fps_and_loops():
    assert looping_frame_index(0.5, 30, duration=2.0) == 15
    assert looping_frame_index(2.5, 30, duration=2.0) == 15
    assert looping_frame_index(3.0, 24, frame_count=48) == 24
    assert looping_frame_index(-10, 0) == 0


def test_renderer_contract_and_real_tiny_export(tmp_path):
    background = Image.new("RGB", (320, 180), (20, 30, 40))
    lines = LrcEngine.parse("[00:00.00](00:00.00)Hello (00:00.10)world")
    style = {
        "resolution": (160, 90),
        "fps": 5,
        "overlay_objects": [{
            "type": "shape", "color": "#ff2d55", "x_pct": 5, "y_pct": 5,
            "w_pct": 10, "h_pct": 10,
        }],
        "vignette_percent": 10,
        "transitions": {"start": {"name": "Fade", "duration": 0.1}, "end": None},
    }
    frame = VideoRenderer.render_frame(background, lines, 0.15, 0.2, style)
    assert frame.size == (160, 90)

    bg_path = tmp_path / "background.png"
    output_path = tmp_path / "tiny.mp4"
    background.save(bg_path)
    progress = []
    success = VideoRenderer.render_video(
        str(output_path), str(bg_path), "", lines, 0.2, style, progress.append
    )
    assert success is True
    assert output_path.exists() and output_path.stat().st_size > 0
    assert progress[-1] == 100


def test_tiki_template_matches_preview_and_export_contract():
    template = next(item for item in TEMPLATES_DATA if item["id"] == "tiki_tiki")
    assert template["template_variant"] == "tiki_tiki"
    assert [singer["role"] for singer in template["custom_singers"]] == ["female", "male"]
    assert template["particles"] is False

    lines = LrcEngine.parse(
        "[00:01.00]Singer A line {singer:female}\n"
        "[00:04.00]Singer B line {singer:male}\n"
        "[00:07.00]Duet line {singer:both}"
    )
    style = {**template, "resolution": (640, 360)}
    frame = VideoRenderer.render_frame(Image.new("RGB", (640, 360), "black"), lines, 1.5, 10, style)
    assert frame.size == (640, 360)
    assert frame.getpixel((10, 350)) == (251, 250, 240)
    assert sum(frame.getpixel((160, 100))) > sum(frame.getpixel((480, 100)))


def test_karaoke_pointer_uses_microphone_in_export():
    assert VideoRenderer.resolve_pointer_icon({}, "male") == "👨"
    assert VideoRenderer.resolve_pointer_icon({}, "female") == "👩"
    assert VideoRenderer.resolve_pointer_icon({}, "both") == "🎤"
    lines = LrcEngine.parse("[00:00.00](00:00.00)Hello")
    style = {
        "resolution": (640, 360),
        "display_mode": "KARAOKE",
        "layout_mode": "center",
        "font_size": 48,
        "pos_y_bottom": 60,
        "pointer": True,
        "pointer_icon": "🎤",
    }
    frame = VideoRenderer.render_frame(Image.new("RGB", (640, 360), "black"), lines, 0.05, 1, style)
    # The badge immediately left of the centered word contains a bright microphone glyph.
    badge_area = frame.crop((245, 190, 290, 235))
    assert any(max(color) > 220 for _, color in badge_area.getcolors(maxcolors=badge_area.width * badge_area.height))


def test_export_fits_long_single_lines_and_animates_rotated_overlays():
    background = Image.new("RGB", (640, 360), "black")
    lines = LrcEngine.parse(
        "[00:00.00]This is an intentionally very long karaoke lyric line that must remain inside the frame"
    )
    lyric_style = {
        "resolution": (640, 360),
        "display_mode": "KARAOKE",
        "layout_mode": "left_right",
        "font_size": 60,
        "pos_y_bottom": 60,
        "pointer": False,
        "base_color": "#ffffff",
        "male_color": "#ffffff",
        "female_color": "#ffffff",
        "both_color": "#ffffff",
    }
    lyric_frame = VideoRenderer.render_frame(background, lines, 0.1, 1, lyric_style)
    bounds = ImageChops.difference(lyric_frame, background).getbbox()
    assert bounds is not None
    assert bounds[0] > 20 and bounds[2] < 620

    vinyl = {
        "type": "vinyl", "title": "LYLIS", "x_pct": 35, "y_pct": 20,
        "w_pct": 30, "h_pct": 55, "rotation": 15,
    }
    frame_a = VideoRenderer.render_frame(
        background, [], 0.0, 2, {"resolution": (640, 360), "overlay_objects": [vinyl]}
    )
    frame_b = VideoRenderer.render_frame(
        background, [], 1.0, 2, {"resolution": (640, 360), "overlay_objects": [vinyl]}
    )
    assert ImageChops.difference(frame_a, frame_b).getbbox() is not None


def test_ambient_album_player_template_and_renderer_contract():
    template = next(item for item in TEMPLATES_DATA if item["id"] == "ambient_album_player")
    assert template["template_variant"] == "ambient_album_player"
    assert template["display_mode"] == "SINGLE"
    assert template["particles"] is False

    lines = LrcEngine.parse(
        "[00:01.00]Current lyric is bright\n"
        "[00:04.00]The next lyric stays muted\n"
        "[00:07.00]Another queued lyric"
    )
    style = {**template, "resolution": (640, 360)}
    background = Image.new("RGB", (640, 360), (90, 180, 170))
    frame = VideoRenderer.render_frame(background, lines, 1.5, 10, style)
    assert frame.size == (640, 360)
    # The cover retains the source art while the surrounding canvas is darkened.
    assert sum(frame.getpixel((90, 90))) > sum(frame.getpixel((620, 340)))
    # Progress track appears below the cover.
    assert sum(frame.getpixel((40, 322))) > 300


def test_walters_reference_template_has_frosted_lyric_queue():
    template = next(item for item in TEMPLATES_DATA if item["id"] == "walters_lyric_queue")
    assert template["template_variant"] == "walters_lyric_queue"
    assert template["reference_url"].endswith("wxWL7ybL_ZM")
    assert template["particles"] is False
    assert template["pointer"] is False

    lines = LrcEngine.parse(
        "[00:01.00]I've got to get away and let you go\n"
        "[00:04.00]But I love you so\n"
        "[00:07.00]I love you so\n"
        "[00:10.00]I love you so\n"
        "[00:13.00]I love you so"
    )
    background = Image.new("RGB", (640, 360), (225, 218, 193))
    style = {**template, "resolution": (640, 360)}
    frame = VideoRenderer.render_frame(background, lines, 4.5, 16, style)

    assert frame.size == (640, 360)
    # Album cover remains light while the surrounding canvas is muted charcoal.
    assert sum(frame.getpixel((125, 170))) > sum(frame.getpixel((610, 340)))
    # The active row's frosted panel is brighter than the gap beneath it.
    assert sum(frame.getpixel((330, 160))) > sum(frame.getpixel((330, 140)))


def test_ksector_reference_template_has_y2k_editorial_layout():
    template = next(item for item in TEMPLATES_DATA if item["id"] == "ksector_2000s_editorial")
    assert template["template_variant"] == "ksector_2000s_editorial"
    assert template["reference_url"].endswith("BbJ4ibqR6PQ")
    assert template["display_mode"] == "COLOR CODED"
    assert template["font_family"] == "Impact"
    assert template["portrait_focus_y"] == 25
    assert template["uppercase_lyrics"] is True

    lines = LrcEngine.parse(
        "[00:01.00]Just one ten minutes\n"
        "[00:04.00]The moment you become mine\n"
        "[00:07.00]Baby you are wavering"
    )
    lines[0].singer = "female"
    background = Image.new("RGB", (640, 360), (92, 76, 62))
    style = {**template, "resolution": (640, 360)}
    intro = VideoRenderer.render_frame(background, lines, 0.0, 10, style)
    active = VideoRenderer.render_frame(background, lines, 1.5, 10, style)

    assert intro.size == (640, 360)
    # The lower editorial field stays ivory while the portrait header remains warm and dark.
    assert sum(intro.getpixel((80, 270))) > sum(intro.getpixel((80, 80)))
    # The oversized title card is replaced by singer-colored lyrics after playback starts.
    assert ImageChops.difference(intro, active).getbbox() is not None

    zero_start_lines = LrcEngine.parse(
        "[00:00.00]Lyrics must win at the first frame\n[00:03.00]Next line"
    )
    zero_start = VideoRenderer.render_frame(background, zero_start_lines, 0.0, 5, style)
    title_only = VideoRenderer.render_frame(background, [], 0.0, 5, style)
    assert ImageChops.difference(zero_start, title_only).getbbox() is not None

    window = MainWindow()
    try:
        window.on_template_applied(template)
        assert window.project.style["portrait_focus_y"] == 25
        assert window.project.style["uppercase_lyrics"] is True
        assert window.preview_widget.portrait_focus_y == 25
        assert window.preview_widget.uppercase_lyrics is True

        saved_state = window.project.to_dict()
        window.style_tab.portrait_focus_y = 70
        window.style_tab.uppercase_lyrics = False
        window.restore_project_state(saved_state)
        assert window.style_tab.portrait_focus_y == 25
        assert window.style_tab.uppercase_lyrics is True
        assert window.preview_widget.portrait_focus_y == 25
        assert window.preview_widget.uppercase_lyrics is True
    finally:
        window.close()


def test_reference_template_applies_complete_style_and_effect_state():
    template = next(item for item in TEMPLATES_DATA if item["id"] == "riptide_sunset")
    assert template["display_mode"] == "SINGLE"
    assert template["layout_mode"] == "center"
    assert template["pointer"] is False

    window = MainWindow()
    try:
        window.on_template_applied(template)
        assert window.project.style["base_color"] == "#ffffff"
        assert window.project.style["stroke_width"] == 3
        assert window.project.style["pos_y_bottom"] == 58.0
        assert window.project.effects["color_tint"] == "Warm Sunset"
        assert window.project.effects["blur"] == 1
        assert window.project.elements["pointer"] is False

        duet = next(item for item in TEMPLATES_DATA if item["id"] == "tiki_tiki")
        window.on_template_applied(duet)
        assert window.project.style["track_artist"] == "SUZANA, VANNDA"
        window.style_tab.custom_singers[0]["name"] = "Edited singer"
        assert duet["custom_singers"][0]["name"] == "SUZANA"
    finally:
        window.close()


def test_every_template_is_editable_and_resets_preset_only_fields():
    window = MainWindow()
    try:
        for template in TEMPLATES_DATA:
            window.on_template_applied(template)
            assert window.project.style["font_family"] == template["font_family"]
            assert window.project.style["font_size"] == template["font_size"]
            assert window.project.effects["particles"] == bool(template.get("particles", False))
            assert window.project.elements["pointer"] == bool(template.get("pointer", False))
            # Controls remain live after applying a preset.
            window.style_tab.slider_font_size.setValue(36)
            assert window.project.style["font_size"] == 36
    finally:
        window.close()


def test_every_template_applies_and_renders_without_stale_visualizer_state():
    window = MainWindow()
    background = Image.new("RGB", (640, 360), (80, 80, 90))
    lines = LrcEngine.parse("[00:00.50]Template smoke test")
    try:
        for template in TEMPLATES_DATA:
            window.on_template_applied(template)
            assert window.project.style["font_family"] == template["font_family"]
            assert window.project.elements["visualizer"] == bool(template.get("visualizer", False))
            frame = VideoRenderer.render_frame(
                background, lines, 1.0, 5.0, {**template, "resolution": (640, 360)}
            )
            assert frame.size == (640, 360)
    finally:
        window.close()


def test_hanako_falling_you_reference_template_renders_vinyl_layout():
    template = next(item for item in TEMPLATES_DATA if item["id"] == "hanako_falling_you")
    assert template["template_variant"] == "hanako_falling_you"
    lines = LrcEngine.parse("[00:01.00]Falling you")
    frame = VideoRenderer.render_frame(Image.new("RGB", (640, 360), (180, 175, 165)), lines, 2.0, 10.0, {**template, "resolution": (640, 360)})
    assert frame.size == (640, 360)
    assert ImageChops.difference(frame, Image.new("RGB", (640, 360), (180, 175, 165))).getbbox() is not None


def test_falling_u_douyin_dj_template():
    template = next(item for item in TEMPLATES_DATA if item["id"] == "falling_u_douyin_dj")
    assert template["template_variant"] == "falling_u_douyin_dj"
    assert template["reference_url"].endswith("kYB3N2SGuO4")
    lines = LrcEngine.parse("[00:01.00]Falling U Falling U\n[00:04.00]Douyin DJ Remix")
    bg = Image.new("RGB", (640, 360), (10, 4, 22))
    frame = VideoRenderer.render_frame(bg, lines, 2.0, 10.0, {**template, "resolution": (640, 360)})
    assert frame.size == (640, 360)
    assert ImageChops.difference(frame, bg).getbbox() is not None

    window = MainWindow()
    try:
        window.on_template_applied(template)
        assert window.preview_widget.template_variant == "falling_u_douyin_dj"
        assert window.style_tab.template_variant == "falling_u_douyin_dj"
    finally:
        window.close()


def test_main_window_features_share_one_project_state():
    window = MainWindow()
    try:
        assert window.tab_widget.count() == 7
        window.on_transition_applied("Fade (Hoà tan)", "start")
        assert window.project.transitions["start"]["name"].startswith("Fade")
        assert window.preview_widget.transitions == window.project.transitions

        window.elements_tab.create_rect_object()
        assert window.project.overlay_objects[-1]["type"] == "shape"
        window.inspector_panel.current_color.setNamedColor("#00ff00")
        window.inspector_panel.emit_change()
        assert window.project.overlay_objects[-1]["color"] == "#00ff00"

        lines = window.current_lrc_lines
        lines[0].singer = "female"
        window.on_singer_roles_updated(lines)
        assert "{singer:female}" in window.project.raw_lrc_text
        json.dumps(window.project.to_dict())

        blank_project = ProjectModel(title="No media")
        window.restore_project_state(blank_project.to_dict())
        assert window.audio_engine.current_file is None
        assert window.preview_widget.bg_pixmap is None
        assert window.timeline_widget.canvas.media_label == "No background"
        assert window.timeline_widget.canvas.audio_label == "No audio"
    finally:
        window.close()


def test_preview_waveform_state_is_initialized_for_audio_reactive_templates():
    window = MainWindow()
    try:
        window.preview_widget.set_waveform([0.2, 1.2, -0.1])
        assert window.preview_widget.waveform_peaks == [0.2, 1.0, 0.0]
    finally:
        window.close()


def test_render_tick_updates_existing_time_labels_without_runtime_error():
    window = MainWindow()
    try:
        window.on_render_tick()
        assert window.lbl_time_cur.text() == "00:00"
    finally:
        window.close()


def test_professional_shell_panels_focus_mode_and_custom_aspect():
    window = MainWindow()
    try:
        window.show()
        app.processEvents()
        assert window.splitter_main.handleWidth() == 1
        assert window.splitter_right.handleWidth() == 1
        assert window.inspector_panel.minimumWidth() == 240
        assert window.inspector_panel.maximumWidth() == 440

        window.change_aspect("4:5")
        assert window.preview_widget.aspect_ratio == "4:5"
        viewport = window.preview_widget.get_viewport_rect()
        assert abs((viewport.width() / viewport.height()) - 0.8) < 0.02

        window.on_preview_zoom_changed("50%")
        assert window.preview_widget.preview_zoom == 0.5
        window.toggle_preview_focus()
        assert window._preview_focus_mode is True
        assert window.header_bar.isHidden()
        assert window.timeline_container.isHidden()
        window.exit_preview_focus()
        assert window._preview_focus_mode is False
        assert not window.header_bar.isHidden()
    finally:
        window.close()


def test_cancelled_custom_aspect_keeps_previous_ratio_and_button(monkeypatch):
    window = MainWindow()
    try:
        window.change_aspect("4:5")
        monkeypatch.setattr("gui.main_window.QInputDialog.getText", lambda *args, **kwargs: ("", False))
        window.btn_aspect_custom.setChecked(True)
        window.choose_custom_aspect()
        assert window.project.aspect_ratio == "4:5"
        assert window.preview_widget.aspect_ratio == "4:5"
        assert window.btn_aspect_45.isChecked()
    finally:
        window.close()


def test_add_layer_uses_existing_tab_widget_and_keeps_project_state():
    window = MainWindow()
    try:
        count_before = len(window.project.overlay_objects)
        window.on_add_layer_clicked()
        assert window.tab_widget.currentWidget() is window.elements_tab
        assert len(window.project.overlay_objects) == count_before + 1
    finally:
        window.close()


def test_overlay_inspector_preserves_visibility_lock_and_opacity_state():
    window = MainWindow()
    try:
        window.elements_tab.create_rect_object()
        obj = window.project.overlay_objects[-1]
        window.inspector_panel.set_object(obj)
        window.inspector_panel.slider_opacity.setValue(45)
        window.inspector_panel.chk_locked.setChecked(True)
        assert obj["opacity"] == 0.45
        assert obj["locked"] is True

        window.inspector_panel.chk_visible.setChecked(False)
        assert obj["visible"] is False
        assert window.preview_widget.overlay_objects[-1]["visible"] is False
    finally:
        window.close()


def test_unsorted_lrc_is_normalized_without_negative_line_durations():
    lines = LrcEngine.parse("[00:08.00]later\n[00:02.00]earlier\n[00:05.00]middle")
    assert [line.line_start for line in lines] == [2.0, 5.0, 8.0]
    assert all(line.line_end >= line.line_start for line in lines)


def test_timeline_clamps_seek_and_ignores_invalid_beat_markers():
    timeline = TimelineCanvas()
    timeline.resize(600, 260)
    timeline.set_duration(2.0)
    timeline.set_zoom(10.0)
    assert timeline.x_to_time(timeline.width()) == 2.0
    timeline.set_current_time(99.0)
    assert timeline.current_time == 2.0
    timeline.set_beat_times([0.5, "bad", None, float("inf"), 3.0])
    assert timeline.beat_times == [0.5]


def test_follow_playhead_autoscroll_respects_zoom_and_manual_scroll():
    timeline = TimelineCanvas()
    timeline.resize(800, 260)
    timeline.set_duration(120.0)
    timeline.set_zoom(10.0)

    timeline.set_current_time(0.0, is_playing=True)
    timeline.set_current_time(9.0, is_playing=True)
    assert timeline.scroll_offset > 0.0
    assert timeline.scroll_offset <= timeline.current_time <= timeline.scroll_offset + timeline.zoom_seconds
    playhead_x = timeline.time_to_x(timeline.current_time)
    assert timeline.header_width <= playhead_x <= timeline.width()

    clip_spacing = timeline.time_to_x(12.0) - timeline.time_to_x(10.0)
    timeline.scroll_horizontally(20.0, user_initiated=True)
    manual_offset = timeline.scroll_offset
    assert timeline._manual_follow_resume_at > 0.0
    timeline.set_current_time(9.5, is_playing=True)
    assert timeline.scroll_offset == manual_offset
    assert abs((timeline.time_to_x(12.0) - timeline.time_to_x(10.0)) - clip_spacing) < 1e-6

    # Follow resumes automatically after the manual-scroll grace period.
    timeline._manual_follow_resume_at = 0.0
    timeline.set_current_time(10.0, is_playing=True)
    assert timeline.scroll_offset <= 10.0 <= timeline.scroll_offset + timeline.zoom_seconds

    # Starting playback again also resumes follow immediately.
    timeline.scroll_horizontally(30.0, user_initiated=True)
    timeline.set_playback_active(False)
    timeline.set_current_time(15.0, is_playing=False)
    timeline.set_playback_active(True)
    assert timeline.scroll_offset <= 15.0 <= timeline.scroll_offset + timeline.zoom_seconds

    timeline.set_zoom(20.0)
    assert timeline.scroll_offset <= 15.0 <= timeline.scroll_offset + timeline.zoom_seconds


def test_follow_playhead_button_can_disable_and_reenable_following():
    widget = TimelineWidget()
    widget.set_duration(100.0)
    widget.canvas.set_zoom(10.0)
    widget.set_current_time(5.0, is_playing=True)

    widget.btn_follow.click()
    assert widget.canvas.follow_playhead_enabled is False
    widget.canvas.scroll_horizontally(30.0, user_initiated=True)
    manual_offset = widget.canvas.scroll_offset
    widget.set_current_time(50.0, is_playing=True)
    assert widget.canvas.scroll_offset == manual_offset

    widget.btn_follow.click()
    assert widget.canvas.follow_playhead_enabled is True
    assert widget.canvas.scroll_offset <= 50.0 <= widget.canvas.scroll_offset + widget.canvas.zoom_seconds


def test_project_loader_sanitizes_malformed_optional_state():
    project = ProjectModel.from_dict({
        "title": None,
        "duration": "not-a-number",
        "aspect_ratio": "broken",
        "fps": "fast",
        "style": {"font_size": "large", "custom_singers": [None, {}]},
        "effects": {"brightness": "bright"},
        "overlay_objects": [None, {"type": "text"}],
        "album_audio_paths": [None, "song.mp3"],
        "language": "unknown",
    })
    assert project.title == "Untitled Project"
    assert project.duration == 42.0
    assert project.aspect_ratio == "16:9"
    assert project.fps == 30
    assert project.style["font_size"] == 32
    assert project.style["custom_singers"][0]["name"] == "Singer 1"
    assert project.overlay_objects == [{"type": "text"}]
    assert project.album_audio_paths == ["song.mp3"]
    assert project.language == "vi"


def test_project_restore_clears_previous_singers_cover_and_custom_templates():
    window = MainWindow()
    try:
        first = ProjectModel(title="First")
        first.style["custom_singers"] = [{"name": "Singer A", "color": "#123456"}]
        first.custom_templates = [{"id": "project_one_template", "name": "Project One"}]
        window.restore_project_state(first.to_dict())
        assert window.style_tab.custom_singers[0]["name"] == "Singer A"
        assert any(item.get("id") == "project_one_template" for _, item in window.templates_tab.cards)

        window.preview_widget.album_cover_pixmap = QPixmap(2, 2)
        second = ProjectModel(title="Second", aspect_ratio="4:5")
        window.restore_project_state(second.to_dict())
        assert window.style_tab.custom_singers == []
        assert window.preview_widget.album_cover_pixmap.isNull()
        assert not any(item.get("id") == "project_one_template" for _, item in window.templates_tab.cards)
        assert window.btn_aspect_45.isChecked()

        second.aspect_ratio = "21:9"
        window.restore_project_state(second.to_dict())
        assert window.btn_aspect_custom.isChecked()
        assert window.preview_widget.aspect_ratio == "21:9"
    finally:
        window.close()


def test_english_language_switch_updates_core_editing_chrome():
    window = MainWindow()
    try:
        window.set_language(1)
        assert window.project.language == "en"
        assert window.btn_nav_lyrics.text() == "📝 LYRICS"
        assert window.btn_export.text() == "🚀 Export Video"
        assert window.timeline_widget.btn_split.text() == "✂ Split"
        window.set_language(0)
        assert window.project.language == "vi"
        assert "LỜI" in window.btn_nav_lyrics.text()
    finally:
        window.close()


def test_eminem_rap_hiphop_album_template():
    preset = next((tpl for tpl in TEMPLATES_DATA if tpl.get("id") == "eminem_rap_hiphop_album"), None)
    assert preset is not None
    assert preset.get("template_variant") == "eminem_rap_hiphop_album"
    assert preset.get("font_family") == "Impact"

    lines = [
        LyricLine(0.0, 3.0, raw_text="Lose Yourself in the music"),
        LyricLine(3.0, 6.0, raw_text="The moment you own it you never let it go"),
    ]
    style = dict(preset)
    frame = VideoRenderer.render_frame(Image.new("RGB", (1280, 720), (0, 0, 0)), lines, 1.5, 6.0, style)
    assert frame.size == (1920, 1080)
