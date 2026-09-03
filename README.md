# Lylis Karaoke Studio (Python & PyQt5 Desktop)

A professional, high-performance standalone Desktop Karaoke & Lyric Video Synchronizer application built with **Python 3.12** and **PyQt5**.

---

## 🌟 Key Features

1. **Word-Level LRC Synchronizer & Tap-to-Sync**:
   - Enhanced word-by-word timestamps matching Lylis syntax: `[00:28.84](00:28.84)Chiếc (00:29.12)nón (00:29.42)ba (00:29.79)tầm...`
   - **`⏰ Tạo thời gian LRC` (Spacebar Mode)**: Tap the spacebar in real time as the audio plays to record word timestamps with visual previous/current/next word cues.
   - Import & Export `.LRC`, `.SRT`, and `.TXT` lyrics.

2. **Dual-Line Karaoke Engine (60 FPS `QPainter` Canvas)**:
   - Progressive sub-pixel text clipping sweep:
     $$\text{progress} = \max\left(0.0, \min\left(1.0, \frac{\text{currentTime} - \text{word.startTime}}{\text{word.endTime} - \text{word.startTime}}\right)\right)$$
   - Dual-line layout modes:
     - **`Trái phải` (Staggered Left-Right)**: Line 0 at top slot ($Y=66\%$, left-aligned), Line 1 at bottom slot ($Y=78\%$, right-aligned).
     - **`Căn giữa` (Centered)**: Both lines centered at $66\%$ and $78\%$.
   - Style presets: *Classic Blue/Cyan, Gold Glow, Neon Pink, Emerald Mint, Custom*.
   - Outer outline stroke (3-8px), drop shadow, and full Vietnamese Unicode diacritics support (`ă`, `â`, `đ`, `ê`, `ô`, `ơ`, `ư`).
   - Aspect ratio selector: `📱 9:16`, `🖥️ 16:9`, `⏹ 1:1`.

3. **7-Layer Sequencer Timeline**:
   - `Layer 8`: FX & Overlays
   - `Layer 7`: **Word Syllables** (Purple chips with live active highlighting)
   - `Layer 6`: Lyric Lines (Blue bars)
   - `Layer 5 & 4`: Elements & Visual Effects
   - `Layer 3`: Background Media (Orange video/image track)
   - `Layer 2`: Audio Track & Amplitude Peaks (Green waveform track)
   - Draggable red playhead scrubber line + Zoom slider (`5s`–`60s`).

4. **1080p MP4 Video Exporter**:
   - Offline 1080p Full HD video rendering using `imageio_ffmpeg` and `PIL` with audio muxing in a background `QThread`.

5. **12-Preset Template Gallery**:
   - Includes a warm, centered sunset lyric preset inspired by the supplied Riptide reference, plus duet, ballad, acoustic, EDM, lofi, retro, modern, and vertical short-form designs.
   - Presets apply typography, layout, colors, motion, grading, particles, vignette, glow, visualizer, and pointer settings as one complete look.

---

## 🚀 Installation & Launch

### 1. Requirements
- Python 3.10+ (Python 3.12 recommended)
- Dependencies in `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Launch Application

Run directly in terminal:
```bash
python main.py
```

Or double-click [run.bat](file:///d:/New%20folder%20(76)/run.bat) on Windows.

`run.bat` automatically uses `python`, the Windows `py` launcher, or `uv` (in that order).

### Project workflow

- Use **Mở / Ctrl+O** and **Lưu / Ctrl+S** for complete `.lylis.json` project files.
- Preview, timeline, project persistence, and MP4 export share the same style, effects, transitions, overlays, singer roles, aspect ratio, and media state.
- Audio pitch, tempo, and center-vocal reduction are processed into a temporary preview mix; tempo changes also rescale lyric timing to remain synchronized.

---

## 📂 Project Architecture

```
d:/New folder (76)/
├── main.py                     # High-DPI Desktop entry point (Fusion Style)
├── run.bat                     # Windows 1-Click launcher
├── requirements.txt            # Python dependencies
├── README.md                   # Application documentation
├── assets/                     # Sample audio & background images
├── core/
│   ├── lrc_engine.py           # Word-by-word synced LRC & SRT parser/serializer
│   ├── audio_engine.py         # Pygame mixer audio engine with waveform extraction
│   ├── sample_data.py          # Preloaded Vietnamese ballad & acoustic sample generator
│   └── video_renderer.py       # 1080p MP4 renderer with audio muxing
└── gui/
    ├── main_window.py          # Studio controller (Aspect Ratio, Toolbar, Tabs, Scrubber)
    ├── preview_widget.py       # 60 FPS QPainter canvas with word-by-word sweeping wipe
    ├── timeline_widget.py      # 7-Layer sequencer with zoom slider & playhead
    ├── tap_sync_dialog.py      # Spacebar real-time Tap-to-Sync recorder
    ├── export_dialog.py        # Background MP4 video export worker
    └── tabs/
        ├── media_tab.py        # Media & audio asset management
        ├── lyrics_tab.py       # LRC text editor, sync triggers, import/export
        ├── style_tab.py        # Font styling, weights, layout modes, wipe colors
        └── elements_tab.py     # Waveform visualizer, particles, watermark
```
