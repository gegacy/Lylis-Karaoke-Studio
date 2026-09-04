"""
Lylis Karaoke Studio - Unified Path & Environment Resolver
Handles asset location, writable user directories, and runtime resolution
for both standard Python development mode and PyInstaller frozen executables.
"""
import os
import sys
from typing import Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_app_root() -> str:
    """
    Returns the root directory of the application.
    Supports PyInstaller frozen builds (sys._MEIPASS and sys.executable)
    as well as standard development environment.
    """
    if getattr(sys, "frozen", False):
        # In PyInstaller, check MEIPASS first, fallback to executable dir
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass and os.path.isdir(meipass):
            return meipass
        return os.path.dirname(sys.executable)
    return _PROJECT_ROOT

def get_asset_path(*subpaths: str) -> str:
    """
    Resolve path to an asset file or folder.
    Checks frozen PyInstaller bundles, executable directory, and source assets.
    """
    candidate_roots = []
    
    # 1. PyInstaller unpack directory
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidate_roots.append(os.path.join(meipass, "assets"))
        candidate_roots.append(os.path.join(os.path.dirname(sys.executable), "assets"))
        # PyInstaller 6 _internal directory
        candidate_roots.append(os.path.join(os.path.dirname(sys.executable), "_internal", "assets"))
    
    # 2. Project root assets
    candidate_roots.append(os.path.join(_PROJECT_ROOT, "assets"))
    
    for root in candidate_roots:
        target = os.path.join(root, *subpaths) if subpaths else root
        if os.path.exists(target):
            return os.path.abspath(target)
            
    # Fallback to default primary location even if not yet existing (e.g. creating a new sample)
    primary = os.path.join(candidate_roots[-1], *subpaths) if subpaths else candidate_roots[-1]
    return os.path.abspath(primary)

def get_user_data_dir() -> str:
    """
    Returns a guaranteed-writable user data directory.
    On Windows: %APPDATA%/LylisKaraokeStudio
    On other platforms: ~/.lylis_karaoke_studio
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        data_dir = os.path.join(base, "LylisKaraokeStudio")
    else:
        data_dir = os.path.join(os.path.expanduser("~"), ".lylis_karaoke_studio")
    try:
        os.makedirs(data_dir, exist_ok=True)
    except Exception:
        pass
    return data_dir

def get_safe_writable_path(filename: str) -> str:
    """
    Returns a writable file path. First checks if app root is writable,
    otherwise falls back to user data directory.
    """
    app_root = get_app_root()
    test_path = os.path.join(app_root, filename)
    try:
        # Check if we can write to app root
        with open(test_path, "a", encoding="utf-8") as _:
            pass
        return test_path
    except (OSError, PermissionError):
        # Read-only directory (e.g., Program Files), fallback to user data dir
        return os.path.join(get_user_data_dir(), filename)
