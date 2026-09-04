# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for Lylis Karaoke Studio.
Builds standalone Windows desktop application with custom app icon, bundled FFmpeg, and design license.
"""
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

BASE_DIR = os.path.abspath(SPECPATH)

datas = [
    (os.path.join(BASE_DIR, 'assets'), 'assets'),
]

# Include LICENSE in root of build output if present
lic_file = os.path.join(BASE_DIR, 'LICENSE')
if os.path.exists(lic_file):
    datas.append((lic_file, '.'))

# Collect data files for imageio_ffmpeg (bundles ffmpeg.exe binary) and pygame
try:
    datas += collect_data_files('imageio_ffmpeg')
except Exception as e:
    print(f"[Warning] collect_data_files('imageio_ffmpeg') failed: {e}")

try:
    datas += collect_data_files('pygame')
except Exception as e:
    print(f"[Warning] collect_data_files('pygame') failed: {e}")

hiddenimports = [
    'PyQt5',
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'pygame',
    'pygame.mixer',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'imageio',
    'imageio_ffmpeg',
    'numpy',
    'core',
    'core.paths',
    'core.sample_data',
    'core.lrc_engine',
    'core.ass_generator',
    'core.audio_engine',
    'core.video_renderer',
    'core.auto_editor',
    'core.project_model',
    'core.undo_manager',
    'core.cache_manager',
    'gui',
    'gui.license_dialog',
    'gui.preview_widget',
    'gui.timeline_widget',
    'gui.inspector_panel',
    'gui.tap_sync_dialog',
    'gui.export_dialog',
    'gui.style_theme',
    'gui.tabs.media_tab',
    'gui.tabs.lyrics_tab',
    'gui.tabs.style_tab',
    'gui.tabs.elements_tab',
    'gui.tabs.effects_tab',
    'gui.tabs.transitions_tab',
    'gui.tabs.templates_tab',
]

excludes = [
    'tkinter', 'matplotlib', 'scipy', 'pandas', 'IPython',
    'torch', 'torchvision', 'torchaudio', 'transformers', 'datasets', 'pyarrow',
    'tensorflow', 'tensorboard', 'onnx', 'onnxruntime', 'cv2', 'sklearn', 'scikit-learn',
    'dask', 'numba', 'llvmlite', 'pytest', '_pytest', 'unittest',
    'fsspec', 'uvicorn', 'websockets', 'pydub', 'librosa', 'sqlalchemy'
]

a = Analysis(
    ['main.py'],
    pathex=[BASE_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LylisKaraokeStudio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed application (no console popup)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(BASE_DIR, 'assets', 'app_icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LylisKaraokeStudio',
)
