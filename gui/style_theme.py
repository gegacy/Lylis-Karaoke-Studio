"""
Lylis Karaoke Studio - Exact Reference Studio Theme (Modern Light Workspace + Clean Controls)
"""

DARK_THEME_QSS = """
/* ==========================================================================
   GLOBAL WINDOW & TYPOGRAPHY
   ========================================================================== */
QMainWindow {
    background-color: #f1f3f9;
}

QWidget {
    color: #1e293b;
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 13px;
}

/* Tooltips */
QToolTip {
    background-color: #1e293b;
    color: #ffffff;
    border: 1px solid #334155;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
}

/* Splitters */
QSplitter::handle {
    background-color: #e2e8f0;
    width: 1px;
    height: 1px;
}
QSplitter::handle:hover {
    background-color: #ff2d55;
}

/* ==========================================================================
   CARDS & GROUP BOXES
   ========================================================================== */
QGroupBox {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    background-color: #ffffff;
    margin-top: 14px;
    padding: 14px 12px 12px 12px;
    font-weight: 700;
    font-size: 11px;
    color: #0f172a;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: 3px;
    padding: 0 6px;
    color: #ff2d55;
    background-color: #ffffff;
    border-radius: 4px;
    border: 1px solid #e2e8f0;
}

/* ==========================================================================
   BUTTONS
   ========================================================================== */
QPushButton {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 12px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #f8fafc;
    border-color: #94a3b8;
    color: #0f172a;
}

QPushButton:pressed {
    background-color: #f1f5f9;
}

QPushButton:disabled {
    background-color: #f8fafc;
    color: #94a3b8;
    border-color: #e2e8f0;
}

/* Primary Coral Button */
QPushButton.primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff2d55, stop:1 #ff5277);
    color: #ffffff;
    border: none;
    font-weight: 700;
    padding: 7px 16px;
    border-radius: 6px;
}

QPushButton.primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff476d, stop:1 #ff6b8b);
}

/* ==========================================================================
   INPUTS & TEXT EDITORS
   ========================================================================== */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    selection-background-color: #ff2d55;
    selection-color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #ff2d55;
    background-color: #ffffff;
}

/* ==========================================================================
   COMBOBOX
   ========================================================================== */
QComboBox {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
    font-weight: 600;
}

QComboBox:hover {
    border-color: #94a3b8;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #cbd5e1;
    selection-background-color: #ff2d55;
    selection-color: #ffffff;
    padding: 4px;
    border-radius: 6px;
    outline: none;
}

/* ==========================================================================
   SLIDERS (Fixed Qt Cross-Platform Rendering)
   ========================================================================== */
QSlider:horizontal {
    min-height: 20px;
}

QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background: #e2e8f0;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #ff2d55;
    border-radius: 2px;
}

QSlider::add-page:horizontal {
    background: #e2e8f0;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #ff2d55;
    border: 2px solid #ffffff;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}

QSlider::handle:horizontal:hover {
    background: #ff476d;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

/* ==========================================================================
   CHECKBOXES
   ========================================================================== */
QCheckBox {
    color: #334155;
    spacing: 9px;
    font-size: 12px;
    font-weight: 500;
}

/* ==========================================================================
   SCROLLBARS
   ========================================================================== */
QScrollBar:vertical {
    background: #f1f5f9;
    width: 6px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 20px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #f1f5f9;
    height: 6px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #cbd5e1;
    min-width: 20px;
    border-radius: 3px;
}

QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

"""
