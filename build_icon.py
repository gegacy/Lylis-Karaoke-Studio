"""
Build script for Lylis Karaoke Studio application icons.
Converts the master PNG/source image into multi-resolution Windows ICO and PNG assets.
"""
import os
import sys
from PIL import Image

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
SOURCE_PNG = os.path.join(ASSETS_DIR, "app_icon.png")
OUTPUT_ICO = os.path.join(ASSETS_DIR, "app_icon.ico")

SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

def build_icons():
    print("=" * 60)
    print("   Lylis Karaoke Studio - Icon Asset Generator")
    print("=" * 60)
    
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    if not os.path.exists(SOURCE_PNG):
        print(f"[ERROR] Source image not found at: {SOURCE_PNG}")
        sys.exit(1)
        
    print(f"Loading master image: {SOURCE_PNG}")
    img = Image.open(SOURCE_PNG).convert("RGBA")
    print(f"Master image dimensions: {img.width}x{img.height}")
    
    # Save multi-size ICO
    print(f"Generating multi-resolution Windows ICO ({len(SIZES)} sizes: {SIZES})...")
    img.save(OUTPUT_ICO, format="ICO", sizes=SIZES)
    ico_size = os.path.getsize(OUTPUT_ICO)
    print(f"[OK] Saved Windows icon: {OUTPUT_ICO} ({ico_size:,} bytes)")
    
    # Verify with PyQt5 if available
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QIcon
        app = QApplication.instance() or QApplication(sys.argv)
        qicon = QIcon(OUTPUT_ICO)
        if not qicon.isNull():
            print("[OK] Verified: PyQt5 QIcon successfully loaded the generated ICO file.")
        else:
            print("[WARNING] PyQt5 loaded QIcon as null.")
    except Exception as e:
        print(f"[INFO] PyQt5 verification skipped ({e})")
        
    print("\nIcon assets generated successfully!")

if __name__ == "__main__":
    build_icons()
