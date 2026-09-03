"""
Lylis Karaoke Studio - Desktop Application Entry Point
"""
import sys
import os
import time
import traceback

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_crash_logger():
    """Ensure any unhandled exception anywhere in Python or Qt slots is logged."""
    def excepthook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(f"\n[FATAL ERROR]\n{tb_text}", file=sys.stderr, flush=True)
        print(f"\n[FATAL ERROR]\n{tb_text}", file=sys.stdout, flush=True)

        try:
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n=== Crash at {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                f.write(tb_text + "\n")
        except Exception:
            pass

    sys.excepthook = excepthook

setup_crash_logger()

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from gui.main_window import MainWindow
from core.cache_manager import CacheManager

def main():
    try:
        # Auto clean stale cache files on startup
        try:
            CacheManager.auto_clean_on_start()
        except Exception as e:
            print(f"[Startup Warning] Cache cleanup error: {e}", file=sys.stderr)

        # Enable High DPI scaling safely
        try:
            if hasattr(Qt, 'AA_EnableHighDpiScaling'):
                QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
            if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
                QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        except Exception:
            pass

        app = QApplication(sys.argv)
        app.setApplicationName("Lylis Karaoke Studio")
        app.setStyle("Fusion")

        window = MainWindow()
        window.show()

        exit_code = app.exec_()
        sys.exit(exit_code)
    except Exception as exc:
        tb_text = traceback.format_exc()
        print(f"\n[Application Exception]\n{tb_text}", file=sys.stderr, flush=True)
        print(f"\n[Application Exception]\n{tb_text}", file=sys.stdout, flush=True)
        try:
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n=== Crash at {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                f.write(tb_text + "\n")
        except Exception:
            pass
        sys.exit(1)

if __name__ == '__main__':
    main()
