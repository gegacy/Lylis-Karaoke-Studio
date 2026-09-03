# 🎤 Lylis Karaoke Studio (Python 3.12 & PyQt5 Desktop)

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-green.svg?logo=qt&logoColor=white)](https://pypi.org/project/PyQt5/)
[![FFmpeg](https://img.shields.io/badge/Render-FFmpeg_1080p-orange.svg?logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](#)
[![Status](https://img.shields.io/badge/Build-52%2F52%20Tests%20Passing-brightgreen.svg)](#)

A professional, high-performance standalone Desktop Karaoke & Lyric Video Creation Studio built with **Python 3.12** and **PyQt5**. Engineered for precision syllable-level synchronization, 60 FPS sub-pixel text rendering, CapCut-style multi-track timeline editing, and background 1080p Full HD video export with audio muxing.

---

## 🌟 Key Features

### 1. 🎵 Precision Word-Level LRC Synchronizer & Tap-to-Sync
- **Lylis Syllable Syntax**: Enhanced word-by-word timestamps compatible with professional karaoke systems:
  ```lrc
  [00:02.50](00:02.50)Nhân (00:03.10)duyên (00:03.60)phải (00:04.20)kiếm {singer:male}
  [00:05.80](00:05.80)Mà (00:06.30)làm (00:06.80)anh (00:07.40)nhớ (00:08.00)ánh (00:08.50)mắt (00:09.10)đầu {singer:female}
  ```
- **⏰ Real-Time Tap-to-Sync (Spacebar Mode)**: Tap the spacebar in real time as audio plays to mark word transitions with previous, current, and upcoming syllable cues.
- **Import & Export**: Seamlessly import and export `.LRC` (standard & enhanced word-by-word), SubRip `.SRT` (HTML tag stripping supported), `.ASS`, and plain `.TXT`.

---

### 2. ⚡ 60 FPS Dual-Line Karaoke Canvas Engine
- **Sub-Pixel Text Sweep Animation**:
  $$\text{progress} = \max\left(0.0, \min\left(1.0, \frac{\text{currentTime} - \text{word.startTime}}{\text{word.endTime} - \text{word.startTime}}\right)\right)$$
- **Alternating Dual-Line Staggering**:
  - **Slot 0 (Top)**: Dedicated to even lines (0, 2, 4...) with a 2.0s lead-in.
  - **Slot 1 (Bottom)**: Dedicated to odd lines (1, 3, 5...) appearing as Slot 0 starts singing.
  - **Clean Intro & Interludes**: Automatically keeps canvas clean during instrumental music intros and guitar solos.
- **Layout & Typography Options**:
  - **`Trái - Phải` (Staggered Left-Right)**: Slot 0 aligned left, Slot 1 aligned right.
  - **`Căn giữa` (Centered)**: Centered layout for both lines.
  - **`Đơn dòng` (Single Line)** & **`Từng chữ` (Build Mode)**.
- **Visual Stylings**:
  - Customizable stroke width (2–10px), soft multi-layer drop shadows, golden glow aura, and font weight up to 900 (Black).
  - Retro singer avatars (`👤 Nam`, `👤 Nữ`, `🎤 Song Ca`) and microphone pointer animations.
  - Full Vietnamese Unicode diacritics support (`ă`, `â`, `đ`, `ê`, `ô`, `ơ`, `ư`).

---

### 3. 🎬 CapCut-Style 7-Layer Sequencer Timeline
- **Track Hierarchy**:
  - **Layer 7**: **Word Syllables** (Interactive purple syllable chips with live audio playhead tracking).
  - **Layer 6**: Secondary Lyric Cues.
  - **Layer 5**: Subtitle Tracks.
  - **Layer 4**: Lower Thirds & Overlays.
  - **Layer 3**: **Lyric Lines** (Orange clip blocks with interactive edge trimming).
  - **Layer 2**: **Media Clips** (Video and image assets with draggable durations).
  - **Layer 1**: **Audio Track & Waveform** (Decibel amplitude peak visualization).
- **Pro Editing Capabilities**:
  - **Interactive Trimming**: Left/right edge drag handles with `SizeHorCursor` and live timecode badges (`00:23 (+1.40s)`).
  - **Magnetic Snapping**: Snap to playhead, adjacent clip boundaries, and detected beat markers with cyan guide lines.
  - **Clip Drag & Move**: Smooth repositioning with `OpenHand` / `ClosedHand` cursor feedback.
  - **Unified & Ripple Delete**: Delete single clips or ripple-shift trailing clips automatically (`Shift+Delete`).
  - **Split & Duplicate**: Split clips at playhead (`S` or `Ctrl+B`) and instant cloning (`Ctrl+D`).
  - **Copy & Paste**: Clipboard buffer supporting multi-clip copy (`Ctrl+C`) and paste at playhead (`Ctrl+V`).
  - **Multi-Selection**: Marquee bounding box selection and right-click Context Menu.

---

### 4. 🤖 AI & Intelligent Lyric Services
- **Google Gemini 2.5 / 1.5 Integration**:
  - Auto-extract lyrics directly from song audio or YouTube links.
  - Automatic Duet Role Detection (`Nam` / `Nữ` / `Song Ca`) for every line.
- **Local Whisper Transcription**:
  - On-device vocal recognition and word boundary alignment via `faster-whisper`.
- **One-Click Auto Editor (`AUTO EDIT`)**:
  - Automatic silence trimming, beat detection, and beat-snapped line synchronization.

---

### 5. 🎨 12-Preset Template Gallery
One-click complete visual styling packages:
- **Tiki Tiki Sunset**: Warm centered golden script on paper field with singer portrait cards.
- **Walters Lyric Queue**: Frosted vertical glass list with active line magnifying lens.
- **Ambient Album Player**: Circular rotating vinyl with glowing ambient backlight.
- **Multi-Song Album Player**: CD jewel-case cover art with interactive track selector.
- **K-Sector 2000s (Y2K Editorial)**: Retro magazine layout with singer headers.
- **Falling You Douyin DJ**: Vinyl player with dancing neon stereo equalizer.
- **Eminem Rap & Hip-Hop**: Heavy bold uppercase typography with LED stereo bars and parental advisory badge.
- **Ballad, Lofi, Acoustic, EDM, Retro, Modern & Vertical (9:16)**.

---

### 6. 📦 1080p MP4 Video Exporter
- High-efficiency frame-by-frame rendering powered by `imageio_ffmpeg` and `Pillow`.
- Multi-threaded background `QThread` rendering with progress percentage and remaining time estimation.
- Lossless audio muxing into standard H.264 / AAC MP4 video.
- Aspect ratio selection: `📱 9:16 (TikTok/Reels)`, `🖥️ 16:9 (YouTube)`, `⏹ 1:1 (Square)`.

---

## ⌨️ Keyboard Shortcuts Cheatsheet

| Shortcut | Action |
|---|---|
| <kbd>Space</kbd> | Play / Pause playback |
| <kbd>S</kbd> or <kbd>Ctrl</kbd>+<kbd>B</kbd> | **Split** clip at playhead |
| <kbd>Ctrl</kbd>+<kbd>D</kbd> | **Duplicate** selected clip |
| <kbd>Ctrl</kbd>+<kbd>C</kbd> | **Copy** selected clip(s) |
| <kbd>Ctrl</kbd>+<kbd>V</kbd> | **Paste** clip(s) at playhead |
| <kbd>Del</kbd> / <kbd>Backspace</kbd> | **Delete** selected clip(s) |
| <kbd>Shift</kbd>+<kbd>Delete</kbd> | **Ripple Delete** (delete & shift trailing clips) |
| <kbd>Ctrl</kbd>+<kbd>Z</kbd> | **Undo** |
| <kbd>Ctrl</kbd>+<kbd>Y</kbd> | **Redo** |
| <kbd>Ctrl</kbd>+<kbd>O</kbd> | **Open Project** (`.lylis.json`) |
| <kbd>Ctrl</kbd>+<kbd>S</kbd> | **Save Project** |
| <kbd>Ctrl</kbd>+<kbd>E</kbd> | **Export Video** dialog |

---

## 🚀 Installation & Quick Start

### 1. Prerequisites
- **Python 3.10+** (Python 3.12 recommended)
- **FFmpeg** (installed automatically via `imageio-ffmpeg` or system PATH)

### 2. Install Dependencies
```bash
git clone https://github.com/gegacy/Lylis-Karaoke-Studio.git
cd Lylis-Karaoke-Studio
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python main.py
```
*Or double-click `run.bat` on Windows for zero-config launcher with automatic environment detection.*

---

## 📂 Project Architecture

```
Lylis-Karaoke-Studio/
├── main.py                     # High-DPI Desktop application entry point
├── run.bat                     # Windows 1-click launcher script
├── requirements.txt            # Python dependencies
├── README.md                   # Application documentation
├── .gitignore                  # Git ignore rules for Python & PyQt5
│
├── assets/                     # Media assets
│   ├── icons/                  # Modern & retro singer badges
│   ├── sample_audio.wav        # Acoustic sample audio track
│   └── sample_bg.jpg           # Default studio backdrop
│
├── core/                       # Audio/Video & Core Business Logic
│   ├── lrc_engine.py           # Word-level LRC/SRT parser & serializer
│   ├── audio_engine.py         # Pygame mixer, pitch/tempo, waveform extraction
│   ├── video_renderer.py       # 1080p MP4 rendering engine & audio muxer
│   ├── auto_editor.py          # Auto-sync, beat detection, silence trimming
│   ├── project_model.py        # Project state serialization & schema
│   ├── undo_manager.py         # Multi-step Undo/Redo command stack
│   ├── cache_manager.py        # Stale cache cleanup & temp management
│   └── ai/
│       ├── gemini_service.py   # Google Gemini AI lyric extraction & role detection
│       ├── voice_detector.py   # Audio alignment & voice activity detection
│       └── faster_whisper_service.py # Local whisper transcription worker
│
├── gui/                        # PyQt5 User Interface
│   ├── main_window.py          # Master window, menus, toolbar & shortcuts
│   ├── preview_widget.py       # 60 FPS QPainter karaoke preview canvas
│   ├── timeline_widget.py      # CapCut multi-track timeline sequencer
│   ├── inspector_panel.py      # Property inspector for selected elements
│   ├── tap_sync_dialog.py      # Spacebar Tap-to-Sync dialog
│   ├── export_dialog.py        # Background MP4 export worker dialog
│   ├── gemini_dialog.py        # AI lyric extraction & duet detection dialog
│   └── tabs/
│       ├── lyrics_tab.py       # LRC text editor, sync triggers, import/export
│       ├── media_tab.py        # Media & audio asset management
│       ├── style_tab.py        # Font, colors, layout modes, singer config
│       ├── elements_tab.py     # Particles, visualizer, watermark
│       ├── effects_tab.py      # Color grading, brightness, contrast
│       ├── transitions_tab.py  # Scene transitions (Fade, Slide, Zoom)
│       └── templates_tab.py    # 12-preset visual template gallery
│
└── tests/                      # Automated Test Suite (52 Unit/Integration Tests)
    ├── test_all_features.py
    ├── test_integration_regressions.py
    └── test_ai_analysis_regressions.py
```

---

## 🧪 Running Automated Tests

Run the complete test suite with `pytest`:
```bash
python -m pytest tests -v
```

All 52 unit and regression tests run offline without external API dependencies.

---

## 📄 License

Proprietary software developed by **gegacy**. All rights reserved.
